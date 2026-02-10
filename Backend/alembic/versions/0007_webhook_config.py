"""add webhook config columns to app_config

Revision ID: 0007_webhook_config
Revises: 0006_user_auth
Create Date: 2026-02-10 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_webhook_config"
down_revision: Union[str, None] = "0006_user_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("app_config", sa.Column("zapier_webhook_url", sa.String(1024), nullable=True))
    op.add_column("app_config", sa.Column("zapier_webhook_secret", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("app_config", "zapier_webhook_secret")
    op.drop_column("app_config", "zapier_webhook_url")
