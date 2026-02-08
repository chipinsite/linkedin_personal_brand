from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import SourceMaterial
from ..schemas import SourceIngestRequest, SourceMaterialRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.research_ingestion import DEFAULT_FEEDS, ingest_feeds

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceMaterialRead])
def list_sources(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return db.query(SourceMaterial).order_by(SourceMaterial.created_at.desc()).limit(100).all()


@router.post("/ingest")
def ingest_sources(
    payload: SourceIngestRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    configured = [item.strip() for item in settings.research_feed_urls.split(",") if item.strip()]
    feeds = payload.feed_urls or configured or DEFAULT_FEEDS
    created = ingest_feeds(db=db, feed_urls=feeds, max_items_per_feed=payload.max_items_per_feed)
    log_audit(
        db=db,
        actor="api",
        action="source.ingest",
        resource_type="source_material",
        detail={"created": created, "feeds_count": len(feeds)},
    )
    return {"created": created, "feeds_count": len(feeds)}
