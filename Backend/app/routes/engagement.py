from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PublishedPost
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.engagement import _is_post_due_for_poll, poll_and_store_comments
from datetime import datetime, timezone

router = APIRouter(prefix="/engagement", tags=["engagement"])


@router.post("/poll")
def poll_comments(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    result = poll_and_store_comments(db=db, since_minutes=15)
    log_audit(
        db=db,
        actor="api",
        action="engagement.poll",
        resource_type="comment",
        detail=result,
    )
    return result


@router.get("/status")
def monitoring_status(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    now = datetime.now(timezone.utc)
    monitored = (
        db.query(PublishedPost)
        .filter(PublishedPost.published_at.is_not(None))
        .filter(PublishedPost.comment_monitoring_until.is_not(None))
        .all()
    )
    active = [p for p in monitored if p.comment_monitoring_until and p.comment_monitoring_until > now]
    due = [p for p in active if _is_post_due_for_poll(p, now)]
    return {
        "monitored_total": len(monitored),
        "active_total": len(active),
        "due_total": len(due),
    }
