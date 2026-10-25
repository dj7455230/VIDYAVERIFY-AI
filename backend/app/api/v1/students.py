"""Student record management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.student import StudentRecord, Enrolment
from app.models.institution import Institution
from app.models.academic import Course, AcademicYear
from app.models.validation import ValidationIssue
from app.models.submission import SubmissionBatch
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _mask_id(ref: str) -> str:
    """Mask an identifier for display. Show first 4 and last 4 chars."""
    if not ref or len(ref) < 10:
        return ref
    return f"{ref[:4]}{'*' * (len(ref) - 8)}{ref[-4:]}"


@router.get("/students")
async def list_students(
    institution_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(StudentRecord)
    
    # Institution scoping
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(StudentRecord.institution_id.in_(inst_ids) if inst_ids else False)
    elif institution_id:
        query = query.filter(StudentRecord.institution_id == institution_id)
    
    if course_id:
        query = query.filter(StudentRecord.course_id == course_id)
    if academic_year_id:
        query = query.filter(StudentRecord.academic_year_id == academic_year_id)
    if verification_status:
        query = query.filter(StudentRecord.verification_status == verification_status)
    if search:
        query = query.filter(
            StudentRecord.student_name.ilike(f"%{search}%") |
            StudentRecord.apaar_reference.ilike(f"%{search}%")
        )
    
    total = query.count()
    students = query.order_by(StudentRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for s in students:
        inst = db.query(Institution).filter(Institution.id == s.institution_id).first()
        course = db.query(Course).filter(Course.id == s.course_id).first()
        result.append({
            "id": s.id,
            "apaar_reference_masked": _mask_id(s.apaar_reference),
            "student_name": s.student_name,
            "institution_id": s.institution_id,
            "institution_name": inst.name if inst else "Unknown",
            "course_id": s.course_id,
            "course_name": course.name if course else "Unknown",
            "academic_year_id": s.academic_year_id,
            "admission_status": s.admission_status,
            "enrolment_status": s.enrolment_status,
            "verification_status": s.verification_status,
            "is_synthetic": s.is_synthetic,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/students/{student_id}")
async def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    # Institution scoping
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if student.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this student record")
    
    inst = db.query(Institution).filter(Institution.id == student.institution_id).first()
    course = db.query(Course).filter(Course.id == student.course_id).first()
    ay = db.query(AcademicYear).filter(AcademicYear.id == student.academic_year_id).first()
    enrolments = db.query(Enrolment).filter(Enrolment.student_record_id == student_id).all()
    
    # Related issues
    issues = db.query(ValidationIssue).filter(ValidationIssue.student_record_id == student_id).all()
    
    return {
        "id": student.id,
        "apaar_reference_masked": _mask_id(student.apaar_reference),
        "student_name": student.student_name,
        "institution_id": student.institution_id,
        "institution_name": inst.name if inst else "Unknown",
        "course_id": student.course_id,
        "course_name": course.name if course else "Unknown",
        "academic_year_id": student.academic_year_id,
        "academic_year": ay.year_code if ay else None,
        "admission_status": student.admission_status,
        "enrolment_status": student.enrolment_status,
        "verification_status": student.verification_status,
        "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
        "gender": student.gender,
        "source_submission_batch_id": student.source_submission_batch_id,
        "source_row_number": student.source_row_number,
        "is_synthetic": student.is_synthetic,
        "enrolments": [
            {
                "id": e.id,
                "enrolment_number": e.enrolment_number,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in enrolments
        ],
        "related_issues": [
            {
                "id": i.id,
                "issue_code": i.issue_code,
                "severity": i.severity,
                "status": i.status,
                "explanation": i.explanation,
            }
            for i in issues
        ],
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }
