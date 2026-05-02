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


class RecurrentExpenseService:
    """Recurrent expense business logic service."""

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
    def get_recurrent_expenses(
        db: Session,
        user_id: str,
        active: bool | None = None,
        category: str | None = None,
        currency: str | None = None,
    ) -> list[models.RecurrentExpense]:
        """List recurrent expenses for a user with optional filters.

        Args:
            db: Active database session.
            user_id: The authenticated user's ID.
            active: Optional filter by active status.
            category: Optional filter by expense category.
            currency: Optional filter by currency code.

        Returns:
            List of matching recurrent expenses ordered by created_at descending.
        """
        query = db.query(models.RecurrentExpense).filter(
            models.RecurrentExpense.user_id == user_id
        )

        if active is not None:
            query = query.filter(models.RecurrentExpense.active == active)

        if category:
            query = query.filter(models.RecurrentExpense.category == category)

        if currency:
            query = query.filter(models.RecurrentExpense.currency == currency)

        return query.order_by(models.RecurrentExpense.created_at.desc()).all()

    @staticmethod
    def get_recurrent_expense_by_id(
        db: Session,
        recurrent_expense_id: str,
        user_id: str,
    ) -> models.RecurrentExpense | None:
        """Get a single recurrent expense verifying ownership.

        Args:
            db: Active database session.
            recurrent_expense_id: The recurrent expense UUID as a string.
            user_id: The authenticated user's ID.

        Returns:
            The RecurrentExpense if found and owned by user, else None.
        """
        return (
            db.query(models.RecurrentExpense)
            .filter(
                and_(
                    models.RecurrentExpense.id == recurrent_expense_id,
                    models.RecurrentExpense.user_id == user_id,
                )
            )
            .first()
        )

    @staticmethod
    def create_recurrent_expense(
        db: Session,
        data: schemas.RecurrentExpenseCreate,
        user_id: str,
    ) -> models.RecurrentExpense:
        """Create a new recurrent expense.

        Args:
            db: Active database session.
            data: Validated creation schema.
            user_id: The authenticated user's ID.

        Returns:
            The newly created RecurrentExpense.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method does not
                exist or does not belong to the user.
        """
        logger.info(
            "Creating recurrent expense",
            extra={"user_id": user_id, "description": data.description},
        )

        RecurrentExpenseService._verify_payment_method(
            db, data.payment_method_id, user_id
        )

        recurrent_expense = models.RecurrentExpense(
            user_id=user_id,
            payment_method_id=data.payment_method_id,
            description=data.description,
            currency=data.currency,
            base_amount=data.base_amount,
            category=data.category,
            recurrence_type=data.recurrence_type,
            recurrence_config=data.recurrence_config,
            reference_date=data.reference_date,
            autopay=data.autopay,
        )

        db.add(recurrent_expense)
        db.commit()
        db.refresh(recurrent_expense)

        logger.info(
            "Recurrent expense created successfully",
            extra={
                "user_id": user_id,
                "recurrent_expense_id": str(recurrent_expense.id),
            },
        )

        return recurrent_expense

    @staticmethod
    def update_recurrent_expense(
        db: Session,
        recurrent_expense: models.RecurrentExpense,
        data: schemas.RecurrentExpenseUpdate,
        user_id: str,
    ) -> models.RecurrentExpense:
        """Update an existing recurrent expense.

        Args:
            db: Active database session.
            recurrent_expense: The existing recurrent expense ORM instance.
            data: Validated update schema (partial).
            user_id: The authenticated user's ID.

        Returns:
            The updated RecurrentExpense.

        Raises:
            PaymentMethodNotFoundExceptionError: If the new payment method does not
                exist or does not belong to the user.
            InvalidRecurrenceConfigExceptionError: If recurrence_config is updated
                without recurrence_type and is invalid for the existing type.
        """
        logger.info(
            "Updating recurrent expense",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )

        update_data = data.model_dump(exclude_unset=True)

        if "payment_method_id" in update_data:
            RecurrentExpenseService._verify_payment_method(
                db, update_data["payment_method_id"], user_id
            )

        # When only recurrence_config is updated (no recurrence_type change),
        # validate the new config against the existing recurrence_type.
        if "recurrence_config" in update_data and "recurrence_type" not in update_data:
            validator = _RECURRENCE_VALIDATORS.get(recurrent_expense.recurrence_type)
            if validator:
                try:
                    validator(update_data["recurrence_config"])
                except ValueError as exc:
                    raise InvalidRecurrenceConfigExceptionError(str(exc)) from exc

        for field, value in update_data.items():
            setattr(recurrent_expense, field, value)

        db.commit()
        db.refresh(recurrent_expense)

        logger.info(
            "Recurrent expense updated successfully",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )

        return recurrent_expense

    @staticmethod
    def delete_recurrent_expense(
        db: Session,
        recurrent_expense: models.RecurrentExpense,
    ) -> None:
        """Soft delete a recurrent expense by setting active to False.

        Args:
            db: Active database session.
            recurrent_expense: The recurrent expense ORM instance to deactivate.
        """
        logger.info(
            "Deactivating recurrent expense",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )

        recurrent_expense.active = False
        db.commit()

        logger.info(
            "Recurrent expense deactivated successfully",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )


# Singleton service instance
recurrent_expense_service = RecurrentExpenseService()
