"""SubmissionBatch and SubmissionFileMetadata models."""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base
from app.models.base import TimestampMixin


class SubmissionBatch(Base, TimestampMixin):
    """A versioned submission batch from an institution."""
    __tablename__ = "submission_batches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    # draft, uploaded, validated, issues_found, corrected, resubmitted, accepted, rejected
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_batch_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("submission_batches.id", ondelete="SET NULL"), nullable=True)

    files: Mapped[list["SubmissionFileMetadata"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class SubmissionFileMetadata(Base, TimestampMixin):
    """Metadata for an uploaded file in a submission batch."""
    __tablename__ = "submission_file_metadata"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("submission_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # csv, xlsx
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)  # relative path, outside public dir
    column_mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    batch: Mapped["SubmissionBatch"] = relationship(back_populates="files")
