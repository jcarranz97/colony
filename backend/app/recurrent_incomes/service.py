import logging
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.payment_methods import models as pm_models

from . import models, schemas
from .exceptions import (
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
)
from .schemas import _RECURRENCE_VALIDATORS

logger = logging.getLogger(__name__)


class RecurrentIncomeService:
    """Recurrent income business logic service."""

    @staticmethod
    def _verify_payment_method(
        db: Session,
        payment_method_id: UUID,
        user_id: str,
    ) -> pm_models.PaymentMethod:
        """Verify a payment method exists and belongs to the user.

        Args:
            db: Active database session.
            payment_method_id: UUID of the payment method to verify.
            user_id: The authenticated user's ID.

        Returns:
            The PaymentMethod instance.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method does not
                exist or does not belong to the user.
        """
        pm = (
            db.query(pm_models.PaymentMethod)
            .filter(
                and_(
                    pm_models.PaymentMethod.id == payment_method_id,
                    pm_models.PaymentMethod.user_id == user_id,
                    pm_models.PaymentMethod.active.is_(True),
                )
            )
            .first()
        )
        if not pm:
            raise PaymentMethodNotFoundExceptionError(str(payment_method_id))
        return pm

    @staticmethod
    def get_recurrent_incomes(
        db: Session,
        user_id: str,
        active: bool | None = None,
        currency: str | None = None,
    ) -> list[models.RecurrentIncome]:
        """List recurrent incomes for a user with optional filters.

        Args:
            db: Active database session.
            user_id: The authenticated user's ID.
            active: Optional filter by active status.
            currency: Optional filter by currency code.

        Returns:
            List of matching recurrent incomes ordered by created_at descending.
        """
        query = db.query(models.RecurrentIncome).filter(
            models.RecurrentIncome.user_id == user_id
        )

        if active is not None:
            query = query.filter(models.RecurrentIncome.active == active)

        if currency:
            query = query.filter(models.RecurrentIncome.currency == currency)

        return query.order_by(models.RecurrentIncome.created_at.desc()).all()

    @staticmethod
    def get_recurrent_income_by_id(
        db: Session,
        recurrent_income_id: str,
        user_id: str,
    ) -> models.RecurrentIncome | None:
        """Get a single recurrent income verifying ownership.

        Args:
            db: Active database session.
            recurrent_income_id: The recurrent income UUID as a string.
            user_id: The authenticated user's ID.

        Returns:
            The RecurrentIncome if found and owned by user, else None.
        """
        return (
            db.query(models.RecurrentIncome)
            .filter(
                and_(
                    models.RecurrentIncome.id == recurrent_income_id,
                    models.RecurrentIncome.user_id == user_id,
                )
            )
            .first()
        )

    @staticmethod
    def create_recurrent_income(
        db: Session,
        data: schemas.RecurrentIncomeCreate,
        user_id: str,
    ) -> models.RecurrentIncome:
        """Create a new recurrent income.

        Args:
            db: Active database session.
            data: Validated creation schema.
            user_id: The authenticated user's ID.

        Returns:
            The newly created RecurrentIncome.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method does not
                exist or does not belong to the user.
        """
        logger.info(
            "Creating recurrent income",
            extra={"user_id": user_id, "description": data.description},
        )

        RecurrentIncomeService._verify_payment_method(
            db, data.payment_method_id, user_id
        )

        recurrent_income = models.RecurrentIncome(
            user_id=user_id,
            payment_method_id=data.payment_method_id,
            description=data.description,
            currency=data.currency,
            base_amount=data.base_amount,
            recurrence_type=data.recurrence_type,
            recurrence_config=data.recurrence_config,
            reference_date=data.reference_date,
        )

        db.add(recurrent_income)
        db.commit()
        db.refresh(recurrent_income)

        logger.info(
            "Recurrent income created successfully",
            extra={
                "user_id": user_id,
                "recurrent_income_id": str(recurrent_income.id),
            },
        )

        return recurrent_income

    @staticmethod
    def update_recurrent_income(
        db: Session,
        recurrent_income: models.RecurrentIncome,
        data: schemas.RecurrentIncomeUpdate,
        user_id: str,
    ) -> models.RecurrentIncome:
        """Update an existing recurrent income.

        Args:
            db: Active database session.
            recurrent_income: The existing recurrent income ORM instance.
            data: Validated update schema (partial).
            user_id: The authenticated user's ID.

        Returns:
            The updated RecurrentIncome.

        Raises:
            PaymentMethodNotFoundExceptionError: If the new payment method does not
                exist or does not belong to the user.
            InvalidRecurrenceConfigExceptionError: If recurrence_config is updated
                without recurrence_type and is invalid for the existing type.
        """
        logger.info(
            "Updating recurrent income",
            extra={"recurrent_income_id": str(recurrent_income.id)},
        )

        update_data = data.model_dump(exclude_unset=True)

        if "payment_method_id" in update_data:
            RecurrentIncomeService._verify_payment_method(
                db, update_data["payment_method_id"], user_id
            )

        # When only recurrence_config is updated (no recurrence_type change),
        # validate the new config against the existing recurrence_type.
        if "recurrence_config" in update_data and "recurrence_type" not in update_data:
            validator = _RECURRENCE_VALIDATORS.get(recurrent_income.recurrence_type)
            if validator:
                try:
                    validator(update_data["recurrence_config"])
                except ValueError as exc:
                    raise InvalidRecurrenceConfigExceptionError(str(exc)) from exc

        for field, value in update_data.items():
            setattr(recurrent_income, field, value)

        db.commit()
        db.refresh(recurrent_income)

        logger.info(
            "Recurrent income updated successfully",
            extra={"recurrent_income_id": str(recurrent_income.id)},
        )

        return recurrent_income

    @staticmethod
    def delete_recurrent_income(
        db: Session,
        recurrent_income: models.RecurrentIncome,
    ) -> None:
        """Soft delete a recurrent income by setting active to False.

        Args:
            db: Active database session.
            recurrent_income: The recurrent income ORM instance to deactivate.
        """
        logger.info(
            "Deactivating recurrent income",
            extra={"recurrent_income_id": str(recurrent_income.id)},
        )

        recurrent_income.active = False
        db.commit()

        logger.info(
            "Recurrent income deactivated successfully",
            extra={"recurrent_income_id": str(recurrent_income.id)},
        )


# Singleton service instance
recurrent_income_service = RecurrentIncomeService()
