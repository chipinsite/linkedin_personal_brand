"""add learning metrics tables

Revision ID: 0005_learning_metrics
Revises: 0004_comment_monitoring_windows
Create Date: 2026-02-06 14:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_learning_metrics"
down_revision: Union[str, None] = "0004_comment_monitoring_windows"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "engagement_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("published_post_id", sa.Uuid(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("reactions", sa.Integer(), nullable=False),
        sa.Column("comments_count", sa.Integer(), nullable=False),
        sa.Column("shares", sa.Integer(), nullable=False),
        sa.Column("engagement_rate", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["published_post_id"], ["published_posts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "learning_weights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("format_weights_json", sa.Text(), nullable=False),
        sa.Column("tone_weights_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("learning_weights")
    op.drop_table("engagement_metrics")
