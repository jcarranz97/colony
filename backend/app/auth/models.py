from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class User(BaseModel):
    """User model representing application users."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    preferred_currency: Mapped[str] = mapped_column(
        ENUM("USD", "MXN", name="currency_code"), default="USD"
    )
    locale: Mapped[str] = mapped_column(String(10), default="en-US")

    # Relationships will be added when other domains are implemented
    # payment_methods = relationship("PaymentMethod", back_populates="user")
    # expense_templates = relationship("ExpenseTemplate", back_populates="user")
    # cycles = relationship("Cycle", back_populates="user")

    def __repr__(self) -> str:
        """String representation of the User model."""
        return (
            f"<User(email='{self.email}', name='{self.first_name} {self.last_name}')>"
        )
