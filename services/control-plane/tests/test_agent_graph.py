import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_investigation_workflow
from app.agent.nodes import skeptic_verifier_node
from app.agent.state import Hypothesis, InvestigationState
from app.services.incident_service import CreateIncidentRequest, create_incident


@pytest.mark.asyncio
async def test_full_investigation_workflow_execution(db_session: AsyncSession) -> None:
    req = CreateIncidentRequest(title="Graph Test", severity="high", target_service="inventory")
    inc = await create_incident(db_session, req)
    inc_id = inc.id
    state = InvestigationState(incident_id=inc_id)

    final_state = await run_investigation_workflow(db_session, state)

    assert final_state.status in ["resolved", "remediating", "rca_ready"]
    assert final_state.rca_report is not None
    assert final_state.rca_report.is_conclusive is True
    assert final_state.rca_report.primary_service == "inventory"
    assert "triage_node" in final_state.history
    assert "telemetry_investigator_node" in final_state.history
    assert "hypothesis_generator_node" in final_state.history
    assert "skeptic_verifier_node" in final_state.history
    assert "rca_synthesizer_node" in final_state.history


@pytest.mark.asyncio
async def test_skeptic_verifier_contradiction_rejection(db_session: AsyncSession) -> None:
    req = CreateIncidentRequest(title="Graph Test 2", severity="high", target_service="inventory")
    inc = await create_incident(db_session, req)
    inc_id = inc.id
    state = InvestigationState(incident_id=inc_id)
    weak_hypothesis = Hypothesis(
        id="hyp_weak",
        target_service="auth",
        root_cause_category="config",
        description="Hallucinated config failure without telemetry evidence",
        confidence=0.30,
        status="proposed",
    )
    state.hypotheses.append(weak_hypothesis)

    res_state = await skeptic_verifier_node(db_session, state)

    rejected_hyp = res_state.hypotheses[0]
    assert rejected_hyp.status == "rejected"
    assert any("REJECTED" in feedback for feedback in res_state.skeptic_feedback)


def test_empty_knowledge_search_advances_to_hypothesis() -> None:
    from app.agent.graph import route_next_node

    state = InvestigationState(
        incident_id="empty-knowledge",
        status="investigating",
        telemetry_evidence=[{"tool": "metrics.query"}],
        knowledge_search_completed=True,
    )
    assert state.knowledge_docs == []
    assert route_next_node(state) == "hypothesis"


@pytest.mark.asyncio
async def test_investigation_api_endpoints(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from app.agent.agent_runner import execute_investigation
    from app.remediation.executor import TelemetrySnapshot

    snapshots = iter(
        [
            TelemetrySnapshot(service="inventory", status_code=503, latency_ms=10, healthy=False),
            TelemetrySnapshot(service="inventory", status_code=200, latency_ms=5, healthy=True),
        ]
    )

    async def fake_capture(_service: str) -> TelemetrySnapshot:
        return next(snapshots)

    async def fake_clear(_step: object) -> None:
        return None

    monkeypatch.setattr("app.remediation.executor.capture_service_telemetry", fake_capture)
    monkeypatch.setattr("app.remediation.executor._clear_sandbox_fault", fake_clear)
    monkeypatch.setattr(
        "app.api.v1.investigations.run_investigation_task.delay",
        lambda _incident_id: SimpleNamespace(id="test-celery-task"),
    )

    inc_res = await async_client.post(
        "/api/v1/incidents", json={"title": "Test Incident for API", "severity": "high"}
    )
    inc_id = inc_res.json()["id"]

    trigger_res = await async_client.post(
        "/api/v1/investigations/trigger", json={"incident_id": inc_id}
    )
    assert trigger_res.status_code == 202
    data = trigger_res.json()
    assert data["incident_id"] == inc_id
    assert data == {
        "incident_id": inc_id,
        "status": "queued",
        "task_id": "test-celery-task",
    }
    duplicate_res = await async_client.post(
        "/api/v1/investigations/trigger", json={"incident_id": inc_id}
    )
    assert duplicate_res.status_code == 409

    monkeypatch.setattr(
        "app.api.v1.investigations.celery_app.AsyncResult",
        lambda _task_id: SimpleNamespace(
            status="SUCCESS",
            failed=lambda: False,
            successful=lambda: True,
            result={"incident_id": inc_id, "status": "remediating"},
        ),
    )
    task_res = await async_client.get("/api/v1/investigations/tasks/test-celery-task")
    assert task_res.status_code == 200
    assert task_res.json()["investigation_status"] == "remediating"

    # The API only enqueues. Execute the worker operation explicitly in this unit test.
    from app.db.session import engine

    async with AsyncSession(engine) as worker_session:
        await execute_investigation(worker_session, inc_id)

    status_res = await async_client.get(f"/api/v1/investigations/{inc_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["incident_id"] == inc_id

    # We should be paused at remediating / human review
    assert status_data["status"] == "remediating"
    plan_id = (
        status_data["rca_report"]["plan_id"]
        if status_data.get("rca_report") and "plan_id" in status_data["rca_report"]
        else None
    )

    # Let's extract the actual plan_id from the state
    from app.agent.agent_runner import get_investigation_checkpoint
    async with AsyncSession(engine) as session:
        state = await get_investigation_checkpoint(session, inc_id)
        assert state is not None
        assert state.remediation_plan is not None
        plan_id = state.remediation_plan.plan_id

        # Now submit human review to approve it
        approve_res = await async_client.post(
            f"/api/v1/remediations/{plan_id}/review",
            json={
                "incident_id": inc_id,
                "decision": "approve",
                "reviewer": "test_eng",
                "comments": "looks good",
            },
        )
        assert approve_res.status_code == 200

        # Verify it resumed and went to outcome/resolved
        state = await get_investigation_checkpoint(session, inc_id)
        assert state.remediation_plan.approved is True
        assert state.status in ["resolved", "outcome"]
        assert "outcome_verifier_node" in state.history
