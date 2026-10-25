"""Academic Trust Graph endpoints — generates nodes and edges from DB relationships."""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.student import StudentRecord
from app.models.institution import Institution
from app.models.academic import Course, InstitutionApproval, IntakeApproval
from app.models.submission import SubmissionBatch
from app.models.validation import ValidationIssue
from app.models.risk import RiskCase
from app.models.investigation import InvestigationCase
from app.models.duplicate import DuplicateCandidate
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/graph")
async def get_trust_graph(
    institution_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get graph nodes and edges from real database relationships."""
    nodes = []
    edges = []
    node_set = set()
    _edge_counter = [0]
    
    def add_node(node_id: str, node_type: str, label: str, data: dict, risk: str = None):
        if node_id not in node_set:
            nodes.append({
                "id": node_id,
                "type": node_type,
                "data": {"label": label, **data, "risk_band": risk},
            })
            node_set.add(node_id)
    
    def add_edge(source: str, target: str, label: str, edge_type: str = "default"):
        _edge_counter[0] += 1
        edge_id = f"e{_edge_counter[0]}-{source}-{target}"
        edges.append({
            "id": edge_id,
            "source": source,
            "target": target,
            "label": label,
            "type": edge_type,
        })
    
    # Scope
    scoped_inst_ids = None
    if current_user.has_role("INSTITUTION_ADMIN"):
        scoped_inst_ids = get_user_institution_ids(db, current_user)
    
    # If student_id given, build graph around that student
    if student_id:
        student = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student record not found")
        if scoped_inst_ids and student.institution_id not in scoped_inst_ids:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        add_node(student.id, "student", student.student_name, {
            "apaar_masked": student.apaar_reference[:4] + "***",
            "admission_status": student.admission_status,
        })
        
        inst = db.query(Institution).filter(Institution.id == student.institution_id).first()
        if inst:
            add_node(inst.id, "institution", inst.name, {"code": inst.code, "type": inst.institution_type})
            add_edge(inst.id, student.id, "enrols")
        
        course = db.query(Course).filter(Course.id == student.course_id).first()
        if course:
            add_node(course.id, "course", course.name, {"code": course.code, "type": course.course_type})
            add_edge(course.id, student.id, "has_student")
        
        # Submission batch
        if student.source_submission_batch_id:
            batch = db.query(SubmissionBatch).filter(SubmissionBatch.id == student.source_submission_batch_id).first()
            if batch:
                add_node(batch.id, "submission", f"Batch v{batch.version}", {"status": batch.status, "total_rows": batch.total_rows})
                add_edge(batch.id, student.id, "contains")
        
        # Validation issues
        issues = db.query(ValidationIssue).filter(ValidationIssue.student_record_id == student_id).all()
        for issue in issues[:20]:
            add_node(issue.id, "issue", f"{issue.issue_code}", {"severity": issue.severity, "status": issue.status})
            add_edge(student.id, issue.id, "has_issue")
        
        # Risk cases
        risks = db.query(RiskCase).filter(RiskCase.entity_ref == student_id).all()
        for r in risks:
            add_node(r.id, "risk", r.title, {"score": r.risk_score, "band": r.risk_band})
            add_edge(student.id, r.id, "has_risk")
        
        # Duplicate candidates
        dupes = db.query(DuplicateCandidate).filter(
            (DuplicateCandidate.student_record_id_1 == student_id) |
            (DuplicateCandidate.student_record_id_2 == student_id)
        ).all()
        for d in dupes:
            other_id = d.student_record_id_2 if d.student_record_id_1 == student_id else d.student_record_id_1
            other = db.query(StudentRecord).filter(StudentRecord.id == other_id).first()
            if other:
                add_node(other.id, "student", other.student_name, {
                    "apaar_masked": other.apaar_reference[:4] + "***",
                    "admission_status": other.admission_status,
                }, risk="potential_conflict")
                edge_type = "potential_conflict" if d.is_cross_institution else "possible_match"
                add_edge(student.id, other.id, f"match {d.match_score:.0f}%", edge_type)
        
        # Investigation cases
        inv_cases = db.query(InvestigationCase).filter(InvestigationCase.linked_student_record_id == student_id).all()
        for ic in inv_cases:
            add_node(ic.id, "case", ic.title, {"status": ic.status, "severity": ic.severity})
            add_edge(student.id, ic.id, "investigated_in")
    
    # General graph for institution
    elif institution_id or not case_id:
        # Get institutions
        inst_query = db.query(Institution).filter(Institution.is_active == True)
        if scoped_inst_ids:
            inst_query = inst_query.filter(Institution.id.in_(scoped_inst_ids))
        if institution_id:
            inst_query = inst_query.filter(Institution.id == institution_id)
        
        institutions = inst_query.limit(10).all()
        for inst in institutions:
            add_node(inst.id, "institution", inst.name, {"code": inst.code, "type": inst.institution_type})
            
            # Courses
            intakes = db.query(IntakeApproval).filter(IntakeApproval.institution_id == inst.id).limit(10).all()
            for intake in intakes:
                course = db.query(Course).filter(Course.id == intake.course_id).first()
                if course:
                    add_node(course.id, "course", course.name, {"code": course.code})
                    add_edge(inst.id, course.id, "offers", "approval")
            
            # Submissions
            subs = db.query(SubmissionBatch).filter(SubmissionBatch.institution_id == inst.id).limit(10).all()
            for s in subs:
                add_node(s.id, "submission", f"Batch v{s.version}", {"status": s.status})
                add_edge(inst.id, s.id, "submitted")
            
            # Students
            students = db.query(StudentRecord).filter(StudentRecord.institution_id == inst.id).limit(20).all()
            for s in students:
                add_node(s.id, "student", s.student_name, {
                    "apaar_masked": s.apaar_reference[:4] + "***",
                    "admission_status": s.admission_status,
                })
                add_edge(inst.id, s.id, "enrols")
            
            # Risk cases
            risks = db.query(RiskCase).filter(RiskCase.institution_id == inst.id).limit(10).all()
            for r in risks:
                add_node(r.id, "risk", r.title, {"score": r.risk_score, "band": r.risk_band}, risk=r.risk_band)
                add_edge(inst.id, r.id, "has_risk")
    
    return {
        "nodes": nodes[:limit],
        "edges": edges[:limit * 2],
        "node_count": len(nodes[:limit]),
        "edge_count": len(edges[:limit * 2]),
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }
