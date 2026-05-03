from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.households.dependencies import CurrentActiveHousehold

from . import schemas, service
from .dependencies import RecurrentIncomeDep
from .exceptions import (
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
    RecurrentIncomeNotFoundExceptionError,
)

router = APIRouter(prefix="/recurrent-incomes", tags=["recurrent-incomes"])

DatabaseDep = Annotated[Session, Depends(get_db)]


@router.get(
    "/health",
    summary="Recurrent incomes health check",
    description="Health check endpoint for recurrent incomes domain",
)
async def recurrent_incomes_health_check() -> dict[str, str]:
    """Recurrent incomes domain health check."""
    return {"status": "healthy", "domain": "recurrent_incomes"}


@router.get(
    "/",
    response_model=list[schemas.RecurrentIncomeResponse],
    summary="Get all recurrent incomes",
    description=(
        "Retrieve all recurrent incomes for the active household with optional filters."
    ),
)
async def get_recurrent_incomes(
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
    active: bool | None = Query(None, description="Filter by active status"),
    currency: str | None = Query(None, description="Filter by currency"),
) -> list[schemas.RecurrentIncomeResponse]:
    """Get all recurrent incomes for the active household."""
    incomes = service.recurrent_income_service.get_recurrent_incomes(
        db, str(current_household.id), active=active, currency=currency
    )
    return [schemas.RecurrentIncomeResponse.model_validate(t) for t in incomes]


@router.post(
    "/",
    response_model=schemas.RecurrentIncomeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recurrent income",
    description="Create a new recurrent income for the active household.",
)
async def create_recurrent_income(
    data: schemas.RecurrentIncomeCreate,
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
) -> schemas.RecurrentIncomeResponse:
    """Create a new recurrent income."""
    try:
        income = service.recurrent_income_service.create_recurrent_income(
            db, data, str(current_household.id)
        )
        return schemas.RecurrentIncomeResponse.model_validate(income)
    except PaymentMethodNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get(
    "/{recurrent_income_id}",
    response_model=schemas.RecurrentIncomeResponse,
    summary="Get a recurrent income",
    description="Retrieve a specific recurrent income by ID.",
)
async def get_recurrent_income(
    recurrent_income: RecurrentIncomeDep,
) -> schemas.RecurrentIncomeResponse:
    """Get a specific recurrent income by ID."""
    return schemas.RecurrentIncomeResponse.model_validate(recurrent_income)


@router.put(
    "/{recurrent_income_id}",
    response_model=schemas.RecurrentIncomeResponse,
    summary="Update a recurrent income",
    description="Update an existing recurrent income.",
)
async def update_recurrent_income(
    data: schemas.RecurrentIncomeUpdate,
    recurrent_income: RecurrentIncomeDep,
    current_household: CurrentActiveHousehold,
    db: DatabaseDep,
) -> schemas.RecurrentIncomeResponse:
    """Update an existing recurrent income."""
    try:
        updated = service.recurrent_income_service.update_recurrent_income(
            db, recurrent_income, data, str(current_household.id)
        )
        return schemas.RecurrentIncomeResponse.model_validate(updated)
    except PaymentMethodNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    except InvalidRecurrenceConfigExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete(
    "/{recurrent_income_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recurrent income",
    description="Soft delete a recurrent income (deactivate).",
)
async def delete_recurrent_income(
    recurrent_income: RecurrentIncomeDep,
    db: DatabaseDep,
) -> None:
    """Soft delete a recurrent income."""
    try:
        service.recurrent_income_service.delete_recurrent_income(db, recurrent_income)
    except RecurrentIncomeNotFoundExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
