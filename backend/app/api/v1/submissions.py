"""Submission upload, preview, and column mapping endpoints."""

import os
import json
import uuid as uuid_mod
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.submission import SubmissionBatch, SubmissionFileMetadata
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Canonical schema columns
CANONICAL_COLUMNS = [
    "apaar_reference", "student_name", "date_of_birth", "gender",
    "institution_code", "course_code", "academic_year",
    "admission_status", "enrolment_status", "enrolment_number",
]


@router.post("/submissions/upload")
async def upload_file(
    institution_id: str = Form(...),
    academic_year_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a CSV or XLSX file for a new submission batch."""
    # Verify institution access
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this institution")
    
    # Check file type
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
    
    # Check file size
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")
    
    # Store file outside public dir
    stored_name = f"{uuid_mod.uuid4().hex}{ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(storage_path, "wb") as f:
        f.write(content)
    
    # Parse and preview
    try:
        if ext == ".csv":
            df = pd.read_csv(storage_path, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(storage_path, dtype=str)
    except Exception as e:
        os.remove(storage_path)
        raise HTTPException(status_code=422, detail=f"File parse error: {str(e)}")
    
    detected_headers = list(df.columns)
    
    # Create submission batch
    batch = SubmissionBatch(
        institution_id=institution_id,
        academic_year_id=academic_year_id,
        submitted_by_user_id=current_user.id,
        status="uploaded",
        total_rows=len(df),
    )
    db.add(batch)
    db.flush()
    
    # Store file metadata
    file_meta = SubmissionFileMetadata(
        batch_id=batch.id,
        original_filename=filename,
        stored_filename=stored_name,
        file_type=ext.lstrip("."),
        file_size_bytes=len(content),
        storage_path=storage_path,
        row_count=len(df),
    )
    db.add(file_meta)
    
    # Audit log
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="upload_submission",
        entity_type="submission_batch",
        entity_ref=batch.id,
        outcome="success",
        reason=f"Uploaded {filename} with {len(df)} rows",
    ))
    db.commit()
    
    # Preview first 20 rows
    preview_rows = df.head(20).fillna("").to_dict(orient="records")
    
    return {
        "batch_id": batch.id,
        "total_rows": len(df),
        "detected_headers": detected_headers,
        "canonical_columns": CANONICAL_COLUMNS,
        "preview": preview_rows,
        "file_type": ext.lstrip("."),
        "status": "uploaded",
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.post("/submissions/{batch_id}/map-columns")
async def map_columns(
    batch_id: str,
    mapping: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Map uploaded columns to canonical schema."""
    batch = db.query(SubmissionBatch).filter(SubmissionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Verify access
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if batch.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    file_meta = db.query(SubmissionFileMetadata).filter(
        SubmissionFileMetadata.batch_id == batch_id
    ).first()
    if not file_meta:
        raise HTTPException(status_code=404, detail="File metadata not found")
    
    file_meta.column_mapping = json.dumps(mapping)
    db.commit()
    
    return {
        "batch_id": batch_id,
        "mapping": mapping,
        "message": "Column mapping saved",
    }


@router.get("/submissions")
async def list_submissions(
    institution_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(SubmissionBatch)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(SubmissionBatch.institution_id.in_(inst_ids) if inst_ids else False)
    elif institution_id:
        query = query.filter(SubmissionBatch.institution_id == institution_id)
    
    if status:
        query = query.filter(SubmissionBatch.status == status)
    
    total = query.count()
    batches = query.order_by(SubmissionBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": b.id,
                "institution_id": b.institution_id,
                "academic_year_id": b.academic_year_id,
                "version": b.version,
                "status": b.status,
                "total_rows": b.total_rows,
                "valid_rows": b.valid_rows,
                "invalid_rows": b.invalid_rows,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "parent_batch_id": b.parent_batch_id,
            }
            for b in batches
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/submissions/{batch_id}")
async def get_submission(
    batch_id: str,
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
    
    files = db.query(SubmissionFileMetadata).filter(
        SubmissionFileMetadata.batch_id == batch_id
    ).all()
    
    from app.models.validation import ValidationIssue
    issues = db.query(ValidationIssue).filter(ValidationIssue.batch_id == batch_id).all()
    
    return {
        "id": batch.id,
        "institution_id": batch.institution_id,
        "academic_year_id": batch.academic_year_id,
        "version": batch.version,
        "status": batch.status,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "invalid_rows": batch.invalid_rows,
        "notes": batch.notes,
        "parent_batch_id": batch.parent_batch_id,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "files": [
            {
                "id": f.id,
                "original_filename": f.original_filename,
                "file_type": f.file_type,
                "file_size_bytes": f.file_size_bytes,
                "row_count": f.row_count,
                "column_mapping": json.loads(f.column_mapping) if f.column_mapping else None,
            }
            for f in files
        ],
        "issues_count": len(issues),
        "issues_by_severity": {
            "critical": sum(1 for i in issues if i.severity == "critical"),
            "error": sum(1 for i in issues if i.severity == "error"),
            "warning": sum(1 for i in issues if i.severity == "warning"),
            "info": sum(1 for i in issues if i.severity == "info"),
        },
    }


@router.get("/submissions/{batch_id}/preview")
async def get_submission_preview(
    batch_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get normalized record preview for a submission batch."""
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
    if not file_meta or not os.path.exists(file_meta.storage_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    mapping = json.loads(file_meta.column_mapping) if file_meta.column_mapping else None
    
    if file_meta.file_type == "csv":
        df = pd.read_csv(file_meta.storage_path, dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(file_meta.storage_path, dtype=str)
    
    if mapping:
        df = df.rename(columns={v: k for k, v in mapping.items() if v in df.columns})
    
    preview = df.head(limit).fillna("").to_dict(orient="records")
    
    return {
        "batch_id": batch_id,
        "total_rows": len(df),
        "columns": list(df.columns),
        "preview": preview,
        "mapping_applied": bool(mapping),
    }
