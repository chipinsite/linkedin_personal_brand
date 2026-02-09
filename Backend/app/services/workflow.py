from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Draft, DraftStatus, PostFormat, PostTone, PublishedPost
from .config_state import is_kill_switch_on, is_posting_enabled
from .content_generation import select_format_and_tone, select_theme
from .guardrails import validate_post
from .learning import get_effective_weight_maps
from .llm import generate_linkedin_post
from .research_ingestion import select_research_context
from .telegram_service import send_draft_approval_notification, send_telegram_message
from .time_utils import random_schedule_for_day


def _posting_frequency_guard(db: Session) -> None:
    # In production-like environments, prevent unusually high posting frequency.
    if settings.app_env == "test":
        return

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=20)
    recent_drafts = (
        db.query(func.count(Draft.id))
        .filter(Draft.created_at >= cutoff)
        .scalar()
    ) or 0
    if recent_drafts > 0:
        raise RuntimeError("Posting frequency guard: a draft already exists in the recent window")


def create_system_draft(db: Session) -> Draft:
    if is_kill_switch_on(db):
        raise RuntimeError("Kill switch is active")

    if not is_posting_enabled(db):
        raise RuntimeError("Posting is disabled")
    _posting_frequency_guard(db)

    pillar, sub_theme = select_theme()
    format_weights, tone_weights = get_effective_weight_maps(db)
    post_format, tone = select_format_and_tone(format_weights=format_weights, tone_weights=tone_weights)
    research_context, citations = select_research_context(db=db, pillar=pillar)
    content = generate_linkedin_post(
        pillar=pillar,
        sub_theme=sub_theme,
        post_format=post_format,
        tone=tone,
        research_context=research_context,
    )

    result = validate_post(content)
    draft = Draft(
        pillar_theme=pillar,
        sub_theme=sub_theme,
        format=post_format,
        tone=tone,
        content_body=content,
        status=DraftStatus.pending,
        guardrail_check_passed=result.passed,
        guardrail_violations=json.dumps(result.violations) if result.violations else None,
        source_citations=citations,
    )

    if not result.passed:
        # Fallback to a compliant concise template when validation fails.
        draft.content_body = (
            f"One practical lesson from {sub_theme.lower()} in {pillar.lower()}: clarity of operating cadence "
            "drives better outcomes than adding more tools.\n\n"
            "What process change has improved your campaign performance this year? #Adtech #AI"
        )
        second_pass = validate_post(draft.content_body)
        draft.guardrail_check_passed = second_pass.passed
        draft.guardrail_violations = json.dumps(second_pass.violations) if second_pass.violations else None
        if not second_pass.passed:
            draft.status = DraftStatus.rejected
            draft.rejection_reason = "GUARDRAIL_FAILURE"

    db.add(draft)
    db.commit()
    db.refresh(draft)

    if draft.status == DraftStatus.pending:
        send_approval_notification(db, draft)
    return draft


def send_approval_notification(db: Session, draft: Draft) -> bool:
    """Send draft approval notification via Telegram.

    Uses the enhanced notification format with inline keyboard buttons.

    Args:
        db: Database session
        draft: Draft to notify about

    Returns:
        True if notification was sent successfully
    """
    return send_draft_approval_notification(db=db, draft=draft)


def approve_draft_and_schedule(db: Session, draft: Draft, scheduled_time: datetime | None) -> PublishedPost:
    draft.status = DraftStatus.approved
    draft.approval_timestamp = datetime.now(timezone.utc)

    scheduled = scheduled_time or random_schedule_for_day()

    published = PublishedPost(
        draft_id=draft.id,
        content_body=draft.content_body,
        format=PostFormat(draft.format.value),
        tone=PostTone(draft.tone.value),
        scheduled_time=scheduled,
    )
    db.add(published)
    db.commit()
    db.refresh(published)
    return published


def publish_due_manual_posts(db: Session) -> int:
    if is_kill_switch_on(db) or not is_posting_enabled(db):
        return 0

    now = datetime.now(timezone.utc)
    due_posts = (
        db.query(PublishedPost)
        .filter(PublishedPost.scheduled_time.is_not(None))
        .filter(PublishedPost.scheduled_time <= now)
        .filter(PublishedPost.published_at.is_(None))
        .filter(PublishedPost.manual_publish_notified_at.is_(None))
        .all()
    )

    for post in due_posts:
        message = (
            "Manual Publish Reminder\n\n"
            "Your approved LinkedIn post is due now. Publish this content manually and then confirm via "
            f"POST /posts/{post.id}/confirm-manual-publish with linkedin_post_url.\n\n"
            f"{post.content_body}"
        )
        send_telegram_message(db=db, text=message, event_type="MANUAL_PUBLISH_REMINDER")
        post.manual_publish_notified_at = now
    db.commit()

    return len(due_posts)


def send_golden_hour_engagement_prompt(db: Session, post: PublishedPost) -> bool:
    text = (
        "Golden Hour Engagement Prompt\n\n"
        "For the next 60-90 minutes:\n"
        "- Reply quickly to substantive comments\n"
        "- Ask one follow-up question to deepen discussion\n"
        "- Avoid generic one-word replies\n"
        "- Keep conversation relevant to your niche topic\n\n"
        f"Post URL: {post.linkedin_post_url or 'not provided'}"
    )
    return send_telegram_message(db=db, text=text, event_type="GOLDEN_HOUR_PROMPT")
