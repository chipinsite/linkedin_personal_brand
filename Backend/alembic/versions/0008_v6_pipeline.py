"""V6 content pipeline items table

Revision ID: 0008_v6_pipeline
Revises: 0007_webhook_config
Create Date: 2026-02-10 14:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_v6_pipeline"
down_revision: Union[str, None] = "0007_webhook_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Use sa.String for enum columns to avoid SQLAlchemy auto CREATE TYPE on PostgreSQL.
    # Convert to native enums afterward (same pattern as 0001_initial).
    op.create_table(
        "content_pipeline_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        # Draft link (optional until Writer creates one)
        sa.Column("draft_id", sa.Uuid(), nullable=True),

        # Pipeline status (String first, converted to enum on PG)
        sa.Column("status", sa.String(length=32), nullable=False, server_default="backlog"),

        # Claim fields for atomic worker processing
        sa.Column("claimed_by", sa.String(length=128), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_stage", sa.String(length=32), nullable=True),
        sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True),

        # Quality gate results
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("readability_score", sa.Float(), nullable=True),
        sa.Column("fact_check_status", sa.String(length=32), nullable=True),

        # Revision tracking
        sa.Column("revision_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_revisions", sa.Integer(), nullable=False, server_default="3"),

        # Social amplification status (String first, converted to enum on PG)
        sa.Column("social_status", sa.String(length=32), nullable=True),

        # Error and scheduling
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),

        # Topic metadata (seeded by Scout)
        sa.Column("topic_keyword", sa.String(length=256), nullable=True),
        sa.Column("pillar_theme", sa.String(length=120), nullable=True),
        sa.Column("sub_theme", sa.String(length=120), nullable=True),

        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # On PostgreSQL, create native enum types and convert varchar columns.
    # SQLAlchemy persists Python enum NAMES (lowercase) by default.
    if is_pg:
        op.execute(
            "CREATE TYPE pipelinestatus AS ENUM ("
            "'backlog', 'todo', 'writing', 'review', "
            "'ready_to_publish', 'published', 'amplified', 'done'"
            ")"
        )
        op.execute(
            "CREATE TYPE socialstatus AS ENUM ("
            "'pending', 'amplified', 'monitoring_complete'"
            ")"
        )

        op.execute(
            "ALTER TABLE content_pipeline_items "
            "ALTER COLUMN status TYPE pipelinestatus USING status::pipelinestatus"
        )
        op.execute(
            "ALTER TABLE content_pipeline_items "
            "ALTER COLUMN social_status TYPE socialstatus USING social_status::socialstatus"
        )


def downgrade() -> None:
    op.drop_table("content_pipeline_items")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS socialstatus")
        op.execute("DROP TYPE IF EXISTS pipelinestatus")
