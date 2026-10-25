"""StudentRecord and Enrolment models."""

import uuid
from datetime import date
from sqlalchemy import String, Integer, ForeignKey, Boolean, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class StudentRecord(Base, TimestampMixin):
    """A student academic record (fictional / synthetic in demo mode)."""
    __tablename__ = "student_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Masked/pseudonymous APAAR reference (fictional)
    apaar_reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Do NOT store Aadhaar or real sensitive identifiers
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_status: Mapped[str] = mapped_column(String(30), nullable=False)  # admitted, enrolled, graduated, dropped
    enrolment_status: Mapped[str] = mapped_column(String(30), nullable=False)  # active, inactive, pending
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified", nullable=False)  # unverified, pending, verified, failed
    source_submission_batch_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("submission_batches.id", ondelete="SET NULL"), nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    enrolments: Mapped[list["Enrolment"]] = relationship(back_populates="student_record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_student_inst_ay", "institution_id", "academic_year_id"),
        Index("ix_student_inst_course_ay", "institution_id", "course_id", "academic_year_id"),
    )


class Enrolment(Base, TimestampMixin):
    """A specific enrolment record for a student in a course for an academic year."""
    __tablename__ = "enrolments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_record_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_records.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolment_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student_record: Mapped["StudentRecord"] = relationship(back_populates="enrolments")

    __table_args__ = (
        Index("ix_enrol_inst_course_ay", "institution_id", "course_id", "academic_year_id"),
    )
