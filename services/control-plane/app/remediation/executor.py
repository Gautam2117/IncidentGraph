import time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RemediationPlan, RemediationStep
from app.db.models.remediation_models import (
    RemediationExecution as DBRemediationExecution,
)
from app.db.models.remediation_models import RemediationPlan as DBRemediationPlan
from app.scenarios.runtime import (
    build_probe_request,
    get_business_endpoint,
    get_service_url,
)
from app.services.incident_service import add_incident_event

ALLOWED_ACTIONS = frozenset(
    {
        "scale_pool",
        "restart_service",
        "rollback_deploy",
        "reset_circuit_breaker",
        "flush_cache",
    }
)
ALLOWED_SERVICES = frozenset(
    {"gateway", "auth", "orders", "payments", "inventory", "notifications"}
)


class ActionParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: str | None = None


class ScalePoolParameters(ActionParameters):
    max_connections: int = Field(default=20, ge=1, le=200)


class RollbackParameters(ActionParameters):
    version: str = Field(default="previous", min_length=1, max_length=64, pattern=r"^[\w.-]+$")


PARAMETER_SCHEMAS: dict[str, type[ActionParameters]] = {
    "scale_pool": ScalePoolParameters,
    "restart_service": ActionParameters,
    "rollback_deploy": RollbackParameters,
    "reset_circuit_breaker": ActionParameters,
    "flush_cache": ActionParameters,
}


class TelemetrySnapshot(BaseModel):
    service: str
    status_code: int | None = None
    latency_ms: float
    healthy: bool
    error: str | None = None


class ExecutionStepResult(BaseModel):
    step_number: int
    action_type: str
    target_service: str
    success: bool
    message: str
    dry_run: bool = False
    backend_acknowledged: bool = False


class RemediationExecutionResult(BaseModel):
    plan_id: str
    incident_id: str
    success: bool
    dry_run: bool
    step_results: list[ExecutionStepResult] = Field(default_factory=list)
    verification_passed: bool = False
    before_telemetry: TelemetrySnapshot | None = None
    after_telemetry: TelemetrySnapshot | None = None


def _validate_step(step: RemediationStep) -> ActionParameters:
    if step.action_type not in ALLOWED_ACTIONS:
        raise ValueError(
            f"Action '{step.action_type}' is forbidden. Arbitrary shell or exec actions are "
            "strictly prohibited."
        )
    if step.target_service not in ALLOWED_SERVICES:
        raise ValueError(f"Target service '{step.target_service}' is not in the sandbox allow-list")
    try:
        params = PARAMETER_SCHEMAS[step.action_type].model_validate(step.parameters)
    except ValidationError as exc:
        raise ValueError(f"Invalid parameters for action '{step.action_type}': {exc}") from exc
    if params.service is not None and params.service != step.target_service:
        raise ValueError("Parameter service must match the remediation target service")
    return params


async def capture_service_telemetry(target_service: str) -> TelemetrySnapshot:
    """Probe the real sandbox business endpoint and preserve observed recovery evidence."""
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(
                f"{get_service_url(target_service)}{get_business_endpoint(target_service)}",
                json=build_probe_request(target_service),
            )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return TelemetrySnapshot(
            service=target_service,
            status_code=response.status_code,
            latency_ms=latency_ms,
            healthy=response.status_code < 400,
        )
    except Exception as exc:
        return TelemetrySnapshot(
            service=target_service,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            healthy=False,
            error=type(exc).__name__,
        )


async def _clear_sandbox_fault(step: RemediationStep) -> None:
    """Trusted executor boundary: disable fault state through the bounded demo API."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{get_service_url(step.target_service)}/faults",
            params={"endpoint": get_business_endpoint(step.target_service)},
            json={
                "enabled": False,
                "scenario_id": f"remediation-{step.action_type}",
                "fault_kind": "remediation",
                "latency_ms": 0.0,
                "error_rate": 0.0,
                "pool_exhaustion": False,
                "timeout": False,
            },
        )
        response.raise_for_status()


async def execute_remediation_step(
    step: RemediationStep, dry_run: bool = False
) -> ExecutionStepResult:
    try:
        params = _validate_step(step)
    except ValueError as exc:
        return ExecutionStepResult(
            step_number=step.step_number,
            action_type=step.action_type,
            target_service=step.target_service,
            success=False,
            message=str(exc),
            dry_run=dry_run,
        )

    if dry_run:
        return ExecutionStepResult(
            step_number=step.step_number,
            action_type=step.action_type,
            target_service=step.target_service,
            success=True,
            message=(
                f"[DRY-RUN PREVIEW] Validated '{step.action_type}' with "
                f"parameters {params.model_dump(exclude_none=True)} for '{step.target_service}'."
            ),
            dry_run=True,
        )

    try:
        await _clear_sandbox_fault(step)
    except Exception as exc:
        return ExecutionStepResult(
            step_number=step.step_number,
            action_type=step.action_type,
            target_service=step.target_service,
            success=False,
            message=f"Sandbox remediation backend rejected '{step.action_type}': {type(exc).__name__}",
            backend_acknowledged=False,
        )

    return ExecutionStepResult(
        step_number=step.step_number,
        action_type=step.action_type,
        target_service=step.target_service,
        success=True,
        message=(
            f"Sandbox action '{step.action_type}' changed fault state for "
            f"'{step.target_service}' and was acknowledged by the service."
        ),
        backend_acknowledged=True,
    )


async def verify_post_remediation_health(target_service: str) -> bool:
    return (await capture_service_telemetry(target_service)).healthy


async def execute_remediation_plan(
    session: AsyncSession,
    plan: RemediationPlan,
    dry_run: bool = False,
) -> RemediationExecutionResult:
    if plan.requires_human_approval and not plan.approved and not dry_run:
        raise ValueError(
            f"Remediation plan '{plan.plan_id}' requires explicit human approval before execution."
        )

    target_service = plan.steps[0].target_service if plan.steps else None
    before = (
        await capture_service_telemetry(target_service) if target_service and not dry_run else None
    )
    step_results = [await execute_remediation_step(step, dry_run=dry_run) for step in plan.steps]
    steps_succeeded = bool(step_results) and all(result.success for result in step_results)
    after = (
        await capture_service_telemetry(target_service)
        if target_service and steps_succeeded and not dry_run
        else None
    )
    verification_passed = bool(after and after.healthy)
    overall_success = steps_succeeded and (dry_run or verification_passed)

    payload: dict[str, Any] = {
        "plan_id": plan.plan_id,
        "dry_run": dry_run,
        "success": overall_success,
        "verification_passed": verification_passed,
        "before_telemetry": before.model_dump() if before else None,
        "after_telemetry": after.model_dump() if after else None,
        "step_results": [result.model_dump() for result in step_results],
    }
    db_plan = await session.get(DBRemediationPlan, plan.plan_id)
    if db_plan is None:
        db_plan = DBRemediationPlan(
            id=plan.plan_id,
            incident_id=plan.incident_id,
            description="\n".join(step.description for step in plan.steps),
            requires_human_approval=plan.requires_human_approval,
            approved=plan.approved,
        )
        session.add(db_plan)
        await session.flush()
    session.add_all(
        [
            DBRemediationExecution(
                plan_id=plan.plan_id,
                action_type=result.action_type,
                target=result.target_service,
                parameters=next(
                    (
                        step.parameters
                        for step in plan.steps
                        if step.step_number == result.step_number
                    ),
                    {},
                ),
                status=(
                    "dry_run"
                    if dry_run
                    else "succeeded"
                    if result.success and verification_passed
                    else "failed"
                ),
                result_data={
                    "step": result.model_dump(mode="json"),
                    "verification_passed": verification_passed,
                    "before": before.model_dump(mode="json") if before else None,
                    "after": after.model_dump(mode="json") if after else None,
                },
            )
            for result in step_results
        ]
    )
    await session.commit()
    await add_incident_event(
        session=session,
        incident_id=plan.incident_id,
        event_type="remediation",
        actor="remediation_executor",
        title=f"Remediation Executed ({'DRY-RUN' if dry_run else 'LIVE'})",
        payload=payload,
    )

    return RemediationExecutionResult(
        plan_id=plan.plan_id,
        incident_id=plan.incident_id,
        success=overall_success,
        dry_run=dry_run,
        step_results=step_results,
        verification_passed=verification_passed,
        before_telemetry=before,
        after_telemetry=after,
    )
