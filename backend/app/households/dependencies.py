from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.database import get_db

from .exceptions import (
    HouseholdForbiddenExceptionError,
    UserHasNoActiveHouseholdExceptionError,
)
from .models import Household
from .service import household_service


async def get_current_active_household(
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> Household:
    """Resolve the current user's active household.

    Args:
        current_user: Authenticated active user.
        db: Active database session.

    Returns:
        The Household the user is currently operating in.

    Raises:
        UserHasNoActiveHouseholdExceptionError: If no active household is set.
        HouseholdNotFoundExceptionError: If the household no longer exists.
    """
    if not current_user.active_household_id:
        raise UserHasNoActiveHouseholdExceptionError
    return household_service.get_household_by_id(db, current_user.active_household_id)


async def get_target_household(
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
    household_id: Annotated[
        UUID | None,
        Query(
            description=(
                "Scope the request to a specific household the user belongs "
                "to. When omitted, the user's active household is used."
            ),
        ),
    ] = None,
) -> Household:
    """Resolve the household a request should operate on.

    When ``household_id`` is supplied the user must be a member of that
    household; this lets multi-household clients (such as the MCP server)
    target any household without mutating the user's active household.
    When omitted, the active household is used — the default the web
    frontend relies on.

    Args:
        current_user: Authenticated active user.
        db: Active database session.
        household_id: Optional explicit household to scope to.

    Returns:
        The Household the request should operate on.

    Raises:
        UserHasNoActiveHouseholdExceptionError: If no household is given and
            the user has no active household.
        HouseholdNotFoundExceptionError: If the household does not exist.
        HouseholdForbiddenExceptionError: If the user is not a member of the
            requested household.
    """
    if household_id is None:
        return await get_current_active_household(current_user, db)

    household = household_service.get_household_by_id(db, household_id)
    if not household_service.is_member(db, current_user.id, household_id):
        raise HouseholdForbiddenExceptionError(household_id)
    return household


# Type aliases for dependency injection
CurrentActiveHousehold = Annotated[Household, Depends(get_current_active_household)]
TargetHousehold = Annotated[Household, Depends(get_target_household)]
