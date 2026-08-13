import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RemediationPlan, RemediationStep
from app.db.models.remediation_models import RemediationExecution
from app.remediation.executor import execute_remediation_plan, verify_post_remediation_health
from app.remediation.review import HumanReviewDecision, submit_human_review
from app.services.incident_service import CreateIncidentRequest, create_incident


@pytest.mark.asyncio
async def test_human_review_approval_flow(db_session: AsyncSession) -> None:
    inc = await create_incident(
        db_session, CreateIncidentRequest(title="Remediation Test Incident", severity="high")
    )
    plan_id = "plan_test_001"

    rec = await submit_human_review(
        session=db_session,
        plan_id=plan_id,
        incident_id=inc.id,
        decision=HumanReviewDecision.APPROVE,
        reviewer="engineer_test",
        comments="Approved for off-peak execution",
    )

    assert rec.plan_id == plan_id
    assert rec.decision == HumanReviewDecision.APPROVE
    assert rec.reviewer == "engineer_test"


@pytest.mark.asyncio
async def test_remediation_dry_run_simulation(db_session: AsyncSession) -> None:
    inc = await create_incident(
        db_session, CreateIncidentRequest(title="Dry Run Test Incident", severity="medium")
    )
    plan = RemediationPlan(
        plan_id="plan_dry_001",
        incident_id=str(inc.id),
        steps=[
            RemediationStep(
                step_number=1,
                action_type="scale_pool",
                description="Scale connection pool to 20",
                target_service="inventory",
                parameters={"max_connections": 20},
            )
        ],
        requires_human_approval=True,
        approved=False,
    )

    # Dry-run execution should succeed even when unapproved
    res = await execute_remediation_plan(db_session, plan, dry_run=True)
    assert res.success is True
    assert res.dry_run is True
    assert len(res.step_results) == 1
    assert res.step_results[0].dry_run is True
    assert "[DRY-RUN PREVIEW]" in res.step_results[0].message
    persisted = await db_session.scalar(
        select(func.count(RemediationExecution.id)).where(
            RemediationExecution.plan_id == plan.plan_id
        )
    )
    assert persisted and persisted >= 1


@pytest.mark.asyncio
async def test_remediation_live_execution_and_verification(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    from unittest.mock import AsyncMock, MagicMock

    degraded = MagicMock(status_code=503)
    ack = MagicMock(status_code=200)
    recovered = MagicMock(status_code=200)
    healthy = MagicMock(status_code=200)
    mock_client = AsyncMock()
    mock_client.post.side_effect = [degraded, ack, recovered, healthy]
    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    monkeypatch.setattr("app.remediation.executor.httpx.AsyncClient", mock_client_class)

    inc = await create_incident(
        db_session, CreateIncidentRequest(title="Live Execution Test Incident", severity="high")
    )
    plan = RemediationPlan(
        plan_id="plan_live_001",
        incident_id=str(inc.id),
        steps=[
            RemediationStep(
                step_number=1,
                action_type="scale_pool",
                description="Scale inventory pod connections",
                target_service="inventory",
            )
        ],
        requires_human_approval=False,
        approved=True,
    )

    res = await execute_remediation_plan(db_session, plan, dry_run=False)
    assert res.success is True
    assert res.dry_run is False
    assert res.verification_passed is True
    assert res.before_telemetry is not None
    assert res.before_telemetry.healthy is False
    assert res.after_telemetry is not None
    assert res.after_telemetry.healthy is True
    assert res.step_results[0].backend_acknowledged is True

    health_ok = await verify_post_remediation_health("inventory")
    assert health_ok is True


@pytest.mark.asyncio
async def test_remediation_api_endpoints(async_client: AsyncClient) -> None:
    inc_res = await async_client.post(
        "/api/v1/incidents", json={"title": "Remediation API Test", "severity": "medium"}
    )
    inc_id = inc_res.json()["id"]

    review_res = await async_client.post(
        "/api/v1/remediations/plan_api_001/review",
        json={"incident_id": inc_id, "decision": "approve", "reviewer": "admin"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["decision"] == "approve"


@pytest.mark.asyncio
async def test_forbidden_arbitrary_shell_exec(db_session: AsyncSession) -> None:
    inc = await create_incident(
        db_session, CreateIncidentRequest(title="Forbidden Exec Test", severity="critical")
    )
    plan = RemediationPlan(
        plan_id="plan_forbidden_001",
        incident_id=str(inc.id),
        steps=[
            RemediationStep(
                step_number=1,
                action_type="shell",
                description="Attempt arbitrary shell execution",
                target_service="inventory",
                parameters={"command": "rm -rf /"},
            )
        ],
        requires_human_approval=False,
        approved=True,
    )

    res = await execute_remediation_plan(db_session, plan, dry_run=False)
    assert res.success is False
    assert "forbidden" in res.step_results[0].message.lower()
    assert (
        "arbitrary shell or exec actions are strictly prohibited"
        in res.step_results[0].message.lower()
    )
