from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ENUM

from app.models import BaseModel


class User(BaseModel):
    """User model representing application users."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    preferred_currency = Column(ENUM("USD", "MXN", name="currency_code"), default="USD")
    locale = Column(String(10), default="en-US")

    # Relationships will be added when other domains are implemented
    # payment_methods = relationship("PaymentMethod", back_populates="user")
    # expense_templates = relationship("ExpenseTemplate", back_populates="user")
    # cycles = relationship("Cycle", back_populates="user")

    def __repr__(self) -> str:
        """String representation of the User model."""
        return (
            f"<User(email='{self.email}', name='{self.first_name} {self.last_name}')>"
        )
