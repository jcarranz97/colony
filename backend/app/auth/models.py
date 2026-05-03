import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel


class User(BaseModel):
    """User model representing application users."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_currency: Mapped[str] = mapped_column(
        ENUM("USD", "MXN", name="currency_code"), default="USD"
    )
    locale: Mapped[str] = mapped_column(String(10), default="en-US")
    role: Mapped[str] = mapped_column(
        ENUM("admin", "user", name="user_role"), nullable=False, default="user"
    )
    active_household_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("households.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Which household the user is currently operating in
    active_household = relationship(
        "Household",
        foreign_keys=[active_household_id],
    )
    # All household memberships (many-to-many join records)
    household_memberships = relationship(
        "UserHouseholdMembership", back_populates="user"
    )

    def __repr__(self) -> str:
        """String representation of the User model."""
        return f"<User(username='{self.username}')>"
