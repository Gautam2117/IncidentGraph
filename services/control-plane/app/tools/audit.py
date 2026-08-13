from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.db.models.audit_models import AuditEvent
from app.db.session import AsyncSessionLocal
from app.observability.tracer import redact_sensitive_payload


class ToolAuditRecord(BaseModel):
    audit_id: str
    tool_name: str
    inputs: dict[str, Any]
    success: bool
    duration_ms: float
    actor: str = "agent"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


async def log_tool_audit(
    audit_id: str,
    tool_name: str,
    inputs: dict[str, Any],
    success: bool,
    duration_ms: float,
    actor: str = "agent",
) -> ToolAuditRecord:
    safe_inputs = redact_sensitive_payload(inputs)
    if not isinstance(safe_inputs, dict):
        safe_inputs = {}
    record = ToolAuditRecord(
        audit_id=audit_id,
        tool_name=tool_name,
        inputs=safe_inputs,
        success=success,
        duration_ms=duration_ms,
        actor=actor,
    )
    async with AsyncSessionLocal() as session:
        session.add(
            AuditEvent(
                actor=actor,
                action="tool.execute",
                resource_type="operational_tool",
                resource_id=audit_id,
                details=record.model_dump(mode="json"),
            )
        )
        await session.commit()
    return record


async def get_tool_audit_logs(tool_name: str | None = None) -> list[dict[str, Any]]:
    statement = (
        select(AuditEvent)
        .where(AuditEvent.action == "tool.execute")
        .order_by(AuditEvent.created_at.asc())
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(statement)
        events = result.scalars().all()
    records = [event.details for event in events]
    if tool_name:
        records = [record for record in records if record.get("tool_name") == tool_name]
    return records
