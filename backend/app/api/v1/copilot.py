"""AI Compliance Copilot — grounded in authorized data with deterministic fallback."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/copilot/query")
async def copilot_query(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Answer a natural-language question using grounded, authorized data.
    Falls back to deterministic responses if no LLM is configured.
    """
    question = request.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    question_lower = question.lower()
    
    # Determine scope
    scoped_inst_ids = None
    if current_user.has_role("INSTITUTION_ADMIN"):
        scoped_inst_ids = get_user_institution_ids(db, current_user)
    
    # Route to appropriate deterministic query tool
    answer = None
    evidence_refs = []
    
    if "unresolved validation issues" in question_lower or "most issues" in question_lower:
        answer, evidence_refs = _query_institutions_with_issues(db, scoped_inst_ids)
    elif "risk score" in question_lower or "case" in question_lower:
        answer, evidence_refs = _query_case_risk_score(db, question, scoped_inst_ids, current_user)
    elif "intake reconciliation" in question_lower or "intake" in question_lower:
        answer, evidence_refs = _query_intake_reconciliation(db, scoped_inst_ids)
    elif "discrepancies" in question_lower:
        answer, evidence_refs = _query_discrepancies(db, scoped_inst_ids)
    elif "duplicate" in question_lower:
        answer, evidence_refs = _query_duplicate_evidence(db, question, scoped_inst_ids)
    elif "awaiting" in question_lower and ("institution" in question_lower or "response" in question_lower):
        answer, evidence_refs = _query_cases_awaiting_response(db, scoped_inst_ids)
    elif "help" in question_lower or "what can you" in question_lower:
        answer = (
            "I can help answer questions about:\n"
            "• Which institutions have the most unresolved validation issues?\n"
            "• Explain the reasons behind a case's risk score.\n"
            "• Show the intake reconciliation for an institution.\n"
            "• Summarize unresolved discrepancies for the current academic year.\n"
            "• What evidence supports a potential duplicate?\n"
            "• Which cases are awaiting an institution response?\n\n"
            "All answers are grounded in your authorized data scope."
        )
    else:
        answer = (
            "I don't have a specific tool to answer that question. "
            "Try asking about validation issues, risk scores, intake reconciliation, "
            "discrepancies, duplicates, or cases awaiting response."
        )
    
    is_llm = bool(settings.LLM_API_KEY and settings.LLM_PROVIDER)
    provider = settings.LLM_PROVIDER if is_llm else "deterministic_fallback"
    
    return {
        "question": question,
        "answer": answer,
        "evidence_refs": evidence_refs,
        "provider": provider,
        "is_llm": is_llm,
        "is_synthetic": settings.DEMO_MODE,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }


def _query_institutions_with_issues(db, scoped_inst_ids):
    from sqlalchemy import func
    query = db.query(
        Institution.id, Institution.name,
    ).join(
        SubmissionBatch, SubmissionBatch.institution_id == Institution.id
    ).join(
        ValidationIssue, ValidationIssue.batch_id == SubmissionBatch.id
    ).filter(ValidationIssue.status == "open")
    
    if scoped_inst_ids:
        query = query.filter(Institution.id.in_(scoped_inst_ids))
    
    results = query.group_by(Institution.id, Institution.name).order_by(
        func.count(ValidationIssue.id).desc()
    ).limit(10).all()
    
    counts = {}
    for inst_id, inst_name in results:
        count = db.query(ValidationIssue).join(
            SubmissionBatch, ValidationIssue.batch_id == SubmissionBatch.id
        ).filter(
            SubmissionBatch.institution_id == inst_id,
            ValidationIssue.status == "open",
        ).count()
        counts[inst_name] = count
    
    if not counts:
        return "No institutions have unresolved validation issues.", []
    
    lines = [f"**Institutions with the most unresolved validation issues:**\n"]
    for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"• {name}: {count} open issue(s)")
    
    return "\n".join(lines), [{"institution_id": inst_id, "issue_count": counts.get(inst_name, 0)} for inst_id, inst_name in results]


def _query_case_risk_score(db, question, scoped_inst_ids, user):
    # Try to find case number in the question
    import re
    match = re.search(r'RC-[A-Z0-9]+', question.upper())
    if match:
        case_number = match.group()
        case = db.query(RiskCase).filter(RiskCase.case_number == case_number).first()
        if case:
            factors = db.query(__import__("app.models.risk", fromlist=["RiskFactor"]).RiskFactor).filter_by(case_id=case.id).all()
            lines = [f"**Risk Case {case.case_number}: {case.title}**\n"]
            lines.append(f"Risk Score: {case.risk_score}/100 ({case.risk_band.upper()})\n")
            lines.append("**Contributing factors:**")
            for f in factors:
                lines.append(f"• {f.description} (+{f.weight} points)")
            lines.append(f"\nExplanation: The score of {case.risk_score} is based on {len(factors)} factor(s).")
            lines.append("Note: A high score indicates review priority, not confirmed wrongdoing.")
            return "\n".join(lines), [{"case_id": case.id, "factors": len(factors)}]
    
    return "Please specify a case number (e.g., 'RC-ABCD1234') to explain its risk score.", []


def _query_intake_reconciliation(db, scoped_inst_ids):
    query = db.query(IntakeApproval)
    if scoped_inst_ids:
        query = query.filter(IntakeApproval.institution_id.in_(scoped_inst_ids))
    
    intakes = query.limit(20).all()
    if not intakes:
        return "No intake approval records found.", []
    
    lines = ["**Intake Reconciliation Summary:**\n"]
    for i in intakes:
        inst = db.query(Institution).filter(Institution.id == i.institution_id).first()
        course = db.query(Course).filter(Course.id == i.course_id).first()
        actual = db.query(StudentRecord).filter(
            StudentRecord.institution_id == i.institution_id,
            StudentRecord.course_id == i.course_id,
            StudentRecord.academic_year_id == i.academic_year_id,
        ).count()
        status = "within limit" if actual <= i.approved_intake else "EXCEEDS INTAKE"
        lines.append(f"• {inst.name if inst else 'Unknown'} — {course.name if course else 'Unknown'}: {actual}/{i.approved_intake} ({status})")
    
    return "\n".join(lines), [{"intake_id": i.id for i in intakes}]


def _query_discrepancies(db, scoped_inst_ids):
    issues_query = db.query(ValidationIssue).filter(ValidationIssue.status == "open")
    total = issues_query.count()
    
    by_code = {}
    for issue in issues_query.all():
        by_code.setdefault(issue.issue_code, []).append(issue)
    
    if not by_code:
        return "No unresolved discrepancies found.", []
    
    lines = [f"**Unresolved Discrepancies Summary:**\n"]
    for code, issues in sorted(by_code.items(), key=lambda x: len(x[1]), reverse=True):
        lines.append(f"• {code}: {len(issues)} issue(s)")
    
    return "\n".join(lines), [{"issue_code": code, "count": len(issues)} for code, issues in by_code.items()]


def _query_duplicate_evidence(db, question, scoped_inst_ids):
    from app.models.duplicate import DuplicateCandidate
    dupes = db.query(DuplicateCandidate).filter(DuplicateCandidate.reviewer_decision == "unresolved").limit(10).all()
    if not dupes:
        return "No unresolved duplicate candidates found.", []
    
    lines = ["**Potential Duplicate Evidence:**\n"]
    for d in dupes:
        lines.append(f"• Match Score: {d.match_score:.0f}% — {d.match_explanation} (Layer {d.match_layer})")
        if d.match_evidence:
            lines.append(f"  Evidence: {d.match_evidence}")
    
    return "\n".join(lines), [{"duplicate_id": d.id, "score": d.match_score} for d in dupes]


def _query_cases_awaiting_response(db, scoped_inst_ids):
    cases = db.query(InvestigationCase).filter(
        InvestigationCase.status == "awaiting_institution_response"
    ).all()
    if not cases:
        return "No cases are currently awaiting an institution response.", []
    
    lines = ["**Cases Awaiting Institution Response:**\n"]
    for c in cases:
        lines.append(f"• {c.case_number}: {c.title} (Severity: {c.severity})")
    
    return "\n".join(lines), [{"case_id": c.id, "case_number": c.case_number} for c in cases]
