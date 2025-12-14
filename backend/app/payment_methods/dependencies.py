from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentActiveUser
from app.dependencies import get_db

from . import service
from .exceptions import PaymentMethodNotFoundException


async def get_payment_method_by_id(
    payment_method_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[Session, Depends(get_db)],
) -> service.models.PaymentMethod:
    """Dependency to get payment method by ID and verify ownership."""
    payment_method = service.payment_method_service.get_payment_method_by_id(
        db, payment_method_id, str(current_user.id)
    )

    if not payment_method:
        raise PaymentMethodNotFoundException(payment_method_id)

    return payment_method


# Type alias for dependency injection
PaymentMethodDep = Annotated[
    service.models.PaymentMethod, Depends(get_payment_method_by_id)
]
