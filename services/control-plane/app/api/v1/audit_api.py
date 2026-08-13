from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserProfile, UserRole, require_role
from app.db.models.audit_models import AuditEvent
from app.db.session import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventDTO(BaseModel):
    id: str
    actor: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, object]
    created_at: datetime


@router.get("/events", response_model=list[AuditEventDTO])
async def list_audit_events(
    action: str | None = Query(default=None, max_length=100),
    actor: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ADMIN)),
) -> list[AuditEventDTO]:
    statement = select(AuditEvent)
    if action:
        statement = statement.where(AuditEvent.action == action)
    if actor:
        statement = statement.where(AuditEvent.actor == actor)
    statement = statement.order_by(AuditEvent.created_at.desc()).limit(limit)
    events = (await session.execute(statement)).scalars().all()
    return [
        AuditEventDTO(
            id=str(event.id),
            actor=event.actor,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            details=event.details,
            created_at=event.created_at,
        )
        for event in events
    ]
