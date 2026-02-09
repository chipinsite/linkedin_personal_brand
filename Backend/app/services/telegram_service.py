"""Telegram Service.

Provides messaging capabilities for the Telegram notification channel:
- Simple text messages
- Messages with inline keyboard buttons
- Draft approval notification formatting
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import NotificationLog

if TYPE_CHECKING:
    from ..models import Draft

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Core Messaging
# ─────────────────────────────────────────────────────────────────────────────

def _is_telegram_configured() -> bool:
    """Check if Telegram credentials are configured."""
    return bool(settings.telegram_bot_token and settings.telegram_chat_id)


def _log_notification(
    db: Session,
    event_type: str,
    payload: dict,
    success: bool,
    error_message: str | None = None,
) -> None:
    """Log notification attempt to database."""
    db.add(
        NotificationLog(
            channel="telegram",
            event_type=event_type,
            payload=json.dumps(payload),
            success=success,
            error_message=error_message,
        )
    )
    db.commit()


def send_telegram_message(db: Session, text: str, event_type: str) -> bool:
    """Send a simple text message via Telegram.

    Args:
        db: Database session
        text: Message text
        event_type: Event type for logging

    Returns:
        True if message was sent successfully
    """
    payload = {"chat_id": settings.telegram_chat_id, "text": text}

    if not _is_telegram_configured():
        _log_notification(
            db, event_type, payload, False,
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
        )
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        response = httpx.post(url, json=payload, timeout=10)
        ok = response.status_code == 200
        _log_notification(db, event_type, payload, ok, None if ok else response.text)
        return ok
    except Exception as exc:
        logger.warning(f"Telegram send failed: {exc}")
        _log_notification(db, event_type, payload, False, str(exc))
        return False


def send_telegram_message_with_keyboard(
    db: Session,
    text: str,
    event_type: str,
    inline_keyboard: list[list[dict]],
    parse_mode: str | None = None,
) -> bool:
    """Send a message with inline keyboard buttons.

    Args:
        db: Database session
        text: Message text
        event_type: Event type for logging
        inline_keyboard: Keyboard layout [[{text, callback_data}, ...], ...]
        parse_mode: Optional parse mode (Markdown, HTML)

    Returns:
        True if message was sent successfully
    """
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": inline_keyboard},
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    if not _is_telegram_configured():
        _log_notification(
            db, event_type, payload, False,
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
        )
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        response = httpx.post(url, json=payload, timeout=10)
        ok = response.status_code == 200
        _log_notification(db, event_type, payload, ok, None if ok else response.text)
        return ok
    except Exception as exc:
        logger.warning(f"Telegram send with keyboard failed: {exc}")
        _log_notification(db, event_type, payload, False, str(exc))
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Draft Notification Formatting
# ─────────────────────────────────────────────────────────────────────────────

def format_draft_notification(draft: Draft) -> str:
    """Format a draft for Telegram approval notification.

    Matches CLAUDE.md section 6.2 notification payload format.

    Args:
        draft: Draft to format

    Returns:
        Formatted notification text
    """
    # Extract sources preview
    sources_preview = ""
    if draft.source_citations:
        try:
            items = json.loads(draft.source_citations)
            if isinstance(items, list) and items:
                lines = [f"• {item.get('source', 'Unknown')}" for item in items[:3]]
                sources_preview = "\n\nSources:\n" + "\n".join(lines)
        except (json.JSONDecodeError, TypeError):
            pass

    # Guardrail status
    guardrail_status = "✅ Passed" if draft.guardrail_check_passed else "⚠️ Check manually"

    # Build notification text
    text = f"""📝 Draft Ready for Approval

Theme: {draft.pillar_theme} > {draft.sub_theme}
Format: {draft.format.value}
Tone: {draft.tone.value}
Guardrails: {guardrail_status}{sources_preview}

─────────────────────────

{draft.content_body}

─────────────────────────

Commands:
/approve {draft.id}
/reject {draft.id} <reason>
/preview {draft.id}"""

    return text


def build_draft_keyboard(draft_id: str) -> list[list[dict]]:
    """Build inline keyboard for draft approval.

    Args:
        draft_id: UUID of the draft

    Returns:
        Inline keyboard layout
    """
    # Callback data format: action:id (must be under 64 bytes)
    short_id = str(draft_id)[:8]  # Use first 8 chars of UUID for callback
    return [
        [
            {"text": "✅ Approve", "callback_data": f"approve:{short_id}"},
            {"text": "❌ Reject", "callback_data": f"reject:{short_id}"},
        ],
        [
            {"text": "👁 Preview Full", "callback_data": f"preview:{short_id}"},
        ],
    ]


def send_draft_approval_notification(db: Session, draft: Draft) -> bool:
    """Send draft approval notification with inline keyboard.

    Args:
        db: Database session
        draft: Draft to notify about

    Returns:
        True if notification was sent successfully
    """
    text = format_draft_notification(draft)
    keyboard = build_draft_keyboard(str(draft.id))

    return send_telegram_message_with_keyboard(
        db=db,
        text=text,
        event_type="DRAFT_APPROVAL",
        inline_keyboard=keyboard,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Comment Escalation Notifications
# ─────────────────────────────────────────────────────────────────────────────

def format_escalation_notification(
    comment_text: str,
    commenter_name: str,
    commenter_profile_url: str | None,
    commenter_follower_count: int | None,
    high_value_reason: str | None,
    post_url: str | None,
    suggested_replies: list[str] | None = None,
) -> str:
    """Format a comment escalation notification.

    Matches CLAUDE.md section 6.2 escalation payload format.

    Args:
        comment_text: The comment text
        commenter_name: Name of the commenter
        commenter_profile_url: LinkedIn profile URL (if available)
        commenter_follower_count: Follower count (if available)
        high_value_reason: Why this was flagged as high-value
        post_url: URL of the LinkedIn post
        suggested_replies: Optional list of suggested reply options

    Returns:
        Formatted notification text
    """
    # Reason display mapping
    reason_display = {
        "PARTNERSHIP_SIGNAL": "Partnership signal",
        "TECHNICAL_QUESTION": "Technical question",
        "OBJECTION": "Objection/Challenge",
        "INFLUENTIAL": "Influential commenter",
        "MEDIA_INQUIRY": "Media inquiry",
    }

    reason_text = reason_display.get(high_value_reason, high_value_reason or "High-value")
    follower_text = f"{commenter_follower_count:,}" if commenter_follower_count else "Unknown"
    profile_text = commenter_profile_url or "Not available"
    post_text = post_url or "Not available"

    # Build suggested replies section
    replies_section = ""
    if suggested_replies:
        replies_lines = [f"{i+1}. {reply}" for i, reply in enumerate(suggested_replies)]
        replies_section = "\n\nSuggested Replies:\n" + "\n".join(replies_lines)

    text = f"""🔔 High Value Comment Detected

Post: {post_text}

Commenter: {commenter_name}
Profile: {profile_text}
Followers: {follower_text}

─────────────────────────

{comment_text}

─────────────────────────

Escalation Reason: {reason_text}{replies_section}

Actions:
📤 Reply manually on LinkedIn
🚫 Ignore if not relevant"""

    return text


def build_escalation_keyboard(comment_id: str) -> list[list[dict]]:
    """Build inline keyboard for escalation notification.

    Args:
        comment_id: UUID of the comment

    Returns:
        Inline keyboard layout
    """
    short_id = str(comment_id)[:8]
    return [
        [
            {"text": "✅ Mark Resolved", "callback_data": f"resolve:{short_id}"},
            {"text": "🚫 Ignore", "callback_data": f"ignore:{short_id}"},
        ],
    ]


def send_escalation_notification(
    db: Session,
    comment_id: str,
    comment_text: str,
    commenter_name: str,
    commenter_profile_url: str | None,
    commenter_follower_count: int | None,
    high_value_reason: str | None,
    post_url: str | None,
    suggested_replies: list[str] | None = None,
) -> bool:
    """Send comment escalation notification with inline keyboard.

    Args:
        db: Database session
        comment_id: Comment UUID for callback
        comment_text: The comment text
        commenter_name: Name of the commenter
        commenter_profile_url: LinkedIn profile URL
        commenter_follower_count: Follower count
        high_value_reason: Why this was flagged
        post_url: URL of the LinkedIn post
        suggested_replies: Optional suggested reply options

    Returns:
        True if notification was sent successfully
    """
    text = format_escalation_notification(
        comment_text=comment_text,
        commenter_name=commenter_name,
        commenter_profile_url=commenter_profile_url,
        commenter_follower_count=commenter_follower_count,
        high_value_reason=high_value_reason,
        post_url=post_url,
        suggested_replies=suggested_replies,
    )
    keyboard = build_escalation_keyboard(comment_id)

    return send_telegram_message_with_keyboard(
        db=db,
        text=text,
        event_type="COMMENT_ESCALATION",
        inline_keyboard=keyboard,
    )
