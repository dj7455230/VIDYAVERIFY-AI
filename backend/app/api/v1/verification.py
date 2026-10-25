"""Verification portal and integration sandbox endpoints."""

import json
import uuid as uuid_mod
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.student import StudentRecord
from app.models.verification import VerificationRequest, VerificationEvent, StudentIdentityCheck
from app.models.institution import Institution
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _simulate_verification(student: StudentRecord) -> dict:
    """DEMO_SIMULATOR provider — returns simulated outcomes based on synthetic data."""
    # Deterministic outcome based on APAAR reference hash
    ref_hash = hash(student.apaar_reference) % 100
    
    if ref_hash < 60:
        return {
            "status": "matched",
            "result_summary": "Matched in synthetic dataset (DEMO_SIMULATOR)",
            "response_data": json.dumps({
                "provider": "DEMO_SIMULATOR",
                "matched": True,
                "confidence": "high",
                "note": "This is a simulated result, not a real verification.",
            }),
        }
    elif ref_hash < 80:
        return {
            "status": "not_found",
            "result_summary": "Not found in synthetic dataset (DEMO_SIMULATOR)",
            "response_data": json.dumps({
                "provider": "DEMO_SIMULATOR",
                "matched": False,
                "note": "This is a simulated result.",
            }),
        }
    elif ref_hash < 95:
        return {
            "status": "manual_review",
            "result_summary": "Requires manual review (DEMO_SIMULATOR)",
            "response_data": json.dumps({
                "provider": "DEMO_SIMULATOR",
                "matched": None,
                "note": "Simulated ambiguous result.",
            }),
        }
    else:
        return {
            "status": "provider_unavailable",
            "result_summary": "Provider temporarily unavailable (DEMO_SIMULATOR)",
            "response_data": json.dumps({
                "provider": "DEMO_SIMULATOR",
                "matched": None,
                "error": "simulated_timeout",
            }),
        }


@router.post("/verification/request")
async def create_verification_request(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a verification request using the DEMO_SIMULATOR provider."""
    student_id = request_data.get("student_id")
    student = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if student.institution_id not in inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Create request
    req = VerificationRequest(
        request_reference=f"VR-{uuid_mod.uuid4().hex[:10].upper()}",
        student_record_id=student_id,
        institution_id=student.institution_id,
        requested_by=current_user.id,
        provider_name="DEMO_SIMULATOR",
        status="pending",
    )
    db.add(req)
    db.flush()
    
    # Add event
    db.add(VerificationEvent(
        request_id=req.id,
        event_type="created",
        provider_name="DEMO_SIMULATOR",
        outcome="pending",
    ))
    
    # Simulate verification
    result = _simulate_verification(student)
    req.status = result["status"]
    req.result_summary = result["result_summary"]
    req.response_data = result["response_data"]
    req.completed_at = datetime.now(timezone.utc)
    
    # Update student verification status
    if result["status"] == "matched":
        student.verification_status = "verified"
    elif result["status"] == "not_found":
        student.verification_status = "failed"
    elif result["status"] == "manual_review":
        student.verification_status = "pending"
    
    # Add completion event
    db.add(VerificationEvent(
        request_id=req.id,
        event_type="completed",
        provider_name="DEMO_SIMULATOR",
        outcome=result["status"],
        event_data=result["response_data"],
    ))
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="verification_request",
        entity_type="verification_request",
        entity_ref=req.id,
        outcome="success",
        reason=f"DEMO_SIMULATOR: {result['status']}",
    ))
    db.commit()
    
    return {
        "request_id": req.id,
        "request_reference": req.request_reference,
        "status": req.status,
        "result_summary": req.result_summary,
        "provider": "DEMO_SIMULATOR",
        "is_simulated": True,
        "demo_label": "This is a simulated verification result, NOT a real APAAR verification.",
        "completed_at": req.completed_at.isoformat() if req.completed_at else None,
    }


@router.get("/verification/requests")
async def list_verification_requests(
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(VerificationRequest)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(VerificationRequest.institution_id.in_(inst_ids) if inst_ids else False)
    elif institution_id:
        query = query.filter(VerificationRequest.institution_id == institution_id)
    
    if status:
        query = query.filter(VerificationRequest.status == status)
    
    total = query.count()
    requests = query.order_by(VerificationRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": r.id,
                "request_reference": r.request_reference,
                "student_record_id": r.student_record_id,
                "institution_id": r.institution_id,
                "provider_name": r.provider_name,
                "status": r.status,
                "result_summary": r.result_summary,
                "is_simulated": True,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in requests
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "demo_label": "All verification results are simulated (DEMO_SIMULATOR). Not real APAAR verification.",
    }


@router.get("/verification/provider-status")
async def get_provider_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the status of configured verification providers."""
    return {
        "providers": [
            {
                "name": "DEMO_SIMULATOR",
                "status": "active",
                "is_real_integration": False,
                "description": "Simulated verification provider for demonstration. Returns fictional outcomes.",
                "environment": "demo",
            },
        ],
        "note": "No real APAAR/AICTE verification provider is configured. The DEMO_SIMULATOR returns fictional results only.",
    }
