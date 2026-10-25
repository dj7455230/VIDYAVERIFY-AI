"""ValidationIssue model."""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class ValidationIssue(Base, TimestampMixin):
    """A validation issue detected in a submission row or field."""
    __tablename__ = "validation_issues"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("submission_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    student_record_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="SET NULL"), nullable=True)
    issue_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # info, warning, error, critical
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observed_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)
    # open, under_review, resolved, accepted_justified
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
