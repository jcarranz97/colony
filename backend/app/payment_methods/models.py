from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import relationship

from app.models import BaseModel

from .constants import CurrencyCode, PaymentMethodType


class PaymentMethod(BaseModel):
    """Payment method model for users."""

    __tablename__ = "payment_methods"

    # Core fields
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    method_type = Column(ENUM(PaymentMethodType), nullable=False)
    default_currency = Column(ENUM(CurrencyCode), nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payment_methods")
    # The following relationships will be added when other domains are implemented
    # expense_templates = relationship(
    #    "ExpenseTemplate", back_populates="payment_method")
    # cycle_expenses = relationship("CycleExpense", back_populates="payment_method")

    # Table constraints
    __table_args__ = (
        # Unique constraint for user + name combination
        {"schema": None},  # Default schema
    )

    def __repr__(self) -> str:
        """String representation of the PaymentMethod model."""
        return (
            f"<PaymentMethod(id={self.id}, name='{self.name}', "
            f"type='{self.method_type}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "method_type": self.method_type.value,
            "default_currency": self.default_currency.value,
            "description": self.description,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
