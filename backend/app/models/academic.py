"""AcademicYear, Course, InstitutionApproval, IntakeApproval models."""

import uuid
from sqlalchemy import String, Integer, ForeignKey, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import date
from app.database import Base
from app.models.base import TimestampMixin


class AcademicYear(Base, TimestampMixin):
    __tablename__ = "academic_years"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    year_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g., "2025-2026"
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ug, pg, diploma, certificate
    duration_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Unique constraint on code + name
    __table_args__ = (UniqueConstraint("code", "name", name="uq_course_code_name"),)


class InstitutionApproval(Base, TimestampMixin):
    """Approval record for an institution for a specific academic year."""
    __tablename__ = "institution_approvals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False)  # approved, pending, expired, revoked
    approval_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approval_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institution: Mapped["Institution"] = relationship(back_populates="approvals")
    academic_year: Mapped["AcademicYear"] = relationship()

    __table_args__ = (UniqueConstraint("institution_id", "academic_year_id", name="uq_inst_ay_approval"),)


class IntakeApproval(Base, TimestampMixin):
    """Approved intake for a course at an institution for an academic year."""
    __tablename__ = "intake_approvals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_intake: Mapped[int] = mapped_column(Integer, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "course_id", "academic_year_id", name="uq_inst_course_ay"),
    )
