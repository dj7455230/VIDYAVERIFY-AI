"""Notification model."""

import uuid
from sqlalchemy import String, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class Notification(Base, TimestampMixin):
    """In-app notification for users."""
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # validation_issue, duplicate_detected, risk_change, case_assigned, clarification_received, audit
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ref_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ref_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
