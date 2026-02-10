"""V6 Writer Agent.

Claims TODO pipeline items, generates LinkedIn post drafts using the
existing content engine, links the draft back to the pipeline item,
and transitions to REVIEW.

On generation failure, transitions back to TODO with error details.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from ...models import ContentPipelineItem, PipelineStatus
from ..claim_lock import attempt_claim, release_claim, verify_claim
from ..content_engine import generate_draft
from ..pipeline import (
    get_unclaimed_items_by_status,
    increment_revision,
    transition,
)
from ..research_ingestion import select_research_context

logger = logging.getLogger(__name__)

WORKER_ID_PREFIX = "writer"


def _worker_id() -> str:
    return f"{WORKER_ID_PREFIX}-{uuid.uuid4().hex[:8]}"


def process_one_item(db: Session, item: ContentPipelineItem, worker_id: str) -> bool:
    """Process a single pipeline item through the Writer stage.

    Args:
        db: Database session
        item: Pipeline item at TODO status
        worker_id: Unique worker identifier

    Returns:
        True if draft was generated and item transitioned to REVIEW
    """
    # Transition TODO → WRITING
    try:
        transition(db, item.id, PipelineStatus.todo, PipelineStatus.writing)
    except Exception as e:
        logger.warning("Writer: failed to transition item %s to WRITING: %s", item.id, e)
        release_claim(db, item.id, "writing")
        return False

    # Generate draft using content engine
    try:
        research_context, _ = select_research_context(
            db=db,
            pillar=item.pillar_theme or "Adtech fundamentals and market dynamics",
        )

        result = generate_draft(
            db=db,
            research_context=research_context,
            pillar_override=item.pillar_theme,
            sub_theme_override=item.sub_theme,
        )

        if result.success and result.draft:
            # Link draft to pipeline item
            item.draft_id = result.draft.id
            item.updated_at = result.draft.created_at
            db.commit()

            # Transition WRITING → REVIEW
            transition(db, item.id, PipelineStatus.writing, PipelineStatus.review)
            release_claim(db, item.id, "writing")

            logger.info(
                "Writer: generated draft %s for pipeline item %s",
                result.draft.id, item.id,
            )
            return True
        else:
            # Generation failed but produced a manual-required draft
            error_msg = result.error_message or "Draft generation failed guardrails"
            increment_revision(db, item.id, error_msg)

            if result.draft:
                item.draft_id = result.draft.id
                db.commit()

            # Send back to TODO for retry
            transition(db, item.id, PipelineStatus.writing, PipelineStatus.todo)
            release_claim(db, item.id, "writing")

            logger.warning(
                "Writer: draft generation failed for item %s — %s",
                item.id, error_msg,
            )
            return False

    except Exception as e:
        logger.error("Writer: error processing item %s: %s", item.id, e)
        increment_revision(db, item.id, f"Writer error: {str(e)[:200]}")

        # Try to send back to TODO
        try:
            transition(db, item.id, PipelineStatus.writing, PipelineStatus.todo)
        except Exception:
            logger.error("Writer: failed to revert item %s to TODO", item.id)

        release_claim(db, item.id, "writing")
        return False


def run_writer(db: Session, max_items: int = 3) -> int:
    """Execute the Writer agent.

    Claims unclaimed TODO items, generates drafts, and transitions
    to REVIEW on success.

    Args:
        db: Database session
        max_items: Maximum items to process in one run

    Returns:
        Number of items successfully processed
    """
    unclaimed = get_unclaimed_items_by_status(db, PipelineStatus.todo)
    if not unclaimed:
        logger.debug("Writer: no unclaimed TODO items")
        return 0

    worker_id = _worker_id()
    processed = 0

    for item in unclaimed[:max_items]:
        # Attempt to claim
        if not attempt_claim(db, item.id, "writing", worker_id):
            continue

        # Verify claim
        if not verify_claim(db, item.id, "writing", worker_id):
            continue

        if process_one_item(db, item, worker_id):
            processed += 1

    logger.info("Writer: processed %d/%d items", processed, len(unclaimed[:max_items]))
    return processed
