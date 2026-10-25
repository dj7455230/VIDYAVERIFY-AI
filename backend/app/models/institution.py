"""Institution and InstitutionUserMembership models."""

import uuid
from sqlalchemy import String, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin


class Institution(Base, TimestampMixin):
    __tablename__ = "institutions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    institution_type: Mapped[str] = mapped_column(String(50), nullable=False)  # university, college, institute
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    memberships: Mapped[list["InstitutionUserMembership"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    approvals: Mapped[list["InstitutionApproval"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Institution {self.code} {self.name}>"


class InstitutionUserMembership(Base, TimestampMixin):
    """Maps users to institutions they can access (for institution-scoped roles)."""
    __tablename__ = "institution_user_memberships"
    __table_args__ = (UniqueConstraint("user_id", "institution_id", name="uq_user_institution"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)

    institution: Mapped["Institution"] = relationship(back_populates="memberships")
