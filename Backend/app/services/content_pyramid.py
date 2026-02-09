"""Content Pyramid Service.

Defines the three-tier content pyramid structure for LinkedIn thought leadership:
- Tier 1: Pillar Themes (3 core topics)
- Tier 2: Sub-Themes (4-6 per pillar)
- Tier 3: Post Angles (8 types)

Provides topic selection logic that avoids repeating sub-themes within 7 days.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# ─────────────────────────────────────────────────────────────────────────────
# Tier 1: Pillar Themes
# ─────────────────────────────────────────────────────────────────────────────

PILLAR_THEMES = [
    "Adtech fundamentals and market dynamics",
    "Agentic AI applications in advertising technology",
    "Artificial intelligence in advertising operations and strategy",
]


# ─────────────────────────────────────────────────────────────────────────────
# Tier 2: Sub-Themes (matching CLAUDE.md section 4.1)
# ─────────────────────────────────────────────────────────────────────────────

PILLAR_SUB_THEMES: dict[str, list[str]] = {
    "Adtech fundamentals and market dynamics": [
        "Programmatic buying",
        "Supply path optimisation",
        "Measurement and attribution",
        "Retail media",
        "CTV and audio",
        "Privacy and identity",
    ],
    "Agentic AI applications in advertising technology": [
        "Autonomous campaign management",
        "AI bidding agents",
        "Creative optimisation agents",
        "Reporting and insight agents",
        "Multi-agent orchestration",
    ],
    "Artificial intelligence in advertising operations and strategy": [
        "Generative creative",
        "Audience modelling",
        "Media mix modelling",
        "Conversational commerce",
        "Predictive analytics",
        "AI ethics in marketing",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Tier 3: Post Angles (8 types per CLAUDE.md section 4.1)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PostAngle:
    """Represents a post angle type with its characteristics."""

    id: str
    name: str
    description: str
    prompt_guidance: str


POST_ANGLES: list[PostAngle] = [
    PostAngle(
        id="news_commentary",
        name="News commentary",
        description="Commentary on recent developments in the industry",
        prompt_guidance="Comment on a recent news item or announcement, providing analysis and implications.",
    ),
    PostAngle(
        id="framework_explanation",
        name="Framework or mental model explanation",
        description="Explains concepts, frameworks, or processes clearly",
        prompt_guidance="Explain a useful framework or mental model with practical application examples.",
    ),
    PostAngle(
        id="contrarian_take",
        name="Contrarian take",
        description="Takes a clear position against industry consensus",
        prompt_guidance="Present a contrarian viewpoint on a commonly held belief, with reasoned arguments.",
    ),
    PostAngle(
        id="case_study",
        name="Case study breakdown",
        description="Breakdown of a case study with lessons learned",
        prompt_guidance="Analyze a real case study and extract actionable lessons for the audience.",
    ),
    PostAngle(
        id="tool_review",
        name="Tool or platform review",
        description="Review of a tool, platform, or technology",
        prompt_guidance="Review a tool or platform, focusing on practical utility and honest assessment.",
    ),
    PostAngle(
        id="future_prediction",
        name="Future prediction",
        description="Predictions about future trends with reasoning",
        prompt_guidance="Make a specific prediction about the future, clearly labeling it as a prediction with reasoning.",
    ),
    PostAngle(
        id="personal_experience",
        name="Personal experience and lessons learned",
        description="Shares personal experience and lessons",
        prompt_guidance="Share a personal experience and the lessons learned from it.",
    ),
    PostAngle(
        id="audience_question",
        name="Question posed to audience",
        description="Poses a thought-provoking question to invite discussion",
        prompt_guidance="Pose a thought-provoking question to the audience to spark discussion.",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TopicSelection:
    """Represents a selected topic combination."""

    pillar_theme: str
    sub_theme: str
    post_angle: PostAngle


@dataclass
class CoverageStats:
    """Statistics for content coverage analysis."""

    pillar_theme: str
    sub_theme: str
    post_count_30_days: int
    last_posted_at: datetime | None


@dataclass
class PyramidSummary:
    """Summary of the content pyramid with coverage statistics."""

    pillars: list[str]
    sub_themes: dict[str, list[str]]
    post_angles: list[dict]
    coverage: list[CoverageStats]


# ─────────────────────────────────────────────────────────────────────────────
# Topic Selection Logic
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_sub_themes(db: Session, days: int = 7) -> list[str]:
    """Get sub-themes used in published posts within the last N days.

    Args:
        db: Database session
        days: Number of days to look back (default 7)

    Returns:
        List of sub-theme strings used recently
    """
    from ..models import Draft, PublishedPost

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Query published posts within the window
    recent_posts = (
        db.query(PublishedPost)
        .join(Draft)
        .filter(PublishedPost.published_at >= cutoff)
        .all()
    )

    return [post.draft.sub_theme for post in recent_posts if post.draft]


def get_sub_theme_coverage(db: Session, days: int = 30) -> list[CoverageStats]:
    """Get coverage statistics for all sub-themes.

    Args:
        db: Database session
        days: Number of days to analyze (default 30)

    Returns:
        List of CoverageStats for each sub-theme
    """
    from ..models import Draft, PublishedPost

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    coverage: list[CoverageStats] = []

    for pillar, sub_themes in PILLAR_SUB_THEMES.items():
        for sub_theme in sub_themes:
            posts = (
                db.query(PublishedPost)
                .join(Draft)
                .filter(
                    Draft.pillar_theme == pillar,
                    Draft.sub_theme == sub_theme,
                    PublishedPost.published_at >= cutoff,
                )
                .order_by(PublishedPost.published_at.desc())
                .all()
            )

            last_posted = posts[0].published_at if posts else None
            coverage.append(
                CoverageStats(
                    pillar_theme=pillar,
                    sub_theme=sub_theme,
                    post_count_30_days=len(posts),
                    last_posted_at=last_posted,
                )
            )

    return coverage


def select_topic(db: Session | None = None) -> TopicSelection:
    """Select the next topic combination based on rotation schedule.

    Avoids repeating sub-themes used in the last 7 days.
    Prioritizes pillars and sub-themes with lower recent coverage.

    Args:
        db: Optional database session for history-aware selection

    Returns:
        TopicSelection with pillar, sub-theme, and post angle
    """
    recent_sub_themes: list[str] = []
    if db:
        recent_sub_themes = get_recent_sub_themes(db, days=7)

    # Build list of available sub-themes (not used in last 7 days)
    available_options: list[tuple[str, str]] = []
    for pillar, sub_themes in PILLAR_SUB_THEMES.items():
        for sub_theme in sub_themes:
            if sub_theme not in recent_sub_themes:
                available_options.append((pillar, sub_theme))

    # If all sub-themes were used recently, fall back to all options
    if not available_options:
        for pillar, sub_themes in PILLAR_SUB_THEMES.items():
            for sub_theme in sub_themes:
                available_options.append((pillar, sub_theme))

    # Select randomly from available options
    pillar, sub_theme = random.choice(available_options)

    # Select random post angle
    post_angle = random.choice(POST_ANGLES)

    return TopicSelection(
        pillar_theme=pillar,
        sub_theme=sub_theme,
        post_angle=post_angle,
    )


def get_pyramid_summary(db: Session | None = None) -> PyramidSummary:
    """Get the full content pyramid structure with coverage stats.

    Args:
        db: Optional database session for coverage statistics

    Returns:
        PyramidSummary with pillars, sub-themes, angles, and coverage
    """
    coverage: list[CoverageStats] = []
    if db:
        coverage = get_sub_theme_coverage(db, days=30)

    return PyramidSummary(
        pillars=PILLAR_THEMES,
        sub_themes=PILLAR_SUB_THEMES,
        post_angles=[
            {
                "id": angle.id,
                "name": angle.name,
                "description": angle.description,
            }
            for angle in POST_ANGLES
        ],
        coverage=coverage,
    )
