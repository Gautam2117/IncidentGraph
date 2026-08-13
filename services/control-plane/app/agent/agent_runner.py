from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_investigation_workflow
from app.agent.state import InvestigationState
from app.db.models.investigation_models import (
    Evidence as DBEvidence,
)
from app.db.models.investigation_models import (
    Hypothesis as DBHypothesis,
)
from app.db.models.investigation_models import (
    Investigation as DBInvestigation,
)
from app.db.models.investigation_models import (
    ToolCall as DBToolCall,
)
from app.db.models.remediation_models import RemediationPlan as DBRemediationPlan


async def get_investigation_checkpoint(
    session: AsyncSession, incident_id: str
) -> InvestigationState | None:
    stmt = select(DBInvestigation).where(DBInvestigation.incident_id == incident_id)
    result = await session.execute(stmt)
    inv = result.scalars().first()
    if not inv or not inv.state:
        return None
    return InvestigationState.model_validate(inv.state)


async def save_investigation_checkpoint(session: AsyncSession, state: InvestigationState) -> None:
    stmt = select(DBInvestigation).where(DBInvestigation.incident_id == state.incident_id)
    result = await session.execute(stmt)
    inv = result.scalars().first()

    if inv:
        inv.state = state.model_dump(mode="json")
        inv.status = state.status
    else:
        inv = DBInvestigation(
            incident_id=state.incident_id,
            status=state.status,
            state=state.model_dump(mode="json"),
        )
        session.add(inv)

    await session.flush()
    # The JSON checkpoint is the execution source of truth; relational rows are
    # rebuilt as queryable evidence/audit projections after every checkpoint.
    hypothesis_ids = select(DBHypothesis.id).where(DBHypothesis.investigation_id == inv.id)
    await session.execute(delete(DBEvidence).where(DBEvidence.hypothesis_id.in_(hypothesis_ids)))
    await session.execute(delete(DBHypothesis).where(DBHypothesis.investigation_id == inv.id))
    await session.execute(delete(DBToolCall).where(DBToolCall.investigation_id == inv.id))

    for hypothesis in state.hypotheses:
        db_hypothesis = DBHypothesis(
            investigation_id=inv.id,
            title=hypothesis.root_cause_category,
            description=hypothesis.description,
            confidence=hypothesis.confidence,
            status=hypothesis.status,
        )
        session.add(db_hypothesis)
        await session.flush()
        session.add_all(
            [
                DBEvidence(
                    hypothesis_id=db_hypothesis.id,
                    evidence_type="telemetry",
                    description=description,
                    supports=True,
                    data={},
                )
                for description in hypothesis.supporting_evidence
            ]
        )

    session.add_all(
        [
            DBToolCall(
                investigation_id=inv.id,
                tool_name=str(item.get("tool", "unknown")),
                arguments=dict(item.get("arguments", {})),
                result={"data": item.get("data")},
            )
            for item in state.telemetry_evidence
        ]
    )

    if state.remediation_plan:
        db_plan = await session.get(DBRemediationPlan, state.remediation_plan.plan_id)
        if db_plan is None:
            db_plan = DBRemediationPlan(
                id=state.remediation_plan.plan_id,
                incident_id=state.incident_id,
                description="\n".join(step.description for step in state.remediation_plan.steps),
                requires_human_approval=state.remediation_plan.requires_human_approval,
                approved=state.remediation_plan.approved,
            )
            session.add(db_plan)
        else:
            db_plan.approved = state.remediation_plan.approved
            db_plan.description = "\n".join(
                step.description for step in state.remediation_plan.steps
            )

    await session.commit()


async def execute_investigation(session: AsyncSession, incident_id: str) -> InvestigationState:
    state = await get_investigation_checkpoint(session, incident_id) or InvestigationState(
        incident_id=incident_id
    )
    # Establish the durable parent row before any live model call records are
    # written by graph nodes.
    await save_investigation_checkpoint(session, state)
    # LangGraph's PostgreSQL saver performs CREATE INDEX CONCURRENTLY during
    # first-time setup. End the SQLAlchemy read transaction first so its
    # virtual XID cannot deadlock the saver in another connection.
    await session.commit()
    final_state = await run_investigation_workflow(session, state)
    await save_investigation_checkpoint(session, final_state)
    return final_state


async def stream_investigation_events(
    session: AsyncSession, incident_id: str
) -> AsyncGenerator[dict[str, Any], None]:
    state = await get_investigation_checkpoint(session, incident_id) or InvestigationState(
        incident_id=incident_id
    )
    await save_investigation_checkpoint(session, state)

    yield {"event": "start", "incident_id": incident_id, "step_count": state.step_count}

    final_state = await run_investigation_workflow(session, state)
    await save_investigation_checkpoint(session, final_state)

    for node_name in final_state.history:
        yield {"event": "node_executed", "node": node_name, "status": final_state.status}

    yield {
        "event": "complete",
        "incident_id": incident_id,
        "rca": final_state.rca_report.model_dump() if final_state.rca_report else None,
    }
