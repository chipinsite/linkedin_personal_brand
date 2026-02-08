import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PublishedPost
from ..schemas import ManualPublishConfirm, PostMetricsUpdate, PublishedPostRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.learning import record_post_metrics
from ..services.workflow import publish_due_manual_posts, send_golden_hour_engagement_prompt

router = APIRouter(prefix="/posts", tags=["posts"])


def _extract_linkedin_post_id(url: str) -> str | None:
    cleaned = url.strip().rstrip("/")
    if not cleaned:
        return None
    if "/" not in cleaned:
        return cleaned
    return cleaned.rsplit("/", 1)[-1] or None


@router.get("", response_model=list[PublishedPostRead])
def list_posts(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return db.query(PublishedPost).order_by(PublishedPost.scheduled_time.desc().nullslast()).all()


@router.get("/{post_id}", response_model=PublishedPostRead)
def get_post(post_id: uuid.UUID, db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    post = db.query(PublishedPost).filter(PublishedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/publish-due")
def publish_due(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    processed = publish_due_manual_posts(db)
    log_audit(
        db=db,
        actor="api",
        action="post.publish_due",
        resource_type="published_post",
        detail={"processed": processed},
    )
    return {"processed": processed}


@router.post("/{post_id}/confirm-manual-publish", response_model=PublishedPostRead)
def confirm_manual_publish(
    post_id: uuid.UUID,
    payload: ManualPublishConfirm,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    post = db.query(PublishedPost).filter(PublishedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    now = datetime.now(timezone.utc)
    post.linkedin_post_url = payload.linkedin_post_url
    post.linkedin_post_id = post.linkedin_post_id or _extract_linkedin_post_id(payload.linkedin_post_url)
    post.published_at = now
    post.actual_publish_time = now
    post.comment_monitoring_started_at = now
    post.comment_monitoring_until = now + timedelta(hours=48)
    post.last_comment_poll_at = None
    db.commit()
    db.refresh(post)
    send_golden_hour_engagement_prompt(db=db, post=post)
    log_audit(
        db=db,
        actor="api",
        action="post.confirm_manual_publish",
        resource_type="published_post",
        resource_id=str(post.id),
        detail={"linkedin_post_url": payload.linkedin_post_url},
    )
    return post


@router.post("/{post_id}/metrics", response_model=PublishedPostRead)
def update_post_metrics(
    post_id: uuid.UUID,
    payload: PostMetricsUpdate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    post = db.query(PublishedPost).filter(PublishedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    record_post_metrics(
        db=db,
        post=post,
        impressions=payload.impressions,
        reactions=payload.reactions,
        comments_count=payload.comments_count,
        shares=payload.shares,
    )
    db.refresh(post)
    log_audit(
        db=db,
        actor="api",
        action="post.metrics_update",
        resource_type="published_post",
        resource_id=str(post.id),
        detail=payload.model_dump(),
    )
    return post
