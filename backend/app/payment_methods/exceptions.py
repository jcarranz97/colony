from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class PaymentMethodExceptionError(AppExceptionError):
    """Base payment method exception."""


class PaymentMethodNotFoundExceptionError(PaymentMethodExceptionError):
    """Exception raised when a payment method is not found."""

    def __init__(self, payment_method_id: str | None = None) -> None:
        details = {"payment_method_id": payment_method_id} if payment_method_id else {}
        super().__init__(
            error_code=ErrorCode.PAYMENT_METHOD_NOT_FOUND,
            message="Payment method not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class PaymentMethodNameExistsExceptionError(PaymentMethodExceptionError):
    """Exception raised when payment method name already exists for user."""

    def __init__(self, name: str) -> None:
        super().__init__(
            error_code=ErrorCode.PAYMENT_METHOD_NAME_EXISTS,
            message=f"Payment method with name '{name}' already exists",
            status_code=status.HTTP_409_CONFLICT,
            details={"name": name},
        )


class PaymentMethodInUseExceptionError(PaymentMethodExceptionError):
    """Exception raised when trying to delete a payment method that's in use."""

    def __init__(self, payment_method_id: str) -> None:
        super().__init__(
            error_code=ErrorCode.PAYMENT_METHOD_IN_USE,
            message="Cannot delete payment method that is in use",
            status_code=status.HTTP_409_CONFLICT,
            details={"payment_method_id": payment_method_id},
        )


class InvalidPaymentMethodTypeExceptionError(PaymentMethodExceptionError):
    """Exception raised when payment method type is invalid."""

    def __init__(self, method_type: str) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_PAYMENT_METHOD_TYPE,
            message=f"Invalid payment method type: {method_type}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"method_type": method_type},
        )


class InvalidCurrencyExceptionError(PaymentMethodExceptionError):
    """Exception raised when currency is invalid."""

    def __init__(self, currency: str) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_CURRENCY,
            message=f"Invalid currency: {currency}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"currency": currency},
        )
