"""Institution and approval registry endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, require_roles, get_user_institution_ids
from app.models.user import User
from app.models.institution import Institution
from app.models.academic import InstitutionApproval, IntakeApproval, Course, AcademicYear
from app.models.student import StudentRecord
from app.models.validation import ValidationIssue
from app.models.submission import SubmissionBatch
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/institutions")
async def list_institutions(
    search: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Institution).filter(Institution.is_active == True)
    
    # Scope for institution admins
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(Institution.id.in_(inst_ids) if inst_ids else False)
    
    if search:
        query = query.filter(Institution.name.ilike(f"%{search}%") | Institution.code.ilike(f"%{search}%"))
    if approval_status and academic_year_id:
        subq = db.query(InstitutionApproval.institution_id).filter(
            InstitutionApproval.approval_status == approval_status,
            InstitutionApproval.academic_year_id == academic_year_id,
        )
        query = query.filter(Institution.id.in_(subq))
    
    total = query.count()
    institutions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for inst in institutions:
        # Get submissions count
        subs = db.query(SubmissionBatch).filter(SubmissionBatch.institution_id == inst.id).count()
        # Get student records count
        students = db.query(StudentRecord).filter(StudentRecord.institution_id == inst.id).count()
        # Get open issues
        issues = db.query(ValidationIssue).join(
            SubmissionBatch, ValidationIssue.batch_id == SubmissionBatch.id
        ).filter(
            SubmissionBatch.institution_id == inst.id,
            ValidationIssue.status == "open",
        ).count()
        # Get approvals
        approvals = db.query(InstitutionApproval).filter(
            InstitutionApproval.institution_id == inst.id
        ).all()
        
        result.append({
            "id": inst.id,
            "code": inst.code,
            "name": inst.name,
            "institution_type": inst.institution_type,
            "location": inst.location,
            "state": inst.state,
            "city": inst.city,
            "is_synthetic": inst.is_synthetic,
            "submission_count": subs,
            "student_count": students,
            "open_issues": issues,
            "approvals": [
                {
                    "id": a.id,
                    "academic_year_id": a.academic_year_id,
                    "approval_status": a.approval_status,
                    "approval_date": a.approval_date.isoformat() if a.approval_date else None,
                }
                for a in approvals
            ],
        })
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/institutions/{institution_id}")
async def get_institution(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.security.dependencies import enforce_institution_scope
    enforce_institution_scope(current_user, institution_id, db)
    
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Approvals
    approvals = db.query(InstitutionApproval).filter(
        InstitutionApproval.institution_id == institution_id
    ).all()
    
    # Intake approvals
    intakes = db.query(IntakeApproval).filter(
        IntakeApproval.institution_id == institution_id
    ).all()
    intake_data = []
    for i in intakes:
        course = db.query(Course).filter(Course.id == i.course_id).first()
        ay = db.query(AcademicYear).filter(AcademicYear.id == i.academic_year_id).first()
        actual = db.query(StudentRecord).filter(
            StudentRecord.institution_id == institution_id,
            StudentRecord.course_id == i.course_id,
            StudentRecord.academic_year_id == i.academic_year_id,
        ).count()
        intake_data.append({
            "id": i.id,
            "course_id": i.course_id,
            "course_name": course.name if course else "Unknown",
            "course_code": course.code if course else None,
            "academic_year_id": i.academic_year_id,
            "academic_year": ay.year_code if ay else None,
            "approved_intake": i.approved_intake,
            "actual_enrolment": actual,
            "variance": actual - i.approved_intake,
            "status": "within_limit" if actual <= i.approved_intake else "exceeds_intake",
        })
    
    # Recent submissions
    recent_subs = db.query(SubmissionBatch).filter(
        SubmissionBatch.institution_id == institution_id
    ).order_by(SubmissionBatch.created_at.desc()).limit(10).all()
    
    # Clarification requests
    from app.models.clarification import ClarificationRequest
    clarifications = db.query(ClarificationRequest).filter(
        ClarificationRequest.institution_id == institution_id,
        ClarificationRequest.status == "open",
    ).limit(10).all()
    
    return {
        "id": inst.id,
        "code": inst.code,
        "name": inst.name,
        "institution_type": inst.institution_type,
        "location": inst.location,
        "state": inst.state,
        "city": inst.city,
        "is_synthetic": inst.is_synthetic,
        "approvals": [
            {
                "id": a.id,
                "academic_year_id": a.academic_year_id,
                "approval_status": a.approval_status,
                "approval_date": a.approval_date.isoformat() if a.approval_date else None,
                "expiry_date": a.expiry_date.isoformat() if a.expiry_date else None,
            }
            for a in approvals
        ],
        "intake_approvals": intake_data,
        "recent_submissions": [
            {
                "id": s.id,
                "version": s.version,
                "status": s.status,
                "total_rows": s.total_rows,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in recent_subs
        ],
        "open_clarifications": [
            {
                "id": c.id,
                "request_reference": c.request_reference,
                "subject": c.subject,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in clarifications
        ],
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }
