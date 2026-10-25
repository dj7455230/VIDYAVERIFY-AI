"""Validation engine endpoints: run validation, list issues, resolve issues."""

import json
import uuid as uuid_mod
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.submission import SubmissionBatch, SubmissionFileMetadata
from app.models.validation import ValidationIssue
from app.models.student import StudentRecord
from app.models.institution import Institution
from app.models.academic import Course, AcademicYear, IntakeApproval
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()

REQUIRED_FIELDS = ["apaar_reference", "student_name", "institution_code", "course_code", "academic_year", "admission_status"]


@router.post("/submissions/{batch_id}/validate")
async def validate_submission(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run validation rules against a submission batch."""
    batch = db.query(SubmissionBatch).filter(SubmissionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if batch.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    file_meta = db.query(SubmissionFileMetadata).filter(
        SubmissionFileMetadata.batch_id == batch_id
    ).first()
    if not file_meta or not __import__("os").path.exists(file_meta.storage_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    mapping = json.loads(file_meta.column_mapping) if file_meta.column_mapping else None
    
    if file_meta.file_type == "csv":
        df = pd.read_csv(file_meta.storage_path, dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(file_meta.storage_path, dtype=str)
    
    if mapping:
        df = df.rename(columns={v: k for k, v in mapping.items() if v in df.columns})
    
    # Clear existing issues
    db.query(ValidationIssue).filter(ValidationIssue.batch_id == batch_id).delete()
    
    issues = []
    valid_rows = 0
    invalid_rows = 0
    seen_apaars = {}
    
    inst = db.query(Institution).filter(Institution.id == batch.institution_id).first()
    
    for idx, row in df.iterrows():
        row_num = int(idx) + 1
        row_has_errors = False
        
        # 1. Required fields check
        for field in REQUIRED_FIELDS:
            val = str(row.get(field, "")).strip()
            if not val or val.lower() == "nan":
                issues.append(ValidationIssue(
                    batch_id=batch_id,
                    issue_code="REQUIRED_FIELD_MISSING",
                    severity="error",
                    field_name=field,
                    row_number=row_num,
                    explanation=f"Required field '{field}' is missing or empty",
                    expected_value="Non-empty value",
                    observed_value=str(row.get(field, "")),
                    recommended_action=f"Provide a valid value for '{field}'",
                    status="open",
                ))
                row_has_errors = True
        
        # 2. Duplicate APAAR within submission
        apaar = str(row.get("apaar_reference", "")).strip()
        if apaar and apaar.lower() != "nan":
            if apaar in seen_apaars:
                issues.append(ValidationIssue(
                    batch_id=batch_id,
                    issue_code="DUPLICATE_WITHIN_SUBMISSION",
                    severity="error",
                    field_name="apaar_reference",
                    row_number=row_num,
                    explanation=f"APAAR reference '{apaar[:4]}***' already appears at row {seen_apaars[apaar]}",
                    observed_value=apaar,
                    recommended_action="Review and remove duplicate entry or provide a unique reference",
                    status="open",
                ))
                row_has_errors = True
            else:
                seen_apaars[apaar] = row_num
        
        # 3. Date format check (date_of_birth)
        dob = str(row.get("date_of_birth", "")).strip()
        if dob and dob.lower() != "nan":
            try:
                pd.to_datetime(dob, format="%Y-%m-%d")
            except Exception:
                issues.append(ValidationIssue(
                    batch_id=batch_id,
                    issue_code="INVALID_DATE_FORMAT",
                    severity="warning",
                    field_name="date_of_birth",
                    row_number=row_num,
                    explanation=f"Date of birth '{dob}' is not in YYYY-MM-DD format",
                    expected_value="YYYY-MM-DD",
                    observed_value=dob,
                    recommended_action="Use ISO date format YYYY-MM-DD",
                    status="open",
                ))
        
        # 4. Invalid course reference
        course_code = str(row.get("course_code", "")).strip()
        if course_code and course_code.lower() != "nan":
            course = db.query(Course).filter(Course.code == course_code).first()
            if not course:
                issues.append(ValidationIssue(
                    batch_id=batch_id,
                    issue_code="INVALID_COURSE_REFERENCE",
                    severity="error",
                    field_name="course_code",
                    row_number=row_num,
                    explanation=f"Course code '{course_code}' is not found in the system",
                    observed_value=course_code,
                    recommended_action="Verify the course code matches an approved course",
                    status="open",
                ))
                row_has_errors = True
        
        # 5. Intake exceeded check
        if inst and course_code and course_code.lower() != "nan":
            course = db.query(Course).filter(Course.code == course_code).first()
            if course:
                intake = db.query(IntakeApproval).filter(
                    IntakeApproval.institution_id == inst.id,
                    IntakeApproval.course_id == course.id,
                    IntakeApproval.academic_year_id == batch.academic_year_id,
                ).first()
                if intake:
                    current_count = db.query(StudentRecord).filter(
                        StudentRecord.institution_id == inst.id,
                        StudentRecord.course_id == course.id,
                        StudentRecord.academic_year_id == batch.academic_year_id,
                    ).count()
                    if current_count + 1 > intake.approved_intake:
                        issues.append(ValidationIssue(
                            batch_id=batch_id,
                            issue_code="INTAKE_EXCEEDED",
                            severity="critical",
                            field_name="course_code",
                            row_number=row_num,
                            explanation=f"Enrolment for {course.name} would exceed approved intake of {intake.approved_intake}",
                            expected_value=f"Max {intake.approved_intake}",
                            observed_value=f"Would be {current_count + 1}",
                            recommended_action="Review intake approval or remove excess enrolments",
                            status="open",
                        ))
                        row_has_errors = True
        
        if row_has_errors:
            invalid_rows += 1
        else:
            valid_rows += 1
    
    # Insert all issues
    for issue in issues:
        db.add(issue)
    
    batch.status = "issues_found" if issues else "validated"
    batch.valid_rows = valid_rows
    batch.invalid_rows = invalid_rows
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="validate_submission",
        entity_type="submission_batch",
        entity_ref=batch_id,
        outcome="success",
        reason=f"Found {len(issues)} issues",
    ))
    db.commit()
    
    return {
        "batch_id": batch_id,
        "status": batch.status,
        "total_rows": batch.total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "issues_count": len(issues),
        "issues_by_severity": {
            "critical": sum(1 for i in issues if i.severity == "critical"),
            "error": sum(1 for i in issues if i.severity == "error"),
            "warning": sum(1 for i in issues if i.severity == "warning"),
            "info": sum(1 for i in issues if i.severity == "info"),
        },
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/submissions/{batch_id}/issues")
async def list_issues(
    batch_id: str,
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    issue_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    batch = db.query(SubmissionBatch).filter(SubmissionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if batch.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(ValidationIssue).filter(ValidationIssue.batch_id == batch_id)
    if severity:
        query = query.filter(ValidationIssue.severity == severity)
    if status:
        query = query.filter(ValidationIssue.status == status)
    if issue_code:
        query = query.filter(ValidationIssue.issue_code == issue_code)
    
    total = query.count()
    issues = query.order_by(ValidationIssue.row_number).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": i.id,
                "issue_code": i.issue_code,
                "severity": i.severity,
                "field_name": i.field_name,
                "row_number": i.row_number,
                "explanation": i.explanation,
                "expected_value": i.expected_value,
                "observed_value": i.observed_value,
                "recommended_action": i.recommended_action,
                "status": i.status,
                "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
                "resolution_note": i.resolution_note,
            }
            for i in issues
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/submissions/{batch_id}/issues/{issue_id}/resolve")
async def resolve_issue(
    batch_id: str,
    issue_id: str,
    resolution: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark an issue as resolved or accepted with justification."""
    issue = db.query(ValidationIssue).filter(
        ValidationIssue.id == issue_id,
        ValidationIssue.batch_id == batch_id,
    ).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    new_status = resolution.get("status", "resolved")
    note = resolution.get("note", "")
    if new_status not in ("resolved", "accepted_justified"):
        raise HTTPException(status_code=400, detail="Invalid status. Use 'resolved' or 'accepted_justified'")
    if new_status == "accepted_justified" and not note:
        raise HTTPException(status_code=400, detail="Justification note required for accepted_justified")
    
    issue.status = new_status
    issue.resolved_at = datetime.now(timezone.utc)
    issue.resolved_by = current_user.id
    issue.resolution_note = note
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="resolve_issue",
        entity_type="validation_issue",
        entity_ref=issue_id,
        outcome="success",
        reason=note,
    ))
    db.commit()
    
    return {
        "issue_id": issue_id,
        "status": issue.status,
        "message": "Issue resolved",
    }
