from enum import Enum


class ErrorCode(str, Enum):
    """Expense templates error codes."""

    EXPENSE_TEMPLATE_NOT_FOUND = "EXPENSE_TEMPLATE_NOT_FOUND"
    PAYMENT_METHOD_NOT_FOUND = "PAYMENT_METHOD_NOT_FOUND"
    INVALID_RECURRENCE_CONFIG = "INVALID_RECURRENCE_CONFIG"


class CurrencyCode(str, Enum):
    """Supported currency codes (local copy — avoids cross-domain peer import)."""

    USD = "USD"
    MXN = "MXN"


class ExpenseCategory(str, Enum):
    """Expense category types."""

    FIXED = "fixed"
    VARIABLE = "variable"


class RecurrenceType(str, Enum):
    """Recurrence pattern types."""

    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
