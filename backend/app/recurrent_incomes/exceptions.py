from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class RecurrentIncomeExceptionError(AppExceptionError):
    """Base recurrent income exception."""


class RecurrentIncomeNotFoundExceptionError(RecurrentIncomeExceptionError):
    """Raised when a recurrent income is not found or not owned by the user."""

    def __init__(self, recurrent_income_id: str | None = None) -> None:
        """Initialize the exception.

        Args:
            recurrent_income_id: The ID of the recurrent income that was not found.
        """
        details = (
            {"recurrent_income_id": recurrent_income_id} if recurrent_income_id else {}
        )
        super().__init__(
            error_code=ErrorCode.RECURRENT_INCOME_NOT_FOUND,
            message="Recurrent income not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class PaymentMethodNotFoundExceptionError(RecurrentIncomeExceptionError):
    """Raised when the referenced payment method is not found or not owned by user."""

    def __init__(self, payment_method_id: str | None = None) -> None:
        """Initialize the exception.

        Args:
            payment_method_id: The ID of the payment method that was not found.
        """
        details = {"payment_method_id": payment_method_id} if payment_method_id else {}
        super().__init__(
            error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND,
            message="Payment method not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class InvalidRecurrenceConfigExceptionError(RecurrentIncomeExceptionError):
    """Raised when recurrence_config does not match the recurrence_type."""

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Description of the validation error.
        """
        super().__init__(
            error_code=ErrorCode.INVALID_RECURRENCE_CONFIG,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
