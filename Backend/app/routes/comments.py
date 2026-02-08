from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Comment
from ..schemas import CommentCreate, CommentRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.comment_triage import triage_comment
from ..services.config_state import is_comment_replies_enabled, is_kill_switch_on

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("", response_model=CommentRead)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    comment = Comment(**payload.model_dump())
    triage = triage_comment(
        comment_text=comment.comment_text,
        follower_count=comment.commenter_follower_count,
    )
    comment.is_high_value = triage.high_value
    comment.high_value_reason = triage.reason
    comment.escalated = triage.high_value
    comment.escalated_at = datetime.now(timezone.utc) if triage.high_value else None

    auto_reply_count = (
        db.query(Comment)
        .filter(Comment.published_post_id == comment.published_post_id)
        .filter(Comment.auto_reply_sent.is_(True))
        .count()
    )
    if (
        triage.auto_reply
        and not is_kill_switch_on(db)
        and is_comment_replies_enabled(db)
        and auto_reply_count < settings.max_auto_replies
    ):
        comment.auto_reply_sent = True
        comment.auto_reply_text = "Thanks for your perspective. I appreciate you adding this angle."
        comment.auto_reply_sent_at = datetime.now(timezone.utc)

    db.add(comment)
    db.commit()
    db.refresh(comment)
    log_audit(
        db=db,
        actor="api",
        action="comment.create",
        resource_type="comment",
        resource_id=str(comment.id),
        detail={"high_value": comment.is_high_value, "auto_reply_sent": comment.auto_reply_sent},
    )
    return comment


@router.get("", response_model=list[CommentRead])
def list_comments(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return db.query(Comment).order_by(Comment.commented_at.desc()).all()
