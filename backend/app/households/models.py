import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import BaseModel

if TYPE_CHECKING:
    from app.auth.models import User


class Household(BaseModel):
    """Group of users that share financial data."""

    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    memberships: Mapped[list["UserHouseholdMembership"]] = relationship(
        "UserHouseholdMembership", back_populates="household"
    )

    def __repr__(self) -> str:
        """String representation of Household."""
        return f"<Household(name='{self.name}')>"


class UserHouseholdMembership(Base):
    """Join table: many-to-many link between users and households."""

    __tablename__ = "user_household_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="household_memberships")
    household: Mapped[Household] = relationship(
        "Household", back_populates="memberships"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "household_id", name="unique_user_household"),
    )

    def __repr__(self) -> str:
        """String representation of UserHouseholdMembership."""
        return (
            f"<UserHouseholdMembership("
            f"user_id={self.user_id}, household_id={self.household_id})>"
        )
