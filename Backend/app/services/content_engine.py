"""Content Engine Service.

Orchestrates the content generation pipeline:
1. Topic selection from content pyramid
2. Format and tone selection with weighted sampling
3. Draft generation using LLM
4. Guardrail validation
5. Retry logic for failed generations
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ..models import Draft, DraftStatus, PostFormat, PostTone
from .content_pyramid import (
    POST_ANGLES,
    PostAngle,
    TopicSelection,
    select_topic,
)
from .guardrails import GuardrailResult, validate_post
from .llm_client import generate_text, is_mock_mode

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MAX_GENERATION_ATTEMPTS = 3

# Default format weights (CLAUDE.md section 4.2)
DEFAULT_FORMAT_WEIGHTS: dict[PostFormat, float] = {
    PostFormat.text: 0.50,
    PostFormat.image: 0.30,
    PostFormat.carousel: 0.20,
}

# Default tone weights (CLAUDE.md section 4.3)
DEFAULT_TONE_WEIGHTS: dict[PostTone, float] = {
    PostTone.educational: 0.40,
    PostTone.opinionated: 0.25,
    PostTone.direct: 0.20,
    PostTone.exploratory: 0.15,
}

# Brand voice rules (CLAUDE.md section 7.2)
BRAND_VOICE_RULES = """
- Use "I" not "we" (first person singular)
- Complete sentences, active voice
- Direct opening, no filler phrases
- Clear call to action or question at the end
- No emojis in body, optional single emoji at end
- Maximum 3 hashtags
"""

# Banned phrases (CLAUDE.md section 7.3)
BANNED_PHRASES = [
    "game changer",
    "disrupt",
    "synergy",
    "leverage",
    "pivot",
    "deep dive",
    "unpack",
    "double down",
    "move the needle",
    "low hanging fruit",
]


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GenerationResult:
    """Result of a draft generation attempt."""

    success: bool
    draft: Draft | None = None
    guardrail_result: GuardrailResult | None = None
    attempts: int = 0
    requires_manual: bool = False
    error_message: str | None = None


@dataclass
class ContentParameters:
    """Parameters for content generation."""

    pillar_theme: str
    sub_theme: str
    post_format: PostFormat
    tone: PostTone
    post_angle: PostAngle
    research_context: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Weight Selection
# ─────────────────────────────────────────────────────────────────────────────

def _weighted_choice(weights: dict) -> any:
    """Select a random item using weighted sampling."""
    options = list(weights.keys())
    values = list(weights.values())
    return random.choices(options, weights=values, k=1)[0]


def get_effective_format_weights(db: Session | None = None) -> dict[PostFormat, float]:
    """Get format weights adjusted by engagement performance.

    Args:
        db: Optional database session for learning weights

    Returns:
        Dictionary of PostFormat to weight
    """
    if db is None:
        return DEFAULT_FORMAT_WEIGHTS.copy()

    try:
        from .learning import get_effective_weight_maps
        weights = get_effective_weight_maps(db)
        if weights and weights.get("format"):
            return {
                PostFormat(k): v
                for k, v in weights["format"].items()
            }
    except Exception as e:
        logger.warning(f"Failed to get learned format weights: {e}")

    return DEFAULT_FORMAT_WEIGHTS.copy()


def get_effective_tone_weights(db: Session | None = None) -> dict[PostTone, float]:
    """Get tone weights adjusted by engagement performance.

    Args:
        db: Optional database session for learning weights

    Returns:
        Dictionary of PostTone to weight
    """
    if db is None:
        return DEFAULT_TONE_WEIGHTS.copy()

    try:
        from .learning import get_effective_weight_maps
        weights = get_effective_weight_maps(db)
        if weights and weights.get("tone"):
            return {
                PostTone(k): v
                for k, v in weights["tone"].items()
            }
    except Exception as e:
        logger.warning(f"Failed to get learned tone weights: {e}")

    return DEFAULT_TONE_WEIGHTS.copy()


def select_format(db: Session | None = None) -> PostFormat:
    """Select a post format using weighted random sampling.

    Args:
        db: Optional database session for engagement-adjusted weights

    Returns:
        Selected PostFormat
    """
    weights = get_effective_format_weights(db)
    return _weighted_choice(weights)


def select_tone(db: Session | None = None) -> PostTone:
    """Select a post tone using weighted random sampling.

    Args:
        db: Optional database session for engagement-adjusted weights

    Returns:
        Selected PostTone
    """
    weights = get_effective_tone_weights(db)
    return _weighted_choice(weights)


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Building
# ─────────────────────────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    """Build the system prompt for content generation."""
    return """You are a LinkedIn content writer for Sphiwe, a Head of Sales with 19 years of commercial experience in Sub-Saharan Africa, specialising in Adtech and AI in advertising.

Your role is to create professional LinkedIn posts that establish thought leadership. Follow these principles:

1. QUALITY: Focus on substance over style. Every post must deliver genuine insight.
2. AUTHENTICITY: Write in first person singular, with a clear personal voice.
3. CREDIBILITY: Label predictions as predictions. Don't make unverified claims.
4. STRUCTURE: Use clear paragraphs. Optimise for dwell time with a strong first line.
5. ENGAGEMENT: End with a clear takeaway or discussion question.

FORBIDDEN:
- Hype language and buzzwords
- Engagement bait phrases
- External URLs in post body
- More than 3 hashtags
- Fluff or filler content"""


def _build_user_prompt(params: ContentParameters, stricter: bool = False) -> str:
    """Build the user prompt for content generation.

    Args:
        params: Content generation parameters
        stricter: If True, add extra constraints for retry attempts
    """
    banned_list = ", ".join(BANNED_PHRASES)

    base_prompt = f"""Write a LinkedIn post with these specifications:

TOPIC:
- Pillar theme: {params.pillar_theme}
- Sub-theme: {params.sub_theme}
- Post angle: {params.post_angle.name} - {params.post_angle.prompt_guidance}

FORMAT: {params.post_format.value}
TONE: {params.tone.value}

BRAND VOICE RULES:
{BRAND_VOICE_RULES}

BANNED PHRASES (do not use any of these):
{banned_list}

CONSTRAINTS:
- Use South African English
- Keep between 150 and 300 words
- Maximum 3 hashtags at the end
- No external URLs
- If making a prediction, clearly label it as such
- End with a practical takeaway or discussion question"""

    if params.research_context:
        base_prompt += f"""

RESEARCH CONTEXT (use for grounding, cite if specific):
{params.research_context}"""

    if stricter:
        base_prompt += """

ADDITIONAL CONSTRAINTS (stricter mode):
- Be even more concise (aim for 200 words)
- Avoid any phrase that could be considered promotional
- Focus purely on insight and practical value
- Double-check against banned phrases before responding"""

    base_prompt += """

Return ONLY the post content, nothing else. No preamble, no explanation."""

    return base_prompt


# ─────────────────────────────────────────────────────────────────────────────
# Draft Generation
# ─────────────────────────────────────────────────────────────────────────────

def _generate_content(params: ContentParameters, stricter: bool = False) -> str:
    """Generate post content using LLM.

    Args:
        params: Content generation parameters
        stricter: If True, use stricter constraints

    Returns:
        Generated content string
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(params, stricter=stricter)

    response = generate_text(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=800,
        temperature=0.7 if not stricter else 0.5,
    )

    logger.info(
        f"Generated content: mock={response.is_mock}, "
        f"tokens={response.total_tokens}"
    )

    return response.content


def _create_draft(
    db: Session,
    params: ContentParameters,
    content: str,
    guardrail_result: GuardrailResult,
) -> Draft:
    """Create and persist a draft record.

    Args:
        db: Database session
        params: Content parameters used
        content: Generated content
        guardrail_result: Result of guardrail validation

    Returns:
        Created Draft object
    """
    draft = Draft(
        pillar_theme=params.pillar_theme,
        sub_theme=params.sub_theme,
        format=params.post_format,
        tone=params.tone,
        content_body=content,
        status=DraftStatus.pending,
        guardrail_check_passed=guardrail_result.passed,
        guardrail_violations=json.dumps(guardrail_result.violations) if guardrail_result.violations else None,
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return draft


def _create_manual_required_draft(
    db: Session,
    params: ContentParameters,
    violations: list[str],
) -> Draft:
    """Create a draft that requires manual creation.

    Args:
        db: Database session
        params: Content parameters
        violations: Guardrail violations from final attempt

    Returns:
        Created Draft object with requires_manual flag
    """
    content = (
        f"[MANUAL CREATION REQUIRED]\n\n"
        f"Topic: {params.pillar_theme} > {params.sub_theme}\n"
        f"Format: {params.post_format.value}\n"
        f"Tone: {params.tone.value}\n"
        f"Angle: {params.post_angle.name}\n\n"
        f"Auto-generation failed after {MAX_GENERATION_ATTEMPTS} attempts.\n"
        f"Last violations: {', '.join(violations)}"
    )

    draft = Draft(
        pillar_theme=params.pillar_theme,
        sub_theme=params.sub_theme,
        format=params.post_format,
        tone=params.tone,
        content_body=content,
        status=DraftStatus.pending,
        guardrail_check_passed=False,
        guardrail_violations=json.dumps(violations),
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return draft


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_draft(
    db: Session,
    research_context: str = "",
    pillar_override: str | None = None,
    sub_theme_override: str | None = None,
    format_override: PostFormat | None = None,
    tone_override: PostTone | None = None,
) -> GenerationResult:
    """Generate a new LinkedIn post draft.

    This is the main entry point for content generation. It:
    1. Selects topic from pyramid (or uses overrides)
    2. Selects format and tone with weighted sampling
    3. Generates content using LLM
    4. Validates against guardrails
    5. Retries up to 3 times on failure
    6. Creates draft record

    Args:
        db: Database session
        research_context: Optional research context to ground the post
        pillar_override: Override topic selection with specific pillar
        sub_theme_override: Override topic selection with specific sub-theme
        format_override: Override format selection
        tone_override: Override tone selection

    Returns:
        GenerationResult with draft or error details
    """
    # Step 1: Select topic
    if pillar_override and sub_theme_override:
        topic = TopicSelection(
            pillar_theme=pillar_override,
            sub_theme=sub_theme_override,
            post_angle=random.choice(POST_ANGLES),
        )
    else:
        topic = select_topic(db)

    # Step 2: Select format and tone
    post_format = format_override or select_format(db)
    tone = tone_override or select_tone(db)

    params = ContentParameters(
        pillar_theme=topic.pillar_theme,
        sub_theme=topic.sub_theme,
        post_format=post_format,
        tone=tone,
        post_angle=topic.post_angle,
        research_context=research_context,
    )

    logger.info(
        f"Generating draft: pillar={params.pillar_theme}, "
        f"sub_theme={params.sub_theme}, format={params.post_format.value}, "
        f"tone={params.tone.value}, angle={params.post_angle.id}"
    )

    # Step 3-5: Generate with retry loop
    last_violations: list[str] = []

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            # Generate content (stricter on retry)
            content = _generate_content(params, stricter=(attempt > 1))

            # Validate against guardrails
            guardrail_result = validate_post(content)

            if guardrail_result.passed:
                # Success - create and return draft
                draft = _create_draft(db, params, content, guardrail_result)
                logger.info(f"Draft generated successfully: id={draft.id}, attempts={attempt}")
                return GenerationResult(
                    success=True,
                    draft=draft,
                    guardrail_result=guardrail_result,
                    attempts=attempt,
                )

            # Guardrails failed - log and retry
            last_violations = guardrail_result.violations
            logger.warning(
                f"Guardrail validation failed (attempt {attempt}): "
                f"{guardrail_result.violations}"
            )

        except Exception as e:
            logger.error(f"Generation error (attempt {attempt}): {e}")
            last_violations = [f"GENERATION_ERROR: {str(e)}"]

    # All attempts exhausted - create manual-required draft
    logger.error(
        f"Draft generation failed after {MAX_GENERATION_ATTEMPTS} attempts. "
        f"Creating manual-required draft."
    )

    draft = _create_manual_required_draft(db, params, last_violations)

    return GenerationResult(
        success=False,
        draft=draft,
        guardrail_result=GuardrailResult(passed=False, violations=last_violations),
        attempts=MAX_GENERATION_ATTEMPTS,
        requires_manual=True,
        error_message=f"Generation failed after {MAX_GENERATION_ATTEMPTS} attempts",
    )


def get_current_weights(db: Session | None = None) -> dict:
    """Get current format and tone weights.

    Args:
        db: Optional database session for learning-adjusted weights

    Returns:
        Dictionary with format_weights and tone_weights
    """
    return {
        "format_weights": {
            k.value: v for k, v in get_effective_format_weights(db).items()
        },
        "tone_weights": {
            k.value: v for k, v in get_effective_tone_weights(db).items()
        },
    }
