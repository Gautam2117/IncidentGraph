"""version knowledge documents

Revision ID: e3b17c2f829a
Revises: d2a6f14bd2ef
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3b17c2f829a"
down_revision: str | None = "d2a6f14bd2ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_documents",
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        op.f("ix_knowledge_documents_status"),
        "knowledge_documents",
        ["status"],
        unique=False,
    )
    op.alter_column("knowledge_documents", "status", server_default=None)
    op.alter_column("knowledge_documents", "version", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_documents_status"), table_name="knowledge_documents")
    op.drop_column("knowledge_documents", "version")
    op.drop_column("knowledge_documents", "status")
