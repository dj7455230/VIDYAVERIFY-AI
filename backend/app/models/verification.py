"""StudentIdentityCheck, VerificationRequest, VerificationEvent models."""

import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class StudentIdentityCheck(Base, TimestampMixin):
    """Identity verification check for a student record (simulated)."""
    __tablename__ = "student_identity_checks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_record_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="DEMO_SIMULATOR", nullable=False)
    request_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    # pending, matched, not_found, manual_review, provider_unavailable, error
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON (simulated)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class VerificationRequest(Base, TimestampMixin):
    """A verification request record."""
    __tablename__ = "verification_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    student_record_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="DEMO_SIMULATOR", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    # pending, in_progress, matched, not_found, manual_review, provider_unavailable, cancelled, error
    request_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    response_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON (simulated)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    events: Mapped[list["VerificationEvent"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class VerificationEvent(Base, TimestampMixin):
    """Event log for a verification request."""
    __tablename__ = "verification_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("verification_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # created, sent, received, completed, failed, cancelled, retried
    provider_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    outcome: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    request: Mapped["VerificationRequest"] = relationship(back_populates="events")
