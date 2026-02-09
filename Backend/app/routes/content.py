"""Content Engine API Routes.

Provides endpoints for AI-powered content generation using the content pyramid.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import (
    ContentGenerateRequest,
    ContentGenerateResponse,
    ContentPyramidRead,
    ContentWeightsRead,
    DraftRead,
    PostAngleRead,
    SubThemeCoverage,
)
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.content_engine import generate_draft, get_current_weights
from ..services.content_pyramid import get_pyramid_summary

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/generate-draft", response_model=ContentGenerateResponse)
def generate_content_draft(
    payload: ContentGenerateRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Generate a new draft using the AI content engine.

    The content engine:
    1. Selects topic from content pyramid (or uses provided overrides)
    2. Selects format and tone with weighted sampling
    3. Generates content using LLM
    4. Validates against guardrails
    5. Retries up to 3 times on failure
    6. Creates draft record
    """
    result = generate_draft(
        db=db,
        research_context=payload.research_context or "",
        pillar_override=payload.pillar_override,
        sub_theme_override=payload.sub_theme_override,
        format_override=payload.format_override,
        tone_override=payload.tone_override,
    )

    # Log audit trail
    log_audit(
        db=db,
        actor="api",
        action="content.generate",
        resource_type="draft",
        resource_id=str(result.draft.id) if result.draft else None,
        detail={
            "success": result.success,
            "attempts": result.attempts,
            "requires_manual": result.requires_manual,
        },
    )

    return ContentGenerateResponse(
        success=result.success,
        draft=DraftRead.model_validate(result.draft) if result.draft else None,
        attempts=result.attempts,
        requires_manual=result.requires_manual,
        error_message=result.error_message,
        guardrail_violations=result.guardrail_result.violations if result.guardrail_result else None,
    )


@router.get("/pyramid", response_model=ContentPyramidRead)
def get_content_pyramid(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Get the content pyramid structure with coverage statistics.

    Returns:
    - Pillar themes (tier 1)
    - Sub-themes per pillar (tier 2)
    - Post angles (tier 3)
    - Coverage stats: posts per sub-theme in last 30 days
    """
    summary = get_pyramid_summary(db)

    return ContentPyramidRead(
        pillars=summary.pillars,
        sub_themes=summary.sub_themes,
        post_angles=[
            PostAngleRead(
                id=angle["id"],
                name=angle["name"],
                description=angle["description"],
            )
            for angle in summary.post_angles
        ],
        coverage=[
            SubThemeCoverage(
                pillar_theme=stat.pillar_theme,
                sub_theme=stat.sub_theme,
                post_count_30_days=stat.post_count_30_days,
                last_posted_at=stat.last_posted_at,
            )
            for stat in summary.coverage
        ],
    )


@router.get("/weights", response_model=ContentWeightsRead)
def get_content_weights(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Get current format and tone selection weights.

    Weights are adjusted over time based on engagement performance.
    """
    weights = get_current_weights(db)

    return ContentWeightsRead(
        format_weights=weights["format_weights"],
        tone_weights=weights["tone_weights"],
    )
