from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class CycleExceptionError(AppExceptionError):
    """Base cycles domain exception."""


class CycleNotFoundExceptionError(CycleExceptionError):
    """Raised when a cycle cannot be found."""

    def __init__(self, cycle_id: str | None = None) -> None:
        """Initialize CycleNotFoundExceptionError.

        Args:
            cycle_id: Optional cycle UUID for context in the error details.
        """
        details = {"cycle_id": cycle_id} if cycle_id else {}
        super().__init__(
            error_code=ErrorCode.CYCLE_NOT_FOUND,
            message="Cycle not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class CycleNameExistsExceptionError(CycleExceptionError):
    """Raised when a cycle name already exists for the user."""

    def __init__(self, name: str) -> None:
        """Initialize CycleNameExistsExceptionError.

        Args:
            name: The duplicate cycle name.
        """
        super().__init__(
            error_code=ErrorCode.CYCLE_NAME_EXISTS,
            message=f"A cycle named '{name}' already exists",
            status_code=status.HTTP_409_CONFLICT,
            details={"name": name},
        )


class CycleExpenseNotFoundExceptionError(CycleExceptionError):
    """Raised when a cycle expense cannot be found."""

    def __init__(self, expense_id: str | None = None) -> None:
        """Initialize CycleExpenseNotFoundExceptionError.

        Args:
            expense_id: Optional expense UUID for context in the error details.
        """
        details = {"expense_id": expense_id} if expense_id else {}
        super().__init__(
            error_code=ErrorCode.CYCLE_EXPENSE_NOT_FOUND,
            message="Cycle expense not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class CycleIncomeNotFoundExceptionError(CycleExceptionError):
    """Raised when a cycle income cannot be found."""

    def __init__(self, income_id: str | None = None) -> None:
        """Initialize CycleIncomeNotFoundExceptionError.

        Args:
            income_id: Optional income UUID for context in the error details.
        """
        details = {"income_id": income_id} if income_id else {}
        super().__init__(
            error_code=ErrorCode.CYCLE_INCOME_NOT_FOUND,
            message="Cycle income not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class CycleGenerationExceptionError(CycleExceptionError):
    """Raised when automatic expense generation from templates fails."""

    def __init__(self, message: str = "Failed to generate cycle expenses") -> None:
        """Initialize CycleGenerationExceptionError.

        Args:
            message: Human-readable description of the generation failure.
        """
        super().__init__(
            error_code=ErrorCode.CYCLE_GENERATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class PaymentMethodNotFoundExceptionError(CycleExceptionError):
    """Raised when a referenced payment method cannot be found."""

    def __init__(self, payment_method_id: str) -> None:
        """Initialize PaymentMethodNotFoundExceptionError.

        Args:
            payment_method_id: UUID of the missing payment method.
        """
        super().__init__(
            error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND,
            message="Payment method not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"payment_method_id": payment_method_id},
        )


class ExchangeRateDateExistsExceptionError(CycleExceptionError):
    """Raised when a rate for the same currency pair and date already exists."""

    def __init__(self, from_currency: str, to_currency: str, rate_date: str) -> None:
        """Initialize ExchangeRateDateExistsExceptionError.

        Args:
            from_currency: Source currency code.
            to_currency: Target currency code.
            rate_date: The date that already has a rate.
        """
        super().__init__(
            error_code=ErrorCode.EXCHANGE_RATE_DATE_EXISTS,
            message=(
                f"An exchange rate for {from_currency} → {to_currency} "
                f"on {rate_date} already exists"
            ),
            status_code=status.HTTP_409_CONFLICT,
            details={
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate_date": rate_date,
            },
        )


class ExchangeRateNotFoundExceptionError(CycleExceptionError):
    """Raised when no exchange rate is available for the requested currency pair."""

    def __init__(self, from_currency: str, to_currency: str) -> None:
        """Initialize ExchangeRateNotFoundExceptionError.

        Args:
            from_currency: Source currency code.
            to_currency: Target currency code.
        """
        super().__init__(
            error_code=ErrorCode.EXCHANGE_RATE_NOT_FOUND,
            message=(
                f"No exchange rate found for {from_currency} → {to_currency}. "
                "Please add an exchange rate before creating expenses in this currency."
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"from_currency": from_currency, "to_currency": to_currency},
        )
