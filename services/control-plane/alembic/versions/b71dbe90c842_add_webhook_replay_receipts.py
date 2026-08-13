"""add webhook replay receipts

Revision ID: b71dbe90c842
Revises: 36eb1e23b172
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b71dbe90c842"
down_revision: str | None = "36eb1e23b172"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processed_webhooks",
        sa.Column("delivery_id", sa.String(length=255), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("signature_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=op.f("fk_processed_webhooks_incident_id_incidents"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processed_webhooks")),
        sa.UniqueConstraint("delivery_id", name=op.f("uq_processed_webhooks_delivery_id")),
    )
    op.create_index(
        op.f("ix_processed_webhooks_delivery_id"),
        "processed_webhooks",
        ["delivery_id"],
        unique=True,
    )
    op.create_index(op.f("ix_processed_webhooks_id"), "processed_webhooks", ["id"], unique=False)
    op.create_index(
        op.f("ix_processed_webhooks_incident_id"),
        "processed_webhooks",
        ["incident_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_processed_webhooks_incident_id"), table_name="processed_webhooks")
    op.drop_index(op.f("ix_processed_webhooks_id"), table_name="processed_webhooks")
    op.drop_index(op.f("ix_processed_webhooks_delivery_id"), table_name="processed_webhooks")
    op.drop_table("processed_webhooks")
