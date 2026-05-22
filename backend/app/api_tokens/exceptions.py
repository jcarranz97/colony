from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class ApiTokenExceptionError(AppExceptionError):
    """Base API token exception."""


class ApiTokenNotFoundExceptionError(ApiTokenExceptionError):
    """Exception raised when an API token is not found."""

    def __init__(self, token_id: str | None = None) -> None:
        details = {"token_id": token_id} if token_id else {}
        super().__init__(
            error_code=ErrorCode.API_TOKEN_NOT_FOUND,
            message="API token not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )
