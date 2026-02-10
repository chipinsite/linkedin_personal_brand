"""Atomic claim-lock service for V6 content pipeline.

Provides safe multi-worker claim semantics so that only one agent
can process a pipeline item at a time.  The pattern is:

    1. attempt_claim(db, item_id, stage, worker_id)
    2. verify_claim(db, item_id, stage, worker_id)
    3. ... do work ...
    4. release_claim(db, item_id, stage)

If step 2 fails, another worker won the race — back off gracefully.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..models import ContentPipelineItem

logger = logging.getLogger(__name__)

# Default claim TTL — claims older than this are considered stale.
DEFAULT_CLAIM_TTL_MINUTES = 30


def attempt_claim(
    db: Session,
    item_id,
    stage: str,
    worker_id: str,
    ttl_minutes: int = DEFAULT_CLAIM_TTL_MINUTES,
) -> bool:
    """Attempt to atomically claim a pipeline item.

    Uses UPDATE ... WHERE claimed_by IS NULL to ensure only one worker
    wins. Returns True if the claim was written, False if another worker
    already holds the claim.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ttl_minutes)

    rows = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.id == item_id)
        .filter(ContentPipelineItem.claimed_by.is_(None))
        .update(
            {
                ContentPipelineItem.claimed_by: worker_id,
                ContentPipelineItem.claimed_at: now,
                ContentPipelineItem.claim_stage: stage,
                ContentPipelineItem.claim_expires_at: expires,
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    if rows == 1:
        logger.info("Claim acquired: item=%s stage=%s worker=%s", item_id, stage, worker_id)
        return True

    logger.debug("Claim failed (already held): item=%s stage=%s worker=%s", item_id, stage, worker_id)
    return False


def verify_claim(
    db: Session,
    item_id,
    stage: str,
    worker_id: str,
) -> bool:
    """Re-fetch the item and verify this worker still holds the claim.

    Must be called after attempt_claim() before doing actual work,
    to guard against very tight race windows.
    """
    item = db.query(ContentPipelineItem).filter(ContentPipelineItem.id == item_id).first()
    if item is None:
        return False

    return (
        item.claimed_by == worker_id
        and item.claim_stage == stage
    )


def release_claim(
    db: Session,
    item_id,
    stage: str,
) -> bool:
    """Release a claim after processing is complete.

    Clears all claim fields. Returns True if the release matched a row.
    """
    rows = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.id == item_id)
        .filter(ContentPipelineItem.claim_stage == stage)
        .update(
            {
                ContentPipelineItem.claimed_by: None,
                ContentPipelineItem.claimed_at: None,
                ContentPipelineItem.claim_stage: None,
                ContentPipelineItem.claim_expires_at: None,
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    if rows == 1:
        logger.info("Claim released: item=%s stage=%s", item_id, stage)
        return True
    return False


def find_stale_claims(
    db: Session,
    max_age_minutes: int = DEFAULT_CLAIM_TTL_MINUTES,
) -> list[ContentPipelineItem]:
    """Return pipeline items with claims older than the given threshold.

    These are candidates for automatic recovery by Morgan PM.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)

    stale = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.claimed_by.is_not(None))
        .filter(ContentPipelineItem.claimed_at <= cutoff)
        .all()
    )
    return stale


def force_release_claim(
    db: Session,
    item_id,
) -> bool:
    """Unconditionally release a claim regardless of stage or worker.

    Used by Morgan PM for stale claim recovery.
    """
    rows = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.id == item_id)
        .filter(ContentPipelineItem.claimed_by.is_not(None))
        .update(
            {
                ContentPipelineItem.claimed_by: None,
                ContentPipelineItem.claimed_at: None,
                ContentPipelineItem.claim_stage: None,
                ContentPipelineItem.claim_expires_at: None,
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    if rows == 1:
        logger.info("Claim force-released: item=%s", item_id)
        return True
    return False
