"""Add pipeline_mode column to app_config

Revision ID: 0009_pipeline_mode
Revises: 0008_v6_pipeline
Create Date: 2026-02-10 22:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_pipeline_mode"
down_revision: Union[str, None] = "0008_v6_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Add pipeline_mode as String first, then convert on PostgreSQL.
    op.add_column(
        "app_config",
        sa.Column("pipeline_mode", sa.String(length=20), nullable=False, server_default="legacy"),
    )

    if is_pg:
        op.execute(
            "CREATE TYPE pipelinemode AS ENUM ("
            "'legacy', 'shadow', 'v6', 'disabled'"
            ")"
        )
        op.execute(
            "ALTER TABLE app_config "
            "ALTER COLUMN pipeline_mode TYPE pipelinemode USING pipeline_mode::pipelinemode"
        )


def downgrade() -> None:
    op.drop_column("app_config", "pipeline_mode")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS pipelinemode")
