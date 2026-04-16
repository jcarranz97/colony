"""Business logic for expense cycles and cycle expenses."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.expense_templates import models as template_models
from app.payment_methods import models as pm_models

from . import models, schemas
from .constants import CurrencyCode, ExpenseCategory, ExpenseStatus
from .exceptions import (
    CycleGenerationExceptionError,
    CycleNameExistsExceptionError,
    ExchangeRateNotFoundExceptionError,
    PaymentMethodNotFoundExceptionError,
)
from .utils import calculate_occurrences

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_usd_rate(db: Session, from_currency: str) -> Decimal:
    """Return the most recent exchange rate to convert *from_currency* to USD.

    If *from_currency* is already USD the identity rate ``1`` is returned
    immediately without a database query.

    Args:
        db: Active database session.
        from_currency: Source currency code (e.g. ``"MXN"``).

    Returns:
        Decimal exchange rate to multiply native amounts by.

    Raises:
        ExchangeRateNotFoundExceptionError: If no rate exists for the pair.
    """
    if from_currency in {CurrencyCode.USD.value, CurrencyCode.USD}:
        return Decimal("1")

    rate_row = (
        db.query(models.ExchangeRate)
        .filter(
            and_(
                models.ExchangeRate.from_currency == from_currency,
                models.ExchangeRate.to_currency == CurrencyCode.USD.value,
            )
        )
        .order_by(models.ExchangeRate.rate_date.desc())
        .first()
    )

    if not rate_row:
        raise ExchangeRateNotFoundExceptionError(str(from_currency), "USD")

    return rate_row.rate


def _recalculate_remaining_balance(
    db: Session,
    cycle: models.Cycle,
) -> None:
    """Recalculate and persist ``remaining_balance`` on *cycle*.

    The balance is ``income_amount`` minus the sum of ``amount_usd`` for all
    active, non-cancelled expenses in the cycle.

    Args:
        db: Active database session.
        cycle: The Cycle ORM instance to update.
    """
    total_usd = sum(
        e.amount_usd
        for e in cycle.expenses
        if e.active and e.status != ExpenseStatus.CANCELLED
    ) or Decimal("0")
    cycle.remaining_balance = cycle.income_amount - total_usd
    db.flush()


def _verify_payment_method(
    db: Session, payment_method_id: UUID, user_id: str
) -> pm_models.PaymentMethod:
    """Verify a payment method exists and belongs to the user.

    Args:
        db: Active database session.
        payment_method_id: UUID of the payment method to verify.
        user_id: The authenticated user's ID.

    Returns:
        The active PaymentMethod instance.

    Raises:
        PaymentMethodNotFoundExceptionError: If not found or inactive.
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


# ---------------------------------------------------------------------------
# Cycle service
# ---------------------------------------------------------------------------


class CycleService:
    """CRUD and business logic for expense cycles."""

    @staticmethod
    def get_cycles(
        db: Session,
        user_id: str,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[models.Cycle], int]:
        """Return a paginated list of cycles for *user_id*.

        Args:
            db: Active database session.
            user_id: The authenticated user's ID.
            status: Optional filter by cycle status.
            page: 1-based page number.
            per_page: Maximum items per page.

        Returns:
            Tuple of (list of Cycle instances, total count).
        """
        query = (
            db.query(models.Cycle)
            .filter(
                and_(
                    models.Cycle.user_id == user_id,
                    models.Cycle.active.is_(True),
                )
            )
            .options(selectinload(models.Cycle.expenses))
        )

        if status:
            query = query.filter(models.Cycle.status == status)

        total = query.count()
        cycles = (
            query.order_by(models.Cycle.start_date.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return cycles, total

    @staticmethod
    def get_cycle_by_id(
        db: Session, cycle_id: str, user_id: str
    ) -> models.Cycle | None:
        """Return a single active cycle owned by *user_id*.

        Args:
            db: Active database session.
            cycle_id: UUID string of the cycle to fetch.
            user_id: The authenticated user's ID.

        Returns:
            The Cycle instance, or None if not found / not owned.
        """
        return (
            db.query(models.Cycle)
            .filter(
                and_(
                    models.Cycle.id == cycle_id,
                    models.Cycle.user_id == user_id,
                    models.Cycle.active.is_(True),
                )
            )
            .options(selectinload(models.Cycle.expenses))
            .first()
        )

    @staticmethod
    def create_cycle(
        db: Session,
        data: schemas.CycleCreate,
        user_id: str,
    ) -> models.Cycle:
        """Create a new cycle and optionally generate expenses from templates.

        When ``data.generate_from_templates`` is True all active expense
        templates for the user are inspected and occurrences that fall within
        the new cycle's date range are created as CycleExpense records.

        Args:
            db: Active database session.
            data: Validated cycle creation schema.
            user_id: The authenticated user's ID.

        Returns:
            The newly created Cycle instance with expenses loaded.

        Raises:
            CycleNameExistsExceptionError: If a cycle with the same name exists.
            CycleGenerationExceptionError: If template generation fails.
        """
        logger.info(
            "Creating cycle",
            extra={"user_id": user_id, "name": data.name},
        )

        cycle = models.Cycle(
            user_id=user_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            income_amount=data.income_amount,
            remaining_balance=data.income_amount,
            status="draft",
        )

        try:
            db.add(cycle)
            db.flush()  # populate cycle.id
        except IntegrityError as exc:
            db.rollback()
            logger.warning(
                "Cycle name conflict",
                extra={"user_id": user_id, "name": data.name},
            )
            raise CycleNameExistsExceptionError(data.name) from exc

        if data.generate_from_templates:
            CycleService._generate_expenses_from_templates(db, cycle, user_id)

        _recalculate_remaining_balance(db, cycle)
        db.commit()
        db.refresh(cycle)

        # Ensure expenses relationship is loaded after commit
        db.query(models.Cycle).options(selectinload(models.Cycle.expenses)).filter(
            models.Cycle.id == cycle.id
        ).first()

        logger.info(
            "Cycle created",
            extra={"user_id": user_id, "cycle_id": str(cycle.id)},
        )
        return cycle

    @staticmethod
    def _generate_expenses_from_templates(
        db: Session,
        cycle: models.Cycle,
        user_id: str,
    ) -> None:
        """Generate CycleExpense rows from the user's active templates.

        For each active template, calculates all recurrence dates within the
        cycle period and inserts a CycleExpense for each occurrence.

        Args:
            db: Active database session.
            cycle: The Cycle instance to attach expenses to.
            user_id: The authenticated user's ID.

        Raises:
            CycleGenerationExceptionError: If an exchange rate is unavailable.
        """
        templates = (
            db.query(template_models.ExpenseTemplate)
            .filter(
                and_(
                    template_models.ExpenseTemplate.user_id == user_id,
                    template_models.ExpenseTemplate.active.is_(True),
                )
            )
            .all()
        )

        for template in templates:
            try:
                occurrence_dates = calculate_occurrences(
                    recurrence_type=template.recurrence_type.value,
                    recurrence_config=template.recurrence_config,
                    reference_date=template.reference_date,
                    cycle_start=cycle.start_date,
                    cycle_end=cycle.end_date,
                )
            except (ValueError, KeyError) as exc:
                logger.warning(
                    "Skipping template due to recurrence error",
                    extra={
                        "template_id": str(template.id),
                        "error": str(exc),
                    },
                )
                continue

            for occurrence_date in occurrence_dates:
                try:
                    rate = _get_usd_rate(db, str(template.currency.value))
                except ExchangeRateNotFoundExceptionError as exc:
                    raise CycleGenerationExceptionError(
                        f"Cannot generate expenses: {exc.message}"
                    ) from exc

                amount_usd = (template.base_amount * rate).quantize(Decimal("0.01"))

                expense = models.CycleExpense(
                    cycle_id=cycle.id,
                    template_id=template.id,
                    payment_method_id=template.payment_method_id,
                    description=template.description,
                    currency=template.currency,
                    amount=template.base_amount,
                    amount_usd=amount_usd,
                    due_date=occurrence_date,
                    category=template.category,
                    autopay_info=template.autopay_info,
                    status=ExpenseStatus.PENDING,
                )
                db.add(expense)

    @staticmethod
    def update_cycle(
        db: Session,
        cycle: models.Cycle,
        data: schemas.CycleUpdate,
    ) -> models.Cycle:
        """Apply a partial update to *cycle*.

        When ``income_amount`` changes, ``remaining_balance`` is recalculated
        to keep it consistent with the new income figure.

        Args:
            db: Active database session.
            cycle: The Cycle ORM instance to update.
            data: Validated partial update schema.

        Returns:
            The updated Cycle instance.

        Raises:
            CycleNameExistsExceptionError: If the new name is already taken.
        """
        logger.info("Updating cycle", extra={"cycle_id": str(cycle.id)})

        update_data = data.model_dump(exclude_unset=True)

        try:
            for field, value in update_data.items():
                setattr(cycle, field, value)
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise CycleNameExistsExceptionError(data.name or cycle.name) from exc

        if "income_amount" in update_data:
            _recalculate_remaining_balance(db, cycle)

        db.commit()
        db.refresh(cycle)

        logger.info("Cycle updated", extra={"cycle_id": str(cycle.id)})
        return cycle

    @staticmethod
    def build_cycle_summary(cycle: models.Cycle) -> schemas.CycleSummaryResponse:
        """Build a detailed financial summary for *cycle*.

        Computes financial totals, per-payment-method breakdowns, per-currency
        stats, and a status count — all from the cycle's already-loaded
        expenses relationship.

        Args:
            cycle: The Cycle ORM instance with expenses loaded.

        Returns:
            CycleSummaryResponse schema instance.
        """
        active = [e for e in cycle.expenses if e.active]
        countable = [e for e in active if e.status != ExpenseStatus.CANCELLED]

        # --- Financial totals ------------------------------------------------
        total_usd = sum((e.amount_usd for e in countable), Decimal("0"))
        fixed_usd = sum(
            (e.amount_usd for e in countable if e.category == ExpenseCategory.FIXED),
            Decimal("0"),
        )
        variable_usd = sum(
            (e.amount_usd for e in countable if e.category == ExpenseCategory.VARIABLE),
            Decimal("0"),
        )
        # USD currency → US expenses; MXN → Mexico expenses
        usa_usd = sum(
            (e.amount_usd for e in countable if e.currency == CurrencyCode.USD),
            Decimal("0"),
        )
        mexico_usd = sum(
            (e.amount_usd for e in countable if e.currency == CurrencyCode.MXN),
            Decimal("0"),
        )
        financial = schemas.FinancialSummary(
            total_expenses_usd=total_usd,
            fixed_expenses_usd=fixed_usd,
            variable_expenses_usd=variable_usd,
            usa_expenses_usd=usa_usd,
            mexico_expenses_usd=mexico_usd,
            net_balance=cycle.income_amount - total_usd,
        )

        # --- By payment method -----------------------------------------------
        pm_groups: dict[str, list[models.CycleExpense]] = {}
        for e in countable:
            pm_groups.setdefault(str(e.payment_method_id), []).append(e)

        by_payment_method: list[schemas.PaymentMethodBreakdown] = []
        for expenses in pm_groups.values():
            pm = expenses[0].payment_method
            by_payment_method.append(
                schemas.PaymentMethodBreakdown(
                    payment_method=schemas.PaymentMethodSummary.model_validate(pm),
                    total_amount=sum((e.amount_usd for e in expenses), Decimal("0")),
                    paid_amount=sum(
                        (e.amount_usd for e in expenses if e.paid), Decimal("0")
                    ),
                    pending_amount=sum(
                        (e.amount_usd for e in expenses if not e.paid), Decimal("0")
                    ),
                    expense_count=len(expenses),
                )
            )

        # --- By currency -----------------------------------------------------
        currency_groups: dict[str, list[models.CycleExpense]] = {}
        for e in countable:
            key = e.currency.value if hasattr(e.currency, "value") else str(e.currency)
            currency_groups.setdefault(key, []).append(e)

        by_currency: dict[str, schemas.CurrencyStats] = {}
        for currency_code, expenses in currency_groups.items():
            native_total = sum((e.amount for e in expenses), Decimal("0"))
            usd_total = sum((e.amount_usd for e in expenses), Decimal("0"))
            by_currency[currency_code] = schemas.CurrencyStats(
                total_amount=native_total,
                total_amount_usd=(
                    usd_total if currency_code != CurrencyCode.USD.value else None
                ),
                expense_count=len(expenses),
            )

        # --- Status breakdown ------------------------------------------------
        status_breakdown = schemas.StatusBreakdown(
            pending=sum(1 for e in active if e.status == ExpenseStatus.PENDING),
            paid=sum(1 for e in active if e.status == ExpenseStatus.PAID),
            overdue=sum(1 for e in active if e.status == ExpenseStatus.OVERDUE),
            cancelled=sum(1 for e in active if e.status == ExpenseStatus.CANCELLED),
        )

        return schemas.CycleSummaryResponse(
            cycle=schemas.CycleInfo.model_validate(cycle),
            financial=financial,
            by_payment_method=by_payment_method,
            by_currency=by_currency,
            status_breakdown=status_breakdown,
        )

    @staticmethod
    def delete_cycle(db: Session, cycle: models.Cycle) -> None:
        """Soft-delete a cycle and all its active expenses.

        Args:
            db: Active database session.
            cycle: The Cycle ORM instance to deactivate.
        """
        logger.info("Deleting cycle", extra={"cycle_id": str(cycle.id)})

        for expense in cycle.expenses:
            expense.active = False

        cycle.active = False
        db.commit()

        logger.info("Cycle deleted", extra={"cycle_id": str(cycle.id)})


# ---------------------------------------------------------------------------
# Cycle expense service
# ---------------------------------------------------------------------------


class CycleExpenseService:
    """CRUD and business logic for individual expenses within a cycle."""

    @staticmethod
    def get_expenses(
        db: Session,
        cycle_id: str,
        status: str | None = None,
        category: str | None = None,
        currency: str | None = None,
        payment_method_id: str | None = None,
    ) -> list[models.CycleExpense]:
        """Return all active expenses for a cycle with optional filters.

        Args:
            db: Active database session.
            cycle_id: UUID string of the parent cycle.
            status: Optional filter by expense status.
            category: Optional filter by expense category.
            currency: Optional filter by currency code.
            payment_method_id: Optional filter by payment method UUID.

        Returns:
            List of matching CycleExpense instances.
        """
        query = db.query(models.CycleExpense).filter(
            and_(
                models.CycleExpense.cycle_id == cycle_id,
                models.CycleExpense.active.is_(True),
            )
        )

        if status:
            query = query.filter(models.CycleExpense.status == status)
        if category:
            query = query.filter(models.CycleExpense.category == category)
        if currency:
            query = query.filter(models.CycleExpense.currency == currency)
        if payment_method_id:
            query = query.filter(
                models.CycleExpense.payment_method_id == payment_method_id
            )

        return query.order_by(models.CycleExpense.due_date.asc()).all()

    @staticmethod
    def get_expense_by_id(
        db: Session, expense_id: str, cycle_id: str
    ) -> models.CycleExpense | None:
        """Return a single active expense that belongs to *cycle_id*.

        Args:
            db: Active database session.
            expense_id: UUID string of the expense.
            cycle_id: UUID string of the parent cycle.

        Returns:
            The CycleExpense instance, or None if not found.
        """
        return (
            db.query(models.CycleExpense)
            .filter(
                and_(
                    models.CycleExpense.id == expense_id,
                    models.CycleExpense.cycle_id == cycle_id,
                    models.CycleExpense.active.is_(True),
                )
            )
            .first()
        )

    @staticmethod
    def create_expense(
        db: Session,
        cycle: models.Cycle,
        data: schemas.CycleExpenseCreate,
        user_id: str,
    ) -> models.CycleExpense:
        """Add a manual expense to *cycle*.

        Args:
            db: Active database session.
            cycle: The parent Cycle ORM instance.
            data: Validated expense creation schema.
            user_id: The authenticated user's ID.

        Returns:
            The newly created CycleExpense instance.

        Raises:
            PaymentMethodNotFoundExceptionError: If the payment method is invalid.
            ExchangeRateNotFoundExceptionError: If no MXN→USD rate is available.
        """
        logger.info(
            "Creating cycle expense",
            extra={"cycle_id": str(cycle.id), "description": data.description},
        )

        _verify_payment_method(db, data.payment_method_id, user_id)

        rate = _get_usd_rate(db, data.currency.value)
        amount_usd = (data.amount * rate).quantize(Decimal("0.01"))

        expense = models.CycleExpense(
            cycle_id=cycle.id,
            payment_method_id=data.payment_method_id,
            description=data.description,
            currency=data.currency,
            amount=data.amount,
            amount_usd=amount_usd,
            due_date=data.due_date,
            category=data.category,
            comments=data.comments,
            autopay_info=data.autopay_info,
            status=ExpenseStatus.PENDING,
        )

        db.add(expense)
        db.flush()

        _recalculate_remaining_balance(db, cycle)
        db.commit()
        db.refresh(expense)

        logger.info(
            "Cycle expense created",
            extra={"cycle_id": str(cycle.id), "expense_id": str(expense.id)},
        )
        return expense

    @staticmethod
    def update_expense(
        db: Session,
        cycle: models.Cycle,
        expense: models.CycleExpense,
        data: schemas.CycleExpenseUpdate,
    ) -> models.CycleExpense:
        """Apply a partial update to *expense*.

        When ``paid`` is set to True and ``paid_at`` is not provided, the
        current UTC timestamp is used.  ``status`` is kept in sync with
        ``paid``: setting ``paid=True`` automatically sets ``status="paid"``.

        Args:
            db: Active database session.
            cycle: Parent Cycle ORM instance (used for balance recalculation).
            expense: The CycleExpense ORM instance to update.
            data: Validated partial update schema.

        Returns:
            The updated CycleExpense instance.
        """
        logger.info("Updating cycle expense", extra={"expense_id": str(expense.id)})

        update_data = data.model_dump(exclude_unset=True)

        # Keep paid / status / paid_at in sync
        if "paid" in update_data:
            if update_data["paid"] and "paid_at" not in update_data:
                update_data["paid_at"] = datetime.now(tz=UTC)
            if update_data["paid"] and "status" not in update_data:
                update_data["status"] = ExpenseStatus.PAID
            elif not update_data["paid"] and "status" not in update_data:
                update_data["status"] = ExpenseStatus.PENDING
                update_data["paid_at"] = None

        for field, value in update_data.items():
            setattr(expense, field, value)

        if "amount" in update_data:
            # amount_usd needs to be recalculated when native amount changes
            rate = _get_usd_rate(db, str(expense.currency.value))
            expense.amount_usd = (expense.amount * rate).quantize(Decimal("0.01"))
            _recalculate_remaining_balance(db, cycle)

        if "status" in update_data and update_data["status"] == ExpenseStatus.CANCELLED:
            _recalculate_remaining_balance(db, cycle)

        db.commit()
        db.refresh(expense)

        logger.info("Cycle expense updated", extra={"expense_id": str(expense.id)})
        return expense

    @staticmethod
    def delete_expense(
        db: Session,
        cycle: models.Cycle,
        expense: models.CycleExpense,
    ) -> None:
        """Soft-delete an expense and update the cycle's remaining balance.

        Args:
            db: Active database session.
            cycle: Parent Cycle ORM instance.
            expense: The CycleExpense ORM instance to deactivate.
        """
        logger.info("Deleting cycle expense", extra={"expense_id": str(expense.id)})

        expense.active = False
        db.flush()

        _recalculate_remaining_balance(db, cycle)
        db.commit()

        logger.info("Cycle expense deleted", extra={"expense_id": str(expense.id)})

    @staticmethod
    def build_expenses_summary(
        expenses: list[models.CycleExpense],
    ) -> schemas.ExpensesSummary:
        """Build an aggregated summary for a filtered list of expenses.

        Args:
            expenses: The list of CycleExpense instances to summarise.

        Returns:
            ExpensesSummary schema instance.
        """
        total_usd = sum((e.amount_usd for e in expenses), Decimal("0"))
        fixed = sum(
            (e.amount_usd for e in expenses if e.category == ExpenseCategory.FIXED),
            Decimal("0"),
        )
        variable = sum(
            (e.amount_usd for e in expenses if e.category == ExpenseCategory.VARIABLE),
            Decimal("0"),
        )
        paid = sum(
            (e.amount_usd for e in expenses if e.paid),
            Decimal("0"),
        )
        pending = sum(
            (e.amount_usd for e in expenses if not e.paid),
            Decimal("0"),
        )
        return schemas.ExpensesSummary(
            total_amount_usd=total_usd,
            fixed_amount=fixed,
            variable_amount=variable,
            paid_amount=paid,
            pending_amount=pending,
            total_count=len(expenses),
        )


# Singleton service instances
cycle_service = CycleService()
cycle_expense_service = CycleExpenseService()
