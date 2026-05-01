import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from app.payment_methods.schemas import PaymentMethodSummary
from app.schemas import AppBaseModel

from .constants import CurrencyCode, CycleStatus, ExpenseCategory, ExpenseStatus

# ---------------------------------------------------------------------------
# Shared / nested schemas
# ---------------------------------------------------------------------------

_MAX_PER_PAGE = 100
_DEFAULT_PER_PAGE = 20


class CycleSummary(BaseModel):
    """Aggregated financial summary computed from a cycle's expenses."""

    total_expenses: Decimal
    fixed_expenses: Decimal
    variable_expenses: Decimal
    expense_count: int
    paid_count: int
    pending_count: int

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: str},
    }


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    page: int
    per_page: int
    total: int
    pages: int


# ---------------------------------------------------------------------------
# Cycle schemas
# ---------------------------------------------------------------------------


class CycleCreate(AppBaseModel):
    """Schema for creating a new expense cycle."""

    name: str = Field(..., min_length=1, max_length=100, description="Cycle name")
    start_date: date = Field(..., description="Cycle start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Cycle end date (YYYY-MM-DD)")
    income_amount: Decimal = Field(
        ..., gt=0, decimal_places=2, description="Expected income for this cycle"
    )
    generate_from_templates: bool = Field(
        False,
        description="When true, automatically generate expenses from active templates",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from name.

        Args:
            v: Raw name value.

        Returns:
            Stripped name.

        Raises:
            ValueError: If name is empty after stripping.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("name cannot be empty or whitespace")
        return stripped

    @model_validator(mode="after")
    def validate_dates(self) -> "CycleCreate":
        """Ensure end_date is strictly after start_date.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If end_date is not after start_date.
        """
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class CycleUpdate(AppBaseModel):
    """Schema for partially updating a cycle (all fields optional)."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Cycle name"
    )
    income_amount: Decimal | None = Field(
        None, gt=0, decimal_places=2, description="Expected income for this cycle"
    )
    status: CycleStatus | None = Field(None, description="Cycle lifecycle status")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        """Strip whitespace from name when provided.

        Args:
            v: Raw name value or None.

        Returns:
            Stripped name or None.

        Raises:
            ValueError: If name is empty after stripping.
        """
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("name cannot be empty or whitespace")
            return stripped
        return v


class CycleResponse(BaseModel):
    """Full cycle response including computed summary."""

    id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    income_amount: Decimal
    remaining_balance: Decimal
    status: CycleStatus
    summary: CycleSummary
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: str},
    }


class CyclesListResponse(BaseModel):
    """Paginated list of cycles."""

    cycles: list[CycleResponse]
    pagination: PaginationMeta


# ---------------------------------------------------------------------------
# Cycle expense schemas
# ---------------------------------------------------------------------------


class CycleExpenseCreate(AppBaseModel):
    """Schema for manually adding an expense to a cycle."""

    description: str = Field(..., min_length=1, max_length=255)
    currency: CurrencyCode
    payment_method_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    due_date: date
    category: ExpenseCategory
    comments: str | None = Field(None, max_length=1000)
    autopay_info: str | None = None

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        """Strip whitespace from description.

        Args:
            v: Raw description value.

        Returns:
            Stripped description.

        Raises:
            ValueError: If description is empty after stripping.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("description cannot be empty or whitespace")
        return stripped


class CycleExpenseUpdate(AppBaseModel):
    """Schema for partially updating a cycle expense (all fields optional)."""

    description: str | None = Field(None, min_length=1, max_length=255)
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    due_date: date | None = None
    status: ExpenseStatus | None = None
    paid: bool | None = None
    paid_at: datetime | None = None
    comments: str | None = Field(None, max_length=1000)
    autopay_info: str | None = None

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        """Strip whitespace from description when provided.

        Args:
            v: Raw description value or None.

        Returns:
            Stripped description or None.

        Raises:
            ValueError: If description is empty after stripping.
        """
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("description cannot be empty or whitespace")
            return stripped
        return v


class CycleExpenseResponse(BaseModel):
    """Full cycle expense response with nested payment method info."""

    id: uuid.UUID
    description: str
    currency: CurrencyCode
    amount: Decimal
    amount_usd: Decimal
    due_date: date
    category: ExpenseCategory
    status: ExpenseStatus
    paid: bool
    paid_at: datetime | None
    comments: str | None
    autopay_info: str | None
    template_id: uuid.UUID | None
    payment_method: PaymentMethodSummary
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def compute_overdue(self) -> "CycleExpenseResponse":
        """Reclassify pending expenses with a past due date as overdue."""
        today = datetime.now(UTC).date()
        if self.status == ExpenseStatus.PENDING and self.due_date < today:
            self.status = ExpenseStatus.OVERDUE
        return self

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: str},
    }


class ExpensesSummary(BaseModel):
    """Aggregated financial summary for a filtered list of expenses."""

    total_amount_usd: Decimal
    fixed_amount: Decimal
    variable_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    total_count: int

    model_config = {"json_encoders": {Decimal: str}}


class CycleExpensesListResponse(BaseModel):
    """Expenses list response with per-query aggregated summary."""

    expenses: list[CycleExpenseResponse]
    summary: ExpensesSummary


# ---------------------------------------------------------------------------
# Cycle summary schemas
# ---------------------------------------------------------------------------


class CycleInfo(BaseModel):
    """Basic cycle info embedded in the summary response."""

    id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    income_amount: Decimal

    model_config = {
        "from_attributes": True,
        "json_encoders": {Decimal: str},
    }


class FinancialSummary(BaseModel):
    """Financial breakdown for the cycle summary."""

    total_expenses_usd: Decimal
    fixed_expenses_usd: Decimal
    variable_expenses_usd: Decimal
    usa_expenses_usd: Decimal
    mexico_expenses_usd: Decimal
    net_balance: Decimal

    model_config = {"json_encoders": {Decimal: str}}


class PaymentMethodBreakdown(BaseModel):
    """Per-payment-method expense breakdown."""

    payment_method: PaymentMethodSummary
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    expense_count: int

    model_config = {"json_encoders": {Decimal: str}}


class CurrencyStats(BaseModel):
    """Expense stats for a single currency."""

    total_amount: Decimal
    total_amount_usd: Decimal | None = None
    expense_count: int

    model_config = {"json_encoders": {Decimal: str}}


class StatusBreakdown(BaseModel):
    """Count of expenses by status."""

    pending: int
    paid: int
    overdue: int
    cancelled: int


class CycleSummaryResponse(BaseModel):
    """Full cycle summary response."""

    cycle: CycleInfo
    financial: FinancialSummary
    by_payment_method: list[PaymentMethodBreakdown]
    by_currency: dict[str, CurrencyStats]
    status_breakdown: StatusBreakdown

    model_config = {"json_encoders": {Decimal: str}}


# ---------------------------------------------------------------------------
# Query parameter types
# ---------------------------------------------------------------------------

PageQuery = Annotated[int, Field(ge=1, default=1)]
PerPageQuery = Annotated[int, Field(ge=1, le=_MAX_PER_PAGE, default=_DEFAULT_PER_PAGE)]
