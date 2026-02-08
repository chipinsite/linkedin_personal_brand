"""add audit logs

Revision ID: 0003_audit_logs
Revises: 0002_sources_and_citations
Create Date: 2026-02-06 13:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_audit_logs"
down_revision: Union[str, None] = "0002_sources_and_citations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("detail_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
