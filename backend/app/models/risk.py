"""RiskCase, RiskFactor, RiskScoreHistory models."""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class RiskCase(Base, TimestampMixin):
    """A risk case aggregating risk factors for a student or institution."""
    __tablename__ = "risk_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)  # student, institution
    entity_ref: Mapped[str] = mapped_column(String(36), nullable=False)  # student_record_id or institution_id
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100
    risk_band: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    # low (0-30), medium (31-60), high (61-80), critical (81-100)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    # open, assigned, under_review, awaiting_response, resolved, closed
    severity: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    assigned_analyst_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    institution_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    risk_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    override_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overridden_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    overridden_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    factors: Mapped[list["RiskFactor"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    score_history: Mapped[list["RiskScoreHistory"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class RiskFactor(Base, TimestampMixin):
    """A contributing factor to a risk score."""
    __tablename__ = "risk_factors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON refs
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    case: Mapped["RiskCase"] = relationship(back_populates="factors")


class RiskScoreHistory(Base, TimestampMixin):
    """History of risk score changes."""
    __tablename__ = "risk_score_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_score: Mapped[float] = mapped_column(Float, nullable=False)
    new_band: Mapped[str] = mapped_column(String(20), nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    factors_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    case: Mapped["RiskCase"] = relationship(back_populates="score_history")
