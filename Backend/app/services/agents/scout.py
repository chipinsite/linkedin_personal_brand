"""V6 Scout Agent.

Scans source_materials for recent Adtech content and seeds
pipeline items at BACKLOG with topic metadata.

The Scout does not claim items — it creates them.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ...models import ContentPipelineItem, PipelineStatus, SourceMaterial
from ..content_pyramid import PILLAR_SUB_THEMES, PILLAR_THEMES
from ..pipeline import create_pipeline_item

logger = logging.getLogger(__name__)

# Minimum number of BACKLOG items before Scout stops seeding
BACKLOG_FLOOR = 5

# How far back to look for source material
SOURCE_LOOKBACK_DAYS = 7


def _count_backlog(db: Session) -> int:
    """Count current items at BACKLOG status."""
    return (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.status == PipelineStatus.backlog)
        .count()
    )


def _pick_sub_theme_for_pillar(pillar: str) -> str | None:
    """Pick a sub-theme for a given pillar."""
    subs = PILLAR_SUB_THEMES.get(pillar, [])
    return subs[0] if subs else None


def _find_recent_sources(db: Session, days: int = SOURCE_LOOKBACK_DAYS) -> list[SourceMaterial]:
    """Find source materials created within the lookback window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return (
        db.query(SourceMaterial)
        .filter(SourceMaterial.created_at >= cutoff)
        .order_by(SourceMaterial.relevance_score.desc())
        .limit(20)
        .all()
    )


def _source_already_in_pipeline(db: Session, source: SourceMaterial) -> bool:
    """Check if a source's topic is already represented in an active pipeline item."""
    keyword = source.title[:256] if source.title else None
    if not keyword:
        return False

    existing = (
        db.query(ContentPipelineItem)
        .filter(ContentPipelineItem.topic_keyword == keyword)
        .filter(ContentPipelineItem.status.not_in([PipelineStatus.done]))
        .first()
    )
    return existing is not None


def run_scout(db: Session, max_items: int = 5) -> list[ContentPipelineItem]:
    """Execute the Scout agent.

    Scans recent source materials and seeds pipeline items for topics
    that are not already in the pipeline.

    Args:
        db: Database session
        max_items: Maximum number of new items to create

    Returns:
        List of newly created pipeline items
    """
    current_backlog = _count_backlog(db)
    if current_backlog >= BACKLOG_FLOOR:
        logger.info(
            "Scout: backlog has %d items (floor=%d) — skipping",
            current_backlog, BACKLOG_FLOOR,
        )
        return []

    items_needed = min(max_items, BACKLOG_FLOOR - current_backlog)
    sources = _find_recent_sources(db)

    created: list[ContentPipelineItem] = []

    for source in sources:
        if len(created) >= items_needed:
            break

        if _source_already_in_pipeline(db, source):
            continue

        pillar = source.pillar_theme
        if not pillar:
            continue

        # Find matching full pillar name
        full_pillar = None
        for p in PILLAR_THEMES:
            if pillar.lower() in p.lower():
                full_pillar = p
                break
        if not full_pillar:
            full_pillar = pillar

        sub_theme = _pick_sub_theme_for_pillar(full_pillar)

        item = create_pipeline_item(
            db=db,
            pillar_theme=full_pillar,
            sub_theme=sub_theme or "",
            topic_keyword=source.title[:256] if source.title else "untitled",
        )

        logger.info(
            "Scout: seeded pipeline item %s — pillar=%s topic=%s",
            item.id, full_pillar, item.topic_keyword[:60] if item.topic_keyword else "?",
        )
        created.append(item)

    logger.info("Scout: created %d new pipeline items", len(created))
    return created
