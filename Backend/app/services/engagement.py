from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Comment, PublishedPost
from .comment_triage import triage_comment
from .config_state import is_comment_replies_enabled, is_kill_switch_on
from .linkedin import LinkedInApiError, fetch_recent_comments_for_post


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def polling_interval_for_post_age(post_age: timedelta) -> timedelta:
    if post_age <= timedelta(hours=2):
        return timedelta(minutes=10)
    if post_age <= timedelta(hours=12):
        return timedelta(minutes=30)
    return timedelta(hours=2)


def _is_post_due_for_poll(post: PublishedPost, now: datetime) -> bool:
    published_at = _as_utc(post.published_at)
    monitoring_until = _as_utc(post.comment_monitoring_until)
    last_poll = _as_utc(post.last_comment_poll_at)

    if not published_at:
        return False
    if not monitoring_until or now >= monitoring_until:
        return False

    interval = polling_interval_for_post_age(now - published_at)
    if not last_poll:
        return True
    return now - last_poll >= interval


def poll_and_store_comments(db: Session, since_minutes: int = 15) -> dict:
    if is_kill_switch_on(db):
        return {"processed_posts": 0, "new_comments": 0, "status": "kill_switch"}

    if settings.linkedin_api_mode != "api" or not settings.linkedin_api_token:
        return {"processed_posts": 0, "new_comments": 0, "status": "not_configured"}

    now = datetime.now(timezone.utc)
    candidate_posts = (
        db.query(PublishedPost)
        .filter(PublishedPost.linkedin_post_id.is_not(None))
        .filter(PublishedPost.published_at.is_not(None))
        .filter(PublishedPost.comment_monitoring_until.is_not(None))
        .all()
    )
    posts = [post for post in candidate_posts if _is_post_due_for_poll(post, now)]
    new_comments = 0
    errors = 0

    for post in posts:
        try:
            fetched = fetch_recent_comments_for_post(post.linkedin_post_id or "", since_minutes=since_minutes)
        except LinkedInApiError:
            errors += 1
            post.last_comment_poll_at = now
            continue
        for item in fetched:
            exists = db.query(Comment).filter(Comment.linkedin_comment_id == item.linkedin_comment_id).first()
            if exists:
                continue

            row = Comment(
                published_post_id=post.id,
                linkedin_comment_id=item.linkedin_comment_id,
                commenter_name=item.commenter_name,
                commenter_profile_url=item.commenter_profile_url,
                commenter_follower_count=item.commenter_follower_count,
                comment_text=item.comment_text,
            )

            triage = triage_comment(comment_text=row.comment_text, follower_count=row.commenter_follower_count)
            row.is_high_value = triage.high_value
            row.high_value_reason = triage.reason
            row.escalated = triage.high_value
            row.escalated_at = datetime.now(timezone.utc) if triage.high_value else None

            auto_reply_count = (
                db.query(Comment)
                .filter(Comment.published_post_id == row.published_post_id)
                .filter(Comment.auto_reply_sent.is_(True))
                .count()
            )
            if (
                triage.auto_reply
                and is_comment_replies_enabled(db)
                and auto_reply_count < settings.max_auto_replies
            ):
                row.auto_reply_sent = True
                row.auto_reply_text = "Thanks for the thoughtful comment."
                row.auto_reply_sent_at = datetime.now(timezone.utc)

            db.add(row)
            new_comments += 1

        post.last_comment_poll_at = now

    db.commit()
    return {"processed_posts": len(posts), "new_comments": new_comments, "errors": errors, "status": "ok"}
