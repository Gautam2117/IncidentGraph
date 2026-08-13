from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent_runner import (
    get_investigation_checkpoint,
    stream_investigation_events,
)
from app.agent.state import InvestigationState
from app.core.auth import UserProfile, UserRole, require_role
from app.db.models.investigation_models import Investigation
from app.db.session import get_db
from app.services.incident_service import get_incident
from app.worker import celery_app, run_investigation_task

router = APIRouter(prefix="/investigations", tags=["investigations"])
TERMINAL_STATUSES = {
    "completed",
    "failed",
    "cancelled",
    "resolved",
    "remediation_failed",
    "remediation_inconclusive",
}


class TriggerInvestigationRequest(BaseModel):
    incident_id: str


@router.get("/tasks/{task_id}")
async def get_investigation_task_status(
    task_id: str,
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> dict[str, Any]:
    """Return durable Celery state, including a bounded failure description."""
    task = celery_app.AsyncResult(task_id)
    payload: dict[str, Any] = {"task_id": task_id, "status": task.status.lower()}
    if task.failed():
        payload["error"] = type(task.result).__name__
    elif task.successful():
        result = task.result if isinstance(task.result, dict) else {}
        payload["incident_id"] = result.get("incident_id")
        payload["investigation_status"] = result.get("status")
    return payload


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_investigation(
    req: TriggerInvestigationRequest,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> dict[str, Any]:
    """Triggers an automated multi-role LangGraph investigation for an incident."""
    if await get_incident(session, req.incident_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{req.incident_id}' not found",
        )
    investigation = await session.scalar(
        select(Investigation)
        .where(Investigation.incident_id == req.incident_id)
        .with_for_update()
    )
    if investigation is not None and str(investigation.status) not in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active investigation already exists for this incident",
        )
    initial_state = InvestigationState(incident_id=req.incident_id).model_dump(mode="json")
    if investigation is None:
        investigation = Investigation(
            incident_id=req.incident_id,
            status="pending",
            state=initial_state,
            cancellation_requested=False,
        )
        session.add(investigation)
    else:
        investigation.status = "pending"
        investigation.state = initial_state
        investigation.task_id = None
        investigation.cancellation_requested = False
    await session.commit()

    try:
        task = run_investigation_task.delay(req.incident_id)
    except Exception as exc:
        investigation.status = "failed"
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Investigation queue is unavailable",
        ) from exc
    investigation.task_id = task.id
    await session.commit()
    return {
        "incident_id": req.incident_id,
        "status": "queued",
        "task_id": task.id,
    }


@router.post("/{incident_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_investigation(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> dict[str, Any]:
    investigation = await session.scalar(
        select(Investigation)
        .where(Investigation.incident_id == incident_id)
        .with_for_update()
    )
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if str(investigation.status) in TERMINAL_STATUSES:
        raise HTTPException(status_code=409, detail="Investigation is already terminal")
    investigation.cancellation_requested = True
    investigation.status = "cancelled"
    await session.commit()
    if investigation.task_id:
        celery_app.control.revoke(investigation.task_id, terminate=False)
    return {
        "incident_id": incident_id,
        "task_id": investigation.task_id,
        "status": "cancellation_requested",
    }


@router.get("/{incident_id}")
async def get_investigation_status(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> dict[str, Any]:
    """Returns current state of an ongoing or completed investigation."""
    state = await get_investigation_checkpoint(session, incident_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation for incident '{incident_id}' not found",
        )
    return dict(state.model_dump())


@router.get("/{incident_id}/stream")
async def stream_investigation(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> StreamingResponse:
    """Streams Server-Sent Events (SSE) as multi-role agent nodes execute."""

    async def event_generator() -> Any:
        async for evt in stream_investigation_events(session, incident_id):
            import json

            yield f"data: {json.dumps(evt)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
