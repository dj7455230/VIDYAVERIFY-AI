"""Potential duplicate detection endpoints."""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.student import StudentRecord
from app.models.duplicate import DuplicateCandidate
from app.models.institution import Institution
from app.models.audit import AuditLog
from app.config import get_settings

router = APIRouter()
settings = get_settings()


def _normalize_name(name: str) -> str:
    """Normalize a name for comparison: lowercase, strip extra spaces."""
    return " ".join(name.lower().strip().split()) if name else ""


@router.post("/duplicates/detect")
async def detect_duplicates(
    threshold: float = Query(70.0, ge=0, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run layered duplicate detection across student records."""
    query = db.query(StudentRecord)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        query = query.filter(StudentRecord.institution_id.in_(inst_ids) if inst_ids else False)
    
    students = query.all()
    
    # Clear existing unresolved candidates
    db.query(DuplicateCandidate).filter(DuplicateCandidate.reviewer_decision == "unresolved").delete()
    
    candidates = []
    
    for i in range(len(students)):
        for j in range(i + 1, len(students)):
            s1 = students[i]
            s2 = students[j]
            
            # Layer 1: Exact APAAR match
            if s1.apaar_reference == s2.apaar_reference:
                score = 100.0
                layer = 1
                explanation = "Exact APAAR reference match"
                cross_inst = s1.institution_id != s2.institution_id
                evidence = json.dumps({"field": "apaar_reference", "s1": s1.apaar_reference[:4] + "***", "s2": s2.apaar_reference[:4] + "***"})
            else:
                # Layer 2: Name + DOB + course match
                name_match = _normalize_name(s1.student_name) == _normalize_name(s2.student_name)
                dob_match = s1.date_of_birth == s2.date_of_birth and s1.date_of_birth is not None
                course_match = s1.course_id == s2.course_id
                
                if name_match and dob_match:
                    score = 85.0
                    layer = 2
                    explanation = "Matching name and date of birth"
                    cross_inst = s1.institution_id != s2.institution_id
                    evidence = json.dumps({
                        "name_match": True,
                        "dob_match": dob_match,
                        "course_match": course_match,
                        "s1_name": s1.student_name,
                        "s2_name": s2.student_name,
                    })
                # Layer 3: Fuzzy name match
                else:
                    try:
                        from rapidfuzz import fuzz
                        name_ratio = fuzz.ratio(_normalize_name(s1.student_name), _normalize_name(s2.student_name))
                    except ImportError:
                        name_ratio = 80 if _normalize_name(s1.student_name)[:10] == _normalize_name(s2.student_name)[:10] else 0
                    
                    if name_ratio >= 80 and s1.date_of_birth == s2.date_of_birth and s1.date_of_birth is not None:
                        score = float(name_ratio)
                        layer = 3
                        explanation = f"Fuzzy name match ({name_ratio:.0f}%) with matching DOB"
                        cross_inst = s1.institution_id != s2.institution_id
                        evidence = json.dumps({
                            "name_fuzz_ratio": name_ratio,
                            "dob_match": True,
                            "s1_name": s1.student_name,
                            "s2_name": s2.student_name,
                        })
                    else:
                        continue
            
            if score >= threshold:
                candidate = DuplicateCandidate(
                    student_record_id_1=s1.id,
                    student_record_id_2=s2.id,
                    match_layer=layer,
                    match_score=score,
                    match_explanation=explanation,
                    match_evidence=evidence,
                    is_cross_institution=cross_inst,
                )
                db.add(candidate)
                candidates.append({
                    "student_1": {"id": s1.id, "name": s1.student_name, "institution_id": s1.institution_id},
                    "student_2": {"id": s2.id, "name": s2.student_name, "institution_id": s2.institution_id},
                    "match_layer": layer,
                    "match_score": score,
                    "explanation": explanation,
                    "is_cross_institution": cross_inst,
                })
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="detect_duplicates",
        entity_type="duplicate_candidates",
        outcome="success",
        reason=f"Found {len(candidates)} candidates",
    ))
    db.commit()
    
    return {
        "candidates_found": len(candidates),
        "candidates": candidates[:50],
        "threshold": threshold,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


@router.get("/duplicates")
async def list_duplicates(
    min_score: float = Query(0, ge=0, le=100),
    max_score: float = Query(100, ge=0, le=100),
    decision: Optional[str] = Query(None),
    cross_institution_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(DuplicateCandidate).filter(
        DuplicateCandidate.match_score >= min_score,
        DuplicateCandidate.match_score <= max_score,
    )
    if decision:
        query = query.filter(DuplicateCandidate.reviewer_decision == decision)
    if cross_institution_only:
        query = query.filter(DuplicateCandidate.is_cross_institution == True)
    
    total = query.count()
    candidates = query.order_by(DuplicateCandidate.match_score.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for c in candidates:
        s1 = db.query(StudentRecord).filter(StudentRecord.id == c.student_record_id_1).first()
        s2 = db.query(StudentRecord).filter(StudentRecord.id == c.student_record_id_2).first()
        inst1 = db.query(Institution).filter(Institution.id == s1.institution_id).first() if s1 else None
        inst2 = db.query(Institution).filter(Institution.id == s2.institution_id).first() if s2 else None
        
        result.append({
            "id": c.id,
            "student_1": {
                "id": s1.id if s1 else None,
                "name": s1.student_name if s1 else "Unknown",
                "apaar_masked": (s1.apaar_reference[:4] + "***") if s1 else None,
                "institution_name": inst1.name if inst1 else "Unknown",
            },
            "student_2": {
                "id": s2.id if s2 else None,
                "name": s2.student_name if s2 else "Unknown",
                "apaar_masked": (s2.apaar_reference[:4] + "***") if s2 else None,
                "institution_name": inst2.name if inst2 else "Unknown",
            },
            "match_layer": c.match_layer,
            "match_score": c.match_score,
            "match_explanation": c.match_explanation,
            "match_evidence": json.loads(c.match_evidence) if c.match_evidence else None,
            "is_cross_institution": c.is_cross_institution,
            "reviewer_decision": c.reviewer_decision,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
        })
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/duplicates/{candidate_id}/review")
async def review_duplicate(
    candidate_id: str,
    review: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a duplicate candidate as confirmed, not duplicate, or needs review."""
    candidate = db.query(DuplicateCandidate).filter(DuplicateCandidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    decision = review.get("decision")
    if decision not in ("confirmed_duplicate", "not_duplicate", "needs_review"):
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    candidate.reviewer_decision = decision
    candidate.reviewer_id = current_user.id
    candidate.reviewed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    candidate.reviewer_note = review.get("note", "")
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="review_duplicate",
        entity_type="duplicate_candidate",
        entity_ref=candidate_id,
        outcome="success",
        reason=f"Decision: {decision}. {review.get('note', '')}",
    ))
    db.commit()
    
    return {
        "candidate_id": candidate_id,
        "decision": candidate.reviewer_decision,
        "message": "Review recorded. Records are NOT merged automatically.",
    }
