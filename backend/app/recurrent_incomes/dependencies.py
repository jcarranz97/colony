from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.households.dependencies import CurrentActiveHousehold

from . import service
from .exceptions import RecurrentIncomeNotFoundExceptionError


async def get_recurrent_income_by_id(
    recurrent_income_id: str,
    current_household: CurrentActiveHousehold,
    db: Annotated[Session, Depends(get_db)],
) -> service.models.RecurrentIncome:
    """Resolve and authorize a recurrent income by path parameter.

    Args:
        recurrent_income_id: The recurrent income UUID from the URL path.
        current_household: The active household.
        db: Active database session.

    Returns:
        The resolved RecurrentIncome instance.

    Raises:
        RecurrentIncomeNotFoundExceptionError: If not found or not in household.
    """
    recurrent_income = service.recurrent_income_service.get_recurrent_income_by_id(
        db, recurrent_income_id, str(current_household.id)
    )
    if not recurrent_income:
        raise RecurrentIncomeNotFoundExceptionError(recurrent_income_id)
    return recurrent_income


RecurrentIncomeDep = Annotated[
    service.models.RecurrentIncome,
    Depends(get_recurrent_income_by_id),
]
