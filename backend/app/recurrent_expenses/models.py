import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

from .constants import CurrencyCode, ExpenseCategory, RecurrenceType


class RecurrentExpense(BaseModel):
    """Recurrent expense template belonging to a household."""

    __tablename__ = "recurrent_expenses"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_method_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_methods.id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[CurrencyCode] = mapped_column(
        ENUM(CurrencyCode, name="currency_code", create_type=False),
        nullable=False,
    )
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(
        ENUM(ExpenseCategory, name="expense_category"),
        nullable=False,
    )
    recurrence_type: Mapped[RecurrenceType] = mapped_column(
        ENUM(RecurrenceType, name="recurrence_type"),
        nullable=False,
    )
    recurrence_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    autopay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    household = relationship("Household")
    payment_method = relationship(
        "PaymentMethod",
        back_populates="recurrent_expenses",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint("base_amount > 0", name="check_base_amount_positive"),
    )

    def __repr__(self) -> str:
        """String representation of RecurrentExpense."""
        return f"<RecurrentExpense(id={self.id}, description='{self.description}')>"
