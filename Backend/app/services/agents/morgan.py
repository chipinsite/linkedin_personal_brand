"""V6 Morgan PM — Pipeline self-healing and health monitoring agent.

Morgan is the operational overseer of the V6 content pipeline.
It runs periodically to:

1. **Recover stale claims** — release pipeline items stuck with expired
   claim locks so other agents can pick them up.
2. **Reset errored items** — items stuck with last_error set and no
   forward progress get reset to an earlier status for retry.
3. **Generate pipeline health report** — aggregated pipeline statistics
   for operational dashboards and alerting.

Named after a reliable project manager who quietly keeps everything
running.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ...models import ContentPipelineItem, PipelineStatus
from ..claim_lock import find_stale_claims, force_release_claim
from ..pipeline import (
    ALLOWED_TRANSITIONS,
    get_pipeline_overview,
    transition,
    TransitionError,
)
from ..audit import log_audit

logger = logging.getLogger(__name__)

WORKER_ID_PREFIX = "morgan"

# Items with errors and no progress for this long (minutes) are candidates for reset.
ERROR_STALE_MINUTES = 60

# Maximum times Morgan will attempt to auto-reset an errored item before giving up.
MORGAN_MAX_AUTO_RESETS = 2


def recover_stale_claims(db: Session, max_age_minutes: int = 30) -> list[dict]:
    """Find and release pipeline items with stale claims.

    Returns a list of recovery records with item details.
    """
    stale_items = find_stale_claims(db, max_age_minutes=max_age_minutes)
    recoveries = []

    for item in stale_items:
        item_id = item.id
        prev_worker = item.claimed_by
        prev_stage = item.claim_stage
        prev_status = item.status.name if item.status else "unknown"

        released = force_release_claim(db, item_id)

        if released:
            record = {
                "item_id": str(item_id),
                "action": "stale_claim_released",
                "previous_worker": prev_worker,
                "previous_stage": prev_stage,
                "status": prev_status,
            }
            recoveries.append(record)
            logger.warning(
                "Morgan: released stale claim on item=%s worker=%s stage=%s status=%s",
                item_id, prev_worker, prev_stage, prev_status,
            )

    if recoveries:
        log_audit(
            db=db,
            actor="morgan",
            action="pipeline.stale_claims_recovered",
            resource_type="pipeline",
            detail={"count": len(recoveries), "items": recoveries},
        )

    return recoveries


def reset_errored_items(db: Session, stale_minutes: int = ERROR_STALE_MINUTES) -> list[dict]:
    """Find pipeline items stuck with errors and reset them for retry.

    An item is considered stuck if:
    - It has a last_error set
    - It is not in a terminal state (DONE)
    - It is not currently claimed by another agent
    - Its updated_at is older than stale_minutes ago

    Reset behavior by status:
    - WRITING → TODO (so Writer can retry)
    - REVIEW → TODO (so Writer can regenerate)
    - READY_TO_PUBLISH → REVIEW (so Editor can re-check)
    - TODO, BACKLOG → left alone (already at starting points)
    - PUBLISHED, AMPLIFIED, DONE → left alone (past the production boundary)

    Returns a list of reset records.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    resets = []

    # Statuses we attempt to reset
    reset_targets = {
        PipelineStatus.writing: PipelineStatus.todo,
        PipelineStatus.review: PipelineStatus.todo,
        PipelineStatus.ready_to_publish: PipelineStatus.backlog,
    }

    for from_status, to_status in reset_targets.items():
        errored_items = (
            db.query(ContentPipelineItem)
            .filter(ContentPipelineItem.status == from_status)
            .filter(ContentPipelineItem.last_error.is_not(None))
            .filter(ContentPipelineItem.claimed_by.is_(None))
            .filter(ContentPipelineItem.updated_at <= cutoff)
            .all()
        )

        for item in errored_items:
            # Check if Morgan has already reset this item too many times
            # We track this by counting how many times the revision count
            # exceeds a threshold relative to max_revisions
            if item.revision_count >= (item.max_revisions + MORGAN_MAX_AUTO_RESETS):
                logger.info(
                    "Morgan: skipping item=%s — exceeded max auto-resets "
                    "(revision_count=%d, max_revisions=%d, morgan_max=%d)",
                    item.id, item.revision_count, item.max_revisions,
                    MORGAN_MAX_AUTO_RESETS,
                )
                continue

            try:
                transition(db, item.id, from_status, to_status)
                # Clear the error after successful reset
                item.last_error = None
                item.updated_at = datetime.now(timezone.utc)
                db.commit()

                record = {
                    "item_id": str(item.id),
                    "action": "error_reset",
                    "from_status": from_status.name,
                    "to_status": to_status.name,
                    "previous_error": item.last_error,
                    "revision_count": item.revision_count,
                }
                resets.append(record)
                logger.info(
                    "Morgan: reset errored item=%s %s → %s (revision %d)",
                    item.id, from_status.name, to_status.name, item.revision_count,
                )
            except (TransitionError, ValueError) as exc:
                logger.warning(
                    "Morgan: failed to reset item=%s: %s", item.id, exc,
                )

    if resets:
        log_audit(
            db=db,
            actor="morgan",
            action="pipeline.errored_items_reset",
            resource_type="pipeline",
            detail={"count": len(resets), "items": resets},
        )

    return resets


def generate_health_report(db: Session) -> dict:
    """Generate a pipeline health report for operational monitoring.

    Returns a summary dict with:
    - overview: status counts from pipeline service
    - stale_claims: count of items with expired claims
    - errored_items: count of items with last_error set (unclaimed)
    - stuck_items: items not updated in 4+ hours that aren't terminal
    - health_status: "healthy", "degraded", or "unhealthy"
    """
    overview = get_pipeline_overview(db)

    # Count stale claims (expired but not released)
    stale_claims = find_stale_claims(db, max_age_minutes=30)
    stale_count = len(stale_claims)

    # Count errored unclaimed items
    errored_count = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.last_error.is_not(None))
        .filter(ContentPipelineItem.claimed_by.is_(None))
        .filter(ContentPipelineItem.status.notin_([PipelineStatus.done, PipelineStatus.backlog]))
        .count()
    )

    # Count stuck items (not updated in 4+ hours, not terminal, not claimed)
    stuck_cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
    non_terminal = [
        PipelineStatus.todo,
        PipelineStatus.writing,
        PipelineStatus.review,
        PipelineStatus.ready_to_publish,
        PipelineStatus.published,
        PipelineStatus.amplified,
    ]
    stuck_count = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.status.in_(non_terminal))
        .filter(ContentPipelineItem.claimed_by.is_(None))
        .filter(ContentPipelineItem.updated_at <= stuck_cutoff)
        .count()
    )

    # Determine overall health
    if stale_count > 0 or errored_count >= 3:
        health_status = "unhealthy"
    elif errored_count > 0 or stuck_count > 0:
        health_status = "degraded"
    else:
        health_status = "healthy"

    report = {
        "overview": overview,
        "stale_claims": stale_count,
        "errored_items": errored_count,
        "stuck_items": stuck_count,
        "health_status": health_status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Morgan: health report — status=%s stale=%d errored=%d stuck=%d total=%d",
        health_status, stale_count, errored_count, stuck_count, overview["total"],
    )

    return report


def run_morgan(db: Session, max_age_minutes: int = 30) -> dict:
    """Run the full Morgan PM self-healing cycle.

    1. Recover stale claims
    2. Reset errored items
    3. Generate health report

    Returns a summary of all actions taken.
    """
    recoveries = recover_stale_claims(db, max_age_minutes=max_age_minutes)
    resets = reset_errored_items(db)
    health = generate_health_report(db)

    return {
        "stale_claims_recovered": len(recoveries),
        "errored_items_reset": len(resets),
        "health": health,
        "recoveries": recoveries,
        "resets": resets,
    }
