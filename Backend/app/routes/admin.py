import enum
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import (
    AppConfig,
    AuditLog,
    Comment,
    Draft,
    EngagementMetric,
    LearningWeight,
    NotificationLog,
    PublishedPost,
    SourceMaterial,
)
from ..schemas import AuditLogRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.config_state import get_or_create_app_config
from ..services.webhook_service import is_webhook_configured, send_test_webhook

router = APIRouter(prefix="/admin", tags=["admin"])


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    return value


def _serialize_rows(rows):
    output = []
    for row in rows:
        output.append({column.name: _serialize_value(getattr(row, column.name)) for column in row.__table__.columns})
    return output


@router.get("/config")
def read_config(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    config = get_or_create_app_config(db)
    return {
        "timezone": settings.timezone,
        "posting_window_start": settings.posting_window_start,
        "posting_window_end": settings.posting_window_end,
        "posting_enabled": config.posting_enabled,
        "comment_replies_enabled": config.comment_replies_enabled,
        "max_auto_replies": settings.max_auto_replies,
        "escalation_follower_threshold": settings.escalation_follower_threshold,
        "linkedin_api_mode": settings.linkedin_api_mode,
        "kill_switch": config.kill_switch,
    }


@router.post("/kill-switch/on")
def kill_switch_on(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    config = get_or_create_app_config(db)
    config.kill_switch = True
    db.commit()
    log_audit(db=db, actor="api", action="admin.kill_switch_on", resource_type="app_config", resource_id="1")
    return {"kill_switch": True}


@router.post("/kill-switch/off")
def kill_switch_off(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    config = get_or_create_app_config(db)
    config.kill_switch = False
    db.commit()
    log_audit(db=db, actor="api", action="admin.kill_switch_off", resource_type="app_config", resource_id="1")
    return {"kill_switch": False}


@router.post("/posting/on")
def posting_on(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    config = get_or_create_app_config(db)
    config.posting_enabled = True
    db.commit()
    log_audit(db=db, actor="api", action="admin.posting_on", resource_type="app_config", resource_id="1")
    return {"posting_enabled": True}


@router.post("/posting/off")
def posting_off(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    config = get_or_create_app_config(db)
    config.posting_enabled = False
    db.commit()
    log_audit(db=db, actor="api", action="admin.posting_off", resource_type="app_config", resource_id="1")
    return {"posting_enabled": False}


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()


@router.get("/algorithm-alignment")
def algorithm_alignment(_auth: None = Depends(require_read_access)):
    return {
        "rule_set": "linkedinAlgos.md",
        "enforced": {
            "hashtag_limit": "1-3 preferred, >3 blocked",
            "mention_overuse": "blocked when >3",
            "engagement_bait": "blocked",
            "external_links_in_body": "blocked",
            "posting_frequency_guard": "production guard enabled",
            "golden_hour_prompt": "enabled after manual publish confirmation",
            "topical_consistency": "adtech/ai niche prompts enforced",
            "comment_polling_windows": "10m/30m/2h over 48h monitoring window",
        },
    }


@router.get("/export-state")
def export_state(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "app": "linkedin_personal_brand",
            "mode": "single-user",
            "version_tag": "v4.0",
        },
        "config": _serialize_rows(db.query(AppConfig).all()),
        "drafts": _serialize_rows(db.query(Draft).order_by(Draft.created_at.desc()).all()),
        "posts": _serialize_rows(db.query(PublishedPost).order_by(PublishedPost.scheduled_time.desc()).all()),
        "comments": _serialize_rows(db.query(Comment).order_by(Comment.commented_at.desc()).all()),
        "sources": _serialize_rows(db.query(SourceMaterial).order_by(SourceMaterial.created_at.desc()).all()),
        "audit_logs": _serialize_rows(db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()),
        "learning_weights": _serialize_rows(db.query(LearningWeight).all()),
        "engagement_metrics": _serialize_rows(db.query(EngagementMetric).order_by(EngagementMetric.collected_at.desc()).all()),
        "notifications": _serialize_rows(db.query(NotificationLog).order_by(NotificationLog.created_at.desc()).all()),
    }


@router.get("/webhook-status")
def webhook_status(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    """Show webhook configuration status and recent delivery stats."""
    configured = is_webhook_configured()

    # Query recent webhook deliveries (last 24 hours)
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = (
        db.query(NotificationLog)
        .filter(NotificationLog.channel == "webhook")
        .filter(NotificationLog.created_at >= cutoff)
        .all()
    )
    success_count = sum(1 for r in recent if r.success)
    failed_count = sum(1 for r in recent if not r.success)

    # Last delivery
    last = (
        db.query(NotificationLog)
        .filter(NotificationLog.channel == "webhook")
        .order_by(NotificationLog.created_at.desc())
        .first()
    )
    last_delivery = None
    if last:
        last_delivery = {
            "event_type": last.event_type,
            "success": last.success,
            "created_at": last.created_at.isoformat() if last.created_at else None,
            "error_message": last.error_message,
        }

    return {
        "configured": configured,
        "url_set": configured,
        "last_delivery": last_delivery,
        "deliveries_24h": {
            "success": success_count,
            "failed": failed_count,
        },
    }


@router.post("/webhook-test")
def webhook_test(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Send a test payload to verify Zapier webhook connectivity."""
    result = send_test_webhook()
    log_audit(
        db=db,
        actor="api",
        action="admin.webhook_test",
        resource_type="webhook",
        detail=result,
    )
    return result
