import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(StrEnum):
    VIEWER = "viewer"
    ENGINEER = "engineer"
    ADMIN = "admin"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RCA_READY = "rca_ready"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentEventType(StrEnum):
    SYSTEM = "system"
    ALERT = "alert"
    WEBHOOK = "webhook"
    USER = "user"
    RETRIEVAL = "retrieval"
    HYPOTHESIS = "hypothesis"
    TOOL = "tool"
    VERIFIER = "verifier"
    RCA = "rca"
    REMEDIATION = "remediation"
    OUTCOME = "outcome"


class User(Base):  # type: ignore[misc]
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(String(50), default=UserRole.ENGINEER, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class Workspace(Base):  # type: ignore[misc]
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)


class ServiceCatalog(Base):  # type: ignore[misc]
    __tablename__ = "service_catalog"

    service_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_team: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Deployment(Base):  # type: ignore[misc]
    __tablename__ = "deployments"

    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), default="production", nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    git_sha: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deployed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)


class Incident(Base):  # type: ignore[misc]
    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        String(50), default=IncidentSeverity.MEDIUM, nullable=False, index=True
    )
    status: Mapped[IncidentStatus] = mapped_column(
        String(50), default=IncidentStatus.OPEN, nullable=False, index=True
    )
    target_service: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    scenario_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    events: Mapped[list["IncidentEvent"]] = relationship(
        "IncidentEvent", back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentEvent(Base):  # type: ignore[misc]
    __tablename__ = "incident_events"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[IncidentEventType] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), default="system", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="events")


class WebhookSource(Base):  # type: ignore[misc]
    __tablename__ = "webhook_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class ProcessedWebhook(Base):  # type: ignore[misc]
    """Durable idempotency receipt for an authenticated webhook delivery."""

    __tablename__ = "processed_webhooks"

    delivery_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
