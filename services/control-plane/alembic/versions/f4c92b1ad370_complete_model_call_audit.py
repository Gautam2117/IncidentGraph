"""complete model call audit fields

Revision ID: f4c92b1ad370
Revises: e3b17c2f829a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f4c92b1ad370"
down_revision: str | None = "e3b17c2f829a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_calls",
        sa.Column("prompt_version", sa.String(length=100), server_default="unknown", nullable=False),
    )
    op.add_column(
        "model_calls",
        sa.Column("graph_version", sa.String(length=100), server_default="unknown", nullable=False),
    )
    op.add_column(
        "model_calls", sa.Column("latency_ms", sa.Float(), server_default="0", nullable=False)
    )
    op.add_column(
        "model_calls",
        sa.Column(
            "structured_output",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("model_calls", "structured_output")
    op.drop_column("model_calls", "latency_ms")
    op.drop_column("model_calls", "graph_version")
    op.drop_column("model_calls", "prompt_version")
