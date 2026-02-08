from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..models import AuditLog


def log_audit(
    db: Session,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    detail: dict | None = None,
) -> None:
    row = AuditLog(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail_json=json.dumps(detail or {}),
    )
    db.add(row)
    db.commit()
