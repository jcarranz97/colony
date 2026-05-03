from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.households.dependencies import CurrentActiveHousehold

from . import schemas, service
from .dependencies import RecurrentExpenseDep
from .exceptions import (
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
    RecurrentExpenseNotFoundExceptionError,
)

router = APIRouter(prefix="/recurrent-expenses", tags=["recurrent-expenses"])

DatabaseDep = Annotated[Session, Depends(get_db)]


@router.get(
    "/health",
    summary="Recurrent expenses health check",
    description="Health check endpoint for recurrent expenses domain",
)
async def recurrent_expenses_health_check() -> dict[str, str]:
    """Recurrent expenses domain health check."""
    return {"status": "healthy", "domain": "recurrent_expenses"}


@router.get(
    "/",
    response_model=list[schemas.RecurrentExpenseResponse],
    summary="Get all recurrent expenses",
    description=(
        "Retrieve all recurrent expenses for the active household "
        "with optional filters."
    ),
)
async def get_recurrent_expenses(
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
    active: bool | None = Query(None, description="Filter by active status"),
    category: str | None = Query(None, description="Filter by category"),
    currency: str | None = Query(None, description="Filter by currency"),
) -> list[schemas.RecurrentExpenseResponse]:
    """Get all recurrent expenses for the active household."""
    recurrent_expenses = service.recurrent_expense_service.get_recurrent_expenses(
        db,
        str(current_household.id),
        active=active,
        category=category,
        currency=currency,
    )
    return [
        schemas.RecurrentExpenseResponse.model_validate(t) for t in recurrent_expenses
    ]


@router.post(
    "/",
    response_model=schemas.RecurrentExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recurrent expense",
    description="Create a new recurrent expense for the active household.",
)
async def create_recurrent_expense(
    data: schemas.RecurrentExpenseCreate,
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
) -> schemas.RecurrentExpenseResponse:
    """Create a new recurrent expense."""
    try:
        recurrent_expense = service.recurrent_expense_service.create_recurrent_expense(
            db, data, str(current_household.id)
        )
        return schemas.RecurrentExpenseResponse.model_validate(recurrent_expense)
    except PaymentMethodNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get(
    "/{recurrent_expense_id}",
    response_model=schemas.RecurrentExpenseResponse,
    summary="Get a recurrent expense",
    description="Retrieve a specific recurrent expense by ID.",
)
async def get_recurrent_expense(
    recurrent_expense: RecurrentExpenseDep,
) -> schemas.RecurrentExpenseResponse:
    """Get a specific recurrent expense by ID."""
    return schemas.RecurrentExpenseResponse.model_validate(recurrent_expense)


@router.put(
    "/{recurrent_expense_id}",
    response_model=schemas.RecurrentExpenseResponse,
    summary="Update a recurrent expense",
    description="Update an existing recurrent expense.",
)
async def update_recurrent_expense(
    data: schemas.RecurrentExpenseUpdate,
    recurrent_expense: RecurrentExpenseDep,
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
) -> schemas.RecurrentExpenseResponse:
    """Update an existing recurrent expense."""
    try:
        updated = service.recurrent_expense_service.update_recurrent_expense(
            db, recurrent_expense, data, str(current_household.id)
        )
        return schemas.RecurrentExpenseResponse.model_validate(updated)
    except PaymentMethodNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    except InvalidRecurrenceConfigExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete(
    "/{recurrent_expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recurrent expense",
    description="Soft delete a recurrent expense (deactivate).",
)
async def delete_recurrent_expense(
    recurrent_expense: RecurrentExpenseDep,
    db: DatabaseDep,
) -> None:
    """Soft delete a recurrent expense."""
    try:
        service.recurrent_expense_service.delete_recurrent_expense(
            db, recurrent_expense
        )
    except RecurrentExpenseNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
