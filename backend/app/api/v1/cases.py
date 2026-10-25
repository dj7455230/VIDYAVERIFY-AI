"""Investigation case management endpoints."""

import uuid as uuid_mod
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, require_roles, get_user_institution_ids
from app.models.user import User
from app.models.investigation import InvestigationCase, CaseEvidence, CaseAction
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()

VALID_STATUSES = ["open", "assigned", "under_review", "awaiting_institution_response", "resolved", "closed"]


@router.get("/cases")
async def list_cases(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    assigned_to_me: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(InvestigationCase)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(InvestigationCase.linked_institution_id.in_(inst_ids) if inst_ids else False)
    
    if status:
        query = query.filter(InvestigationCase.status == status)
    if severity:
        query = query.filter(InvestigationCase.severity == severity)
    if institution_id:
        query = query.filter(InvestigationCase.linked_institution_id == institution_id)
    if assigned_to_me:
        query = query.filter(InvestigationCase.assigned_analyst_id == current_user.id)
    
    total = query.count()
    cases = query.order_by(InvestigationCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": c.id,
                "case_number": c.case_number,
                "title": c.title,
                "description": c.description,
                "severity": c.severity,
                "status": c.status,
                "assigned_analyst_id": c.assigned_analyst_id,
                "linked_institution_id": c.linked_institution_id,
                "linked_risk_case_id": c.linked_risk_case_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            }
            for c in cases
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/cases/{case_id}")
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if case.linked_institution_id and case.linked_institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    evidence = db.query(CaseEvidence).filter(CaseEvidence.case_id == case_id).all()
    actions = db.query(CaseAction).filter(CaseAction.case_id == case_id).order_by(CaseAction.created_at.desc()).all()
    
    return {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "description": case.description,
        "severity": case.severity,
        "status": case.status,
        "assigned_analyst_id": case.assigned_analyst_id,
        "linked_institution_id": case.linked_institution_id,
        "linked_risk_case_id": case.linked_risk_case_id,
        "linked_student_record_id": case.linked_student_record_id,
        "evidence": [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "description": e.description,
                "ref_id": e.ref_id,
                "ref_type": e.ref_type,
                "details": e.details,
                "added_by": e.added_by,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in evidence
        ],
        "action_history": [
            {
                "id": a.id,
                "actor_id": a.actor_id,
                "action_type": a.action_type,
                "previous_status": a.previous_status,
                "new_status": a.new_status,
                "note": a.note,
                "justification": a.justification,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ],
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.post("/cases/{case_id}/assign")
async def assign_case(
    case_id: str,
    assignment: dict,
    current_user: User = Depends(require_roles("AICTE_ADMIN", "FRAUD_ANALYST", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    analyst_id = assignment.get("analyst_id", current_user.id)
    previous_status = case.status
    case.assigned_analyst_id = analyst_id
    if case.status == "open":
        case.status = "assigned"
    
    db.add(CaseAction(
        case_id=case_id,
        actor_id=current_user.id,
        action_type="assign",
        previous_status=previous_status,
        new_status=case.status,
        note=assignment.get("note", ""),
    ))
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="assign_case",
        entity_type="investigation_case",
        entity_ref=case_id,
        outcome="success",
        reason=f"Assigned to {analyst_id}",
    ))
    db.commit()
    
    return {"case_id": case_id, "assigned_to": analyst_id, "status": case.status}


@router.post("/cases/{case_id}/add-evidence")
async def add_evidence(
    case_id: str,
    evidence: dict,
    current_user: User = Depends(require_roles("AICTE_ADMIN", "FRAUD_ANALYST", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    ev = CaseEvidence(
        case_id=case_id,
        evidence_type=evidence.get("evidence_type", "document"),
        description=evidence.get("description", ""),
        ref_id=evidence.get("ref_id"),
        ref_type=evidence.get("ref_type"),
        details=evidence.get("details"),
        added_by=current_user.id,
    )
    db.add(ev)
    db.add(CaseAction(
        case_id=case_id,
        actor_id=current_user.id,
        action_type="add_evidence",
        note=f"Added evidence: {evidence.get('description', '')}",
    ))
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="add_evidence",
        entity_type="investigation_case",
        entity_ref=case_id,
        outcome="success",
    ))
    db.commit()
    
    return {"evidence_id": ev.id, "message": "Evidence added"}


@router.post("/cases/{case_id}/add-note")
async def add_note(
    case_id: str,
    note_data: dict,
    current_user: User = Depends(require_roles("AICTE_ADMIN", "FRAUD_ANALYST", "INSTITUTION_ADMIN", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if case.linked_institution_id and case.linked_institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    db.add(CaseAction(
        case_id=case_id,
        actor_id=current_user.id,
        action_type="add_note",
        note=note_data.get("note", ""),
    ))
    db.commit()
    
    return {"message": "Note added"}


@router.post("/cases/{case_id}/transition")
async def transition_case(
    case_id: str,
    transition: dict,
    current_user: User = Depends(require_roles("AICTE_ADMIN", "FRAUD_ANALYST", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    """Transition a case to a new state."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    new_status = transition.get("new_status")
    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {VALID_STATUSES}")
    
    previous_status = case.status
    case.status = new_status
    
    if new_status == "resolved":
        case.resolved_at = datetime.now(timezone.utc)
        case.resolution_reason = transition.get("reason", "")
        case.resolved_by = current_user.id
    
    db.add(CaseAction(
        case_id=case_id,
        actor_id=current_user.id,
        action_type="status_transition",
        previous_status=previous_status,
        new_status=new_status,
        justification=transition.get("reason", ""),
        note=transition.get("note", ""),
    ))
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="transition_case",
        entity_type="investigation_case",
        entity_ref=case_id,
        outcome="success",
        reason=f"{previous_status} -> {new_status}: {transition.get('reason', '')}",
    ))
    db.commit()
    
    return {
        "case_id": case_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "message": "Case transitioned successfully",
    }
