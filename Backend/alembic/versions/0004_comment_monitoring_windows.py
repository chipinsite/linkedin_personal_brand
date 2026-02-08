"""add comment monitoring windows

Revision ID: 0004_comment_monitoring_windows
Revises: 0003_audit_logs
Create Date: 2026-02-06 13:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_comment_monitoring_windows"
down_revision: Union[str, None] = "0003_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("published_posts", sa.Column("comment_monitoring_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("published_posts", sa.Column("comment_monitoring_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("published_posts", sa.Column("last_comment_poll_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("published_posts", "last_comment_poll_at")
    op.drop_column("published_posts", "comment_monitoring_until")
    op.drop_column("published_posts", "comment_monitoring_started_at")
