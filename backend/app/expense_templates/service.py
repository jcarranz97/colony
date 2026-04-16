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


class ExpenseTemplateService:
    """Expense template business logic service."""

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
    def get_expense_templates(
        db: Session,
        user_id: str,
        active: bool | None = None,
        category: str | None = None,
        currency: str | None = None,
    ) -> list[models.ExpenseTemplate]:
        """List expense templates for a user with optional filters.

        Args:
            db: Active database session.
            user_id: The authenticated user's ID.
            active: Optional filter by active status.
            category: Optional filter by expense category.
            currency: Optional filter by currency code.

        Returns:
            List of matching expense templates ordered by created_at descending.
        """
        query = db.query(models.ExpenseTemplate).filter(
            models.ExpenseTemplate.user_id == user_id
        )

        if active is not None:
            query = query.filter(models.ExpenseTemplate.active == active)

        if category:
            query = query.filter(models.ExpenseTemplate.category == category)

        if currency:
            query = query.filter(models.ExpenseTemplate.currency == currency)

        return query.order_by(models.ExpenseTemplate.created_at.desc()).all()

    @staticmethod
    def get_expense_template_by_id(
        db: Session,
        template_id: str,
        user_id: str,
    ) -> models.ExpenseTemplate | None:
        """Get a single expense template verifying ownership.

        Args:
            db: Active database session.
            template_id: The template UUID as a string.
            user_id: The authenticated user's ID.

        Returns:
            The ExpenseTemplate if found and owned by user, else None.
        """
        return (
            db.query(models.ExpenseTemplate)
            .filter(
                and_(
                    models.ExpenseTemplate.id == template_id,
                    models.ExpenseTemplate.user_id == user_id,
                )
            )
            .first()
        )

    @staticmethod
    def create_expense_template(
        db: Session,
        data: schemas.ExpenseTemplateCreate,
        user_id: str,
    ) -> models.ExpenseTemplate:
        """Create a new expense template.

        Args:
            db: Active database session.
            data: Validated creation schema.
            user_id: The authenticated user's ID.

        Returns:
            The newly created ExpenseTemplate.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method does not
                exist or does not belong to the user.
        """
        logger.info(
            "Creating expense template",
            extra={"user_id": user_id, "description": data.description},
        )

        ExpenseTemplateService._verify_payment_method(
            db, data.payment_method_id, user_id
        )

        template = models.ExpenseTemplate(
            user_id=user_id,
            payment_method_id=data.payment_method_id,
            description=data.description,
            currency=data.currency,
            base_amount=data.base_amount,
            category=data.category,
            recurrence_type=data.recurrence_type,
            recurrence_config=data.recurrence_config,
            reference_date=data.reference_date,
            autopay_info=data.autopay_info,
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(
            "Expense template created successfully",
            extra={"user_id": user_id, "template_id": str(template.id)},
        )

        return template

    @staticmethod
    def update_expense_template(
        db: Session,
        template: models.ExpenseTemplate,
        data: schemas.ExpenseTemplateUpdate,
        user_id: str,
    ) -> models.ExpenseTemplate:
        """Update an existing expense template.

        Args:
            db: Active database session.
            template: The existing template ORM instance.
            data: Validated update schema (partial).
            user_id: The authenticated user's ID.

        Returns:
            The updated ExpenseTemplate.

        Raises:
            PaymentMethodNotFoundExceptionError: If the new payment method does not
                exist or does not belong to the user.
            InvalidRecurrenceConfigExceptionError: If recurrence_config is updated
                without recurrence_type and is invalid for the existing type.
        """
        logger.info(
            "Updating expense template",
            extra={"template_id": str(template.id)},
        )

        update_data = data.model_dump(exclude_unset=True)

        if "payment_method_id" in update_data:
            ExpenseTemplateService._verify_payment_method(
                db, update_data["payment_method_id"], user_id
            )

        # When only recurrence_config is updated (no recurrence_type change),
        # validate the new config against the template's existing recurrence_type.
        if "recurrence_config" in update_data and "recurrence_type" not in update_data:
            validator = _RECURRENCE_VALIDATORS.get(template.recurrence_type)
            if validator:
                try:
                    validator(update_data["recurrence_config"])
                except ValueError as exc:
                    raise InvalidRecurrenceConfigExceptionError(str(exc)) from exc

        for field, value in update_data.items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)

        logger.info(
            "Expense template updated successfully",
            extra={"template_id": str(template.id)},
        )

        return template

    @staticmethod
    def delete_expense_template(
        db: Session,
        template: models.ExpenseTemplate,
    ) -> None:
        """Soft delete an expense template by setting active to False.

        Args:
            db: Active database session.
            template: The template ORM instance to deactivate.
        """
        logger.info(
            "Deactivating expense template",
            extra={"template_id": str(template.id)},
        )

        template.active = False
        db.commit()

        logger.info(
            "Expense template deactivated successfully",
            extra={"template_id": str(template.id)},
        )


# Singleton service instance
expense_template_service = ExpenseTemplateService()
