import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.payment_methods.schemas import PaymentMethodSummary
from app.schemas import AppBaseModel

from .constants import CurrencyCode, ExpenseCategory, RecurrenceType

# Validation constants
_MAX_DAY_OF_WEEK = 6
_MIN_DAY_OF_MONTH = 1
_MAX_DAY_OF_MONTH = 31


# ---------------------------------------------------------------------------
# Recurrence config validators
# ---------------------------------------------------------------------------


def _validate_weekly_config(config: dict[str, Any]) -> None:
    """Validate recurrence config for weekly recurrence.

    Args:
        config: The recurrence configuration dictionary.

    Raises:
        ValueError: If day_of_week is missing or invalid.
    """
    day = config.get("day_of_week")
    if day is None or not isinstance(day, int) or not (0 <= day <= _MAX_DAY_OF_WEEK):
        raise ValueError(
            "weekly recurrence_config requires 'day_of_week' (int 0-6, "
            "0=Sunday, 6=Saturday)"
        )


def _validate_bi_weekly_config(config: dict[str, Any]) -> None:
    """Validate recurrence config for bi-weekly recurrence.

    Args:
        config: The recurrence configuration dictionary.

    Raises:
        ValueError: If interval_days is missing or invalid.
    """
    interval = config.get("interval_days")
    if interval is None or not isinstance(interval, int) or interval <= 0:
        raise ValueError(
            "bi_weekly recurrence_config requires 'interval_days' (positive int)"
        )


def _validate_monthly_config(config: dict[str, Any]) -> None:
    """Validate recurrence config for monthly recurrence.

    Args:
        config: The recurrence configuration dictionary.

    Raises:
        ValueError: If day_of_month is missing/invalid or handle_month_end is not bool.
    """
    dom = config.get("day_of_month")
    if (
        dom is None
        or not isinstance(dom, int)
        or not (_MIN_DAY_OF_MONTH <= dom <= _MAX_DAY_OF_MONTH)
    ):
        raise ValueError("monthly recurrence_config requires 'day_of_month' (int 1-31)")
    handle = config.get("handle_month_end", False)
    if not isinstance(handle, bool):
        raise ValueError("monthly recurrence_config 'handle_month_end' must be a bool")


def _validate_custom_config(config: dict[str, Any]) -> None:
    """Validate recurrence config for custom recurrence.

    Args:
        config: The recurrence configuration dictionary.

    Raises:
        ValueError: If interval, unit, or day_of_month are invalid.
    """
    interval = config.get("interval")
    unit = config.get("unit")
    dom = config.get("day_of_month")

    if not isinstance(interval, int) or interval <= 0:
        raise ValueError("custom recurrence_config requires 'interval' (positive int)")
    valid_units = {"days", "weeks", "months"}
    if unit not in valid_units:
        raise ValueError(
            f"custom recurrence_config 'unit' must be one of {valid_units}"
        )
    if dom is not None and (
        not isinstance(dom, int) or not (_MIN_DAY_OF_MONTH <= dom <= _MAX_DAY_OF_MONTH)
    ):
        raise ValueError("custom recurrence_config 'day_of_month' must be int 1-31")


# Maps each RecurrenceType to its config validator function
_RECURRENCE_VALIDATORS: dict[RecurrenceType, Any] = {
    RecurrenceType.WEEKLY: _validate_weekly_config,
    RecurrenceType.BI_WEEKLY: _validate_bi_weekly_config,
    RecurrenceType.MONTHLY: _validate_monthly_config,
    RecurrenceType.CUSTOM: _validate_custom_config,
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RecurrentExpenseBase(AppBaseModel):
    """Base schema with all required recurrent expense fields."""

    description: str = Field(..., min_length=1, max_length=255)
    currency: CurrencyCode
    payment_method_id: uuid.UUID
    base_amount: Decimal = Field(..., ge=0, decimal_places=2)
    category: ExpenseCategory
    recurrence_type: RecurrenceType
    recurrence_config: dict[str, Any] = Field(default_factory=dict)
    reference_date: date
    autopay: bool = False

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        """Strip whitespace and validate description is non-empty.

        Args:
            v: The description value.

        Returns:
            Stripped description string.

        Raises:
            ValueError: If description is empty after stripping.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("description cannot be empty or whitespace")
        return stripped

    @model_validator(mode="after")
    def validate_recurrence_config(self) -> "RecurrentExpenseBase":
        """Validate recurrence_config shape matches recurrence_type.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If recurrence_config is invalid for the recurrence_type.
        """
        validator = _RECURRENCE_VALIDATORS.get(self.recurrence_type)
        if validator:
            try:
                validator(self.recurrence_config)
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
        return self


class RecurrentExpenseCreate(RecurrentExpenseBase):
    """Schema for creating a new recurrent expense."""


class RecurrentExpenseUpdate(AppBaseModel):
    """Schema for updating a recurrent expense (all fields optional)."""

    description: str | None = Field(default=None, min_length=1, max_length=255)
    currency: CurrencyCode | None = None
    payment_method_id: uuid.UUID | None = None
    base_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    category: ExpenseCategory | None = None
    recurrence_type: RecurrenceType | None = None
    recurrence_config: dict[str, Any] | None = None
    reference_date: date | None = None
    autopay: bool = False
    active: bool | None = None

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str | None) -> str | None:
        """Strip whitespace and validate description when provided.

        Args:
            v: The description value.

        Returns:
            Stripped description string or None.

        Raises:
            ValueError: If description is empty after stripping.
        """
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("description cannot be empty or whitespace")
            return stripped
        return v

    @model_validator(mode="after")
    def validate_recurrence_config(self) -> "RecurrentExpenseUpdate":
        """Validate recurrence_config only when both fields are provided together.

        When only recurrence_config is updated (not recurrence_type), validation
        against the existing DB recurrence_type is deferred to the service layer.

        Returns:
            The validated model instance.

        Raises:
            ValueError: If both recurrence_type and recurrence_config are set
                but config is invalid for that type.
        """
        if self.recurrence_config is not None and self.recurrence_type is not None:
            validator = _RECURRENCE_VALIDATORS.get(self.recurrence_type)
            if validator:
                try:
                    validator(self.recurrence_config)
                except ValueError as exc:
                    raise ValueError(str(exc)) from exc
        return self


class RecurrentExpenseResponse(BaseModel):
    """Response schema for a recurrent expense."""

    id: uuid.UUID
    description: str
    currency: CurrencyCode
    base_amount: Decimal
    category: ExpenseCategory
    recurrence_type: RecurrenceType
    recurrence_config: dict[str, Any]
    reference_date: date
    autopay: bool
    active: bool
    payment_method: PaymentMethodSummary
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        # Serialize Decimal as string to match API spec (e.g. "1200.00")
        "json_encoders": {Decimal: str},
    }
