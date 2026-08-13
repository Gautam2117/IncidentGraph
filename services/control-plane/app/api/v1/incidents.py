from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserProfile, UserRole, require_role
from app.core.config import settings
from app.core.rate_limit import webhook_rate_limit
from app.db.session import get_db
from app.services.incident_service import (
    CreateIncidentRequest,
    IncidentDTO,
    IncidentEventDTO,
    create_incident,
    get_incident,
    get_incident_timeline,
    ingest_webhook_alert,
    list_incidents,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentDTO])
async def get_incidents(
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[IncidentDTO]:
    """Returns list of all incidents filtered by severity or status."""
    return cast(
        list[IncidentDTO],
        await list_incidents(
            session, severity=severity, status=status_filter, limit=limit, offset=offset
        ),
    )


@router.post("", response_model=IncidentDTO, status_code=status.HTTP_201_CREATED)
async def create_new_incident(
    req: CreateIncidentRequest,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.ENGINEER)),
) -> IncidentDTO:
    """Manually creates a new incident."""
    return await create_incident(session, req)


@router.get("/{incident_id}", response_model=IncidentDTO)
async def get_incident_by_id(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> IncidentDTO:
    """Returns detailed information for a specific incident."""
    inc = await get_incident(session, incident_id)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return inc


@router.get("/{incident_id}/timeline", response_model=list[IncidentEventDTO])
async def get_incident_event_timeline(
    incident_id: str,
    session: AsyncSession = Depends(get_db),
    _user: UserProfile = Depends(require_role(UserRole.VIEWER)),
) -> list[IncidentEventDTO]:
    """Returns chronologically ordered timeline events for an incident."""
    inc = await get_incident(session, incident_id)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    return cast(list[IncidentEventDTO], await get_incident_timeline(session, incident_id))


@router.post("/webhooks/ingest", response_model=IncidentDTO)
async def webhook_ingest_alert(
    payload: dict[str, Any],
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_webhook_id: str | None = Header(default=None, alias="X-Webhook-ID"),
    x_webhook_timestamp: str | None = Header(default=None, alias="X-Webhook-Timestamp"),
    _rate_limit: None = Depends(webhook_rate_limit),
    session: AsyncSession = Depends(get_db),
) -> IncidentDTO:
    """Ingests external webhook alert payloads with replay protection."""
    if not settings.WEBHOOK_SIGNING_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook ingestion is disabled until a signing secret is configured",
        )
    try:
        return await ingest_webhook_alert(
            session,
            payload,
            secret=settings.WEBHOOK_SIGNING_SECRET,
            signature=x_signature,
            delivery_id=x_webhook_id,
            signature_timestamp=x_webhook_timestamp,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
