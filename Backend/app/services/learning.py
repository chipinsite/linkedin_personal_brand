from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import EngagementMetric, LearningWeight, PostFormat, PostTone, PublishedPost
from .content_generation import FORMAT_WEIGHTS, TONE_WEIGHTS


def _normalise(raw: dict[str, float], defaults: dict[str, float]) -> dict[str, float]:
    merged = {}
    for key, default in defaults.items():
        merged[key] = max(raw.get(key, default), 0.01)
    total = sum(merged.values())
    return {k: v / total for k, v in merged.items()}


def _compute_from_posts(db: Session, by: str) -> dict[str, float]:
    if by == "format":
        rows = (
            db.query(PublishedPost.format, func.avg(PublishedPost.engagement_rate))
            .filter(PublishedPost.engagement_rate.is_not(None))
            .group_by(PublishedPost.format)
            .all()
        )
        defaults = {k.value: v for k, v in FORMAT_WEIGHTS.items()}
    else:
        rows = (
            db.query(PublishedPost.tone, func.avg(PublishedPost.engagement_rate))
            .filter(PublishedPost.engagement_rate.is_not(None))
            .group_by(PublishedPost.tone)
            .all()
        )
        defaults = {k.value: v for k, v in TONE_WEIGHTS.items()}

    if not rows:
        return defaults

    observed = {item[0].value: float(item[1] or 0.0) for item in rows}
    min_score = min(observed.values())
    shifted = {k: (v - min_score) + 0.01 for k, v in observed.items()}

    # Blend prior defaults (60%) with observed performance (40%) to avoid abrupt shifts.
    normalised_observed = _normalise(shifted, defaults)
    blended = {key: (defaults[key] * 0.60) + (normalised_observed.get(key, 0.0) * 0.40) for key in defaults}
    return _normalise(blended, defaults)


def recompute_learning_weights(db: Session) -> LearningWeight:
    format_weights = _compute_from_posts(db, by="format")
    tone_weights = _compute_from_posts(db, by="tone")

    row = db.query(LearningWeight).filter(LearningWeight.id == 1).first()
    if not row:
        row = LearningWeight(
            id=1,
            format_weights_json=json.dumps(format_weights),
            tone_weights_json=json.dumps(tone_weights),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(row)
    else:
        row.format_weights_json = json.dumps(format_weights)
        row.tone_weights_json = json.dumps(tone_weights)
        row.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(row)
    return row


def get_learning_weights(db: Session) -> LearningWeight:
    row = db.query(LearningWeight).filter(LearningWeight.id == 1).first()
    if row:
        return row
    return recompute_learning_weights(db)


def get_effective_weight_maps(db: Session) -> tuple[dict[PostFormat, float], dict[PostTone, float]]:
    row = get_learning_weights(db)

    raw_format = json.loads(row.format_weights_json)
    raw_tone = json.loads(row.tone_weights_json)

    format_weights = {
        PostFormat.text: float(raw_format.get(PostFormat.text.value, FORMAT_WEIGHTS[PostFormat.text])),
        PostFormat.image: float(raw_format.get(PostFormat.image.value, FORMAT_WEIGHTS[PostFormat.image])),
        PostFormat.carousel: float(raw_format.get(PostFormat.carousel.value, FORMAT_WEIGHTS[PostFormat.carousel])),
    }
    tone_weights = {
        PostTone.educational: float(raw_tone.get(PostTone.educational.value, TONE_WEIGHTS[PostTone.educational])),
        PostTone.opinionated: float(raw_tone.get(PostTone.opinionated.value, TONE_WEIGHTS[PostTone.opinionated])),
        PostTone.direct: float(raw_tone.get(PostTone.direct.value, TONE_WEIGHTS[PostTone.direct])),
        PostTone.exploratory: float(raw_tone.get(PostTone.exploratory.value, TONE_WEIGHTS[PostTone.exploratory])),
    }
    return format_weights, tone_weights


def record_post_metrics(
    db: Session,
    post: PublishedPost,
    impressions: int,
    reactions: int,
    comments_count: int,
    shares: int,
) -> EngagementMetric:
    safe_impressions = max(impressions, 0)
    numerator = max(reactions, 0) + max(comments_count, 0) + max(shares, 0)
    engagement_rate = (numerator / safe_impressions) if safe_impressions > 0 else 0.0

    post.impressions = safe_impressions
    post.reactions = max(reactions, 0)
    post.comments_count = max(comments_count, 0)
    post.shares = max(shares, 0)
    post.engagement_rate = engagement_rate
    post.last_metrics_update = datetime.now(timezone.utc)

    metric = EngagementMetric(
        published_post_id=post.id,
        impressions=post.impressions,
        reactions=post.reactions,
        comments_count=post.comments_count,
        shares=post.shares,
        engagement_rate=post.engagement_rate,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric
