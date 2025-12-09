import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppExceptionError(Exception):
    """Base application exception class.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            },
        }


class ValidationExceptionError(AppExceptionError):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details,
        )


class NotFoundError(AppExceptionError):
    """Exception for resource not found errors."""

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource} not found",
            status_code=404,
        )


class ConflictError(AppExceptionError):
    """Exception for resource conflict errors."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(
            error_code="RESOURCE_CONFLICT", message=message, status_code=409
        )


class InternalServerError(AppExceptionError):
    """Exception for internal server errors."""

    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(
            error_code="INTERNAL_SERVER_ERROR", message=message, status_code=500
        )


class DatabaseError(AppExceptionError):
    """Exception for database-related errors."""

    def __init__(self, message: str = "Database error") -> None:
        super().__init__(error_code="DATABASE_ERROR", message=message, status_code=500)


class ExternalServiceError(AppExceptionError):
    """Exception for external service errors."""

    def __init__(self, service: str, message: str = "External service error") -> None:
        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
            status_code=502,
        )


# Exception Handlers
async def app_exception_handler(
    request: Request, exc: AppExceptionError
) -> JSONResponse:
    """Global exception handler for AppExceptionError instances.

    This handler will catch all AppExceptionError instances and return
    a standardized JSON error response.
    """
    logger.error(
        f"AppExceptionError: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "url": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Global exception handler for HTTPException instances.

    This handler ensures all HTTP exceptions return the same
    JSON format as AppExceptionError.
    """
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "url": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {},
            },
        },
    )


async def validation_exception_handler(
    request: Request, exc: ValueError
) -> JSONResponse:
    """Global exception handler for validation errors."""
    logger.error(
        f"ValidationError: {exc!s}",
        extra={"error": str(exc), "url": str(request.url), "method": request.method},
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": {}},
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for any unhandled exceptions.

    This is a catch-all handler that should never be reached in production,
    but provides a safety net for unexpected errors.
    """
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {exc!s}",
        extra={
            "exception_type": type(exc).__name__,
            "error": str(exc),
            "url": str(request.url),
            "method": request.method,
        },
        exc_info=True,  # Include traceback in logs
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
        },
    )


# Global error codes
class GlobalErrorCode:
    """Global error codes used across the application."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
