"""remove redundant webhook delivery constraint

Revision ID: c821f0b613ce
Revises: b71dbe90c842
Create Date: 2026-08-13
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c821f0b613ce"
down_revision: str | None = "b71dbe90c842"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The unique index created for ``index=True, unique=True`` already enforces
    # delivery idempotency; retaining a second constraint duplicates it.
    op.drop_constraint(
        op.f("uq_processed_webhooks_delivery_id"),
        "processed_webhooks",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        op.f("uq_processed_webhooks_delivery_id"),
        "processed_webhooks",
        ["delivery_id"],
    )
