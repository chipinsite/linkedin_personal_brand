from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import AuditLog
from ..schemas import AuditLogRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.config_state import get_or_create_app_config

router = APIRouter(prefix="/admin", tags=["admin"])


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
