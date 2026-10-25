"""InvestigationCase, CaseEvidence, CaseAction models."""

import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class InvestigationCase(Base, TimestampMixin):
    """An investigation case for fraud analysts."""
    __tablename__ = "investigation_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    # open, assigned, under_review, awaiting_institution_response, resolved, closed
    assigned_analyst_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    linked_risk_case_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("risk_cases.id", ondelete="SET NULL"), nullable=True)
    linked_institution_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_student_record_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    evidence: Mapped[list["CaseEvidence"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    actions: Mapped[list["CaseAction"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class CaseEvidence(Base, TimestampMixin):
    """An evidence item linked to an investigation case."""
    __tablename__ = "case_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # validation_issue, duplicate_candidate, risk_factor, submission_record, verification_result, document
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ref_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # reference to source entity
    ref_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    added_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    case: Mapped["InvestigationCase"] = relationship(back_populates="evidence")


class CaseAction(Base, TimestampMixin):
    """An action taken on an investigation case (audit trail)."""
    __tablename__ = "case_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # assign, reassign, add_evidence, add_note, request_clarification, institution_response, resolve, reopen
    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["InvestigationCase"] = relationship(back_populates="actions")
