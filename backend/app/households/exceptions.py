from uuid import UUID

from fastapi import status

from app.exceptions import AppExceptionError

from .constants import ErrorCode


class HouseholdExceptionError(AppExceptionError):
    """Base household exception."""


class HouseholdNotFoundExceptionError(HouseholdExceptionError):
    """Raised when a household does not exist or is inactive."""

    def __init__(self, household_id: UUID | str) -> None:
        super().__init__(
            error_code=ErrorCode.HOUSEHOLD_NOT_FOUND,
            message=f"Household {household_id} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"household_id": str(household_id)},
        )


class HouseholdNameExistsExceptionError(HouseholdExceptionError):
    """Raised when a household with the given name already exists."""

    def __init__(self, name: str) -> None:
        super().__init__(
            error_code=ErrorCode.HOUSEHOLD_NAME_EXISTS,
            message=f"A household named '{name}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
            details={"name": name},
        )


class UserAlreadyInHouseholdExceptionError(HouseholdExceptionError):
    """Raised when a user is already a member of the household."""

    def __init__(self, user_id: UUID | str, household_id: UUID | str) -> None:
        super().__init__(
            error_code=ErrorCode.USER_ALREADY_IN_HOUSEHOLD,
            message=(
                f"User {user_id} is already a member of household {household_id}."
            ),
            status_code=status.HTTP_409_CONFLICT,
            details={
                "user_id": str(user_id),
                "household_id": str(household_id),
            },
        )


class UserNotInHouseholdExceptionError(HouseholdExceptionError):
    """Raised when a user is not a member of the household."""

    def __init__(self, user_id: UUID | str, household_id: UUID | str) -> None:
        super().__init__(
            error_code=ErrorCode.USER_NOT_IN_HOUSEHOLD,
            message=(f"User {user_id} is not a member of household {household_id}."),
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "user_id": str(user_id),
                "household_id": str(household_id),
            },
        )


class UserHasNoActiveHouseholdExceptionError(HouseholdExceptionError):
    """Raised when a user has no active household selected."""

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.USER_HAS_NO_ACTIVE_HOUSEHOLD,
            message=(
                "No active household selected. "
                "Please set your active household in Settings."
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
