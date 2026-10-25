"""Audit log search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.audit import AuditLog

router = APIRouter()


@router.get("/audit")
async def search_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search audit logs. Only accessible by audit-privileged roles."""
    if not current_user.has_any_role(["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR"]):
        raise HTTPException(status_code=403, detail="Not authorized for audit logs")
    
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if outcome:
        query = query.filter(AuditLog.outcome == outcome)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": l.id,
                "actor_id": l.actor_id,
                "actor_role": l.actor_role,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_ref": l.entity_ref,
                "outcome": l.outcome,
                "reason": l.reason,
                "case_ref": l.case_ref,
                "request_correlation_id": l.request_correlation_id,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }
