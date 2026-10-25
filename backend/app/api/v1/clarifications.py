"""Clarification request endpoints."""

import uuid as uuid_mod
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, require_roles, get_user_institution_ids
from app.models.user import User
from app.models.clarification import ClarificationRequest
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/clarifications")
async def list_clarifications(
    institution_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ClarificationRequest)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(ClarificationRequest.institution_id.in_(inst_ids) if inst_ids else False)
    elif institution_id:
        query = query.filter(ClarificationRequest.institution_id == institution_id)
    
    if status:
        query = query.filter(ClarificationRequest.status == status)
    
    total = query.count()
    items = query.order_by(ClarificationRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": c.id,
                "request_reference": c.request_reference,
                "institution_id": c.institution_id,
                "case_id": c.case_id,
                "subject": c.subject,
                "message": c.message,
                "status": c.status,
                "response": c.response,
                "responded_at": c.responded_at.isoformat() if c.responded_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/clarifications")
async def create_clarification(
    request_data: dict,
    current_user: User = Depends(require_roles("AICTE_ADMIN", "FRAUD_ANALYST", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    """Create a clarification request to an institution."""
    req = ClarificationRequest(
        request_reference=f"CR-{uuid_mod.uuid4().hex[:10].upper()}",
        institution_id=request_data.get("institution_id"),
        case_id=request_data.get("case_id"),
        risk_case_id=request_data.get("risk_case_id"),
        student_record_id=request_data.get("student_record_id"),
        requested_by=current_user.id,
        subject=request_data.get("subject", ""),
        message=request_data.get("message", ""),
        status="open",
    )
    db.add(req)
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="create_clarification",
        entity_type="clarification_request",
        entity_ref=req.id,
        outcome="success",
    ))
    db.commit()
    
    return {
        "id": req.id,
        "request_reference": req.request_reference,
        "status": "open",
        "message": "Clarification request created",
    }


@router.post("/clarifications/{clarification_id}/respond")
async def respond_to_clarification(
    clarification_id: str,
    response_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Institution responds to a clarification request."""
    req = db.query(ClarificationRequest).filter(ClarificationRequest.id == clarification_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Clarification request not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if req.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this institution")
    
    req.response = response_data.get("response", "")
    req.responded_by = current_user.id
    req.responded_at = datetime.now(timezone.utc)
    req.status = "responded"
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="respond_clarification",
        entity_type="clarification_request",
        entity_ref=clarification_id,
        outcome="success",
    ))
    db.commit()
    
    return {
        "id": clarification_id,
        "status": "responded",
        "message": "Response recorded",
    }
