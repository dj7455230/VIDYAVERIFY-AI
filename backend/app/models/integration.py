"""IntegrationEvent model — records external integration interactions."""

import uuid
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class IntegrationEvent(Base, TimestampMixin):
    """Record of integration interactions (simulated in demo)."""
    __tablename__ = "integration_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    request_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    request_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # masked
    response_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # masked
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
