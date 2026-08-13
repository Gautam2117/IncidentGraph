import logging
import time
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.eval_models import ScenarioRun as DBScenarioRun
from app.scenarios.registry import get_scenario
from app.scenarios.runtime import (
    build_fault_config,
    build_probe_request,
    get_business_endpoint,
    get_service_url,
)
from app.scenarios.schema import ScenarioRun, ScenarioRunState

logger = logging.getLogger(__name__)


async def trigger_scenario(session: AsyncSession, scenario_id: str) -> ScenarioRun:
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario '{scenario_id}' not found in registry")

    db_run = DBScenarioRun(
        scenario_id=scenario_id,
        status=ScenarioRunState.TRIGGERED.value,
    )
    session.add(db_run)
    await session.commit()
    await session.refresh(db_run)

    run = ScenarioRun(
        run_id=str(db_run.id),
        scenario_id=scenario_id,
        state=ScenarioRunState.TRIGGERED,
        fault_started_at=datetime.now(UTC).isoformat(),
    )

    target_service = scenario.target_service
    service_url = get_service_url(target_service)
    endpoint = get_business_endpoint(target_service)
    fault_config = build_fault_config(scenario)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            ack = await client.post(
                f"{service_url}/faults",
                params={"endpoint": endpoint},
                json=fault_config,
            )
            ack.raise_for_status()
            run.fault_ack = True

            probe_started = time.perf_counter()
            probe = await client.post(
                f"{service_url}{endpoint}",
                json=build_probe_request(target_service),
            )
            run.probe_latency_ms = round(
                (time.perf_counter() - probe_started) * 1000,
                2,
            )
            run.probe_status_code = probe.status_code

            marker_only = fault_config["fault_kind"] == "marker_only"
            expected_latency = float(fault_config["latency_ms"])
            expects_failure = bool(
                fault_config["pool_exhaustion"]
                or fault_config["timeout"]
                or float(fault_config["error_rate"]) > 0
            )
            if marker_only and probe.status_code >= 400:
                raise RuntimeError("Harmless scenario unexpectedly degraded the service")
            if expects_failure and probe.status_code < 400:
                raise RuntimeError("Injected failure did not affect the business request")
            if expected_latency > 0 and (
                run.probe_latency_ms is None or run.probe_latency_ms < expected_latency * 0.8
            ):
                raise RuntimeError("Injected latency signature was not observed")

            if scenario_id == "recovered_before_investigation":
                clear = await client.post(
                    f"{service_url}/faults",
                    params={"endpoint": endpoint},
                    json={**fault_config, "enabled": False},
                )
                clear.raise_for_status()
        run.state = ScenarioRunState.RUNNING
        db_run.status = run.state.value
        await session.commit()
    except Exception as e:
        logger.error(f"Could not contact {target_service} to inject fault: {e}")
        run.state = ScenarioRunState.FAILED
        run.error_message = str(e)
        db_run.status = run.state.value
        await session.commit()
        raise RuntimeError(f"Failed to inject fault into {target_service}: {e}") from e

    return run


async def reset_scenario(session: AsyncSession, scenario_id: str) -> ScenarioRun:
    stmt = (
        select(DBScenarioRun)
        .where(DBScenarioRun.scenario_id == scenario_id)
        .order_by(DBScenarioRun.created_at.desc())
    )
    result = await session.execute(stmt)
    db_run = result.scalars().first()

    if not db_run:
        db_run = DBScenarioRun(scenario_id=scenario_id, status=ScenarioRunState.IDLE.value)
        session.add(db_run)
        await session.commit()
        await session.refresh(db_run)

    run = ScenarioRun(run_id=str(db_run.id), scenario_id=scenario_id)

    scenario = get_scenario(scenario_id)
    if scenario:
        target_service = scenario.target_service
        service_url = get_service_url(target_service)
        endpoint = get_business_endpoint(target_service)

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(
                    f"{service_url}/faults",
                    params={"endpoint": endpoint},
                    json={
                        **build_fault_config(scenario),
                        "enabled": False,
                        "latency_ms": 0.0,
                        "error_rate": 0.0,
                        "pool_exhaustion": False,
                        "timeout": False,
                    },
                )
                res.raise_for_status()
        except Exception as e:
            logger.error(f"Could not contact {target_service} to clear fault: {e}")
            run.state = ScenarioRunState.FAILED
            run.error_message = str(e)
            db_run.status = run.state.value
            await session.commit()
            raise RuntimeError(f"Failed to clear fault from {target_service}: {e}") from e

    run.state = ScenarioRunState.CLEANED_UP
    run.fault_ended_at = datetime.now(UTC).isoformat()
    db_run.status = run.state.value
    await session.commit()
    return run


async def get_scenario_run(session: AsyncSession, scenario_id: str) -> ScenarioRun | None:
    stmt = (
        select(DBScenarioRun)
        .where(DBScenarioRun.scenario_id == scenario_id)
        .order_by(DBScenarioRun.created_at.desc())
    )
    result = await session.execute(stmt)
    db_run = result.scalars().first()
    if not db_run:
        return None
    return ScenarioRun(
        run_id=str(db_run.id),
        scenario_id=db_run.scenario_id,
        state=ScenarioRunState(db_run.status),
        created_at=db_run.created_at.isoformat(),
    )
