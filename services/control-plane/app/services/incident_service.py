import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Incident,
    IncidentEvent,
    IncidentEventType,
    IncidentSeverity,
    IncidentStatus,
    ProcessedWebhook,
)


class CreateIncidentRequest(BaseModel):
    title: str
    severity: str = "medium"
    target_service: str | None = None
    scenario_id: str | None = None
    summary: str | None = None


class IncidentDTO(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    target_service: str | None = None
    scenario_id: str | None = None
    summary: str | None = None
    created_at: str
    updated_at: str


class IncidentEventDTO(BaseModel):
    id: str
    incident_id: str
    event_type: str
    actor: str
    title: str
    payload: dict[str, Any]
    created_at: str


async def create_incident(session: AsyncSession, req: CreateIncidentRequest) -> IncidentDTO:
    now = datetime.now(UTC)
    inc = Incident(
        title=req.title,
        severity=IncidentSeverity(req.severity),
        status=IncidentStatus.OPEN,
        target_service=req.target_service,
        scenario_id=req.scenario_id,
        summary=req.summary,
    )
    session.add(inc)
    await session.flush()

    evt = IncidentEvent(
        incident_id=inc.id,
        event_type=IncidentEventType.SYSTEM,
        actor="system",
        title="Incident Opened",
        payload={"title": req.title, "severity": req.severity},
    )
    session.add(evt)
    await session.commit()
    await session.refresh(inc)

    return IncidentDTO(
        id=str(inc.id),
        title=inc.title,
        severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
        status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
        target_service=inc.target_service,
        scenario_id=inc.scenario_id,
        summary=inc.summary,
        created_at=inc.created_at.isoformat()
        if hasattr(inc, "created_at") and inc.created_at
        else now.isoformat(),
        updated_at=inc.updated_at.isoformat()
        if hasattr(inc, "updated_at") and inc.updated_at
        else now.isoformat(),
    )


async def list_incidents(
    session: AsyncSession,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[IncidentDTO]:
    stmt = select(Incident).order_by(
        Incident.created_at.desc() if hasattr(Incident, "created_at") else Incident.id.desc()
    )
    if severity:
        stmt = stmt.where(Incident.severity == IncidentSeverity(severity))
    if status:
        stmt = stmt.where(Incident.status == IncidentStatus(status))

    stmt = stmt.limit(min(max(limit, 1), 100)).offset(max(offset, 0))

    result = await session.execute(stmt)
    incidents = result.scalars().all()

    return [
        IncidentDTO(
            id=str(inc.id),
            title=inc.title,
            severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
            status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
            target_service=inc.target_service,
            scenario_id=inc.scenario_id,
            summary=inc.summary,
            created_at=inc.created_at.isoformat()
            if hasattr(inc, "created_at") and inc.created_at
            else "",
            updated_at=inc.updated_at.isoformat()
            if hasattr(inc, "updated_at") and inc.updated_at
            else "",
        )
        for inc in incidents
    ]


async def get_incident(session: AsyncSession, incident_id: str) -> IncidentDTO | None:
    try:
        uid = uuid.UUID(incident_id)
    except ValueError:
        return None

    inc = await session.get(Incident, uid)
    if not inc:
        return None

    return IncidentDTO(
        id=str(inc.id),
        title=inc.title,
        severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
        status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
        target_service=inc.target_service,
        scenario_id=inc.scenario_id,
        summary=inc.summary,
        created_at=inc.created_at.isoformat()
        if hasattr(inc, "created_at") and inc.created_at
        else "",
        updated_at=inc.updated_at.isoformat()
        if hasattr(inc, "updated_at") and inc.updated_at
        else "",
    )


async def get_incident_timeline(session: AsyncSession, incident_id: str) -> list[IncidentEventDTO]:
    try:
        uid = uuid.UUID(incident_id)
    except ValueError:
        return []

    stmt = (
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == uid)
        .order_by(
            IncidentEvent.created_at.asc()
            if hasattr(IncidentEvent, "created_at")
            else IncidentEvent.id.asc()
        )
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    return [
        IncidentEventDTO(
            id=str(evt.id),
            incident_id=str(evt.incident_id),
            event_type=evt.event_type.value
            if hasattr(evt.event_type, "value")
            else str(evt.event_type),
            actor=evt.actor,
            title=evt.title,
            payload=evt.payload or {},
            created_at=evt.created_at.isoformat()
            if hasattr(evt, "created_at") and evt.created_at
            else "",
        )
        for evt in events
    ]


async def add_incident_event(
    session: AsyncSession,
    incident_id: str,
    event_type: str,
    actor: str,
    title: str,
    payload: dict[str, Any],
) -> IncidentEventDTO:
    try:
        uid = uuid.UUID(incident_id)
    except ValueError as exc:
        raise ValueError(f"Invalid incident ID {incident_id}") from exc

    inc = await session.get(Incident, uid)
    if not inc:
        raise ValueError(f"Incident {incident_id} not found")

    evt = IncidentEvent(
        incident_id=uid,
        event_type=IncidentEventType(event_type),
        actor=actor,
        title=title,
        payload=payload,
    )
    session.add(evt)
    await session.commit()
    await session.refresh(evt)

    return IncidentEventDTO(
        id=str(evt.id),
        incident_id=str(evt.incident_id),
        event_type=evt.event_type.value
        if hasattr(evt.event_type, "value")
        else str(evt.event_type),
        actor=evt.actor,
        title=evt.title,
        payload=evt.payload or {},
        created_at=evt.created_at.isoformat()
        if hasattr(evt, "created_at") and evt.created_at
        else datetime.now(UTC).isoformat(),
    )


def verify_webhook_signature(
    payload_bytes: bytes,
    secret: str,
    signature_header: str | None,
    timestamp: str | None = None,
) -> bool:
    """Verifies HMAC-SHA256 signature of incoming webhook alert payload."""
    if not signature_header:
        return False
    signed_payload = f"{timestamp}.".encode() + payload_bytes if timestamp else payload_bytes
    expected_sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    received_sig = signature_header.split("=")[-1] if "=" in signature_header else signature_header
    return hmac.compare_digest(expected_sig, received_sig)


async def ingest_webhook_alert(
    session: AsyncSession,
    payload: dict[str, Any],
    secret: str | None = None,
    signature: str | None = None,
    delivery_id: str | None = None,
    signature_timestamp: str | None = None,
) -> IncidentDTO:
    payload_str = json.dumps(payload, sort_keys=True)
    if not delivery_id or len(delivery_id) > 255:
        raise ValueError("Missing or invalid X-Webhook-ID")
    if not signature_timestamp:
        raise ValueError("Missing X-Webhook-Timestamp")
    try:
        signed_at = datetime.fromtimestamp(int(signature_timestamp), tz=UTC)
    except (TypeError, ValueError, OSError) as exc:
        raise ValueError("Invalid X-Webhook-Timestamp") from exc
    if abs((datetime.now(UTC) - signed_at).total_seconds()) > 300:
        raise ValueError("Webhook timestamp is outside the 5-minute acceptance window")

    if secret and not verify_webhook_signature(
        payload_str.encode("utf-8"), secret, signature, signature_timestamp
    ):
        raise ValueError("Invalid webhook signature")

    receipt = ProcessedWebhook(
        delivery_id=delivery_id,
        payload_hash=hashlib.sha256(payload_str.encode("utf-8")).hexdigest(),
        signature_timestamp=signed_at,
    )
    session.add(receipt)
    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        if isinstance(exc, IntegrityError):
            raise ValueError("Webhook delivery has already been processed") from exc
        raise

    title = payload.get("title", payload.get("summary", "Webhook Alert Received"))
    severity = payload.get("severity", "high")
    service = payload.get("service", payload.get("target_service"))

    inc_req = CreateIncidentRequest(
        title=str(title),
        severity=str(severity),
        target_service=str(service) if service else None,
        summary=f"Automated webhook alert ingestion: {payload_str[:200]}",
    )

    try:
        inc = await create_incident(session, inc_req)
        receipt.incident_id = uuid.UUID(inc.id)
        session.add(receipt)
        await session.commit()
        await add_incident_event(
            session,
            incident_id=inc.id,
            event_type="webhook",
            actor="webhook_ingester",
            title="Alert Webhook Received",
            payload=payload,
        )
        return inc
    except Exception:
        await session.rollback()
        await session.delete(receipt)
        await session.commit()
        raise
