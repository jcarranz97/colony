import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel

from .constants import CurrencyCode, ExpenseCategory, RecurrenceType


class ExpenseTemplate(BaseModel):
    """Expense template model representing a recurring expense definition."""

    __tablename__ = "expense_templates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    payment_method_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_methods.id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # Reuse existing currency_code PostgreSQL enum type (created by users migration)
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
    recurrence_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    autopay_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="expense_templates")
    # lazy="joined" avoids N+1 queries when serializing nested PaymentMethodSummary
    payment_method = relationship(
        "PaymentMethod",
        back_populates="expense_templates",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint("base_amount > 0", name="check_base_amount_positive"),
    )

    def __repr__(self) -> str:
        """String representation of ExpenseTemplate."""
        return (
            f"<ExpenseTemplate(id={self.id}, description='{self.description}')>"
        )
