"""V6 content pipeline status management service.

Handles pipeline item creation, status transitions with validation,
and filtered queries by status.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import ContentPipelineItem, PipelineStatus, SocialStatus

logger = logging.getLogger(__name__)

# Allowed status transitions.  Key is current status, value is set of
# valid target statuses.  Any transition not in this map is rejected.
ALLOWED_TRANSITIONS: dict[PipelineStatus, set[PipelineStatus]] = {
    PipelineStatus.backlog: {PipelineStatus.todo},
    PipelineStatus.todo: {PipelineStatus.writing, PipelineStatus.backlog},
    PipelineStatus.writing: {
        PipelineStatus.review,
        PipelineStatus.todo,       # Writer failure → retry
        PipelineStatus.backlog,    # Max revisions exceeded
    },
    PipelineStatus.review: {
        PipelineStatus.ready_to_publish,
        PipelineStatus.todo,       # Editor sends back for revision
        PipelineStatus.backlog,    # Max revisions exceeded
    },
    PipelineStatus.ready_to_publish: {
        PipelineStatus.published,
        PipelineStatus.backlog,    # Admin rejection
    },
    PipelineStatus.published: {PipelineStatus.amplified},
    PipelineStatus.amplified: {PipelineStatus.done},
    PipelineStatus.done: set(),    # Terminal state
}


class TransitionError(Exception):
    """Raised when an invalid status transition is attempted."""


def is_valid_transition(from_status: PipelineStatus, to_status: PipelineStatus) -> bool:
    """Check whether a status transition is allowed."""
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    return to_status in allowed


def transition(
    db: Session,
    item_id,
    from_status: PipelineStatus,
    to_status: PipelineStatus,
) -> ContentPipelineItem:
    """Atomically transition a pipeline item from one status to another.

    Validates the transition is allowed, then applies it with an
    optimistic WHERE clause on current status.

    Raises:
        TransitionError: if the transition is invalid or the item was
            concurrently modified.
        ValueError: if the item does not exist.
    """
    if not is_valid_transition(from_status, to_status):
        raise TransitionError(
            f"Invalid transition: {from_status.name} → {to_status.name}"
        )

    now = datetime.now(timezone.utc)
    rows = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.id == item_id)
        .filter(ContentPipelineItem.status == from_status)
        .update(
            {
                ContentPipelineItem.status: to_status,
                ContentPipelineItem.updated_at: now,
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    if rows == 0:
        # Could be missing or concurrently changed
        item = db.query(ContentPipelineItem).filter(ContentPipelineItem.id == item_id).first()
        if item is None:
            raise ValueError(f"Pipeline item not found: {item_id}")
        raise TransitionError(
            f"Concurrent modification: expected status={from_status.name}, "
            f"actual={item.status.name}"
        )

    item = db.query(ContentPipelineItem).filter(ContentPipelineItem.id == item_id).first()
    logger.info(
        "Pipeline transition: item=%s %s → %s",
        item_id, from_status.name, to_status.name,
    )
    return item


def create_pipeline_item(
    db: Session,
    pillar_theme: str | None = None,
    sub_theme: str | None = None,
    topic_keyword: str | None = None,
    draft_id=None,
    status: PipelineStatus = PipelineStatus.backlog,
) -> ContentPipelineItem:
    """Create a new pipeline item at the specified status (default: BACKLOG)."""
    item = ContentPipelineItem(
        pillar_theme=pillar_theme,
        sub_theme=sub_theme,
        topic_keyword=topic_keyword,
        draft_id=draft_id,
        status=status,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(
        "Pipeline item created: id=%s status=%s pillar=%s",
        item.id, item.status.name, pillar_theme,
    )
    return item


def get_items_by_status(
    db: Session,
    status: PipelineStatus,
) -> list[ContentPipelineItem]:
    """Return all pipeline items with the given status, ordered by creation time."""
    return (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.status == status)
        .order_by(ContentPipelineItem.created_at.asc())
        .all()
    )


def get_unclaimed_items_by_status(
    db: Session,
    status: PipelineStatus,
) -> list[ContentPipelineItem]:
    """Return unclaimed pipeline items with the given status."""
    return (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.status == status)
        .filter(ContentPipelineItem.claimed_by.is_(None))
        .order_by(ContentPipelineItem.created_at.asc())
        .all()
    )


def get_pipeline_overview(db: Session) -> dict:
    """Return a summary of item counts per pipeline status."""
    counts = {}
    for ps in PipelineStatus:
        count = (
            db.query(ContentPipelineItem)
            .filter(ContentPipelineItem.status == ps)
            .count()
        )
        counts[ps.name] = count

    claimed_count = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.claimed_by.is_not(None))
        .count()
    )

    return {
        "status_counts": counts,
        "total": sum(counts.values()),
        "claimed": claimed_count,
    }


def increment_revision(
    db: Session,
    item_id,
    error_message: str | None = None,
) -> ContentPipelineItem:
    """Increment the revision count and optionally set the last error.

    Returns the updated item.
    """
    item = db.query(ContentPipelineItem).filter(ContentPipelineItem.id == item_id).first()
    if item is None:
        raise ValueError(f"Pipeline item not found: {item_id}")

    item.revision_count += 1
    item.last_error = error_message
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)

    logger.info(
        "Pipeline revision incremented: item=%s count=%d max=%d",
        item_id, item.revision_count, item.max_revisions,
    )
    return item


def has_exceeded_max_revisions(item: ContentPipelineItem) -> bool:
    """Check if the item has exceeded its maximum allowed revisions."""
    return item.revision_count >= item.max_revisions
