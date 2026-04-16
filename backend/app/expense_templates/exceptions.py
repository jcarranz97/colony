from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class ExpenseTemplateExceptionError(AppExceptionError):
    """Base expense template exception."""


class ExpenseTemplateNotFoundExceptionError(ExpenseTemplateExceptionError):
    """Raised when an expense template is not found or not owned by the user."""

    def __init__(self, template_id: str | None = None) -> None:
        """Initialize the exception.

        Args:
            template_id: The ID of the template that was not found.
        """
        details = {"template_id": template_id} if template_id else {}
        super().__init__(
            error_code=ErrorCode.EXPENSE_TEMPLATE_NOT_FOUND,
            message="Expense template not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class PaymentMethodNotFoundExceptionError(ExpenseTemplateExceptionError):
    """Raised when the referenced payment method is not found or not owned by user."""

    def __init__(self, payment_method_id: str | None = None) -> None:
        """Initialize the exception.

        Args:
            payment_method_id: The ID of the payment method that was not found.
        """
        details = (
            {"payment_method_id": payment_method_id} if payment_method_id else {}
        )
        super().__init__(
            error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND,
            message="Payment method not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class InvalidRecurrenceConfigExceptionError(ExpenseTemplateExceptionError):
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
