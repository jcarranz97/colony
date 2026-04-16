from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import service
from .exceptions import CycleExpenseNotFoundExceptionError, CycleNotFoundExceptionError
from .models import Cycle, CycleExpense


async def get_cycle_by_id(
    cycle_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> Cycle:
    """Dependency that resolves and verifies a cycle by ID.

    Args:
        cycle_id: Path parameter — UUID of the cycle.
        current_user: Injected authenticated user.
        db: Injected database session.

    Returns:
        The active Cycle instance owned by the current user.

    Raises:
        CycleNotFoundExceptionError: If the cycle does not exist or the user
            does not own it.
    """
    cycle = service.cycle_service.get_cycle_by_id(db, cycle_id, str(current_user.id))
    if not cycle:
        raise CycleNotFoundExceptionError(cycle_id)
    return cycle


async def get_cycle_expense_by_id(
    cycle_id: str,
    expense_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> CycleExpense:
    """Dependency that resolves and verifies a cycle expense by ID.

    Also ensures the parent cycle exists and belongs to the current user before
    looking up the expense, preventing information leakage.

    Args:
        cycle_id: Path parameter — UUID of the parent cycle.
        expense_id: Path parameter — UUID of the expense.
        current_user: Injected authenticated user.
        db: Injected database session.

    Returns:
        The active CycleExpense instance belonging to the cycle.

    Raises:
        CycleNotFoundExceptionError: If the parent cycle is not found.
        CycleExpenseNotFoundExceptionError: If the expense is not found.
    """
    cycle = service.cycle_service.get_cycle_by_id(db, cycle_id, str(current_user.id))
    if not cycle:
        raise CycleNotFoundExceptionError(cycle_id)

    expense = service.cycle_expense_service.get_expense_by_id(db, expense_id, cycle_id)
    if not expense:
        raise CycleExpenseNotFoundExceptionError(expense_id)

    return expense


# Type aliases for dependency injection
CycleDep = Annotated[Cycle, Depends(get_cycle_by_id)]
CycleExpenseDep = Annotated[CycleExpense, Depends(get_cycle_expense_by_id)]
