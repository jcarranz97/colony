import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.activity.constants import ActivityAction, EntityType
from app.activity.helpers import compute_diff
from app.activity.service import activity_service
from app.auth.models import User
from app.cycles import models as cycle_models
from app.cycles.constants import CurrencyCode as CycleCurrencyCode, CycleStatus
from app.payment_methods import models as pm_models

from . import models, schemas
from .exceptions import (
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
)
from .schemas import _RECURRENCE_VALIDATORS

logger = logging.getLogger(__name__)

# Fields that may be propagated from a recurrent expense template to the
# unpaid cycle expenses generated from it.
_PROPAGATABLE_FIELDS: frozenset[str] = frozenset(
    {"description", "autopay", "payment_method_id", "base_amount"}
)


def _get_cycle_usd_rate(db: Session, from_currency: str) -> Decimal:
    """Return the most recent exchange rate to convert *from_currency* to USD.

    This is a local read-only helper used only by the propagation path so
    that this module does not need to import ``cycles.service``.

    Args:
        db: Active database session.
        from_currency: Source currency code (e.g. ``"MXN"``).

    Returns:
        Decimal exchange rate.  Returns ``1`` immediately for USD.
    """
    if from_currency in {CycleCurrencyCode.USD.value, CycleCurrencyCode.USD}:
        return Decimal("1")

    rate_row = (
        db.query(cycle_models.ExchangeRate)
        .filter(
            and_(
                cycle_models.ExchangeRate.from_currency == from_currency,
                cycle_models.ExchangeRate.to_currency == CycleCurrencyCode.USD.value,
            )
        )
        .order_by(cycle_models.ExchangeRate.rate_date.desc())
        .first()
    )

    if not rate_row:
        return Decimal("1")

    return rate_row.rate


def _propagate_to_open_cycles(
    db: Session,
    template_id: UUID,
    update_data: dict,
    household_id: UUID,
    actor_user_id: UUID,
) -> schemas.PropagationSummary:
    """Apply propagatable template fields to unpaid expenses in open cycles.

    Queries all active, unpaid ``CycleExpense`` rows linked to *template_id*
    whose parent cycle is not completed, then applies the intersection of
    *update_data* with ``_PROPAGATABLE_FIELDS``.  ``base_amount`` is mapped
    to ``amount`` and ``amount_usd`` is recalculated using the most recent
    exchange rate for the expense's currency.

    Every cycle expense that actually changes is recorded in the activity log
    (one ``updated`` event per expense, scoped to its cycle) so the change is
    visible from each affected cycle expense's activity feed.

    Flushes but does **not** commit — the caller owns the transaction.

    Args:
        db: Active database session.
        template_id: UUID of the recurrent expense template.
        update_data: Dict of field→value pairs from the template update.
        household_id: Household that owns the template and its cycle expenses.
        actor_user_id: User performing the update (recorded in activity log).

    Returns:
        A :class:`schemas.PropagationSummary` with the total number of cycle
        expenses updated and a per-cycle breakdown.
    """
    propagatable = {k: v for k, v in update_data.items() if k in _PROPAGATABLE_FIELDS}
    if not propagatable:
        return schemas.PropagationSummary(total_updated=0, cycles=[])

    # Remap template field name to the cycle-expense column name
    amount_value = propagatable.pop("base_amount", None)
    if amount_value is not None:
        propagatable["amount"] = amount_value

    # Fields whose before/after state should be tracked in the activity diff.
    tracked_fields = list(propagatable)
    if "amount" in propagatable:
        tracked_fields.append("amount_usd")

    expenses = (
        db.query(cycle_models.CycleExpense)
        .join(
            cycle_models.Cycle,
            cycle_models.CycleExpense.cycle_id == cycle_models.Cycle.id,
        )
        .filter(
            cycle_models.CycleExpense.template_id == template_id,
            cycle_models.CycleExpense.paid.is_(False),
            cycle_models.CycleExpense.active.is_(True),
            cycle_models.Cycle.status != CycleStatus.COMPLETED,
            cycle_models.Cycle.active.is_(True),
        )
        .all()
    )

    # Per-cycle breakdown so the caller can report exactly what changed.
    cycle_counts: dict[UUID, int] = {}
    cycle_names: dict[UUID, str] = {}
    total_updated = 0
    for expense in expenses:
        before = {field: getattr(expense, field) for field in tracked_fields}
        for field, value in propagatable.items():
            setattr(expense, field, value)
        if "amount" in propagatable:
            rate = _get_cycle_usd_rate(db, str(expense.currency.value))
            expense.amount_usd = (expense.amount * rate).quantize(Decimal("0.01"))
        after = {field: getattr(expense, field) for field in tracked_fields}

        diff = compute_diff(before, after)
        if not diff:
            # Values were already identical — nothing to record or count.
            continue

        activity_service.record(
            db,
            household_id=household_id,
            entity_type=EntityType.CYCLE_EXPENSE,
            entity_id=expense.id,
            cycle_id=expense.cycle_id,
            actor_user_id=actor_user_id,
            action=ActivityAction.UPDATED,
            changes=diff,
        )
        total_updated += 1
        cycle_counts[expense.cycle_id] = cycle_counts.get(expense.cycle_id, 0) + 1
        cycle_names[expense.cycle_id] = expense.cycle.name

    return schemas.PropagationSummary(
        total_updated=total_updated,
        cycles=[
            schemas.CyclePropagationResult(
                cycle_id=cycle_id,
                cycle_name=cycle_names[cycle_id],
                updated_count=count,
            )
            for cycle_id, count in cycle_counts.items()
        ],
    )


class RecurrentExpenseService:
    """Recurrent expense business logic service."""

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
    def get_recurrent_expenses(
        db: Session,
        household_id: str,
        active: bool | None = None,
        category: str | None = None,
        currency: str | None = None,
    ) -> list[models.RecurrentExpense]:
        """List recurrent expenses for a household with optional filters.

        Args:
            db: Active database session.
            household_id: The active household's ID.
            active: Optional filter by active status.
            category: Optional filter by expense category.
            currency: Optional filter by currency code.

        Returns:
            List of matching recurrent expenses ordered by created_at descending.
        """
        query = db.query(models.RecurrentExpense).filter(
            models.RecurrentExpense.household_id == household_id
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
        household_id: str,
    ) -> models.RecurrentExpense | None:
        """Get a single recurrent expense verifying it belongs to the household.

        Args:
            db: Active database session.
            recurrent_expense_id: The recurrent expense UUID as a string.
            household_id: The active household's ID.

        Returns:
            The RecurrentExpense if found and in household, else None.
        """
        return (
            db.query(models.RecurrentExpense)
            .filter(
                and_(
                    models.RecurrentExpense.id == recurrent_expense_id,
                    models.RecurrentExpense.household_id == household_id,
                )
            )
            .first()
        )

    @staticmethod
    def create_recurrent_expense(
        db: Session,
        data: schemas.RecurrentExpenseCreate,
        household_id: str,
        actor: User,
    ) -> models.RecurrentExpense:
        """Create a new recurrent expense for a household.

        Args:
            db: Active database session.
            data: Validated creation schema.
            household_id: The active household's ID.
            actor: The user performing the creation (recorded in activity log).

        Returns:
            The newly created RecurrentExpense.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method is invalid.
        """
        logger.info(
            "Creating recurrent expense",
            extra={
                "household_id": household_id,
                "description": data.description,
            },
        )

        RecurrentExpenseService._verify_payment_method(
            db, data.payment_method_id, household_id
        )

        recurrent_expense = models.RecurrentExpense(
            household_id=household_id,
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
        db.flush()

        activity_service.record(
            db,
            household_id=recurrent_expense.household_id,
            entity_type=EntityType.RECURRENT_EXPENSE,
            entity_id=recurrent_expense.id,
            actor_user_id=actor.id,
            action=ActivityAction.CREATED,
        )

        db.commit()
        db.refresh(recurrent_expense)

        logger.info(
            "Recurrent expense created",
            extra={
                "household_id": household_id,
                "recurrent_expense_id": str(recurrent_expense.id),
            },
        )

        return recurrent_expense

    @staticmethod
    def update_recurrent_expense(
        db: Session,
        recurrent_expense: models.RecurrentExpense,
        data: schemas.RecurrentExpenseUpdate,
        household_id: str,
        actor: User,
    ) -> tuple[models.RecurrentExpense, schemas.PropagationSummary | None]:
        """Update an existing recurrent expense.

        Args:
            db: Active database session.
            recurrent_expense: The existing recurrent expense ORM instance.
            data: Validated update schema (partial).
            household_id: The active household's ID.
            actor: The user performing the update (recorded in activity log).

        Returns:
            A tuple of the updated RecurrentExpense and, when propagation was
            requested, a :class:`schemas.PropagationSummary` describing which
            open-cycle expenses were updated (``None`` otherwise).

        Raises:
            PaymentMethodNotFoundExceptionError: If the new payment method is invalid.
            InvalidRecurrenceConfigExceptionError: If recurrence_config is invalid.
        """
        logger.info(
            "Updating recurrent expense",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )

        update_data = data.model_dump(exclude_unset=True)

        # Strip control flag — not a model field
        should_propagate = update_data.pop("propagate_to_open_cycles", False)

        if "payment_method_id" in update_data:
            RecurrentExpenseService._verify_payment_method(
                db, update_data["payment_method_id"], household_id
            )

        if "recurrence_config" in update_data and "recurrence_type" not in update_data:
            validator = _RECURRENCE_VALIDATORS.get(recurrent_expense.recurrence_type)
            if validator:
                try:
                    validator(update_data["recurrence_config"])
                except ValueError as exc:
                    raise InvalidRecurrenceConfigExceptionError(str(exc)) from exc

        before = {field: getattr(recurrent_expense, field) for field in update_data}

        for field, value in update_data.items():
            setattr(recurrent_expense, field, value)

        db.flush()

        after = {field: getattr(recurrent_expense, field) for field in update_data}
        diff = compute_diff(before, after)
        if diff:
            action = ActivityAction.UPDATED
            if "active" in diff and len(diff) == 1:
                action = (
                    ActivityAction.REACTIVATED
                    if diff["active"]["to"]
                    else ActivityAction.DEACTIVATED
                )
            activity_service.record(
                db,
                household_id=recurrent_expense.household_id,
                entity_type=EntityType.RECURRENT_EXPENSE,
                entity_id=recurrent_expense.id,
                actor_user_id=actor.id,
                action=action,
                changes=diff,
            )

        propagation: schemas.PropagationSummary | None = None
        if should_propagate:
            propagation = _propagate_to_open_cycles(
                db,
                template_id=recurrent_expense.id,
                update_data=update_data,
                household_id=recurrent_expense.household_id,
                actor_user_id=actor.id,
            )
            logger.info(
                "Propagated template fields to open cycle expenses",
                extra={
                    "recurrent_expense_id": str(recurrent_expense.id),
                    "propagated_count": propagation.total_updated,
                },
            )

        db.commit()
        db.refresh(recurrent_expense)

        logger.info(
            "Recurrent expense updated",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )

        return recurrent_expense, propagation

    @staticmethod
    def delete_recurrent_expense(
        db: Session,
        recurrent_expense: models.RecurrentExpense,
        actor: User,
    ) -> None:
        """Soft delete a recurrent expense by setting active to False.

        Args:
            db: Active database session.
            recurrent_expense: The recurrent expense ORM instance to deactivate.
            actor: The user performing the deletion (recorded in activity log).
        """
        logger.info(
            "Deactivating recurrent expense",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )

        recurrent_expense.active = False
        db.flush()

        activity_service.record(
            db,
            household_id=recurrent_expense.household_id,
            entity_type=EntityType.RECURRENT_EXPENSE,
            entity_id=recurrent_expense.id,
            actor_user_id=actor.id,
            action=ActivityAction.DEACTIVATED,
        )

        db.commit()

        logger.info(
            "Recurrent expense deactivated",
            extra={"recurrent_expense_id": str(recurrent_expense.id)},
        )


recurrent_expense_service = RecurrentExpenseService()
