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
        household_id: str,
    ) -> pm_models.PaymentMethod:
        """Verify a payment method exists and belongs to the household.

        Args:
            db: Active database session.
            payment_method_id: UUID of the payment method to verify.
            household_id: The active household's ID.

        Returns:
            The PaymentMethod instance.

        Raises:
            PaymentMethodNotFoundExceptionError: If not found or not in household.
        """
        pm = (
            db.query(pm_models.PaymentMethod)
            .filter(
                and_(
                    pm_models.PaymentMethod.id == payment_method_id,
                    pm_models.PaymentMethod.household_id == household_id,
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
        household_id: str,
        active: bool | None = None,
        currency: str | None = None,
    ) -> list[models.RecurrentIncome]:
        """List recurrent incomes for a household with optional filters.

        Args:
            db: Active database session.
            household_id: The active household's ID.
            active: Optional filter by active status.
            currency: Optional filter by currency code.

        Returns:
            List of matching recurrent incomes ordered by created_at descending.
        """
        query = db.query(models.RecurrentIncome).filter(
            models.RecurrentIncome.household_id == household_id
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
        household_id: str,
    ) -> models.RecurrentIncome | None:
        """Get a single recurrent income verifying it belongs to the household.

        Args:
            db: Active database session.
            recurrent_income_id: The recurrent income UUID as a string.
            household_id: The active household's ID.

        Returns:
            The RecurrentIncome if found and in household, else None.
        """
        return (
            db.query(models.RecurrentIncome)
            .filter(
                and_(
                    models.RecurrentIncome.id == recurrent_income_id,
                    models.RecurrentIncome.household_id == household_id,
                )
            )
            .first()
        )

    @staticmethod
    def create_recurrent_income(
        db: Session,
        data: schemas.RecurrentIncomeCreate,
        household_id: str,
    ) -> models.RecurrentIncome:
        """Create a new recurrent income for a household.

        Args:
            db: Active database session.
            data: Validated creation schema.
            household_id: The active household's ID.

        Returns:
            The newly created RecurrentIncome.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method is invalid.
        """
        logger.info(
            "Creating recurrent income",
            extra={
                "household_id": household_id,
                "description": data.description,
            },
        )

        RecurrentIncomeService._verify_payment_method(
            db, data.payment_method_id, household_id
        )

        recurrent_income = models.RecurrentIncome(
            household_id=household_id,
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
            "Recurrent income created",
            extra={
                "household_id": household_id,
                "recurrent_income_id": str(recurrent_income.id),
            },
        )

        return recurrent_income

    @staticmethod
    def update_recurrent_income(
        db: Session,
        recurrent_income: models.RecurrentIncome,
        data: schemas.RecurrentIncomeUpdate,
        household_id: str,
    ) -> models.RecurrentIncome:
        """Update an existing recurrent income.

        Args:
            db: Active database session.
            recurrent_income: The existing recurrent income ORM instance.
            data: Validated update schema (partial).
            household_id: The active household's ID.

        Returns:
            The updated RecurrentIncome.

        Raises:
            PaymentMethodNotFoundExceptionError: If the new payment method is invalid.
            InvalidRecurrenceConfigExceptionError: If recurrence_config is invalid.
        """
        logger.info(
            "Updating recurrent income",
            extra={"recurrent_income_id": str(recurrent_income.id)},
        )

        update_data = data.model_dump(exclude_unset=True)

        if "payment_method_id" in update_data:
            RecurrentIncomeService._verify_payment_method(
                db, update_data["payment_method_id"], household_id
            )

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
            "Recurrent income updated",
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
            "Recurrent income deactivated",
            extra={"recurrent_income_id": str(recurrent_income.id)},
        )


recurrent_income_service = RecurrentIncomeService()
