from fastapi import HTTPException, status
from app.exceptions import AppException
from .constants import ErrorCode

class AuthException(AppException):
    """Base authentication exception"""
    pass

class UserNotFoundException(AuthException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.USER_NOT_FOUND,
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

class UserAlreadyExistsException(AuthException):
    def __init__(self, email: str):
        super().__init__(
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            message=f"User with email {email} already exists",
            status_code=status.HTTP_409_CONFLICT
        )

class InvalidCredentialsException(AuthException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message="Incorrect email or password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class InactiveUserException(AuthException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.INACTIVE_USER,
            message="User account is inactive",
            status_code=status.HTTP_403_FORBIDDEN
        )

class InvalidTokenException(AuthException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.INVALID_TOKEN,
            message="Could not validate credentials",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class IncorrectPasswordException(AuthException):
    def __init__(self):
        super().__init__(
            error_code=ErrorCode.INCORRECT_PASSWORD,
            message="Current password is incorrect",
            status_code=status.HTTP_400_BAD_REQUEST
        )
