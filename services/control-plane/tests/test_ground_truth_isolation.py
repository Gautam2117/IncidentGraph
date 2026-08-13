import ast
import inspect
import textwrap

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_investigation_workflow
from app.agent.state import InvestigationState
from app.eval.eval_runner import run_scenario_eval
from app.services.incident_service import CreateIncidentRequest, create_incident


@pytest.mark.asyncio
async def test_ground_truth_isolation_verification(db_session: AsyncSession) -> None:
    """Verifies that agent workflow execution has zero access to hidden scenario ground truth."""
    inc = await create_incident(
        db_session,
        CreateIncidentRequest(
            title="Isolation Audit Incident",
            severity="high",
            target_service="orders",
            scenario_id="slow_query_missing_index",
        ),
    )

    state = InvestigationState(incident_id=inc.id, target_service="orders")
    final_state = await run_investigation_workflow(db_session, state)

    # 1. State check: Ensure no ground_truth attribute exists on state
    assert not hasattr(final_state, "ground_truth")
    assert not hasattr(final_state, "sc_ground_truth")

    # 2. Check telemetry evidence: ensure no ground_truth key leaked
    for item in final_state.telemetry_evidence:
        assert "ground_truth" not in item

    # 3. Check hypothesis and RCA report
    assert final_state.rca_report is not None
    assert final_state.rca_report.root_cause_category != ""


def test_evaluator_does_not_read_ground_truth_before_agent_execution() -> None:
    """Hidden labels must be consumed only by the post-run scoring function."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(run_scenario_eval)))
    forbidden_reads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "ground_truth"
    ]
    assert forbidden_reads == []
