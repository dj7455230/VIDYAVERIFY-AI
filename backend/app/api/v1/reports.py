"""Reports and exports endpoints."""

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.institution import Institution
from app.models.student import StudentRecord
from app.models.validation import ValidationIssue
from app.models.submission import SubmissionBatch
from app.models.risk import RiskCase
from app.models.investigation import InvestigationCase
from app.models.academic import IntakeApproval, Course
from app.models.clarification import ClarificationRequest
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _csv_response(data: list[dict], filename: str):
    if not data:
        data = [{"message": "No data available"}]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/institution-summary")
async def institution_summary_report(
    academic_year_id: Optional[str] = Query(None),
    export: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Institution).filter(Institution.is_active == True)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(Institution.id.in_(inst_ids) if inst_ids else False)
    
    institutions = query.all()
    data = []
    for inst in institutions:
        student_count = db.query(StudentRecord).filter(
            StudentRecord.institution_id == inst.id,
            StudentRecord.academic_year_id == academic_year_id if academic_year_id else True,
        ).count()
        submission_count = db.query(SubmissionBatch).filter(SubmissionBatch.institution_id == inst.id).count()
        issue_count = db.query(ValidationIssue).join(
            SubmissionBatch, ValidationIssue.batch_id == SubmissionBatch.id
        ).filter(
            SubmissionBatch.institution_id == inst.id,
            ValidationIssue.status == "open",
        ).count()
        
        data.append({
            "code": inst.code,
            "name": inst.name,
            "type": inst.institution_type,
            "state": inst.state or "",
            "student_count": student_count,
            "submission_count": submission_count,
            "open_issues": issue_count,
            "is_synthetic": inst.is_synthetic,
        })
    
    if export == "csv":
        return _csv_response(data, "institution_summary.csv")
    
    return {
        "report": "institution_summary",
        "items": data,
        "total": len(data),
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/reports/intake-reconciliation")
async def intake_reconciliation_report(
    institution_id: Optional[str] = Query(None),
    export: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(IntakeApproval)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(IntakeApproval.institution_id.in_(inst_ids) if inst_ids else False)
    elif institution_id:
        query = query.filter(IntakeApproval.institution_id == institution_id)
    
    intakes = query.all()
    data = []
    for i in intakes:
        inst = db.query(Institution).filter(Institution.id == i.institution_id).first()
        course = db.query(Course).filter(Course.id == i.course_id).first()
        actual = db.query(StudentRecord).filter(
            StudentRecord.institution_id == i.institution_id,
            StudentRecord.course_id == i.course_id,
            StudentRecord.academic_year_id == i.academic_year_id,
        ).count()
        data.append({
            "institution_name": inst.name if inst else "Unknown",
            "course_name": course.name if course else "Unknown",
            "course_code": course.code if course else "",
            "approved_intake": i.approved_intake,
            "actual_enrolment": actual,
            "variance": actual - i.approved_intake,
            "status": "within_limit" if actual <= i.approved_intake else "exceeds_intake",
        })
    
    if export == "csv":
        return _csv_response(data, "intake_reconciliation.csv")
    
    return {
        "report": "intake_reconciliation",
        "items": data,
        "total": len(data),
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/reports/validation-issues")
async def validation_issues_report(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    export: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationIssue)
    if status:
        query = query.filter(ValidationIssue.status == status)
    if severity:
        query = query.filter(ValidationIssue.severity == severity)
    
    issues = query.limit(500).all()
    data = [
        {
            "id": i.id,
            "issue_code": i.issue_code,
            "severity": i.severity,
            "field_name": i.field_name or "",
            "row_number": i.row_number or "",
            "explanation": i.explanation,
            "status": i.status,
            "created_at": i.created_at.isoformat() if i.created_at else "",
        }
        for i in issues
    ]
    
    if export == "csv":
        return _csv_response(data, "validation_issues.csv")
    
    return {
        "report": "validation_issues",
        "items": data,
        "total": len(data),
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/reports/risk-cases")
async def risk_cases_report(
    risk_band: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    export: Optional[str] = Query(None),
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
    
    cases = query.limit(500).all()
    data = [
        {
            "case_number": c.case_number,
            "title": c.title,
            "risk_score": c.risk_score,
            "risk_band": c.risk_band,
            "status": c.status,
            "severity": c.severity,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        }
        for c in cases
    ]
    
    if export == "csv":
        return _csv_response(data, "risk_cases.csv")
    
    return {
        "report": "risk_cases",
        "items": data,
        "total": len(data),
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/reports/audit")
async def audit_report(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    export: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.audit import AuditLog
    from app.security.dependencies import require_roles
    
    # Only audit-privileged roles
    if not current_user.has_any_role(["SUPER_ADMIN", "AICTE_ADMIN", "AUDITOR"]):
        raise HTTPException(status_code=403, detail="Not authorized for audit reports")
    
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(500).all()
    data = [
        {
            "id": l.id,
            "action": l.action,
            "actor_role": l.actor_role or "",
            "entity_type": l.entity_type or "",
            "entity_ref": l.entity_ref or "",
            "outcome": l.outcome,
            "reason": l.reason or "",
            "created_at": l.created_at.isoformat() if l.created_at else "",
        }
        for l in logs
    ]
    
    if export == "csv":
        return _csv_response(data, "audit_report.csv")
    
    return {
        "report": "audit",
        "items": data,
        "total": len(data),
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }
