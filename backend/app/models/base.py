"""Shared base mixins for all models."""

from datetime import datetime
from sqlalchemy import DateTime, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TimestampMixin:
    """Adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Adds is_deleted flag for soft deletion."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
