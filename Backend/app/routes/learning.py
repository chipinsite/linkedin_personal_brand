from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import LearningWeightsRead
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.learning import get_learning_weights, recompute_learning_weights

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/weights", response_model=LearningWeightsRead)
def read_weights(db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    return get_learning_weights(db)


@router.post("/recompute", response_model=LearningWeightsRead)
def recompute_weights(db: Session = Depends(get_db), _auth: None = Depends(require_write_access)):
    row = recompute_learning_weights(db)
    log_audit(
        db=db,
        actor="api",
        action="learning.recompute",
        resource_type="learning_weight",
        resource_id="1",
    )
    return row
