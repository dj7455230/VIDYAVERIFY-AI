"""SQLAlchemy models package — imports all models for Alembic detection."""

from app.models.user import User, Role, user_roles
from app.models.institution import Institution, InstitutionUserMembership
from app.models.academic import AcademicYear, Course, InstitutionApproval, IntakeApproval
from app.models.student import StudentRecord, Enrolment
from app.models.submission import SubmissionBatch, SubmissionFileMetadata
from app.models.validation import ValidationIssue
from app.models.duplicate import DuplicateCandidate
from app.models.risk import RiskCase, RiskFactor, RiskScoreHistory
from app.models.investigation import CaseEvidence, CaseAction, InvestigationCase
from app.models.verification import StudentIdentityCheck, VerificationRequest, VerificationEvent
from app.models.clarification import ClarificationRequest
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.models.integration import IntegrationEvent
from app.models.config import ConfigurationSetting

__all__ = [
    "User", "Role", "user_roles",
    "Institution", "InstitutionUserMembership",
    "AcademicYear", "Course", "InstitutionApproval", "IntakeApproval",
    "StudentRecord", "Enrolment",
    "SubmissionBatch", "SubmissionFileMetadata",
    "ValidationIssue",
    "DuplicateCandidate",
    "RiskCase", "RiskFactor", "RiskScoreHistory",
    "CaseEvidence", "CaseAction", "InvestigationCase",
    "StudentIdentityCheck", "VerificationRequest", "VerificationEvent",
    "ClarificationRequest",
    "AuditLog", "Notification", "IntegrationEvent", "ConfigurationSetting",
]
