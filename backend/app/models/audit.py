"""AuditLog model — append-only application-level audit events."""

import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base


class AuditLog(Base):
    """Append-only audit log. No updates or deletes allowed."""
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entity_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    outcome: Mapped[str] = mapped_column(String(30), default="success", nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    case_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    request_correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Explicitly no updated_at or is_deleted — append only
