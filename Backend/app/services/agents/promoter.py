"""V6 Promoter Agent.

Claims PUBLISHED pipeline items and sends Telegram engagement reminders
to encourage golden-hour author participation. Transitions items to
AMPLIFIED and then to DONE.

The Promoter ensures the author engages with their audience during the
critical first 60-90 minutes after publication (the "golden hour"),
which is a key LinkedIn algorithm signal.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from ...models import ContentPipelineItem, Draft, PipelineStatus, SocialStatus
from ..claim_lock import attempt_claim, release_claim, verify_claim
from ..pipeline import get_unclaimed_items_by_status, transition
from ..telegram_service import send_telegram_message

logger = logging.getLogger(__name__)

WORKER_ID_PREFIX = "promoter"


def _worker_id() -> str:
    return f"{WORKER_ID_PREFIX}-{uuid.uuid4().hex[:8]}"


def process_one_item(db: Session, item: ContentPipelineItem, worker_id: str) -> bool:
    """Process a single PUBLISHED pipeline item.

    1. Send Telegram golden-hour engagement reminder
    2. Update social_status to AMPLIFIED
    3. Transition pipeline item PUBLISHED → AMPLIFIED → DONE

    Args:
        db: Database session
        item: Pipeline item at PUBLISHED status
        worker_id: Unique worker identifier

    Returns:
        True if item was successfully promoted
    """
    # Build engagement prompt message
    draft = None
    if item.draft_id:
        draft = db.query(Draft).filter_by(id=item.draft_id).first()

    content_preview = ""
    if draft and draft.content_body:
        content_preview = draft.content_body[:200] + ("..." if len(draft.content_body) > 200 else "")

    # Send engagement reminder via Telegram
    send_telegram_message(
        db=db,
        text=(
            "V6 Pipeline — Engagement Reminder\n\n"
            f"Pipeline item: {str(item.id)[:8]}...\n"
            f"Theme: {item.pillar_theme or 'N/A'}\n\n"
            "Golden Hour Actions (next 60-90 minutes):\n"
            "- Reply quickly to substantive comments\n"
            "- Ask one follow-up question to deepen discussion\n"
            "- Avoid generic one-word replies\n"
            "- Keep conversation relevant to your niche topic\n\n"
            f"Content: {content_preview}"
        ),
        event_type="V6_ENGAGEMENT_PROMPT",
    )

    # Update social status
    item.social_status = SocialStatus.amplified
    db.commit()

    # Transition PUBLISHED → AMPLIFIED
    transition(db, item.id, PipelineStatus.published, PipelineStatus.amplified)

    # Transition AMPLIFIED → DONE (completes the pipeline lifecycle)
    transition(db, item.id, PipelineStatus.amplified, PipelineStatus.done)

    # Update social status to monitoring complete
    item.social_status = SocialStatus.monitoring_complete
    db.commit()

    release_claim(db, item.id, "promote")

    logger.info("Promoter: item %s → DONE (engagement prompt sent)", item.id)
    return True


def run_promoter(db: Session, max_items: int = 3) -> int:
    """Execute the Promoter agent.

    Claims unclaimed PUBLISHED items, sends engagement reminders,
    and transitions through AMPLIFIED to DONE.

    Args:
        db: Database session
        max_items: Maximum items to process in one run

    Returns:
        Number of items successfully promoted
    """
    unclaimed = get_unclaimed_items_by_status(db, PipelineStatus.published)
    if not unclaimed:
        logger.debug("Promoter: no unclaimed PUBLISHED items")
        return 0

    worker_id = _worker_id()
    promoted_count = 0

    for item in unclaimed[:max_items]:
        if not attempt_claim(db, item.id, "promote", worker_id):
            continue

        if not verify_claim(db, item.id, "promote", worker_id):
            continue

        if process_one_item(db, item, worker_id):
            promoted_count += 1

    logger.info(
        "Promoter: %d/%d items promoted",
        promoted_count, len(unclaimed[:max_items]),
    )
    return promoted_count
