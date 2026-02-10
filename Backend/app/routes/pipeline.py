"""V6 Pipeline API routes.

Provides visibility and manual control over the V6 content pipeline:
- Pipeline overview with status counts
- Item listing with optional status filter
- Individual item detail
- Manual status transition
- Manual agent trigger endpoints
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ContentPipelineItem, PipelineStatus
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.pipeline import (
    get_items_by_status,
    get_pipeline_overview,
    is_valid_transition,
    transition,
    TransitionError,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# ─── Request / Response Models ──────────────────────────────────────────────

class TransitionRequest(BaseModel):
    """Request body for manual pipeline transition."""
    to_status: str


class PipelineItemResponse(BaseModel):
    """Serialized pipeline item for API responses."""
    id: str
    created_at: str | None = None
    updated_at: str | None = None
    draft_id: str | None = None
    status: str
    claimed_by: str | None = None
    claimed_at: str | None = None
    claim_stage: str | None = None
    quality_score: float | None = None
    readability_score: float | None = None
    fact_check_status: str | None = None
    revision_count: int = 0
    max_revisions: int = 3
    social_status: str | None = None
    last_error: str | None = None
    topic_keyword: str | None = None
    pillar_theme: str | None = None
    sub_theme: str | None = None

    class Config:
        from_attributes = True


def _serialize_item(item: ContentPipelineItem) -> dict:
    """Convert a pipeline item to a JSON-serializable dict."""
    return {
        "id": str(item.id),
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "draft_id": str(item.draft_id) if item.draft_id else None,
        "status": item.status.value if item.status else None,
        "claimed_by": item.claimed_by,
        "claimed_at": item.claimed_at.isoformat() if item.claimed_at else None,
        "claim_stage": item.claim_stage,
        "quality_score": item.quality_score,
        "readability_score": item.readability_score,
        "fact_check_status": item.fact_check_status,
        "revision_count": item.revision_count,
        "max_revisions": item.max_revisions,
        "social_status": item.social_status.value if item.social_status else None,
        "last_error": item.last_error,
        "topic_keyword": item.topic_keyword,
        "pillar_theme": item.pillar_theme,
        "sub_theme": item.sub_theme,
    }


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/overview")
def pipeline_overview(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Return aggregated pipeline status counts."""
    return get_pipeline_overview(db)


@router.get("/items")
def list_pipeline_items(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
    status: str | None = Query(None, description="Filter by pipeline status"),
):
    """List pipeline items, optionally filtered by status."""
    if status:
        # Validate and convert status string to enum
        status_upper = status.upper()
        try:
            ps = PipelineStatus(status_upper)
        except ValueError:
            valid = [s.value for s in PipelineStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid values: {valid}",
            )
        items = get_items_by_status(db, ps)
    else:
        items = (
            db.query(ContentPipelineItem)
            .order_by(ContentPipelineItem.created_at.desc())
            .limit(100)
            .all()
        )

    return [_serialize_item(item) for item in items]


@router.get("/items/{item_id}")
def get_pipeline_item(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Get a single pipeline item by ID."""
    item = db.query(ContentPipelineItem).filter(
        ContentPipelineItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    return _serialize_item(item)


@router.post("/items/{item_id}/transition")
def transition_pipeline_item(
    item_id: uuid.UUID,
    body: TransitionRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually transition a pipeline item to a new status.

    Validates the transition is allowed according to the pipeline rules.
    """
    # Find current item
    item = db.query(ContentPipelineItem).filter(
        ContentPipelineItem.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")

    # Parse target status
    target_upper = body.to_status.upper()
    try:
        to_status = PipelineStatus(target_upper)
    except ValueError:
        valid = [s.value for s in PipelineStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target status '{body.to_status}'. Valid values: {valid}",
        )

    # Validate transition
    from_status = item.status
    if not is_valid_transition(from_status, to_status):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition: {from_status.value} → {to_status.value}",
        )

    # Execute transition
    try:
        updated = transition(db, item_id, from_status, to_status)
    except TransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    log_audit(
        db=db,
        actor="api",
        action="pipeline.manual_transition",
        resource_type="pipeline_item",
        resource_id=str(item_id),
        detail={
            "from_status": from_status.value,
            "to_status": to_status.value,
        },
    )

    return _serialize_item(updated)


@router.post("/run/scout")
def run_scout_agent(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually trigger the Scout agent."""
    from ..services.agents.scout import run_scout
    items = run_scout(db)
    log_audit(
        db=db,
        actor="api",
        action="pipeline.run_scout",
        resource_type="pipeline",
        detail={"items_created": len(items)},
    )
    return {"agent": "scout", "items_created": len(items)}


@router.post("/run/writer")
def run_writer_agent(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually trigger the Writer agent."""
    from ..services.agents.writer import run_writer
    passed = run_writer(db)
    log_audit(
        db=db,
        actor="api",
        action="pipeline.run_writer",
        resource_type="pipeline",
        detail={"items_written": passed},
    )
    return {"agent": "writer", "items_written": passed}


@router.post("/run/editor")
def run_editor_agent(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually trigger the Editor agent."""
    from ..services.agents.editor import run_editor
    passed = run_editor(db)
    log_audit(
        db=db,
        actor="api",
        action="pipeline.run_editor",
        resource_type="pipeline",
        detail={"items_passed": passed},
    )
    return {"agent": "editor", "items_passed": passed}


@router.post("/run/publisher")
def run_publisher_agent(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually trigger the Publisher agent."""
    from ..services.agents.publisher import run_publisher
    published = run_publisher(db)
    log_audit(
        db=db,
        actor="api",
        action="pipeline.run_publisher",
        resource_type="pipeline",
        detail={"items_published": published},
    )
    return {"agent": "publisher", "items_published": published}


@router.post("/run/promoter")
def run_promoter_agent(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually trigger the Promoter agent."""
    from ..services.agents.promoter import run_promoter
    promoted = run_promoter(db)
    log_audit(
        db=db,
        actor="api",
        action="pipeline.run_promoter",
        resource_type="pipeline",
        detail={"items_promoted": promoted},
    )
    return {"agent": "promoter", "items_promoted": promoted}


@router.post("/run/morgan")
def run_morgan_agent(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    """Manually trigger the Morgan PM self-healing agent."""
    from ..services.agents.morgan import run_morgan
    result = run_morgan(db)
    log_audit(
        db=db,
        actor="api",
        action="pipeline.run_morgan",
        resource_type="pipeline",
        detail={
            "stale_claims_recovered": result["stale_claims_recovered"],
            "errored_items_reset": result["errored_items_reset"],
            "health_status": result["health"]["health_status"],
        },
    )
    return {"agent": "morgan", **result}


@router.get("/health")
def pipeline_health(
    db: Session = Depends(get_db),
    _auth: None = Depends(require_read_access),
):
    """Return pipeline health report without performing any healing actions."""
    from ..services.agents.morgan import generate_health_report
    return generate_health_report(db)
