"""V6 Publisher Agent.

Claims READY_TO_PUBLISH pipeline items, creates a PublishedPost record,
fires the Zapier webhook (post.publish_ready), and transitions to PUBLISHED.

The Publisher bridges the V6 pipeline to the existing publishing workflow:
- Creates a PublishedPost linked to the pipeline item's draft
- Triggers webhook for automated LinkedIn posting via Zapier
- Sends Telegram manual-publish reminder as fallback
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ...models import (
    ContentPipelineItem,
    Draft,
    PipelineStatus,
    PostFormat,
    PostTone,
    PublishedPost,
)
from ..claim_lock import attempt_claim, release_claim, verify_claim
from ..pipeline import get_unclaimed_items_by_status, transition
from ..telegram_service import send_telegram_message
from ..time_utils import random_schedule_for_day
from ..webhook_service import send_webhook

logger = logging.getLogger(__name__)

WORKER_ID_PREFIX = "publisher"


def _worker_id() -> str:
    return f"{WORKER_ID_PREFIX}-{uuid.uuid4().hex[:8]}"


def process_one_item(db: Session, item: ContentPipelineItem, worker_id: str, shadow_mode: bool = False) -> bool:
    """Process a single READY_TO_PUBLISH pipeline item.

    1. Retrieve the linked draft
    2. Create a PublishedPost with scheduled time
    3. Fire Zapier webhook (post.publish_ready) — SKIPPED in shadow mode
    4. Send Telegram manual-publish reminder — SKIPPED in shadow mode
    5. Transition pipeline item to PUBLISHED

    Args:
        db: Database session
        item: Pipeline item at READY_TO_PUBLISH status
        worker_id: Unique worker identifier
        shadow_mode: If True, skip webhook and Telegram (dry-run)

    Returns:
        True if item was successfully published
    """
    # Get the linked draft
    if not item.draft_id:
        logger.warning("Publisher: item %s has no draft_id — skipping", item.id)
        release_claim(db, item.id, "publish")
        return False

    draft = db.query(Draft).filter_by(id=item.draft_id).first()
    if not draft:
        logger.warning(
            "Publisher: draft %s not found for item %s — skipping",
            item.draft_id, item.id,
        )
        release_claim(db, item.id, "publish")
        return False

    # Create a PublishedPost record (bridges V6 pipeline to legacy publish model)
    scheduled = random_schedule_for_day()
    now = datetime.now(timezone.utc)

    published_post = PublishedPost(
        draft_id=draft.id,
        content_body=draft.content_body,
        format=PostFormat(draft.format.value) if draft.format else PostFormat.text,
        tone=PostTone(draft.tone.value) if draft.tone else PostTone.educational,
        scheduled_time=scheduled,
        manual_publish_notified_at=now,
    )
    db.add(published_post)
    db.commit()
    db.refresh(published_post)

    if shadow_mode:
        # Shadow mode: log the event but do NOT fire webhook or Telegram
        logger.info(
            "Publisher SHADOW: item %s processed (dry-run) — "
            "webhook and Telegram skipped",
            item.id,
        )
    else:
        # Fire Zapier webhook — primary automated publishing path
        send_webhook(
            db=db,
            event="post.publish_ready",
            data={
                "post_id": str(published_post.id),
                "pipeline_item_id": str(item.id),
                "content": draft.content_body,
                "format": draft.format.value if draft.format else "TEXT",
                "pillar_theme": item.pillar_theme or draft.pillar_theme or "",
                "sub_theme": item.sub_theme or draft.sub_theme or "",
            },
        )

        # Send Telegram manual-publish reminder as fallback
        send_telegram_message(
            db=db,
            text=(
                "V6 Pipeline — Ready to Publish\n\n"
                f"Pipeline item: {str(item.id)[:8]}...\n"
                f"Theme: {item.pillar_theme or 'N/A'}\n"
                f"Sub-theme: {item.sub_theme or 'N/A'}\n\n"
                f"{draft.content_body[:500]}\n\n"
                "Zapier webhook has been fired. Confirm publication when live."
            ),
            event_type="V6_PUBLISH_READY",
        )

    # Transition pipeline item to PUBLISHED
    transition(db, item.id, PipelineStatus.ready_to_publish, PipelineStatus.published)
    release_claim(db, item.id, "publish")

    logger.info(
        "Publisher: item %s → PUBLISHED (post=%s)",
        item.id, published_post.id,
    )
    return True


def run_publisher(db: Session, max_items: int = 3, shadow_mode: bool = False) -> int:
    """Execute the Publisher agent.

    Claims unclaimed READY_TO_PUBLISH items, creates PublishedPost records,
    fires webhooks, and transitions to PUBLISHED.

    In shadow mode, all pipeline processing occurs normally (item transitions,
    PublishedPost creation) but webhook and Telegram notifications are skipped.

    Args:
        db: Database session
        max_items: Maximum items to process in one run
        shadow_mode: If True, skip external notifications (dry-run)

    Returns:
        Number of items successfully published
    """
    unclaimed = get_unclaimed_items_by_status(db, PipelineStatus.ready_to_publish)
    if not unclaimed:
        logger.debug("Publisher: no unclaimed READY_TO_PUBLISH items")
        return 0

    worker_id = _worker_id()
    published_count = 0

    for item in unclaimed[:max_items]:
        if not attempt_claim(db, item.id, "publish", worker_id):
            continue

        if not verify_claim(db, item.id, "publish", worker_id):
            continue

        if process_one_item(db, item, worker_id, shadow_mode=shadow_mode):
            published_count += 1

    mode_label = " (SHADOW)" if shadow_mode else ""
    logger.info(
        "Publisher%s: %d/%d items published",
        mode_label, published_count, len(unclaimed[:max_items]),
    )
    return published_count
