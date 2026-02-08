from __future__ import annotations

import random

from ..models import PostFormat, PostTone

PILLARS: dict[str, list[str]] = {
    "Adtech fundamentals": [
        "Programmatic buying",
        "Supply path optimisation",
        "Measurement and attribution",
        "Retail media",
    ],
    "Agentic AI in Adtech": [
        "Autonomous campaign management",
        "AI bidding agents",
        "Creative optimisation agents",
        "Multi-agent orchestration",
    ],
    "AI in advertising": [
        "Generative creative",
        "Audience modelling",
        "Media mix modelling",
        "Predictive analytics",
    ],
}

FORMAT_WEIGHTS = {
    PostFormat.text: 0.50,
    PostFormat.image: 0.30,
    PostFormat.carousel: 0.20,
}

TONE_WEIGHTS = {
    PostTone.educational: 0.40,
    PostTone.opinionated: 0.25,
    PostTone.direct: 0.20,
    PostTone.exploratory: 0.15,
}


def _weighted_choice(weights: dict):
    options = list(weights.keys())
    values = list(weights.values())
    return random.choices(options, weights=values, k=1)[0]


def select_theme() -> tuple[str, str]:
    pillar = random.choice(list(PILLARS.keys()))
    sub_theme = random.choice(PILLARS[pillar])
    return pillar, sub_theme


def select_format_and_tone(
    format_weights: dict[PostFormat, float] | None = None,
    tone_weights: dict[PostTone, float] | None = None,
) -> tuple[PostFormat, PostTone]:
    post_format = _weighted_choice(format_weights or FORMAT_WEIGHTS)
    tone = _weighted_choice(tone_weights or TONE_WEIGHTS)
    return post_format, tone


def render_draft_content(pillar: str, sub_theme: str, tone: PostTone, post_format: PostFormat) -> str:
    tone_lead = {
        PostTone.educational: "Here is a practical framework I use when evaluating this area:",
        PostTone.opinionated: "I think the market is getting one important point wrong:",
        PostTone.direct: "Straight point:",
        PostTone.exploratory: "I am still testing this idea, but one pattern is emerging:",
    }[tone]

    return (
        f"{tone_lead}\n\n"
        f"In {pillar.lower()}, {sub_theme.lower()} is where execution quality creates real separation. "
        "Most teams focus on tooling first, but the bigger lift is operating discipline: clear objectives, "
        "fast feedback loops, and tighter decision cadence across marketing and data teams.\n\n"
        "My prediction: teams that treat AI systems as accountable operators, not just reporting helpers, "
        "will compound performance faster over the next 12 months.\n\n"
        "What is one operational change that improved outcomes in your team this quarter? "
        "#Adtech #AI #Marketing"
    )
