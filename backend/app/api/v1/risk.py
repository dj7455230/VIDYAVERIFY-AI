"""Explainable risk engine endpoints."""

import json
import uuid as uuid_mod
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids, require_roles
from app.models.user import User
from app.models.risk import RiskCase, RiskFactor, RiskScoreHistory
from app.models.student import StudentRecord
from app.models.institution import Institution
from app.models.validation import ValidationIssue
from app.models.duplicate import DuplicateCandidate
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Configurable risk weights (prototype — not validated policy)
RISK_WEIGHTS = {
    "CROSS_INSTITUTION_CONFLICT": 35,
    "INTAKE_EXCEEDED": 30,
    "UNRESOLVED_VERIFICATION": 15,
    "ACADEMIC_FIELD_INCONSISTENCY": 10,
    "UNUSUAL_REPORTING_PATTERN": 10,
}

RISK_VERSION = "v1.0"


def calculate_risk_score(factors: list[dict]) -> tuple[float, str, list[dict]]:
    """Deterministic risk scoring. Returns (score, band, factor_details)."""
    score = 0.0
    active_factors = [f for f in factors if f.get("is_active", True)]
    # Avoid double-counting: each rule_code counted once
    seen_rules = set()
    factor_details = []
    for f in active_factors:
        rule = f["rule_code"]
        if rule in seen_rules:
            continue
        seen_rules.add(rule)
        weight = RISK_WEIGHTS.get(rule, 0)
        score += weight
        factor_details.append({
            "rule_code": rule,
            "weight": weight,
            "description": f.get("description", ""),
            "evidence_ref": f.get("evidence_ref"),
        })
    score = min(max(score, 0), 100)
    if score <= 30:
        band = "low"
    elif score <= 60:
        band = "medium"
    elif score <= 80:
        band = "high"
    else:
        band = "critical"
    return score, band, factor_details


@router.post("/risk/assess/{student_id}")
async def assess_risk(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assess risk for a student record and create/update a risk case."""
    student = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if student.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Gather factors
    factors = []
    
    # Check for cross-institution duplicates
    dupes = db.query(DuplicateCandidate).filter(
        ((DuplicateCandidate.student_record_id_1 == student_id) |
         (DuplicateCandidate.student_record_id_2 == student_id)),
        DuplicateCandidate.is_cross_institution == True,
        DuplicateCandidate.reviewer_decision.in_(["unresolved", "confirmed_duplicate"]),
    ).all()
    if dupes:
        factors.append({
            "rule_code": "CROSS_INSTITUTION_CONFLICT",
            "description": "Potential cross-institution record conflict detected",
            "evidence_ref": json.dumps([{"duplicate_id": d.id, "score": d.match_score} for d in dupes]),
            "is_active": True,
        })
    
    # Check intake exceeded
    from app.models.academic import IntakeApproval
    intake = db.query(IntakeApproval).filter(
        IntakeApproval.institution_id == student.institution_id,
        IntakeApproval.course_id == student.course_id,
        IntakeApproval.academic_year_id == student.academic_year_id,
    ).first()
    if intake:
        actual = db.query(StudentRecord).filter(
            StudentRecord.institution_id == student.institution_id,
            StudentRecord.course_id == student.course_id,
            StudentRecord.academic_year_id == student.academic_year_id,
        ).count()
        if actual > intake.approved_intake:
            factors.append({
                "rule_code": "INTAKE_EXCEEDED",
                "description": f"Enrolment ({actual}) exceeds approved intake ({intake.approved_intake})",
                "evidence_ref": json.dumps({"approved": intake.approved_intake, "actual": actual}),
                "is_active": True,
            })
    
    # Check unresolved verification
    if student.verification_status in ("pending", "unverified"):
        factors.append({
            "rule_code": "UNRESOLVED_VERIFICATION",
            "description": "Identity verification pending or unverified",
            "evidence_ref": json.dumps({"verification_status": student.verification_status}),
            "is_active": True,
        })
    
    # Check academic field inconsistencies
    field_issues = db.query(ValidationIssue).filter(
        ValidationIssue.student_record_id == student_id,
        ValidationIssue.status == "open",
        ValidationIssue.issue_code.in_(["INVALID_DATE_FORMAT", "ACADEMIC_YEAR_INCONSISTENCY"]),
    ).all()
    if field_issues:
        factors.append({
            "rule_code": "ACADEMIC_FIELD_INCONSISTENCY",
            "description": f"{len(field_issues)} academic field inconsistency issues",
            "evidence_ref": json.dumps([{"issue_id": i.id, "code": i.issue_code} for i in field_issues]),
            "is_active": True,
        })
    
    score, band, factor_details = calculate_risk_score(factors)
    
    # Check if case already exists
    existing = db.query(RiskCase).filter(
        RiskCase.entity_type == "student",
        RiskCase.entity_ref == student_id,
        RiskCase.status != "closed",
    ).first()
    
    if existing:
        previous_score = existing.risk_score
        existing.risk_score = score
        existing.risk_band = band
        existing.risk_version = RISK_VERSION
        # Update factors
        db.query(RiskFactor).filter(RiskFactor.case_id == existing.id).delete()
        case = existing
    else:
        case = RiskCase(
            case_number=f"RC-{uuid_mod.uuid4().hex[:8].upper()}",
            title=f"Risk assessment: {student.student_name}",
            entity_type="student",
            entity_ref=student_id,
            risk_score=score,
            risk_band=band,
            risk_version=RISK_VERSION,
            institution_id=student.institution_id,
        )
        db.add(case)
        db.flush()
    
    # Add factors
    for fd in factor_details:
        db.add(RiskFactor(
            case_id=case.id,
            rule_code=fd["rule_code"],
            rule_version=RISK_VERSION,
            description=fd["description"],
            weight=fd["weight"],
            evidence_ref=fd.get("evidence_ref"),
        ))
    
    # Score history
    db.add(RiskScoreHistory(
        case_id=case.id,
        previous_score=existing.risk_score if existing else None,
        new_score=score,
        new_band=band,
        change_reason="Automated assessment",
        changed_by=current_user.id,
        factors_summary=json.dumps(factor_details),
    ))
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="assess_risk",
        entity_type="risk_case",
        entity_ref=case.id,
        outcome="success",
        reason=f"Score: {score} ({band})",
    ))
    db.commit()
    
    return {
        "case_id": case.id,
        "case_number": case.case_number,
        "student_id": student_id,
        "risk_score": score,
        "risk_band": band,
        "factors": factor_details,
        "explanation": f"Risk score of {score} ({band}) based on {len(factor_details)} contributing factor(s)",
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/risk/cases")
async def list_risk_cases(
    risk_band: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(RiskCase)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(RiskCase.institution_id.in_(inst_ids) if inst_ids else False)
    
    if risk_band:
        query = query.filter(RiskCase.risk_band == risk_band)
    if status:
        query = query.filter(RiskCase.status == status)
    if institution_id:
        query = query.filter(RiskCase.institution_id == institution_id)
    
    total = query.count()
    cases = query.order_by(RiskCase.risk_score.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": c.id,
                "case_number": c.case_number,
                "title": c.title,
                "entity_type": c.entity_type,
                "entity_ref": c.entity_ref,
                "risk_score": c.risk_score,
                "risk_band": c.risk_band,
                "status": c.status,
                "severity": c.severity,
                "institution_id": c.institution_id,
                "risk_version": c.risk_version,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cases
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/risk/cases/{case_id}")
async def get_risk_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = db.query(RiskCase).filter(RiskCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Risk case not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if case.institution_id and case.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    factors = db.query(RiskFactor).filter(RiskFactor.case_id == case_id).all()
    history = db.query(RiskScoreHistory).filter(RiskScoreHistory.case_id == case_id).order_by(
        RiskScoreHistory.created_at.desc()
    ).all()
    
    return {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "description": case.description,
        "entity_type": case.entity_type,
        "entity_ref": case.entity_ref,
        "risk_score": case.risk_score,
        "risk_band": case.risk_band,
        "status": case.status,
        "severity": case.severity,
        "institution_id": case.institution_id,
        "risk_version": case.risk_version,
        "override_justification": case.override_justification,
        "factors": [
            {
                "id": f.id,
                "rule_code": f.rule_code,
                "rule_version": f.rule_version,
                "description": f.description,
                "weight": f.weight,
                "evidence_ref": json.loads(f.evidence_ref) if f.evidence_ref else None,
                "is_active": f.is_active,
            }
            for f in factors
        ],
        "score_history": [
            {
                "id": h.id,
                "previous_score": h.previous_score,
                "new_score": h.new_score,
                "new_band": h.new_band,
                "change_reason": h.change_reason,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
        "explanation": f"Risk score of {case.risk_score} ({case.risk_band}) based on {len(factors)} factor(s)",
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.post("/risk/cases/{case_id}/override")
async def override_risk_score(
    case_id: str,
    override: dict,
    current_user: User = Depends(require_roles("AICTE_ADMIN", "FRAUD_ANALYST", "SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    """Override a risk score with mandatory justification."""
    case = db.query(RiskCase).filter(RiskCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Risk case not found")
    
    justification = override.get("justification", "").strip()
    if not justification:
        raise HTTPException(status_code=400, detail="Justification is required for overrides")
    
    previous_score = case.risk_score
    new_score = float(override.get("new_score", 0))
    new_score = min(max(new_score, 0), 100)
    if new_score <= 30:
        new_band = "low"
    elif new_score <= 60:
        new_band = "medium"
    elif new_score <= 80:
        new_band = "high"
    else:
        new_band = "critical"
    
    case.risk_score = new_score
    case.risk_band = new_band
    case.override_justification = justification
    case.overridden_by = current_user.id
    case.overridden_at = datetime.now(timezone.utc)
    
    db.add(RiskScoreHistory(
        case_id=case_id,
        previous_score=previous_score,
        new_score=new_score,
        new_band=new_band,
        change_reason=f"Manual override: {justification}",
        changed_by=current_user.id,
    ))
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="override_risk_score",
        entity_type="risk_case",
        entity_ref=case_id,
        outcome="success",
        reason=justification,
    ))
    db.commit()
    
    return {
        "case_id": case_id,
        "new_score": new_score,
        "new_band": new_band,
        "message": "Risk score overridden with justification recorded",
    }
