from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Comment, PublishedPost
from .comment_reply import generate_auto_reply, generate_suggested_replies
from .comment_triage import triage_comment
from .config_state import is_comment_replies_enabled, is_kill_switch_on
from .linkedin import (
    LinkedInApiError,
    fetch_post_metrics,
    fetch_recent_comments_for_post,
)
from .telegram_service import send_escalation_notification


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
    """Poll LinkedIn for new comments and process them.

    For each new comment:
    - Triages to determine if high-value
    - Generates auto-reply if eligible (using LLM or fallback)
    - Sends escalation notification via Telegram if high-value

    Args:
        db: Database session
        since_minutes: Look back window for comments

    Returns:
        Dict with processed_posts, new_comments, escalations, errors, status
    """
    if is_kill_switch_on(db):
        return {"processed_posts": 0, "new_comments": 0, "escalations": 0, "status": "kill_switch"}

    if settings.linkedin_api_mode != "api" or not settings.linkedin_api_token:
        # Check for mock mode
        if not settings.linkedin_mock_comments_json:
            return {"processed_posts": 0, "new_comments": 0, "escalations": 0, "status": "not_configured"}

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
    escalations = 0
    errors = 0

    for post in posts:
        try:
            fetched = fetch_recent_comments_for_post(post.linkedin_post_id or "", since_minutes=since_minutes)
        except LinkedInApiError:
            errors += 1
            post.last_comment_poll_at = now
            continue

        # Get post summary for context in replies
        post_summary = post.content_body[:200] if post.content_body else None

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

            # Handle auto-reply for non-high-value comments
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
                # Generate contextual auto-reply using LLM or fallback
                row.auto_reply_sent = True
                row.auto_reply_text = generate_auto_reply(
                    comment_text=row.comment_text,
                    post_summary=post_summary,
                )
                row.auto_reply_sent_at = datetime.now(timezone.utc)

            db.add(row)
            db.flush()  # Get the row ID for escalation notification
            new_comments += 1

            # Send escalation notification for high-value comments
            if triage.high_value:
                suggested_replies = generate_suggested_replies(
                    comment_text=row.comment_text,
                    high_value_reason=triage.reason,
                    post_summary=post_summary,
                )
                send_escalation_notification(
                    db=db,
                    comment_id=str(row.id),
                    comment_text=row.comment_text,
                    commenter_name=row.commenter_name,
                    commenter_profile_url=row.commenter_profile_url,
                    commenter_follower_count=row.commenter_follower_count,
                    high_value_reason=triage.reason,
                    post_url=post.linkedin_post_url,
                    suggested_replies=suggested_replies,
                )
                escalations += 1

        post.last_comment_poll_at = now

    db.commit()
    return {
        "processed_posts": len(posts),
        "new_comments": new_comments,
        "escalations": escalations,
        "errors": errors,
        "status": "ok",
    }


def poll_and_store_metrics(db: Session) -> dict:
    """Poll LinkedIn for post metrics and update the database.

    Fetches metrics for all posts with a linkedin_post_id that were
    published in the last 7 days (active engagement window).

    Args:
        db: Database session

    Returns:
        Dict with updated_posts count, errors count, and status
    """
    if is_kill_switch_on(db):
        return {"updated_posts": 0, "errors": 0, "status": "kill_switch"}

    if settings.linkedin_api_mode != "api" or not settings.linkedin_api_token:
        # Check for mock mode
        if not settings.linkedin_mock_metrics_json:
            return {"updated_posts": 0, "errors": 0, "status": "not_configured"}

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # Get posts from the last 7 days with LinkedIn post IDs
    candidate_posts = (
        db.query(PublishedPost)
        .filter(PublishedPost.linkedin_post_id.is_not(None))
        .filter(PublishedPost.published_at.is_not(None))
        .filter(PublishedPost.published_at >= seven_days_ago)
        .all()
    )

    updated = 0
    errors = 0

    for post in candidate_posts:
        try:
            metrics = fetch_post_metrics(post.linkedin_post_id or "")

            # Update post metrics
            post.impressions = metrics.impressions
            post.reactions = metrics.reactions
            post.comments_count = metrics.comments_count
            post.shares = metrics.shares
            post.engagement_rate = metrics.engagement_rate
            post.last_metrics_update = now

            updated += 1
        except LinkedInApiError:
            errors += 1
            continue

    db.commit()
    return {"updated_posts": updated, "errors": errors, "status": "ok"}
