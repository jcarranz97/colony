from enum import Enum


class ErrorCode(str, Enum):
    """Payment methods error codes."""

    PAYMENT_METHOD_NOT_FOUND = "PAYMENT_METHOD_NOT_FOUND"
    PAYMENT_METHOD_NAME_EXISTS = "PAYMENT_METHOD_NAME_EXISTS"
    PAYMENT_METHOD_IN_USE = "PAYMENT_METHOD_IN_USE"
    INVALID_PAYMENT_METHOD_TYPE = "INVALID_PAYMENT_METHOD_TYPE"
    INVALID_CURRENCY = "INVALID_CURRENCY"


class PaymentMethodType(str, Enum):
    """Payment method types."""

    DEBIT = "debit"
    CREDIT = "credit"
    CASH = "cash"
    TRANSFER = "transfer"


class CurrencyCode(str, Enum):
    """Supported currency codes."""

    USD = "USD"
    MXN = "MXN"


# Business constants
MAX_PAYMENT_METHODS_PER_USER = 20
MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
