from __future__ import annotations

from sqlalchemy.orm import Session

from ..config import settings
from ..models import AppConfig, PipelineMode


def get_or_create_app_config(db: Session) -> AppConfig:
    config = db.query(AppConfig).filter(AppConfig.id == 1).first()
    if config:
        return config

    config = AppConfig(
        id=1,
        posting_enabled=settings.posting_enabled,
        comment_replies_enabled=settings.comment_replies_enabled,
        kill_switch=settings.kill_switch,
        pipeline_mode=PipelineMode.legacy,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def is_kill_switch_on(db: Session) -> bool:
    return get_or_create_app_config(db).kill_switch


def is_posting_enabled(db: Session) -> bool:
    return get_or_create_app_config(db).posting_enabled


def is_comment_replies_enabled(db: Session) -> bool:
    return get_or_create_app_config(db).comment_replies_enabled


def get_pipeline_mode(db: Session) -> PipelineMode:
    """Return the current pipeline mode from persistent config."""
    config = get_or_create_app_config(db)
    mode = getattr(config, "pipeline_mode", None)
    if mode is None:
        return PipelineMode.legacy
    return mode
