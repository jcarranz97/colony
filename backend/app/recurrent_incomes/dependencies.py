from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import service
from .exceptions import RecurrentIncomeNotFoundExceptionError


async def get_recurrent_income_by_id(
    recurrent_income_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> service.models.RecurrentIncome:
    """Resolve and authorize a recurrent income by path parameter.

    Args:
        recurrent_income_id: The recurrent income UUID from the URL path.
        current_user: The authenticated active user.
        db: Active database session.

    Returns:
        The resolved RecurrentIncome instance.

    Raises:
        RecurrentIncomeNotFoundExceptionError: If the recurrent income does not exist
            or does not belong to the current user.
    """
    recurrent_income = service.recurrent_income_service.get_recurrent_income_by_id(
        db, recurrent_income_id, str(current_user.id)
    )
    if not recurrent_income:
        raise RecurrentIncomeNotFoundExceptionError(recurrent_income_id)
    return recurrent_income


RecurrentIncomeDep = Annotated[
    service.models.RecurrentIncome,
    Depends(get_recurrent_income_by_id),
]
