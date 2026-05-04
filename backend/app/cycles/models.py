import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import BaseModel

from .constants import CurrencyCode, CycleStatus, ExpenseCategory, ExpenseStatus


class ExchangeRate(Base):
    """Exchange rate for currency conversion between two currencies on a given date."""

    __tablename__ = "exchange_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    from_currency: Mapped[str] = mapped_column(
        ENUM(CurrencyCode, name="currency_code", create_type=False),
        nullable=False,
    )
    to_currency: Mapped[str] = mapped_column(
        ENUM(CurrencyCode, name="currency_code", create_type=False),
        nullable=False,
    )
    rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint("rate > 0", name="check_exchange_rate_positive"),
        UniqueConstraint(
            "from_currency",
            "to_currency",
            "rate_date",
            name="unique_currency_date",
        ),
    )

    def __repr__(self) -> str:
        """String representation of ExchangeRate."""
        return (
            f"<ExchangeRate({self.from_currency}->{self.to_currency} "
            f"rate={self.rate} date={self.rate_date})>"
        )


class Cycle(BaseModel):
    """Expense management cycle belonging to a household."""

    __tablename__ = "cycles"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    remaining_balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    status: Mapped[CycleStatus] = mapped_column(
        ENUM(CycleStatus, name="cycle_status"),
        nullable=False,
        default=CycleStatus.DRAFT,
    )

    # Relationships
    household = relationship("Household")
    expenses = relationship(
        "CycleExpense",
        back_populates="cycle",
        cascade="all, delete-orphan",
    )
    incomes = relationship(
        "CycleIncome",
        back_populates="cycle",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="valid_cycle_dates"),
        UniqueConstraint("household_id", "name", name="unique_household_cycle_name"),
    )

    @property
    def summary(self) -> dict:
        """Compute a financial summary from the cycle's active expenses."""
        _excluded = {
            ExpenseStatus.CANCELLED,
            ExpenseStatus.PAID_OTHER,
            ExpenseStatus.SKIPPED,
        }
        active = [e for e in self.expenses if e.active]
        countable = [e for e in active if e.status not in _excluded]
        total = sum((e.amount_usd for e in countable), Decimal("0"))
        fixed = sum(
            (e.amount_usd for e in countable if e.category == ExpenseCategory.FIXED),
            Decimal("0"),
        )
        variable = sum(
            (e.amount_usd for e in countable if e.category == ExpenseCategory.VARIABLE),
            Decimal("0"),
        )
        extra = sum(
            (e.amount_usd for e in countable if e.category == ExpenseCategory.EXTRA),
            Decimal("0"),
        )
        expense_count = len(countable)
        paid_count = sum(1 for e in countable if e.paid)
        pending_count = expense_count - paid_count
        return {
            "total_expenses": total,
            "fixed_expenses": fixed,
            "variable_expenses": variable,
            "extra_expenses": extra,
            "expense_count": expense_count,
            "paid_count": paid_count,
            "pending_count": pending_count,
        }

    def __repr__(self) -> str:
        """String representation of Cycle."""
        return f"<Cycle(id={self.id}, name='{self.name}', status='{self.status}')>"


class CycleExpense(BaseModel):
    """Individual expense entry within a cycle."""

    __tablename__ = "cycle_expenses"

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recurrent_expenses.id"),
        nullable=True,
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
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(
        ENUM(ExpenseCategory, name="expense_category", create_type=False),
        nullable=False,
    )
    autopay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[ExpenseStatus] = mapped_column(
        ENUM(ExpenseStatus, name="expense_status"),
        nullable=False,
        default=ExpenseStatus.PENDING,
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    cycle = relationship("Cycle", back_populates="expenses")
    template = relationship("RecurrentExpense", foreign_keys=[template_id])
    payment_method = relationship(
        "PaymentMethod",
        foreign_keys=[payment_method_id],
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_expense_amount_positive"),
        CheckConstraint(
            "amount_usd >= 0", name="check_expense_amount_usd_positive"
        ),
    )

    def __repr__(self) -> str:
        """String representation of CycleExpense."""
        return (
            f"<CycleExpense(id={self.id}, description='{self.description}', "
            f"amount={self.amount} {self.currency})>"
        )


class CycleIncome(BaseModel):
    """Individual income entry within a cycle (auto-generated or manual)."""

    __tablename__ = "cycle_incomes"

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recurrent_incomes.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_method_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_methods.id"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[CurrencyCode] = mapped_column(
        ENUM(CurrencyCode, name="currency_code", create_type=False),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    income_date: Mapped[date] = mapped_column(Date, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    cycle = relationship("Cycle", back_populates="incomes")
    template = relationship("RecurrentIncome", foreign_keys=[template_id])
    payment_method = relationship(
        "PaymentMethod",
        foreign_keys=[payment_method_id],
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_income_amount_positive"),
        CheckConstraint("amount_usd > 0", name="check_income_amount_usd_positive"),
    )

    def __repr__(self) -> str:
        """String representation of CycleIncome."""
        return (
            f"<CycleIncome(id={self.id}, description='{self.description}', "
            f"amount={self.amount} {self.currency})>"
        )
