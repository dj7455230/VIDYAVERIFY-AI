"""Dashboard endpoints with real database-backed metrics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, require_roles, get_user_institution_ids
from app.models.user import User
from app.models.institution import Institution
from app.models.academic import AcademicYear, InstitutionApproval, IntakeApproval, Course
from app.models.student import StudentRecord, Enrolment
from app.models.submission import SubmissionBatch
from app.models.validation import ValidationIssue
from app.models.risk import RiskCase
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _inst_filter(user: User, db: Session, model_class):
    """Return a filter condition for institution-scoped models."""
    if user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, user)
        if hasattr(model_class, "institution_id"):
            return model_class.institution_id.in_(inst_ids) if inst_ids else False
    return None


@router.get("/dashboard/metrics")
async def get_dashboard_metrics(
    academic_year_id: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    submission_status: Optional[str] = Query(None),
    risk_band: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard metrics computed from real database records."""
    # Base filters
    inst_filter = None
    if user_is_inst_admin := current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if not inst_ids:
            return _empty_metrics()
        inst_filter = Institution.id.in_(inst_ids)

    # Apply institution filter
    inst_query = db.query(Institution).filter(Institution.is_active == True)
    if inst_filter is not None:
        inst_query = inst_query.filter(inst_filter)
    if institution_id:
        inst_query = inst_query.filter(Institution.id == institution_id)
    
    total_institutions = inst_query.count()

    # Academic year filter
    ay_filter = None
    if academic_year_id:
        ay_filter = academic_year_id

    # Active approvals
    approval_query = db.query(InstitutionApproval).filter(
        InstitutionApproval.approval_status == "approved"
    )
    if inst_filter is not None:
        subq = inst_query.with_entities(Institution.id)
        approval_query = approval_query.filter(
            InstitutionApproval.institution_id.in_(subq)
        )
    if ay_filter:
        approval_query = approval_query.filter(InstitutionApproval.academic_year_id == ay_filter)
    active_approvals = approval_query.count()

    # Student records
    student_query = db.query(StudentRecord)
    if inst_filter is not None:
        student_query = student_query.filter(
            StudentRecord.institution_id.in_(inst_query.with_entities(Institution.id))
        )
    if institution_id:
        student_query = student_query.filter(StudentRecord.institution_id == institution_id)
    if ay_filter:
        student_query = student_query.filter(StudentRecord.academic_year_id == ay_filter)
    if course_id:
        student_query = student_query.filter(StudentRecord.course_id == course_id)
    student_records_count = student_query.count()

    # Pending submissions
    sub_query = db.query(SubmissionBatch).filter(
        SubmissionBatch.status.in_(["uploaded", "validated", "issues_found"])
    )
    if inst_filter is not None:
        sub_query = sub_query.filter(
            SubmissionBatch.institution_id.in_(inst_query.with_entities(Institution.id))
        )
    if submission_status:
        sub_query = sub_query.filter(SubmissionBatch.status == submission_status)
    if ay_filter:
        sub_query = sub_query.filter(SubmissionBatch.academic_year_id == ay_filter)
    pending_submissions = sub_query.count()

    # Validation issues
    issue_query = db.query(ValidationIssue).filter(ValidationIssue.status == "open")
    if submission_status:
        issue_query = issue_query.filter(ValidationIssue.status == submission_status)
    validation_issues = issue_query.count()

    # Open investigation cases
    case_query = db.query(RiskCase).filter(RiskCase.status.in_(["open", "assigned", "under_review", "awaiting_response"]))
    if risk_band:
        case_query = case_query.filter(RiskCase.risk_band == risk_band)
    open_cases = case_query.count()

    # Cases by risk band
    band_query = db.query(RiskCase.risk_band, func.count(RiskCase.id)).filter(
        RiskCase.status.in_(["open", "assigned", "under_review", "awaiting_response"])
    ).group_by(RiskCase.risk_band)
    if risk_band:
        band_query = band_query.filter(RiskCase.risk_band == risk_band)
    cases_by_band = {band: count for band, count in band_query.all()}
    cases_by_risk = {
        "low": cases_by_band.get("low", 0),
        "medium": cases_by_band.get("medium", 0),
        "high": cases_by_band.get("high", 0),
        "critical": cases_by_band.get("critical", 0),
    }

    # Recent audit activity
    recent_audit = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    recent_audit_activity = [
        {
            "id": a.id,
            "action": a.action,
            "actor_role": a.actor_role,
            "entity_type": a.entity_type,
            "outcome": a.outcome,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in recent_audit
    ]

    # Submission trends (last 7 batches)
    recent_batches = db.query(
        SubmissionBatch.id,
        SubmissionBatch.version,
        SubmissionBatch.status,
        SubmissionBatch.total_rows,
        SubmissionBatch.created_at,
    ).order_by(SubmissionBatch.created_at.desc()).limit(7).all()
    submission_trends = [
        {
            "id": b.id,
            "version": b.version,
            "status": b.status,
            "total_rows": b.total_rows,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in reversed(recent_batches)
    ]

    # Intake reconciliation
    intake_recon = []
    if institution_id or inst_filter is not None:
        inst_ids_to_use = [institution_id] if institution_id else list(inst_query.with_entities(Institution.id))
        for inst_id in inst_ids_to_use[:5]:
            inst = db.query(Institution).filter(Institution.id == inst_id).first()
            if not inst:
                continue
            intakes = db.query(IntakeApproval).filter(IntakeApproval.institution_id == inst_id).all()
            for intake in intakes:
                actual = db.query(StudentRecord).filter(
                    StudentRecord.institution_id == inst_id,
                    StudentRecord.course_id == intake.course_id,
                    StudentRecord.academic_year_id == intake.academic_year_id,
                ).count()
                course = db.query(Course).filter(Course.id == intake.course_id).first()
                intake_recon.append({
                    "institution_id": inst_id,
                    "institution_name": inst.name,
                    "course_id": intake.course_id,
                    "course_name": course.name if course else "Unknown",
                    "approved_intake": intake.approved_intake,
                    "actual_enrolment": actual,
                    "variance": actual - intake.approved_intake,
                    "status": "within_limit" if actual <= intake.approved_intake else "exceeds_intake",
                })

    # Alerts requiring attention
    alerts = []
    # Over-intake alerts
    all_intakes = db.query(IntakeApproval).all()
    for intake in all_intakes[:20]:
        actual = db.query(StudentRecord).filter(
            StudentRecord.institution_id == intake.institution_id,
            StudentRecord.course_id == intake.course_id,
            StudentRecord.academic_year_id == intake.academic_year_id,
        ).count()
        if actual > intake.approved_intake:
            inst = db.query(Institution).filter(Institution.id == intake.institution_id).first()
            course = db.query(Course).filter(Course.id == intake.course_id).first()
            alerts.append({
                "type": "intake_exceeded",
                "severity": "high",
                "message": f"{inst.name if inst else 'Unknown'} — {course.name if course else 'Unknown'} exceeds approved intake",
                "institution_id": intake.institution_id,
                "course_id": intake.course_id,
                "approved": intake.approved_intake,
                "actual": actual,
            })
    # Critical risk cases
    critical_cases = db.query(RiskCase).filter(RiskCase.risk_band == "critical", RiskCase.status != "closed").limit(10).all()
    for c in critical_cases:
        alerts.append({
            "type": "critical_risk_case",
            "severity": "critical",
            "message": f"Critical risk case: {c.title}",
            "case_id": c.id,
            "case_number": c.case_number,
        })

    return {
        "demo_mode": settings.DEMO_MODE,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
        "metrics": {
            "total_institutions": total_institutions,
            "active_approvals": active_approvals,
            "student_records": student_records_count,
            "pending_submissions": pending_submissions,
            "validation_issues": validation_issues,
            "open_cases": open_cases,
        },
        "cases_by_risk": cases_by_risk,
        "recent_audit_activity": recent_audit_activity,
        "submission_trends": submission_trends,
        "intake_reconciliation": intake_recon,
        "alerts": alerts,
    }


def _empty_metrics():
    return {
        "demo_mode": settings.DEMO_MODE,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
        "metrics": {
            "total_institutions": 0,
            "active_approvals": 0,
            "student_records": 0,
            "pending_submissions": 0,
            "validation_issues": 0,
            "open_cases": 0,
        },
        "cases_by_risk": {"low": 0, "medium": 0, "high": 0, "critical": 0},
        "recent_audit_activity": [],
        "submission_trends": [],
        "intake_reconciliation": [],
        "alerts": [],
    }
