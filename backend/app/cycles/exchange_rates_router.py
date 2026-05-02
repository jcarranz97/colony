"""HTTP endpoints for managing currency exchange rates."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentActiveUser

from . import schemas
from .exceptions import ExchangeRateDateExistsExceptionError
from .service import exchange_rate_service

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])

DatabaseDep = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[schemas.ExchangeRateResponse])
async def list_exchange_rates(
    db: DatabaseDep,
    _current_user: CurrentActiveUser,
) -> list[schemas.ExchangeRateResponse]:
    """List all exchange rates ordered by date descending."""
    rates = exchange_rate_service.get_exchange_rates(db)
    return [schemas.ExchangeRateResponse.model_validate(r) for r in rates]


@router.post("/", response_model=schemas.ExchangeRateResponse, status_code=201)
async def create_exchange_rate(
    data: schemas.ExchangeRateCreate,
    db: DatabaseDep,
    _current_user: CurrentActiveUser,
) -> schemas.ExchangeRateResponse:
    """Create a new exchange rate record."""
    try:
        rate = exchange_rate_service.create_exchange_rate(db, data)
        return schemas.ExchangeRateResponse.model_validate(rate)
    except ExchangeRateDateExistsExceptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.put("/{rate_id}", response_model=schemas.ExchangeRateResponse)
async def update_exchange_rate(
    rate_id: UUID,
    data: schemas.ExchangeRateUpdate,
    db: DatabaseDep,
    _current_user: CurrentActiveUser,
) -> schemas.ExchangeRateResponse:
    """Update the rate value of an existing exchange rate record."""
    rate = exchange_rate_service.get_exchange_rate_by_id(db, rate_id)
    if rate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange rate {rate_id} not found",
        )
    updated = exchange_rate_service.update_exchange_rate(db, rate, data)
    return schemas.ExchangeRateResponse.model_validate(updated)
