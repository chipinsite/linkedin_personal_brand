"""add sources and citations

Revision ID: 0002_sources_and_citations
Revises: 0001_initial
Create Date: 2026-02-06 12:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_sources_and_citations"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("drafts", sa.Column("source_citations", sa.Text(), nullable=True))

    op.create_table(
        "source_materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("pillar_theme", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )


def downgrade() -> None:
    op.drop_table("source_materials")
    op.drop_column("drafts", "source_citations")
