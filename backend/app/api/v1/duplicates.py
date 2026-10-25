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
    """Run layered duplicate detection across student records.
    
    Uses SQL GROUP BY to find candidate pairs efficiently, avoiding O(n^2) comparison.
    """
    from sqlalchemy import func, literal, text
    
    base_query = db.query(StudentRecord)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        if inst_ids:
            base_query = base_query.filter(StudentRecord.institution_id.in_(inst_ids))
        else:
            return {"candidates_found": 0, "candidates": [], "threshold": threshold}
    
    # Clear existing unresolved candidates
    db.query(DuplicateCandidate).filter(DuplicateCandidate.reviewer_decision == "unresolved").delete()
    db.commit()
    
    students = base_query.all()
    
    candidates = []
    
    # --- Layer 1: Exact APAAR reference duplicates ---
    # Use SQL GROUP BY to find groups with the same APAAR reference
    apaar_groups = db.query(
        StudentRecord.apaar_reference,
        func.count(StudentRecord.id).label("cnt"),
    ).filter(
        StudentRecord.apaar_reference != None,
        StudentRecord.apaar_reference != "",
    ).group_by(StudentRecord.apaar_reference).having(func.count(StudentRecord.id) > 1)
    
    # Apply scope filter
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        apaar_groups = apaar_groups.filter(StudentRecord.institution_id.in_(inst_ids))
    
    for apaar_ref, cnt in apaar_groups.all():
        group_students = db.query(StudentRecord).filter(StudentRecord.apaar_reference == apaar_ref).all()
        for i in range(len(group_students)):
            for j in range(i + 1, len(group_students)):
                s1, s2 = group_students[i], group_students[j]
                if threshold <= 100:
                    score = 100.0
                    layer = 1
                    explanation = "Exact APAAR reference match"
                    cross_inst = s1.institution_id != s2.institution_id
                    evidence = json.dumps({"field": "apaar_reference", "s1": s1.apaar_reference[:4] + "***", "s2": s2.apaar_reference[:4] + "***"})
                    db.add(DuplicateCandidate(
                        student_record_id_1=s1.id, student_record_id_2=s2.id,
                        match_layer=layer, match_score=score,
                        match_explanation=explanation, match_evidence=evidence,
                        is_cross_institution=cross_inst,
                    ))
                    candidates.append({
                        "student_1": {"id": s1.id, "name": s1.student_name, "institution_id": s1.institution_id},
                        "student_2": {"id": s2.id, "name": s2.student_name, "institution_id": s2.institution_id},
                        "match_layer": layer, "match_score": score,
                        "explanation": explanation, "is_cross_institution": cross_inst,
                    })
    
    # --- Layer 2: Name + DOB match (exact) ---
    # Find groups with the same normalized name and date_of_birth
    # Use a simple lower() comparison for the name
    name_dob_groups = db.query(
        func.lower(func.trim(StudentRecord.student_name)).label("norm_name"),
        StudentRecord.date_of_birth,
    ).filter(
        StudentRecord.date_of_birth != None,
        StudentRecord.student_name != None,
        StudentRecord.student_name != "",
    ).group_by(
        func.lower(func.trim(StudentRecord.student_name)),
        StudentRecord.date_of_birth,
    ).having(func.count(StudentRecord.id) > 1)
    
    if current_user.has_role("INSTITUTION_ADMIN"):
        inst_ids = get_user_institution_ids(db, current_user)
        name_dob_groups = name_dob_groups.filter(StudentRecord.institution_id.in_(inst_ids))
    
    for norm_name, dob, *_ in name_dob_groups.all():
        group_students = db.query(StudentRecord).filter(
            func.lower(func.trim(StudentRecord.student_name)) == norm_name,
            StudentRecord.date_of_birth == dob,
        ).all()
        for i in range(len(group_students)):
            for j in range(i + 1, len(group_students)):
                s1, s2 = group_students[i], group_students[j]
                # Skip if already found in layer 1
                if any(c["student_1"]["id"] == s1.id and c["student_2"]["id"] == s2.id for c in candidates):
                    continue
                if threshold <= 85:
                    score = 85.0
                    layer = 2
                    course_match = s1.course_id == s2.course_id
                    explanation = "Matching name and date of birth"
                    cross_inst = s1.institution_id != s2.institution_id
                    evidence = json.dumps({
                        "name_match": True, "dob_match": True,
                        "course_match": course_match,
                        "s1_name": s1.student_name, "s2_name": s2.student_name,
                    })
                    db.add(DuplicateCandidate(
                        student_record_id_1=s1.id, student_record_id_2=s2.id,
                        match_layer=layer, match_score=score,
                        match_explanation=explanation, match_evidence=evidence,
                        is_cross_institution=cross_inst,
                    ))
                    candidates.append({
                        "student_1": {"id": s1.id, "name": s1.student_name, "institution_id": s1.institution_id},
                        "student_2": {"id": s2.id, "name": s2.student_name, "institution_id": s2.institution_id},
                        "match_layer": layer, "match_score": score,
                        "explanation": explanation, "is_cross_institution": cross_inst,
                    })
    
    # --- Layer 3: Fuzzy name match with same DOB ---
    # Only run on a limited sample of DOB groups to keep response time reasonable
    if threshold <= 85:
        try:
            from rapidfuzz import fuzz
            
            # Get DOB groups with more than 1 student, limited to 500 groups
            dob_groups_query = db.query(
                StudentRecord.date_of_birth,
            ).filter(
                StudentRecord.date_of_birth != None,
            ).group_by(StudentRecord.date_of_birth).having(func.count(StudentRecord.id) > 1).limit(500)
            
            if current_user.has_role("INSTITUTION_ADMIN"):
                inst_ids = get_user_institution_ids(db, current_user)
                dob_groups_query = dob_groups_query.filter(StudentRecord.institution_id.in_(inst_ids))
            
            existing_pairs = set((c["student_1"]["id"], c["student_2"]["id"]) for c in candidates)
            
            for (dob,) in dob_groups_query.all():
                # Limit students per DOB group to avoid large comparisons
                dob_students = db.query(StudentRecord).filter(
                    StudentRecord.date_of_birth == dob
                ).limit(50).all()
                for i in range(len(dob_students)):
                    for j in range(i + 1, len(dob_students)):
                        s1, s2 = dob_students[i], dob_students[j]
                        pair_key = (s1.id, s2.id)
                        if pair_key in existing_pairs:
                            continue
                        
                        norm1 = _normalize_name(s1.student_name)
                        norm2 = _normalize_name(s2.student_name)
                        if not norm1 or not norm2 or norm1 == norm2:
                            continue  # Skip exact matches (already in layer 2)
                        
                        name_ratio = fuzz.ratio(norm1, norm2)
                        if name_ratio >= 80:
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
                            db.add(DuplicateCandidate(
                                student_record_id_1=s1.id, student_record_id_2=s2.id,
                                match_layer=layer, match_score=score,
                                match_explanation=explanation, match_evidence=evidence,
                                is_cross_institution=cross_inst,
                            ))
                            candidates.append({
                                "student_1": {"id": s1.id, "name": s1.student_name, "institution_id": s1.institution_id},
                                "student_2": {"id": s2.id, "name": s2.student_name, "institution_id": s2.institution_id},
                                "match_layer": layer, "match_score": score,
                                "explanation": explanation, "is_cross_institution": cross_inst,
                            })
                            existing_pairs.add(pair_key)
                        if len(candidates) >= 200:
                            break
                    if len(candidates) >= 200:
                        break
                if len(candidates) >= 200:
                    break
        except ImportError:
            pass  # rapidfuzz not available, skip layer 3
    
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
