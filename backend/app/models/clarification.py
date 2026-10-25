"""ClarificationRequest model."""

import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class ClarificationRequest(Base, TimestampMixin):
    """A clarification request sent to an institution."""
    __tablename__ = "clarification_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("investigation_cases.id", ondelete="SET NULL"), nullable=True)
    risk_case_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("risk_cases.id", ondelete="SET NULL"), nullable=True)
    validation_issue_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("validation_issues.id", ondelete="SET NULL"), nullable=True)
    student_record_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="SET NULL"), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    # open, responded, closed, escalated
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
