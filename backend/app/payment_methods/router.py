from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import schemas, service
from .dependencies import PaymentMethodDep
from .exceptions import (
    PaymentMethodInUseException,
    PaymentMethodNameExistsException,
)

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])

# Create dependency aliases
DatabaseDep = Annotated[Session, Depends(get_db)]


@router.get(
    "/",
    response_model=list[schemas.PaymentMethodResponse],
    summary="Get all payment methods",
    description="Retrieve all payment methods for the authenticated user with optional filters",
)
async def get_payment_methods(
    current_user: CurrentActiveUser,
    db: DatabaseDep,
    active: bool | None = Query(None, description="Filter by active status"),
    currency: str | None = Query(None, description="Filter by default currency"),
) -> list[schemas.PaymentMethodResponse]:
    """Get all payment methods for the authenticated user."""
    payment_methods = service.payment_method_service.get_payment_methods(
        db, str(current_user.id), active=active, currency=currency
    )
    return [schemas.PaymentMethodResponse.model_validate(pm) for pm in payment_methods]


@router.post(
    "/",
    response_model=schemas.PaymentMethodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new payment method",
    description="Create a new payment method for the authenticated user",
)
async def create_payment_method(
    payment_method_data: schemas.PaymentMethodCreate,
    current_user: CurrentActiveUser,
    db: DatabaseDep,
) -> schemas.PaymentMethodResponse:
    """Create a new payment method."""
    try:
        payment_method = service.payment_method_service.create_payment_method(
            db, payment_method_data, str(current_user.id)
        )
        return schemas.PaymentMethodResponse.model_validate(payment_method)
    except PaymentMethodNameExistsException as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get(
    "/{payment_method_id}",
    response_model=schemas.PaymentMethodResponse,
    summary="Get a payment method",
    description="Retrieve a specific payment method by ID",
)
async def get_payment_method(
    payment_method: PaymentMethodDep,
) -> schemas.PaymentMethodResponse:
    """Get a specific payment method by ID."""
    return schemas.PaymentMethodResponse.model_validate(payment_method)


@router.put(
    "/{payment_method_id}",
    response_model=schemas.PaymentMethodResponse,
    summary="Update a payment method",
    description="Update an existing payment method",
)
async def update_payment_method(
    payment_method_data: schemas.PaymentMethodUpdate,
    payment_method: PaymentMethodDep,
    db: DatabaseDep,
) -> schemas.PaymentMethodResponse:
    """Update an existing payment method."""
    try:
        updated_payment_method = service.payment_method_service.update_payment_method(
            db, payment_method, payment_method_data
        )
        return schemas.PaymentMethodResponse.model_validate(updated_payment_method)
    except PaymentMethodNameExistsException as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.delete(
    "/{payment_method_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a payment method",
    description="Deactivate a payment method (soft delete)",
)
async def delete_payment_method(
    payment_method: PaymentMethodDep,
    db: DatabaseDep,
) -> None:
    """Deactivate a payment method (soft delete)."""
    try:
        service.payment_method_service.delete_payment_method(db, payment_method)
    except PaymentMethodInUseException as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get(
    "/{payment_method_id}/health",
    summary="Payment method health check",
    description="Health check endpoint for payment methods domain",
)
async def payment_method_health_check() -> dict[str, str]:
    """Payment methods domain health check."""
    return {"status": "healthy", "domain": "payment_methods"}
