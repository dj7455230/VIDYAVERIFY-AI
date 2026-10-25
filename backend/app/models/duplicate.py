"""DuplicateCandidate model."""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class DuplicateCandidate(Base, TimestampMixin):
    """A candidate pair of potentially duplicate student records."""
    __tablename__ = "duplicate_candidates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_record_id_1: Mapped[str] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="CASCADE"), nullable=False, index=True)
    student_record_id_2: Mapped[str] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="CASCADE"), nullable=False, index=True)
    match_layer: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=exact, 2=combination, 3=fuzzy, 4=anomaly
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100
    match_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    match_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON of evidence fields
    reviewer_decision: Mapped[str] = mapped_column(String(30), default="unresolved", nullable=False)
    # unresolved, confirmed_duplicate, not_duplicate, needs_review
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_cross_institution: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linked_case_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("risk_cases.id", ondelete="SET NULL"), nullable=True)
