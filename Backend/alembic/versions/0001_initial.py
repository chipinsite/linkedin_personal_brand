"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-06 11:55:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("posting_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("comment_replies_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("kill_switch", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Use sa.String for all enum columns to avoid SQLAlchemy's automatic
    # CREATE TYPE on PostgreSQL. We alter them to native enums afterward.
    op.create_table(
        "drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pillar_theme", sa.String(length=120), nullable=False),
        sa.Column("sub_theme", sa.String(length=120), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("tone", sa.String(length=20), nullable=False),
        sa.Column("content_body", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("carousel_document_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approval_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(length=256), nullable=True),
        sa.Column("guardrail_check_passed", sa.Boolean(), nullable=False),
        sa.Column("guardrail_violations", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "published_posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("draft_id", sa.Uuid(), nullable=False),
        sa.Column("linkedin_post_id", sa.String(length=128), nullable=True),
        sa.Column("linkedin_post_url", sa.String(length=512), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_publish_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_publish_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_body", sa.Text(), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("tone", sa.String(length=20), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("reactions", sa.Integer(), nullable=True),
        sa.Column("comments_count", sa.Integer(), nullable=True),
        sa.Column("shares", sa.Integer(), nullable=True),
        sa.Column("engagement_rate", sa.Float(), nullable=True),
        sa.Column("last_metrics_update", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["draft_id"], ["drafts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("published_post_id", sa.Uuid(), nullable=False),
        sa.Column("linkedin_comment_id", sa.String(length=128), nullable=True),
        sa.Column("commenter_name", sa.String(length=120), nullable=False),
        sa.Column("commenter_profile_url", sa.String(length=512), nullable=True),
        sa.Column("commenter_follower_count", sa.Integer(), nullable=True),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("commented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_high_value", sa.Boolean(), nullable=False),
        sa.Column("high_value_reason", sa.String(length=64), nullable=True),
        sa.Column("auto_reply_sent", sa.Boolean(), nullable=False),
        sa.Column("auto_reply_text", sa.Text(), nullable=True),
        sa.Column("auto_reply_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated", sa.Boolean(), nullable=False),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manual_reply_sent", sa.Boolean(), nullable=False),
        sa.Column("manual_reply_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["published_post_id"], ["published_posts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # On PostgreSQL, create native enum types and convert the varchar columns.
    # SQLite stores enums as plain strings so no conversion needed.
    if is_pg:
        op.execute("CREATE TYPE postformat AS ENUM ('TEXT', 'IMAGE', 'CAROUSEL')")
        op.execute("CREATE TYPE posttone AS ENUM ('EDUCATIONAL', 'OPINIONATED', 'DIRECT', 'EXPLORATORY')")
        op.execute("CREATE TYPE draftstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')")

        op.execute("ALTER TABLE drafts ALTER COLUMN format TYPE postformat USING format::postformat")
        op.execute("ALTER TABLE drafts ALTER COLUMN tone TYPE posttone USING tone::posttone")
        op.execute("ALTER TABLE drafts ALTER COLUMN status TYPE draftstatus USING status::draftstatus")
        op.execute("ALTER TABLE published_posts ALTER COLUMN format TYPE postformat USING format::postformat")
        op.execute("ALTER TABLE published_posts ALTER COLUMN tone TYPE posttone USING tone::posttone")


def downgrade() -> None:
    op.drop_table("comments")
    op.drop_table("published_posts")
    op.drop_table("notification_logs")
    op.drop_table("drafts")
    op.drop_table("app_config")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS draftstatus")
        op.execute("DROP TYPE IF EXISTS posttone")
        op.execute("DROP TYPE IF EXISTS postformat")
