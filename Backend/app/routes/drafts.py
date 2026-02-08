import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Draft, DraftStatus
from ..schemas import DraftApprove, DraftCreate, DraftRead, DraftReject
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.workflow import approve_draft_and_schedule, create_system_draft

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("", response_model=DraftRead)
def create_draft(
    payload: DraftCreate,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    draft = Draft(**payload.model_dump())
    db.add(draft)
    db.commit()
    db.refresh(draft)
    log_audit(
        db=db,
        actor="api",
        action="draft.create",
        resource_type="draft",
        resource_id=str(draft.id),
    )
    return draft


@router.post("/generate", response_model=DraftRead)
def generate_draft(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    try:
        draft = create_system_draft(db)
        log_audit(
            db=db,
            actor="api",
            action="draft.generate",
            resource_type="draft",
            resource_id=str(draft.id),
            detail={"status": draft.status.value},
        )
        return draft
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[DraftRead])
def list_drafts(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return db.query(Draft).order_by(Draft.created_at.desc()).all()


@router.post("/{draft_id}/approve", response_model=DraftRead)
def approve_draft(
    draft_id: uuid.UUID,
    payload: DraftApprove,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.pending:
        raise HTTPException(status_code=400, detail="Draft not pending")

    approve_draft_and_schedule(db=db, draft=draft, scheduled_time=payload.scheduled_time)
    db.refresh(draft)
    log_audit(
        db=db,
        actor="api",
        action="draft.approve",
        resource_type="draft",
        resource_id=str(draft.id),
    )
    return draft


@router.post("/{draft_id}/reject", response_model=DraftRead)
def reject_draft(
    draft_id: uuid.UUID,
    payload: DraftReject,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status != DraftStatus.pending:
        raise HTTPException(status_code=400, detail="Draft not pending")

    draft.status = DraftStatus.rejected
    draft.rejection_reason = payload.reason
    db.commit()
    db.refresh(draft)
    log_audit(
        db=db,
        actor="api",
        action="draft.reject",
        resource_type="draft",
        resource_id=str(draft.id),
        detail={"reason": payload.reason},
    )
    return draft
