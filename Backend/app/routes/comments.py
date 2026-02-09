from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Comment
from ..schemas import CommentCreate, CommentRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.comment_reply import generate_suggested_replies
from ..services.comment_triage import triage_comment
from ..services.config_state import is_comment_replies_enabled, is_kill_switch_on


class ResolveEscalationPayload(BaseModel):
    """Payload for resolving an escalation."""
    reply_text: str | None = None
    action: str = "resolved"  # "resolved", "ignored", "replied"

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


@router.get("/escalated", response_model=list[CommentRead])
def list_escalated_comments(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    """List all currently escalated comments awaiting resolution."""
    return (
        db.query(Comment)
        .filter(Comment.escalated.is_(True))
        .filter(Comment.manual_reply_sent.is_(False))
        .order_by(Comment.escalated_at.desc())
        .all()
    )


@router.get("/{comment_id}", response_model=CommentRead)
def get_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Get a specific comment by ID."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get("/{comment_id}/suggested-replies")
def get_suggested_replies(
    comment_id: UUID,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Get suggested reply options for a comment.

    Useful for high-value comments that need manual response.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Get post for context
    post_summary = None
    if comment.published_post:
        post_summary = comment.published_post.content_body[:200] if comment.published_post.content_body else None

    replies = generate_suggested_replies(
        comment_text=comment.comment_text,
        high_value_reason=comment.high_value_reason,
        post_summary=post_summary,
    )

    return {"comment_id": str(comment_id), "suggested_replies": replies}


@router.post("/{comment_id}/resolve-escalation", response_model=CommentRead)
def resolve_escalation(
    comment_id: UUID,
    payload: ResolveEscalationPayload,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Resolve an escalated comment.

    Actions:
    - "resolved": Mark as resolved without reply
    - "ignored": Mark as ignored (no action taken)
    - "replied": Mark as manually replied with the provided reply_text
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if not comment.escalated:
        raise HTTPException(status_code=400, detail="Comment is not escalated")

    if payload.action == "replied":
        if not payload.reply_text:
            raise HTTPException(status_code=400, detail="reply_text required for 'replied' action")
        comment.manual_reply_sent = True
        comment.manual_reply_text = payload.reply_text
    elif payload.action in ("resolved", "ignored"):
        comment.manual_reply_sent = True  # Mark as handled even without reply
        comment.manual_reply_text = f"[{payload.action.upper()}]"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {payload.action}")

    db.commit()
    db.refresh(comment)

    log_audit(
        db=db,
        actor="api",
        action="comment.resolve_escalation",
        resource_type="comment",
        resource_id=str(comment.id),
        detail={"action": payload.action, "has_reply": bool(payload.reply_text)},
    )

    return comment
