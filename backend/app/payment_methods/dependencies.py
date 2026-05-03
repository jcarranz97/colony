from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.households.dependencies import CurrentActiveHousehold

from . import service
from .exceptions import PaymentMethodNotFoundExceptionError


async def get_payment_method_by_id(
    payment_method_id: str,
    current_household: CurrentActiveHousehold,
    db: Annotated[Session, Depends(get_db)],
) -> service.models.PaymentMethod:
    """Resolve a payment method by ID, verifying it belongs to the active household."""
    payment_method = service.payment_method_service.get_payment_method_by_id(
        db, payment_method_id, str(current_household.id)
    )

    if not payment_method:
        raise PaymentMethodNotFoundExceptionError(payment_method_id)

    return payment_method


PaymentMethodDep = Annotated[
    service.models.PaymentMethod, Depends(get_payment_method_by_id)
]
