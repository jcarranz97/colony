from enum import Enum


class ErrorCode(str, Enum):
    """Cycles domain error codes."""

    CYCLE_NOT_FOUND = "CYCLE_NOT_FOUND"
    CYCLE_NAME_EXISTS = "CYCLE_NAME_EXISTS"
    CYCLE_EXPENSE_NOT_FOUND = "CYCLE_EXPENSE_NOT_FOUND"
    CYCLE_GENERATION_ERROR = "CYCLE_GENERATION_ERROR"
    PAYMENT_METHOD_NOT_FOUND = "PAYMENT_METHOD_NOT_FOUND"
    INVALID_CYCLE_DATES = "INVALID_CYCLE_DATES"
    EXCHANGE_RATE_NOT_FOUND = "EXCHANGE_RATE_NOT_FOUND"


class CycleStatus(str, Enum):
    """Lifecycle states for expense cycles."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class CurrencyCode(str, Enum):
    """Supported currency codes (local copy — avoids cross-domain peer import)."""

    USD = "USD"
    MXN = "MXN"


class ExpenseCategory(str, Enum):
    """Expense category types."""

    FIXED = "fixed"
    VARIABLE = "variable"


class ExpenseStatus(str, Enum):
    """Lifecycle states for individual cycle expenses."""

    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
