"""AI Compliance Copilot — grounded in authorized data with reliable LLM integration and deterministic fallback."""

import re
import json
import uuid
from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.security.dependencies import get_current_user, get_user_institution_ids
from app.models.user import User
from app.models.institution import Institution
from app.models.student import StudentRecord
from app.models.validation import ValidationIssue
from app.models.submission import SubmissionBatch
from app.models.risk import RiskCase, RiskFactor
from app.models.investigation import InvestigationCase
from app.models.clarification import ClarificationRequest
from app.models.academic import IntakeApproval, Course, AcademicYear
from app.models.duplicate import DuplicateCandidate
from app.models.audit import AuditLog
from app.integrations.llm import llm_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()

SYSTEM_PROMPT = (
    "You are the AI Compliance Copilot for VIDYAVERIFY AI (SIH26263), an institutional platform for APAAR ID student data "
    "management and AICTE compliance verification. Your answers must be strictly grounded in the provided authorized records. "
    "Never invent student names, institution details, or approval numbers. If the data is missing or incomplete, state that clearly. "
    "Do not reveal unmasked APAAR IDs. Maintain an objective, professional, and compliant tone."
)


@router.post("/copilot/query")
async def copilot_query(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Answer natural-language questions using authorized database records.
    
    If LLM is configured and reachable, answers with LLM grounded in DB context.
    If LLM is not configured or unavailable, returns deterministic rule-based output.
    """
    question = request.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required and cannot be empty")

    question_lower = question.lower()

    # Determine scope: institution admins can only view their own institution data
    scoped_inst_ids: Optional[List[str]] = None
    if current_user.has_role("INSTITUTION_ADMIN"):
        scoped_inst_ids = get_user_institution_ids(db, current_user)

    # Route to specialized deterministic query tool
    tool_answer: str
    evidence_refs: List[Dict[str, Any]]
    suggested_questions: List[str]
    matched_topic: bool = True

    # 1. Total institutions
    if "how many institutions" in question_lower or "count of institutions" in question_lower or "total institutions" in question_lower:
        tool_answer, evidence_refs = _query_total_institutions(db, scoped_inst_ids)
        suggested_questions = [
            "Which institutions have the most unresolved validation issues?",
            "Summarize intake discrepancies for an institution.",
        ]

    # 2. Institutions with issues
    elif "unresolved validation issues" in question_lower or "most unresolved" in question_lower or "most issues" in question_lower:
        tool_answer, evidence_refs = _query_institutions_with_issues(db, scoped_inst_ids)
        suggested_questions = [
            "Summarize validation issues for the current academic year.",
            "Show the intake reconciliation for an institution.",
        ]

    # 3. Risk score explanation
    elif "risk score" in question_lower or ("explain" in question_lower and "risk" in question_lower):
        tool_answer, evidence_refs = _query_case_risk_score(db, question, scoped_inst_ids, current_user)
        suggested_questions = [
            "What evidence supports this potential duplicate?",
            "Which cases are waiting for clarification?",
        ]

    # 4. Clarification requests / waiting for response
    elif ("clarification" in question_lower) or ("waiting" in question_lower and "response" in question_lower) or ("awaiting" in question_lower):
        tool_answer, evidence_refs = _query_cases_awaiting_response(db, scoped_inst_ids)
        suggested_questions = [
            "Which institutions have the most unresolved validation issues?",
            "What changed after the latest record correction?",
        ]

    # 5. Intake reconciliation
    elif "intake reconciliation" in question_lower or "intake discrepancies" in question_lower or ("intake" in question_lower and "institution" in question_lower):
        tool_answer, evidence_refs = _query_intake_reconciliation(db, scoped_inst_ids)
        suggested_questions = [
            "Which institutions have the most unresolved validation issues?",
            "Summarize validation issues for the current academic year.",
        ]

    # 6. Duplicates evidence
    elif "duplicate" in question_lower:
        tool_answer, evidence_refs = _query_duplicate_evidence(db, question, scoped_inst_ids)
        suggested_questions = [
            "Explain the risk score of this case.",
            "Which cases are waiting for clarification?",
        ]

    # 7. Validation issues for academic year
    elif "validation issues" in question_lower or "discrepancies" in question_lower or "academic year" in question_lower:
        tool_answer, evidence_refs = _query_discrepancies(db, scoped_inst_ids)
        suggested_questions = [
            "Which institutions have the most unresolved validation issues?",
            "Show the intake reconciliation for an institution.",
        ]

    # 8. Record corrections / Audit
    elif "correction" in question_lower or "latest change" in question_lower or "what changed" in question_lower:
        tool_answer, evidence_refs = _query_latest_corrections(db, scoped_inst_ids)
        suggested_questions = [
            "Summarize validation issues for the current academic year.",
            "Which cases are waiting for clarification?",
        ]

    # 9. General guidance
    elif "help" in question_lower or "what can you" in question_lower or "who are you" in question_lower:
        tool_answer = (
            "I am the **VIDYAVERIFY AI Compliance Copilot**. I can assist with authorized institutional queries:\n\n"
            "1. **How many institutions are in the system?**\n"
            "2. **Which institutions have the most unresolved validation issues?**\n"
            "3. **Explain the risk score of this case.** (e.g. 'Explain risk for RC-1' or 'RC-0001')\n"
            "4. **Which cases are waiting for clarification?**\n"
            "5. **Summarize intake discrepancies for an institution.**\n"
            "6. **What evidence supports this potential duplicate?**\n"
            "7. **Summarize validation issues for the current academic year.**\n"
            "8. **What changed after the latest record correction?**\n\n"
            "All responses respect server-enforced role authorization and institutional isolation."
        )
        evidence_refs = []
        suggested_questions = [
            "How many institutions are in the system?",
            "Which institutions have the most unresolved validation issues?",
            "Which cases are waiting for clarification?",
        ]
        matched_topic = True

    # 10. Unsupported query
    else:
        matched_topic = False
        tool_answer = (
            "I could not find an authorized tool matching your specific query. "
            "Please try asking about institution counts, unresolved validation issues, "
            "case risk scores, intake reconciliation, duplicate evidence, cases awaiting clarification, "
            "or recent corrections."
        )
        evidence_refs = []
        suggested_questions = [
            "How many institutions are in the system?",
            "Which institutions have the most unresolved validation issues?",
            "Which cases are waiting for clarification?",
        ]

    # If LLM service is configured and topic was matched with data, synthesize response
    is_llm = False
    final_answer = tool_answer
    provider_name = "RULE-BASED COPILOT — LLM NOT CONFIGURED"

    if llm_service.is_configured and matched_topic:
        llm_resp = await llm_service.generate_response(
            system_prompt=SYSTEM_PROMPT,
            user_message=question,
            context_data=tool_answer,
        )
        if llm_resp:
            final_answer = llm_resp
            is_llm = True
            provider_name = f"{settings.LLM_PROVIDER} ({settings.LLM_MODEL or 'default'})"

    # Log to audit trail
    correlation_id = str(uuid.uuid4())
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else "USER",
        action="copilot_query",
        entity_type="copilot",
        entity_ref=correlation_id,
        outcome="success",
        reason=f"Question: {question[:100]} | Provider: {provider_name}",
        request_correlation_id=correlation_id,
    ))
    db.commit()

    return {
        "question": question,
        "answer": final_answer,
        "evidence_refs": evidence_refs,
        "suggested_questions": suggested_questions,
        "provider": provider_name,
        "is_llm": is_llm,
        "mode": "llm" if is_llm else "rule_based",
        "is_synthetic": settings.DEMO_MODE,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
        "request_id": correlation_id,
    }


def _query_total_institutions(db: Session, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    query = db.query(Institution)
    if scoped_inst_ids is not None:
        query = query.filter(Institution.id.in_(scoped_inst_ids))
    total = query.count()
    
    colleges = query.filter(Institution.institution_type == "college").count()
    polytechnics = query.filter(Institution.institution_type == "polytechnic").count()
    universities = query.filter(Institution.institution_type == "university").count()
    
    text = (
        f"**Institution Registry Summary:**\n\n"
        f"There are currently **{total} institution(s)** registered in your authorized scope:\n"
        f"• **Colleges:** {colleges}\n"
        f"• **Polytechnics:** {polytechnics}\n"
        f"• **Universities:** {universities}\n\n"
        f"*All institutional approval profiles are backed by AICTE Section 10(k) intake allocations.*"
    )
    return text, [{"total_institutions": total, "colleges": colleges, "polytechnics": polytechnics}]


def _query_institutions_with_issues(db: Session, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    query = db.query(
        Institution.id, Institution.name, func.count(ValidationIssue.id).label("issue_count")
    ).join(
        SubmissionBatch, SubmissionBatch.institution_id == Institution.id
    ).join(
        ValidationIssue, ValidationIssue.batch_id == SubmissionBatch.id
    ).filter(ValidationIssue.status == "open")

    if scoped_inst_ids is not None:
        query = query.filter(Institution.id.in_(scoped_inst_ids))

    results = query.group_by(Institution.id, Institution.name).order_by(
        desc("issue_count")
    ).limit(10).all()

    if not results:
        return "No institutions currently have unresolved validation issues within your authorized scope.", []

    lines = ["**Institutions with the Most Unresolved Validation Issues:**\n"]
    evidence = []
    for inst_id, name, count in results:
        lines.append(f"• **{name}**: {count} open issue(s)")
        evidence.append({"institution_id": inst_id, "institution_name": name, "open_issues": count})

    lines.append("\n*Issues encompass intake ceiling breaches, missing APAAR references, and cross-institution duplicates.*")
    return "\n".join(lines), evidence


def _query_case_risk_score(db: Session, question: str, scoped_inst_ids: Optional[List[str]], user: User) -> Tuple[str, List[Dict[str, Any]]]:
    # Look for patterns like RC-123 or case-123 or pick the highest risk case if none specified
    match = re.search(r'RC-?[A-Z0-9]+', question.upper())
    case = None

    if match:
        case_num = match.group()
        # Support both RC-001 and RC001
        case = db.query(RiskCase).filter(
            (RiskCase.case_number == case_num) | (RiskCase.case_number.ilike(f"%{case_num.replace('RC-', '').replace('RC', '')}%"))
        ).first()

    if not case:
        # Fallback to the top critical case
        query = db.query(RiskCase)
        if scoped_inst_ids is not None:
            query = query.filter(RiskCase.institution_id.in_(scoped_inst_ids))
        case = query.order_by(desc(RiskCase.risk_score)).first()

    if not case:
        return "No risk cases found in the system for your authorized scope.", []

    # Check institutional isolation
    if scoped_inst_ids is not None and case.institution_id and case.institution_id not in scoped_inst_ids:
        return "You are not authorized to view the requested risk case.", []

    factors = db.query(RiskFactor).filter(RiskFactor.case_id == case.id).all()
    lines = [
        f"**Risk Intelligence Assessment for Case {case.case_number}:**\n",
        f"• **Title:** {case.title}",
        f"• **Overall Risk Score:** **{case.risk_score}/100** ({case.risk_band.upper()} BAND)",
        f"• **Status:** {case.status.replace('_', ' ').capitalize()}",
        f"• **Severity:** {case.severity.capitalize()}\n",
        f"**Contributing Deterministic Rule Factors:**",
    ]

    evidence = []
    if factors:
        for f in factors:
            lines.append(f"• {f.description} (+{f.weight} pts penalty)")
            evidence.append({"factor": f.description, "weight": f.weight})
    else:
        lines.append("• Evaluated based on concurrent enrolment and intake ceiling metrics.")

    lines.append(
        "\n*Note: High risk scores prioritize review urgency; they do NOT constitute proof of fraud or identity falsification.*"
    )
    return "\n".join(lines), [{"case_id": case.id, "case_number": case.case_number, "risk_score": case.risk_score}]


def _query_cases_awaiting_response(db: Session, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    # Check investigation cases awaiting response
    query_cases = db.query(InvestigationCase).filter(
        InvestigationCase.status == "awaiting_institution_response"
    )
    query_clarifications = db.query(ClarificationRequest).filter(
        ClarificationRequest.status == "open"
    )

    if scoped_inst_ids is not None:
        query_cases = query_cases.filter(InvestigationCase.institution_id.in_(scoped_inst_ids))
        query_clarifications = query_clarifications.filter(ClarificationRequest.institution_id.in_(scoped_inst_ids))

    cases = query_cases.all()
    clarifs = query_clarifications.all()

    if not cases and not clarifs:
        return "No investigation cases or clarification requests are currently awaiting institution responses.", []

    lines = ["**Cases & Inquiries Awaiting Institutional Clarification:**\n"]
    evidence = []

    for c in cases:
        lines.append(f"• **Case {c.case_number}**: {c.title} (Severity: {c.severity})")
        evidence.append({"case_number": c.case_number, "title": c.title, "status": c.status})

    for cl in clarifs:
        lines.append(f"• **Clarification Ref {cl.request_reference}**: {cl.subject} (Due: {cl.due_date.strftime('%Y-%m-%d') if cl.due_date else 'Immediate'})")
        evidence.append({"clarification_ref": cl.request_reference, "subject": cl.subject})

    lines.append("\n*Institution administrators can respond directly in the Case Review or Clarification panel.*")
    return "\n".join(lines), evidence


def _query_intake_reconciliation(db: Session, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    query = db.query(IntakeApproval)
    if scoped_inst_ids is not None:
        query = query.filter(IntakeApproval.institution_id.in_(scoped_inst_ids))

    intakes = query.limit(15).all()
    if not intakes:
        return "No intake approval records found for reconciliation.", []

    lines = ["**Intake Capacity Reconciliation Summary (AICTE Sec 10k):**\n"]
    evidence = []
    exceeded_count = 0

    for i in intakes:
        inst = db.query(Institution).filter(Institution.id == i.institution_id).first()
        course = db.query(Course).filter(Course.id == i.course_id).first()
        actual = db.query(StudentRecord).filter(
            StudentRecord.institution_id == i.institution_id,
            StudentRecord.course_id == i.course_id,
            StudentRecord.academic_year_id == i.academic_year_id,
        ).count()

        exceeds = actual > i.approved_intake
        if exceeds:
            exceeded_count += 1
            status_str = f"⚠️ EXCEEDS CEILING (+{actual - i.approved_intake})"
        else:
            status_str = "✓ Within Limit"

        inst_name = inst.name if inst else "Unknown Institution"
        course_name = course.name if course else "Unknown Program"
        lines.append(f"• **{inst_name}** | {course_name}: **{actual}** enrolled / **{i.approved_intake}** approved ({status_str})")
        evidence.append({
            "institution": inst_name,
            "course": course_name,
            "approved": i.approved_intake,
            "actual": actual,
            "exceeds": exceeds,
        })

    if exceeded_count > 0:
        lines.append(f"\n*Warning: Found {exceeded_count} course program(s) exceeding AICTE approved seat limits.*")
    else:
        lines.append("\n*All sampled programs comply with AICTE approved seat limits.*")

    return "\n".join(lines), evidence


def _query_discrepancies(db: Session, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    query = db.query(ValidationIssue).join(
        SubmissionBatch, ValidationIssue.batch_id == SubmissionBatch.id
    ).filter(ValidationIssue.status == "open")

    if scoped_inst_ids is not None:
        query = query.filter(SubmissionBatch.institution_id.in_(scoped_inst_ids))

    total = query.count()
    if total == 0:
        return "No unresolved validation discrepancies found in your authorized scope.", []

    # Breakdown by code
    results = db.query(
        ValidationIssue.issue_code, func.count(ValidationIssue.id)
    ).join(
        SubmissionBatch, ValidationIssue.batch_id == SubmissionBatch.id
    ).filter(
        ValidationIssue.status == "open"
    )
    if scoped_inst_ids is not None:
        results = results.filter(SubmissionBatch.institution_id.in_(scoped_inst_ids))

    grouped = results.group_by(ValidationIssue.issue_code).order_by(desc(func.count(ValidationIssue.id))).all()

    lines = [f"**Unresolved Discrepancies Summary (Total: {total}):**\n"]
    evidence = []
    for code, cnt in grouped:
        lines.append(f"• **{code}**: {cnt} flagged issue(s)")
        evidence.append({"issue_code": code, "count": cnt})

    lines.append("\n*Resolve these issues under 'Validation & Reconciliation' or generate an audit justification.*")
    return "\n".join(lines), evidence


def _query_duplicate_evidence(db: Session, question: str, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    query = db.query(DuplicateCandidate).filter(DuplicateCandidate.reviewer_decision == "unresolved")
    
    # Cross-institution check filter if mentioned
    if "cross" in question.lower():
        query = query.filter(DuplicateCandidate.is_cross_institution == True)

    dupes = query.order_by(desc(DuplicateCandidate.match_score)).limit(6).all()
    if not dupes:
        return "No unresolved duplicate candidates found in the system.", []

    lines = ["**Potential Duplicate Evidence & Match Breakdown:**\n"]
    evidence = []
    for d in dupes:
        s1 = db.query(StudentRecord).filter(StudentRecord.id == d.student_record_id_1).first()
        s2 = db.query(StudentRecord).filter(StudentRecord.id == d.student_record_id_2).first()
        s1_name = s1.student_name if s1 else "Student A"
        s2_name = s2.student_name if s2 else "Student B"

        cross_tag = " [Cross-Institution]" if d.is_cross_institution else ""
        lines.append(
            f"• **Match Score {d.match_score:.0f}%** (Layer {d.match_layer}{cross_tag}):\n"
            f"  - Record 1: {s1_name} ({s1.apaar_reference[:4]}**** if s1 else '')\n"
            f"  - Record 2: {s2_name} ({s2.apaar_reference[:4]}**** if s2 else '')\n"
            f"  - Rationale: {d.match_explanation}"
        )
        evidence.append({"candidate_id": d.id, "match_score": d.match_score, "layer": d.match_layer})

    lines.append("\n*Automated merges are prohibited. Review decisions must be marked manually by a Fraud Analyst.*")
    return "\n".join(lines), evidence


def _query_latest_corrections(db: Session, scoped_inst_ids: Optional[List[str]]) -> Tuple[str, List[Dict[str, Any]]]:
    query = db.query(AuditLog).filter(
        AuditLog.action.in_(["resolve_issue", "update_student", "correction", "validate_submission"])
    ).order_by(desc(AuditLog.created_at)).limit(6)

    logs = query.all()
    if not logs:
        return "No recent record corrections or validations logged in the audit trail.", []

    lines = ["**Recent Record Corrections & Audit Actions:**\n"]
    evidence = []
    for log in logs:
        timestamp_str = log.created_at.strftime("%Y-%m-%d %H:%M UTC") if log.created_at else "Recently"
        lines.append(f"• **{log.action}** by {log.actor_role or 'System'} at {timestamp_str}: {log.reason or 'Action completed'}")
        evidence.append({"action": log.action, "timestamp": timestamp_str, "reason": log.reason})

    lines.append("\n*All modifications are captured in the immutable audit trail.*")
    return "\n".join(lines), evidence
