from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.database import get_db

from .exceptions import UserHasNoActiveHouseholdExceptionError
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


# Type aliases for dependency injection
CurrentActiveHousehold = Annotated[Household, Depends(get_current_active_household)]
