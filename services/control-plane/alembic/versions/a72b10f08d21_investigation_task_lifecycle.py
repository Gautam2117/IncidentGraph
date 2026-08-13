"""investigation task lifecycle

Revision ID: a72b10f08d21
Revises: f4c92b1ad370
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a72b10f08d21"
down_revision: str | None = "f4c92b1ad370"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("investigations", sa.Column("task_id", sa.String(length=255), nullable=True))
    op.add_column(
        "investigations",
        sa.Column(
            "cancellation_requested", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    op.create_index(op.f("ix_investigations_task_id"), "investigations", ["task_id"], unique=False)
    op.create_unique_constraint(
        op.f("uq_investigations_incident_id"), "investigations", ["incident_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_investigations_incident_id"), "investigations", type_="unique"
    )
    op.drop_index(op.f("ix_investigations_task_id"), table_name="investigations")
    op.drop_column("investigations", "cancellation_requested")
    op.drop_column("investigations", "task_id")
