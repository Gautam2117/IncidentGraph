from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent_runner import get_investigation_checkpoint
from app.db.models.audit_models import ActionItem as DBActionItem
from app.db.models.audit_models import PostmortemReport as DBPostmortemReport
from app.rag.store import get_rag_store
from app.services.incident_service import add_incident_event, get_incident, get_incident_timeline


class ActionItem(BaseModel):
    id: str
    description: str
    owner_team: str
    status: str = "open"  # open, in_progress, completed


class PostmortemReport(BaseModel):
    id: str
    incident_id: str
    title: str
    severity: str
    target_service: str
    root_cause_category: str
    summary: str
    timeline_summary: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    markdown_content: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


def generate_postmortem_markdown(
    title: str,
    incident_id: str,
    service: str,
    category: str,
    summary: str,
    timeline: list[str],
    action_items: list[ActionItem],
) -> str:
    timeline_str = "\n".join([f"- {t}" for t in timeline])
    actions_str = "\n".join([f"- [ ] **{a.owner_team}**: {a.description}" for a in action_items])

    return f"""# Incident Postmortem: {title}

**Incident ID:** `{incident_id}`
**Primary Target Service:** `{service}`
**Root Cause Category:** `{category}`
**Generated At:** `{datetime.now(UTC).isoformat()}`

---

## Executive Summary
{summary}

## Incident Event Timeline
{timeline_str}

## Preventative Action Items
{actions_str}
"""


async def generate_postmortem(session: AsyncSession, incident_id: str) -> PostmortemReport:
    inc = await get_incident(session, incident_id)
    if not inc:
        raise ValueError(f"Incident '{incident_id}' not found")

    state = await get_investigation_checkpoint(session, incident_id)
    events = await get_incident_timeline(session, incident_id)

    title = inc.title
    service = inc.target_service or "inventory"
    category = (
        state.rca_report.root_cause_category
        if state and getattr(state, "rca_report", None)
        else "database"
    )
    summary = (
        state.rca_report.summary
        if state and getattr(state, "rca_report", None)
        else f"Postmortem analysis for incident {incident_id}"
    )

    timeline_items = [f"{evt.created_at} [{evt.actor}]: {evt.title}" for evt in events]
    if not timeline_items:
        timeline_items = [f"{inc.created_at} [system]: Incident Opened"]

    action_items = [
        ActionItem(
            id="act_001",
            description=f"Add automated alert monitor for {service} connection pool saturation",
            owner_team="platform-eng",
        ),
        ActionItem(
            id="act_002",
            description=f"Update runbook documentation for {category} incident response",
            owner_team="devops",
        ),
    ]

    markdown = generate_postmortem_markdown(
        title=title,
        incident_id=incident_id,
        service=service,
        category=category,
        summary=summary,
        timeline=timeline_items,
        action_items=action_items,
    )

    pm_id = f"pm_{incident_id}"

    db_report = DBPostmortemReport(
        id=pm_id,
        incident_id=incident_id,
        title=title,
        severity=str(inc.severity),
        target_service=service,
        root_cause_category=category,
        summary=summary,
        timeline_summary=timeline_items,
        markdown_content=markdown,
    )
    session.add(db_report)
    await session.flush()

    for act in action_items:
        db_act = DBActionItem(
            postmortem_id=pm_id,
            description=act.description,
            owner_team=act.owner_team,
            status=act.status,
        )
        session.add(db_act)

    await session.commit()

    report = PostmortemReport(
        id=pm_id,
        incident_id=incident_id,
        title=title,
        severity=str(inc.severity),
        target_service=service,
        root_cause_category=category,
        summary=summary,
        timeline_summary=timeline_items,
        action_items=action_items,
        markdown_content=markdown,
    )

    # Auto-ingest into RAG Store for future historical intelligence
    rag_store = get_rag_store()
    await rag_store.add_document(
        session=session,
        doc_id=pm_id,
        title=f"Postmortem: {title}",
        content=markdown,
        category="postmortem",
        metadata={"incident_id": incident_id, "service": service},
    )

    await add_incident_event(
        session=session,
        incident_id=incident_id,
        event_type="outcome",
        actor="postmortem_generator",
        title="Postmortem Generated & Indexed into Knowledge Base",
        payload={"postmortem_id": pm_id},
    )

    return report


async def get_postmortem(session: AsyncSession, incident_id: str) -> PostmortemReport | None:
    stmt = select(DBPostmortemReport).where(DBPostmortemReport.incident_id == incident_id)
    result = await session.execute(stmt)
    db_report = result.scalars().first()

    if not db_report:
        return None

    stmt_act = select(DBActionItem).where(DBActionItem.postmortem_id == db_report.id)
    result_act = await session.execute(stmt_act)
    db_actions = result_act.scalars().all()

    return PostmortemReport(
        id=db_report.id,
        incident_id=str(db_report.incident_id),
        title=db_report.title,
        severity=db_report.severity,
        target_service=db_report.target_service,
        root_cause_category=db_report.root_cause_category,
        summary=db_report.summary,
        timeline_summary=db_report.timeline_summary,
        markdown_content=db_report.markdown_content,
        created_at=db_report.created_at.isoformat(),
        action_items=[
            ActionItem(
                id=str(a.id), description=a.description, owner_team=a.owner_team, status=a.status
            )
            for a in db_actions
        ],
    )
