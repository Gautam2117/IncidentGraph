"""persist evaluation summaries

Revision ID: d2a6f14bd2ef
Revises: c821f0b613ce
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2a6f14bd2ef"
down_revision: str | None = "c821f0b613ce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("external_id", sa.String(64), nullable=True))
    op.add_column(
        "evaluation_runs",
        sa.Column("benchmark_mode", sa.String(20), nullable=False, server_default="legacy"),
    )
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "evaluation_runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute("UPDATE evaluation_runs SET external_id = 'legacy_' || id::text")
    op.alter_column("evaluation_runs", "external_id", nullable=False)
    op.create_index(
        op.f("ix_evaluation_runs_external_id"),
        "evaluation_runs",
        ["external_id"],
        unique=True,
    )
    op.alter_column("evaluation_runs", "benchmark_mode", server_default=None)
    op.alter_column("evaluation_runs", "summary", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_runs_external_id"), table_name="evaluation_runs")
    op.drop_column("evaluation_runs", "completed_at")
    op.drop_column("evaluation_runs", "summary")
    op.drop_column("evaluation_runs", "benchmark_mode")
    op.drop_column("evaluation_runs", "external_id")
