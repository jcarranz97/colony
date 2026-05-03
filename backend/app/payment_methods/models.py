from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

from .constants import CurrencyCode, PaymentMethodType


class PaymentMethod(BaseModel):
    """Payment method belonging to a household."""

    __tablename__ = "payment_methods"

    household_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    method_type: Mapped[PaymentMethodType] = mapped_column(
        ENUM(PaymentMethodType), nullable=False
    )
    default_currency: Mapped[CurrencyCode] = mapped_column(
        ENUM(CurrencyCode), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    household = relationship("Household")
    recurrent_expenses = relationship(
        "RecurrentExpense", back_populates="payment_method"
    )
    recurrent_incomes = relationship("RecurrentIncome", back_populates="payment_method")
    cycle_expenses = relationship("CycleExpense", back_populates="payment_method")

    def __repr__(self) -> str:
        """String representation of PaymentMethod."""
        return (
            f"<PaymentMethod(id={self.id}, name='{self.name}', "
            f"type='{self.method_type}')>"
        )
