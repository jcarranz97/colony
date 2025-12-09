from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class AuthExceptionError(AppExceptionError):
    """Base authentication exception."""


class UserNotFoundExceptionError(AuthExceptionError):
    """Exception raised when a user is not found."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.USER_NOT_FOUND,
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UserAlreadyExistsExceptionError(AuthExceptionError):
    """Exception raised when attempting to create a user that already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            message=f"User with email {email} already exists",
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidCredentialsExceptionError(AuthExceptionError):
    """Exception raised when provided credentials are invalid."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message="Incorrect email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InactiveUserExceptionError(AuthExceptionError):
    """Exception raised when attempting to authenticate an inactive user."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.INACTIVE_USER,
            message="User account is inactive",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidTokenExceptionError(AuthExceptionError):
    """Exception raised when a JWT token is invalid or expired."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_TOKEN,
            message="Could not validate credentials",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class IncorrectPasswordExceptionError(AuthExceptionError):
    """Exception raised when the current password provided is incorrect."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.INCORRECT_PASSWORD,
            message="Current password is incorrect",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PasswordTooWeakExceptionError(AuthExceptionError):
    """Exception raised when a password doesn't meet security requirements."""

    def __init__(
        self, message: str = "Password does not meet security requirements"
    ) -> None:
        super().__init__(
            error_code=ErrorCode.PASSWORD_TOO_WEAK,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class TokenExpiredExceptionError(AuthExceptionError):
    """Exception raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.TOKEN_EXPIRED,
            message="Token has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
