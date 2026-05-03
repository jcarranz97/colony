from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.households.dependencies import CurrentActiveHousehold

from . import service
from .exceptions import RecurrentExpenseNotFoundExceptionError


async def get_recurrent_expense_by_id(
    recurrent_expense_id: str,
    current_household: CurrentActiveHousehold,
    db: Annotated[Session, Depends(get_db)],
) -> service.models.RecurrentExpense:
    """Resolve and authorize a recurrent expense by path parameter.

    Args:
        recurrent_expense_id: The recurrent expense UUID from the URL path.
        current_household: The active household.
        db: Active database session.

    Returns:
        The resolved RecurrentExpense instance.

    Raises:
        RecurrentExpenseNotFoundExceptionError: If not found or not in household.
    """
    recurrent_expense = service.recurrent_expense_service.get_recurrent_expense_by_id(
        db, recurrent_expense_id, str(current_household.id)
    )
    if not recurrent_expense:
        raise RecurrentExpenseNotFoundExceptionError(recurrent_expense_id)
    return recurrent_expense


RecurrentExpenseDep = Annotated[
    service.models.RecurrentExpense,
    Depends(get_recurrent_expense_by_id),
]
