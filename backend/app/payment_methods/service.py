import logging

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .constants import MAX_PAYMENT_METHODS_PER_USER
from .exceptions import (
    PaymentMethodInUseExceptionError,
    PaymentMethodNameExistsExceptionError,
)

logger = logging.getLogger(__name__)


class PaymentMethodService:
    """Payment method business logic service."""

    @staticmethod
    def get_payment_methods(
        db: Session,
        household_id: str,
        active: bool | None = None,
        currency: str | None = None,
    ) -> list[models.PaymentMethod]:
        """Get all payment methods for a household with optional filters."""
        query = db.query(models.PaymentMethod).filter(
            models.PaymentMethod.household_id == household_id
        )

        if active is not None:
            query = query.filter(models.PaymentMethod.active == active)

        if currency:
            query = query.filter(models.PaymentMethod.default_currency == currency)

        return query.order_by(models.PaymentMethod.created_at.desc()).all()

    @staticmethod
    def get_payment_method_by_id(
        db: Session,
        payment_method_id: str,
        household_id: str,
    ) -> models.PaymentMethod | None:
        """Get payment method by ID and verify it belongs to the household."""
        return (
            db.query(models.PaymentMethod)
            .filter(
                and_(
                    models.PaymentMethod.id == payment_method_id,
                    models.PaymentMethod.household_id == household_id,
                )
            )
            .first()
        )

    @staticmethod
    def create_payment_method(
        db: Session,
        payment_method_data: schemas.PaymentMethodCreate,
        household_id: str,
    ) -> models.PaymentMethod:
        """Create a new payment method for a household."""
        logger.info(
            "Creating payment method",
            extra={
                "household_id": household_id,
                "name": payment_method_data.name,
            },
        )

        existing_count = (
            db.query(models.PaymentMethod)
            .filter(
                and_(
                    models.PaymentMethod.household_id == household_id,
                    models.PaymentMethod.active,
                )
            )
            .count()
        )

        if existing_count >= MAX_PAYMENT_METHODS_PER_USER:
            raise PaymentMethodInUseExceptionError(
                f"Maximum {MAX_PAYMENT_METHODS_PER_USER} payment methods allowed"
            )

        existing_method = (
            db.query(models.PaymentMethod)
            .filter(
                and_(
                    models.PaymentMethod.household_id == household_id,
                    models.PaymentMethod.name == payment_method_data.name,
                    models.PaymentMethod.active,
                )
            )
            .first()
        )

        if existing_method:
            raise PaymentMethodNameExistsExceptionError(payment_method_data.name)

        try:
            payment_method = models.PaymentMethod(
                household_id=household_id,
                name=payment_method_data.name,
                method_type=payment_method_data.method_type,
                default_currency=payment_method_data.default_currency,
                description=payment_method_data.description,
            )

            db.add(payment_method)
            db.commit()
            db.refresh(payment_method)

            logger.info(
                "Payment method created",
                extra={
                    "household_id": household_id,
                    "payment_method_id": str(payment_method.id),
                },
            )

            return payment_method

        except IntegrityError as e:
            db.rollback()
            logger.error(
                "Failed to create payment method",
                extra={"household_id": household_id, "error": str(e)},
            )
            raise PaymentMethodNameExistsExceptionError(payment_method_data.name) from e

    @staticmethod
    def update_payment_method(
        db: Session,
        payment_method: models.PaymentMethod,
        payment_method_data: schemas.PaymentMethodUpdate,
    ) -> models.PaymentMethod:
        """Update an existing payment method."""
        logger.info(
            "Updating payment method",
            extra={"payment_method_id": str(payment_method.id)},
        )

        if payment_method_data.name and payment_method_data.name != payment_method.name:
            existing_method = (
                db.query(models.PaymentMethod)
                .filter(
                    and_(
                        models.PaymentMethod.household_id
                        == payment_method.household_id,
                        models.PaymentMethod.name == payment_method_data.name,
                        models.PaymentMethod.active,
                        models.PaymentMethod.id != payment_method.id,
                    )
                )
                .first()
            )

            if existing_method:
                raise PaymentMethodNameExistsExceptionError(payment_method_data.name)

        try:
            update_data = payment_method_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(payment_method, field, value)

            db.commit()
            db.refresh(payment_method)

            logger.info(
                "Payment method updated",
                extra={"payment_method_id": str(payment_method.id)},
            )

            return payment_method

        except IntegrityError as e:
            db.rollback()
            logger.error(
                "Failed to update payment method",
                extra={
                    "payment_method_id": str(payment_method.id),
                    "error": str(e),
                },
            )
            raise PaymentMethodNameExistsExceptionError(
                payment_method_data.name or payment_method.name
            ) from e

    @staticmethod
    def delete_payment_method(
        db: Session,
        payment_method: models.PaymentMethod,
    ) -> None:
        """Soft delete a payment method (deactivate)."""
        logger.info(
            "Deactivating payment method",
            extra={"payment_method_id": str(payment_method.id)},
        )

        payment_method.active = False
        db.commit()

        logger.info(
            "Payment method deactivated",
            extra={"payment_method_id": str(payment_method.id)},
        )

    @staticmethod
    def get_active_payment_methods_for_household(
        db: Session,
        household_id: str,
    ) -> list[models.PaymentMethod]:
        """Get all active payment methods for a household."""
        return (
            db.query(models.PaymentMethod)
            .filter(
                and_(
                    models.PaymentMethod.household_id == household_id,
                    models.PaymentMethod.active,
                )
            )
            .order_by(models.PaymentMethod.name)
            .all()
        )


payment_method_service = PaymentMethodService()
