"""
Seed script: generates deterministic synthetic demo data for VIDYAVERIFY AI.
All data is fictional. No real student records, APAAR IDs, or institutional data is used.
"""

import sys
import os
import random
import uuid
from datetime import date, datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.security.auth import hash_password
from app.models.user import User, Role, user_roles
from app.models.institution import Institution, InstitutionUserMembership
from app.models.academic import AcademicYear, Course, InstitutionApproval, IntakeApproval
from app.models.student import StudentRecord, Enrolment
from app.models.submission import SubmissionBatch, SubmissionFileMetadata
from app.models.validation import ValidationIssue
from app.models.duplicate import DuplicateCandidate
from app.models.risk import RiskCase, RiskFactor, RiskScoreHistory
from app.models.investigation import InvestigationCase, CaseEvidence, CaseAction
from app.models.verification import VerificationRequest, VerificationEvent
from app.models.clarification import ClarificationRequest
from app.models.audit import AuditLog
from app.models.notification import Notification

# Deterministic random
random.seed(42)
DEMO_PASSWORD = hash_password("Demo@2026")

# Fictional name parts
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Ananya", "Diya", "Saanvi", "Aadhya", "Pari", "Riya",
    "Myra", "Anika", "Navya", "Kiara", "Rahul", "Priya", "Karan", "Neha",
    "Rohan", "Meera", "Kabir", "Sara", "Dhruv", "Ira",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Kumar", "Singh", "Reddy", "Nair", "Iyer",
    "Mehta", "Joshi", "Patel", "Rao", "Das", "Bose", "Banerjee", "Chowdhury",
    "Pillai", "Menon", "Kapoor", "Malhotra",
]

INSTITUTION_NAMES = [
    "Bharat Institute of Technology", "National Engineering College", "Indira Gandhi Polytechnic",
    "Tagore College of Engineering", "Sarvodaya Institute of Management", "Vivekananda Technical University",
    "Gandhi Institute of Applied Sciences", "Nehru College of Pharmacy", "Subhash Chandra Institute",
    "Ambedkar Engineering College", "Patel Institute of Architecture", "Radhakrishnan University",
    "Tilak Institute of Law", "Lajpat Rai College", "Bhagat Singh Polytechnic",
    "Rajendra Prasad Medical College", "Maulana Azad Institute", "Rajiv Gandhi Management College",
    "Sarojini Naidu Arts College", "CV Raman Science Institute", "Visvesvaraya Technical Academy",
    "Homi Bhabha Nuclear Institute", "Meghnad Saha Physics College", "JRD Tata Business School",
    "Vikram Sarabhai Space Institute",
]

COURSES = [
    ("CS101", "B.Tech Computer Science", "ug", 4),
    ("EC201", "B.Tech Electronics", "ug", 4),
    ("ME301", "B.Tech Mechanical", "ug", 4),
    ("CE401", "B.Tech Civil Engineering", "ug", 4),
    ("EE501", "B.Tech Electrical", "ug", 4),
    ("IT601", "BCA Information Technology", "ug", 3),
    ("PG701", "M.Tech Data Science", "pg", 2),
    ("PG801", "MBA Finance", "pg", 2),
    ("DP901", "Diploma in Computer Application", "diploma", 1),
    ("PH101", "B.Pharm Pharmacy", "ug", 4),
    ("LA201", "LLB Law", "ug", 3),
    ("AR301", "B.Arch Architecture", "ug", 5),
]

STATES = ["Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Gujarat", "West Bengal", "Telangana", "Rajasthan"]
CITIES = ["Pune", "Bengaluru", "Chennai", "New Delhi", "Ahmedabad", "Kolkata", "Hyderabad", "Jaipur"]

INSTITUTION_TYPES = ["university", "college", "institute"]

ADMISSION_STATUSES = ["admitted", "enrolled", "graduated", "dropped"]
ENROLMENT_STATUSES = ["active", "inactive", "pending"]
VERIFICATION_STATUSES = ["unverified", "pending", "verified", "failed"]

ACADEMIC_YEARS = ["2024-2025", "2025-2026"]


def generate_apaar_reference(year: int, index: int) -> str:
    """Generate a fictional, format-valid APAAR-like reference."""
    return f"APR{year}{index:06d}SYN"


def seed():
    print("Starting synthetic data seeding...")
    print(f"Password hash demo: {DEMO_PASSWORD[:20]}...")
    
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(User).count() > 0:
        print("Database already has users. Skipping seed.")
        db.close()
        return
    
    try:
        # ===== ROLES =====
        print("Creating roles...")
        roles_data = [
            ("SUPER_ADMIN", "Full system access", True),
            ("AICTE_ADMIN", "AICTE-level review and management", True),
            ("INSTITUTION_ADMIN", "Institution-scoped data management", True),
            ("FRAUD_ANALYST", "Risk case investigation", True),
            ("AUDITOR", "Read-only audit access", True),
        ]
        roles = {}
        for name, desc, is_system in roles_data:
            role = Role(name=name, description=desc, is_system=is_system)
            db.add(role)
            db.flush()
            roles[name] = role
        
        # ===== USERS =====
        print("Creating demo users...")
        users_data = [
            ("super.admin@vidyaverify.ai", "Super Admin", ["SUPER_ADMIN"]),
            ("aicte.admin@vidyaverify.ai", "AICTE Admin", ["AICTE_ADMIN"]),
            ("inst.admin@vidyaverify.ai", "Institution Admin", ["INSTITUTION_ADMIN"]),
            ("fraud.analyst@vidyaverify.ai", "Fraud Analyst", ["FRAUD_ANALYST"]),
            ("auditor@vidyaverify.ai", "Auditor", ["AUDITOR"]),
        ]
        users = {}
        for email, name, user_roles_list in users_data:
            user = User(email=email, full_name=name, hashed_password=DEMO_PASSWORD)
            db.add(user)
            db.flush()
            for role_name in user_roles_list:
                user.roles.append(roles[role_name])
            users[email] = user
        db.flush()
        
        # ===== ACADEMIC YEARS =====
        print("Creating academic years...")
        ay_records = {}
        for year_code in ACADEMIC_YEARS:
            start_year = int(year_code.split("-")[0])
            ay = AcademicYear(
                year_code=year_code,
                start_date=date(start_year, 8, 1),
                end_date=date(start_year + 1, 7, 31),
                is_active=True,
            )
            db.add(ay)
            db.flush()
            ay_records[year_code] = ay
        
        # ===== COURSES =====
        print("Creating courses...")
        course_records = {}
        for code, name, ctype, duration in COURSES:
            course = Course(code=code, name=name, course_type=ctype, duration_years=duration, is_synthetic=True)
            db.add(course)
            db.flush()
            course_records[code] = course
        
        # ===== INSTITUTIONS =====
        print("Creating 25 fictional institutions...")
        institutions = []
        for i, name in enumerate(INSTITUTION_NAMES):
            inst = Institution(
                code=f"INST{i+1:03d}",
                name=name,
                institution_type=INSTITUTION_TYPES[i % len(INSTITUTION_TYPES)],
                location=f"{CITIES[i % len(CITIES)]}, {STATES[i % len(STATES)]}",
                state=STATES[i % len(STATES)],
                city=CITIES[i % len(CITIES)],
                is_active=True,
                is_synthetic=True,
            )
            db.add(inst)
            db.flush()
            institutions.append(inst)
        
        # Assign institution admin to first institution
        inst_admin = users["inst.admin@vidyaverify.ai"]
        membership = InstitutionUserMembership(user_id=inst_admin.id, institution_id=institutions[0].id)
        db.add(membership)
        
        # ===== APPROVALS AND INTAKE =====
        print("Creating approvals and intake data...")
        approval_count = 0
        intake_count = 0
        for inst in institutions:
            for ay in ay_records.values():
                # Create approval
                approval_status = "approved" if random.random() > 0.1 else "pending"
                approval = InstitutionApproval(
                    institution_id=inst.id,
                    academic_year_id=ay.id,
                    approval_status=approval_status,
                    approval_date=date(2024, 7, 15) if approval_status == "approved" else None,
                    expiry_date=date(2030, 7, 31) if approval_status == "approved" else None,
                    approval_reference=f"APR-2024-{inst.code}-{ay.year_code}",
                    is_synthetic=True,
                )
                db.add(approval)
                db.flush()
                approval_count += 1
                
                # Create intake for subset of courses (5-8 per institution)
                inst_courses = random.sample(COURSES, min(6, len(COURSES)))
                for course_code, _, _, _ in inst_courses:
                    course = course_records[course_code]
                    approved_intake = random.choice([60, 120, 180, 240])
                    intake = IntakeApproval(
                        institution_id=inst.id,
                        course_id=course.id,
                        academic_year_id=ay.id,
                        approved_intake=approved_intake,
                        is_synthetic=True,
                    )
                    db.add(intake)
                    db.flush()
                    intake_count += 1
        
        print(f"Created {approval_count} approvals, {intake_count} intake records")
        
        # ===== STUDENT RECORDS AND ENROLMENTS =====
        print("Creating ~5000 synthetic student records...")
        student_count = 0
        enrolment_count = 0
        all_students = []
        
        # Track for cross-institution duplicates
        cross_inst_seeds = {}  # (name, dob) -> list of students
        
        for inst in institutions:
            ay = ay_records["2025-2026"]
            inst_intakes = db.query(IntakeApproval).filter(
                IntakeApproval.institution_id == inst.id,
                IntakeApproval.academic_year_id == ay.id,
            ).all()
            
            for intake in inst_intakes:
                # Generate between 80% and 110% of approved intake (some exceed)
                actual_count = int(intake.approved_intake * random.uniform(0.8, 1.15))
                
                for s_idx in range(actual_count):
                    first = random.choice(FIRST_NAMES)
                    last = random.choice(LAST_NAMES)
                    name = f"{first} {last}"
                    
                    year_offset = random.randint(2000, 2006)
                    dob = date(year_offset, random.randint(1, 12), random.randint(1, 28))
                    
                    apaar = generate_apaar_reference(2025, student_count + 1)
                    
                    student = StudentRecord(
                        apaar_reference=apaar,
                        student_name=name,
                        institution_id=inst.id,
                        course_id=intake.course_id,
                        academic_year_id=ay.id,
                        admission_status=random.choice(ADMISSION_STATUSES),
                        enrolment_status=random.choice(ENROLMENT_STATUSES),
                        verification_status=random.choice(VERIFICATION_STATUSES),
                        date_of_birth=dob,
                        gender=random.choice(["M", "F", "O"]),
                        is_synthetic=True,
                    )
                    db.add(student)
                    db.flush()
                    all_students.append(student)
                    student_count += 1
                    
                    # Create enrolment
                    enrolment = Enrolment(
                        student_record_id=student.id,
                        institution_id=inst.id,
                        course_id=intake.course_id,
                        academic_year_id=ay.id,
                        enrolment_number=f"ENR{2025}{student_count:06d}",
                        status="active",
                        is_synthetic=True,
                    )
                    db.add(enrolment)
                    db.flush()
                    enrolment_count += 1
                    
                    # Track for cross-institution duplicates
                    key = (name.lower(), dob)
                    if key not in cross_inst_seeds:
                        cross_inst_seeds[key] = []
                    cross_inst_seeds[key].append(student)
        
        print(f"Created {student_count} student records, {enrolment_count} enrolments")
        
        # ===== CREATE CONTROLLED CROSS-INSTITUTION DUPLICATES =====
        print("Creating controlled duplicate scenarios...")
        dup_count = 0
        for key, students in cross_inst_seeds.items():
            if len(students) >= 2:
                # Take a subset of pairs that are cross-institution
                inst_ids = set(s.institution_id for s in students)
                if len(inst_ids) >= 2:
                    # Pick two from different institutions
                    s1 = students[0]
                    s2 = next(s for s in students[1:] if s.institution_id != s1.institution_id)
                    candidate = DuplicateCandidate(
                        student_record_id_1=s1.id,
                        student_record_id_2=s2.id,
                        match_layer=2,
                        match_score=85.0,
                        match_explanation="Matching name and date of birth across institutions",
                        match_evidence=f'{{"name_match": true, "dob_match": true, "s1_name": "{s1.student_name}", "s2_name": "{s2.student_name}"}}',
                        is_cross_institution=True,
                        reviewer_decision="unresolved",
                    )
                    db.add(candidate)
                    dup_count += 1
                    if dup_count >= 15:
                        break
        
        print(f"Created {dup_count} cross-institution duplicate candidates")
        
        # ===== SUBMISSION BATCHES =====
        print("Creating 50+ submission batches...")
        batch_count = 0
        for inst in institutions[:15]:  # First 15 institutions
            for _ in range(random.randint(3, 5)):
                ay = random.choice(list(ay_records.values()))
                batch = SubmissionBatch(
                    institution_id=inst.id,
                    academic_year_id=ay.id,
                    submitted_by_user_id=inst_admin.id if inst == institutions[0] else users["aicte.admin@vidyaverify.ai"].id,
                    version=1,
                    status=random.choice(["uploaded", "validated", "issues_found", "accepted", "corrected"]),
                    total_rows=random.randint(50, 300),
                    valid_rows=random.randint(40, 280),
                    invalid_rows=random.randint(0, 20),
                )
                db.add(batch)
                db.flush()
                batch_count += 1
        
        print(f"Created {batch_count} submission batches")
        
        # ===== VALIDATION ISSUES =====
        print("Creating 200+ validation issues...")
        issue_count = 0
        issue_codes = [
            ("REQUIRED_FIELD_MISSING", "error", "Required field is missing"),
            ("DUPLICATE_WITHIN_SUBMISSION", "error", "Duplicate row detected"),
            ("INVALID_DATE_FORMAT", "warning", "Date format is incorrect"),
            ("INVALID_COURSE_REFERENCE", "error", "Course code not found"),
            ("INTAKE_EXCEEDED", "critical", "Enrolment exceeds approved intake"),
            ("ACADEMIC_YEAR_INCONSISTENCY", "warning", "Academic year mismatch"),
        ]
        batches = db.query(SubmissionBatch).all()
        for batch in batches:
            num_issues = random.randint(0, 8)
            for _ in range(num_issues):
                code, severity, desc = random.choice(issue_codes)
                issue = ValidationIssue(
                    batch_id=batch.id,
                    issue_code=code,
                    severity=severity,
                    field_name=random.choice(["apaar_reference", "student_name", "date_of_birth", "course_code"]),
                    row_number=random.randint(1, batch.total_rows),
                    explanation=desc,
                    expected_value="Valid value" if severity != "critical" else "Within approved intake",
                    observed_value="Missing" if severity == "error" else "Invalid",
                    recommended_action="Correct the field value",
                    status=random.choice(["open", "under_review", "resolved", "accepted_justified"]),
                )
                db.add(issue)
                issue_count += 1
                if issue_count >= 200:
                    break
            if issue_count >= 200:
                break
        
        print(f"Created {issue_count} validation issues")
        
        # ===== RISK CASES =====
        print("Creating 50+ risk cases...")
        risk_count = 0
        risk_weights = {
            "CROSS_INSTITUTION_CONFLICT": 35,
            "INTAKE_EXCEEDED": 30,
            "UNRESOLVED_VERIFICATION": 15,
            "ACADEMIC_FIELD_INCONSISTENCY": 10,
            "UNUSUAL_REPORTING_PATTERN": 10,
        }
        
        # Pick students with issues
        students_with_dupes = set()
        dupes = db.query(DuplicateCandidate).all()
        for d in dupes:
            students_with_dupes.add(d.student_record_id_1)
            students_with_dupes.add(d.student_record_id_2)
        
        for student_id in list(students_with_dupes)[:50]:
            student = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
            if not student:
                continue
            
            factors = []
            if student_id in students_with_dupes:
                factors.append("CROSS_INSTITUTION_CONFLICT")
            if student.verification_status in ("unverified", "pending"):
                factors.append("UNRESOLVED_VERIFICATION")
            
            score = sum(risk_weights.get(f, 0) for f in factors)
            score = min(score, 100)
            if score <= 30:
                band = "low"
            elif score <= 60:
                band = "medium"
            elif score <= 80:
                band = "high"
            else:
                band = "critical"
            
            case = RiskCase(
                case_number=f"RC-{risk_count+1:04d}",
                title=f"Risk assessment: {student.student_name}",
                entity_type="student",
                entity_ref=student.id,
                risk_score=float(score),
                risk_band=band,
                status=random.choice(["open", "assigned", "under_review", "resolved"]),
                severity=band,
                institution_id=student.institution_id,
                risk_version="v1.0",
            )
            db.add(case)
            db.flush()
            
            for f in factors:
                db.add(RiskFactor(
                    case_id=case.id,
                    rule_code=f,
                    rule_version="v1.0",
                    description=f"Factor: {f}",
                    weight=risk_weights[f],
                    is_active=True,
                ))
            
            db.add(RiskScoreHistory(
                case_id=case.id,
                new_score=float(score),
                new_band=band,
                change_reason="Initial assessment",
                factors_summary=",".join(factors),
            ))
            risk_count += 1
        
        print(f"Created {risk_count} risk cases")
        
        # Create some high/critical risk cases by adding more factors
        print("Creating additional high-risk cases...")
        for rc in db.query(RiskCase).filter(RiskCase.risk_band == "medium").limit(20):
            rc.risk_score = 75.0
            rc.risk_band = "high"
            rc.severity = "high"
            db.add(RiskScoreHistory(
                case_id=rc.id,
                previous_score=50.0,
                new_score=75.0,
                new_band="high",
                change_reason="Additional risk factors detected",
                factors_summary="CROSS_INSTITUTION_CONFLICT,UNRESOLVED_VERIFICATION,INTAKE_EXCEEDED",
            ))
        for rc in db.query(RiskCase).filter(RiskCase.risk_band == "medium").limit(10):
            rc.risk_score = 85.0
            rc.risk_band = "critical"
            rc.severity = "critical"
            db.add(RiskScoreHistory(
                case_id=rc.id,
                previous_score=50.0,
                new_score=85.0,
                new_band="critical",
                change_reason="Multiple critical factors detected",
                factors_summary="CROSS_INSTITUTION_CONFLICT,INTAKE_EXCEEDED,UNRESOLVED_VERIFICATION,ACADEMIC_FIELD_INCONSISTENCY",
            ))
        db.flush()
        
        # ===== INVESTIGATION CASES =====
        print("Creating 50+ investigation cases...")
        inv_count = 0
        risk_cases = db.query(RiskCase).filter(RiskCase.risk_band.in_(["high", "critical", "medium"])).all()
        for rc in risk_cases[:50]:
            inv = InvestigationCase(
                case_number=f"INV-{inv_count+1:04d}",
                title=f"Investigation: {rc.title}",
                description=f"Investigation linked to risk case {rc.case_number}",
                severity=rc.risk_band,
                status=random.choice(["open", "assigned", "under_review", "awaiting_institution_response", "resolved", "closed"]),
                assigned_analyst_id=users["fraud.analyst@vidyaverify.ai"].id if random.random() > 0.5 else None,
                linked_risk_case_id=rc.id,
                linked_institution_id=rc.institution_id,
            )
            db.add(inv)
            db.flush()
            
            # Add some evidence
            db.add(CaseEvidence(
                case_id=inv.id,
                evidence_type="risk_factor",
                description=f"Risk score: {rc.risk_score} ({rc.risk_band})",
                ref_id=rc.id,
                ref_type="risk_case",
                added_by=users["fraud.analyst@vidyaverify.ai"].id,
            ))
            
            # Add an action
            db.add(CaseAction(
                case_id=inv.id,
                actor_id=users["fraud.analyst@vidyaverify.ai"].id if inv.assigned_analyst_id else users["aicte.admin@vidyaverify.ai"].id,
                action_type="create",
                new_status="open",
                note="Case created from risk assessment",
            ))
            inv_count += 1
        
        print(f"Created {inv_count} investigation cases")
        
        # ===== VERIFICATION REQUESTS =====
        print("Creating 100+ verification requests...")
        ver_count = 0
        random_students = random.sample(all_students, min(100, len(all_students)))
        for student in random_students:
            req = VerificationRequest(
                request_reference=f"VR-{ver_count+1:05d}",
                student_record_id=student.id,
                institution_id=student.institution_id,
                requested_by=users["inst.admin@vidyaverify.ai"].id,
                provider_name="DEMO_SIMULATOR",
                status=random.choice(["matched", "not_found", "manual_review", "provider_unavailable"]),
                result_summary="Simulated verification result (DEMO_SIMULATOR)",
                response_data='{"provider": "DEMO_SIMULATOR", "note": "Simulated result"}',
                completed_at=datetime.now(timezone.utc),
            )
            db.add(req)
            db.flush()
            
            db.add(VerificationEvent(
                request_id=req.id,
                event_type="completed",
                provider_name="DEMO_SIMULATOR",
                outcome=req.status,
            ))
            ver_count += 1
        
        print(f"Created {ver_count} verification requests")
        
        # ===== CLARIFICATION REQUESTS =====
        print("Creating clarification requests...")
        clar_count = 0
        for inv in db.query(InvestigationCase).filter(InvestigationCase.status == "awaiting_institution_response").all()[:10]:
            req = ClarificationRequest(
                request_reference=f"CR-{clar_count+1:04d}",
                institution_id=inv.linked_institution_id,
                case_id=inv.id,
                requested_by=users["aicte.admin@vidyaverify.ai"].id,
                subject=f"Clarification needed for case {inv.case_number}",
                message="Please provide additional documentation for the flagged records.",
                status="open",
            )
            db.add(req)
            clar_count += 1
        
        print(f"Created {clar_count} clarification requests")
        
        # ===== NOTIFICATIONS =====
        print("Creating notifications...")
        notif_count = 0
        for user in users.values():
            for _ in range(5):
                db.add(Notification(
                    user_id=user.id,
                    title=random.choice([
                        "New validation issue detected",
                        "Risk case assigned",
                        "Clarification request received",
                        "Submission batch processed",
                        "Verification completed",
                    ]),
                    message=f"Demo notification #{notif_count+1}",
                    notification_type=random.choice(["validation_issue", "risk_change", "case_assigned", "clarification_received"]),
                    is_read=random.choice([True, False]),
                ))
                notif_count += 1
        print(f"Created {notif_count} notifications")
        
        # ===== AUDIT LOGS =====
        print("Creating initial audit logs...")
        for action in ["login", "create_user", "seed_data"]:
            db.add(AuditLog(
                actor_id=users["super.admin@vidyaverify.ai"].id,
                actor_role="SUPER_ADMIN",
                action=action,
                entity_type="system",
                outcome="success",
                reason="Initial seed" if action == "seed_data" else None,
                created_at=datetime.now(timezone.utc),
            ))
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("SYNTHETIC DATA SEEDING COMPLETE")
        print("=" * 60)
        print(f"Roles: {db.query(Role).count()}")
        print(f"Users: {db.query(User).count()}")
        print(f"Institutions: {db.query(Institution).count()}")
        print(f"Courses: {db.query(Course).count()}")
        print(f"Academic Years: {db.query(AcademicYear).count()}")
        print(f"Approvals: {db.query(InstitutionApproval).count()}")
        print(f"Intake Approvals: {db.query(IntakeApproval).count()}")
        print(f"Student Records: {db.query(StudentRecord).count()}")
        print(f"Enrolments: {db.query(Enrolment).count()}")
        print(f"Submission Batches: {db.query(SubmissionBatch).count()}")
        print(f"Validation Issues: {db.query(ValidationIssue).count()}")
        print(f"Duplicate Candidates: {db.query(DuplicateCandidate).count()}")
        print(f"Risk Cases: {db.query(RiskCase).count()}")
        print(f"Investigation Cases: {db.query(InvestigationCase).count()}")
        print(f"Verification Requests: {db.query(VerificationRequest).count()}")
        print(f"Clarifications: {db.query(ClarificationRequest).count()}")
        print(f"Notifications: {db.query(Notification).count()}")
        print("=" * 60)
        print("\nDemo credentials (LOCAL DEMO ONLY):")
        print("  super.admin@vidyaverify.ai / Demo@2026")
        print("  aicte.admin@vidyaverify.ai / Demo@2026")
        print("  inst.admin@vidyaverify.ai / Demo@2026")
        print("  fraud.analyst@vidyaverify.ai / Demo@2026")
        print("  auditor@vidyaverify.ai / Demo@2026")
        print("\nAll data is SYNTHETIC. No real records are stored.")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
