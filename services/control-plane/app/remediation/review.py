from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent_runner import get_investigation_checkpoint, save_investigation_checkpoint
from app.db.models.remediation_models import HumanReviewRecord as DBHumanReviewRecord
from app.services.incident_service import add_incident_event


class HumanReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"


class HumanReviewRecord(BaseModel):
    plan_id: str
    incident_id: str
    decision: HumanReviewDecision
    reviewer: str = "engineer"
    comments: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


async def submit_human_review(
    session: AsyncSession,
    plan_id: str,
    incident_id: str,
    decision: HumanReviewDecision,
    reviewer: str = "engineer",
    comments: str | None = None,
) -> HumanReviewRecord:
    record = HumanReviewRecord(
        plan_id=plan_id,
        incident_id=incident_id,
        decision=decision,
        reviewer=reviewer,
        comments=comments,
    )

    db_record = DBHumanReviewRecord(
        plan_id=plan_id,
        incident_id=incident_id,
        decision=decision.value,
        reviewer=reviewer,
        comments=comments,
    )
    session.add(db_record)
    await session.commit()
    await session.refresh(db_record)

    # Resume or update investigation checkpoint
    state = await get_investigation_checkpoint(session, incident_id)
    if state and state.remediation_plan and state.remediation_plan.plan_id == plan_id:
        if decision == HumanReviewDecision.APPROVE:
            state.remediation_plan.approved = True
            state.status = "remediating"
        elif decision == HumanReviewDecision.REJECT:
            state.remediation_plan.approved = False
            state.status = "rca_ready"
        elif decision == HumanReviewDecision.REQUEST_MORE_EVIDENCE:
            state.remediation_plan.approved = False
            state.status = "investigating"
            # Trigger further investigation loop
            state.telemetry_evidence.clear()
            state.skeptic_feedback.clear()

        await save_investigation_checkpoint(session, state)

        # Resume the agent graph execution now that state is updated
        from app.agent.agent_runner import execute_investigation

        await execute_investigation(session, incident_id)

    await add_incident_event(
        session=session,
        incident_id=incident_id,
        event_type="system",
        actor=reviewer,
        title=f"Human Review Submitted: {decision.upper()}",
        payload=record.model_dump(),
    )

    return record


async def get_human_review_history(session: AsyncSession, plan_id: str) -> list[HumanReviewRecord]:
    stmt = (
        select(DBHumanReviewRecord)
        .where(DBHumanReviewRecord.plan_id == plan_id)
        .order_by(DBHumanReviewRecord.timestamp.asc())
    )
    result = await session.execute(stmt)
    records = result.scalars().all()

    return [
        HumanReviewRecord(
            plan_id=str(r.plan_id),
            incident_id=str(r.incident_id),
            decision=HumanReviewDecision(r.decision),
            reviewer=r.reviewer,
            comments=r.comments,
            timestamp=r.timestamp.isoformat(),
        )
        for r in records
    ]
