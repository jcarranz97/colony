import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.cycles.constants import CurrencyCode as CycleCurrencyCode, CycleStatus
from app.cycles.models import Cycle, CycleExpense
from app.households.models import Household
from app.payment_methods.constants import (
    CurrencyCode as PMCurrencyCode,
    PaymentMethodType,
)
from app.payment_methods.models import PaymentMethod
from app.recurrent_expenses.constants import (
    CurrencyCode,
    ExpenseCategory,
    RecurrenceType,
)
from app.recurrent_expenses.exceptions import (
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
)
from app.recurrent_expenses.models import RecurrentExpense
from app.recurrent_expenses.schemas import (
    RecurrentExpenseCreate,
    RecurrentExpenseUpdate,
)
from app.recurrent_expenses.service import recurrent_expense_service


class TestGetRecurrentExpenses:
    def test_returns_only_household_recurrent_expenses(
        self,
        db,
        test_household,
        other_household,
        test_payment_method,
        other_payment_method,
    ):
        t1 = RecurrentExpense(
            household_id=test_household.id,
            payment_method_id=test_payment_method.id,
            description="My Template",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        t2 = RecurrentExpense(
            household_id=other_household.id,
            payment_method_id=other_payment_method.id,
            description="Other Template",
            currency=CurrencyCode.USD,
            base_amount=Decimal("200.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 15},
            reference_date=date(2024, 12, 15),
        )
        db.add_all([t1, t2])
        db.commit()

        results = recurrent_expense_service.get_recurrent_expenses(
            db, str(test_household.id)
        )
        assert len(results) == 1
        assert results[0].description == "My Template"

    def test_filter_by_active(self, db, test_household, test_payment_method):
        active_t = RecurrentExpense(
            household_id=test_household.id,
            payment_method_id=test_payment_method.id,
            description="Active",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
            active=True,
        )
        inactive_t = RecurrentExpense(
            household_id=test_household.id,
            payment_method_id=test_payment_method.id,
            description="Inactive",
            currency=CurrencyCode.USD,
            base_amount=Decimal("50.00"),
            category=ExpenseCategory.VARIABLE,
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_config={"day_of_week": 1},
            reference_date=date(2024, 12, 1),
            active=False,
        )
        db.add_all([active_t, inactive_t])
        db.commit()

        results = recurrent_expense_service.get_recurrent_expenses(
            db, str(test_household.id), active=True
        )
        assert all(t.active for t in results)
        assert len(results) == 1

    def test_filter_by_category(self, db, test_household, test_payment_method):
        fixed_t = RecurrentExpense(
            household_id=test_household.id,
            payment_method_id=test_payment_method.id,
            description="Fixed",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        variable_t = RecurrentExpense(
            household_id=test_household.id,
            payment_method_id=test_payment_method.id,
            description="Variable",
            currency=CurrencyCode.USD,
            base_amount=Decimal("50.00"),
            category=ExpenseCategory.VARIABLE,
            recurrence_type=RecurrenceType.WEEKLY,
            recurrence_config={"day_of_week": 3},
            reference_date=date(2024, 12, 1),
        )
        db.add_all([fixed_t, variable_t])
        db.commit()

        results = recurrent_expense_service.get_recurrent_expenses(
            db, str(test_household.id), category="fixed"
        )
        assert len(results) == 1
        assert results[0].description == "Fixed"


class TestGetRecurrentExpenseById:
    def test_returns_none_for_other_household(
        self, db, test_household, other_household, test_payment_method
    ):
        recurrent_expense = RecurrentExpense(
            household_id=test_household.id,
            payment_method_id=test_payment_method.id,
            description="Mine",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        db.add(recurrent_expense)
        db.commit()

        result = recurrent_expense_service.get_recurrent_expense_by_id(
            db, str(recurrent_expense.id), str(other_household.id)
        )
        assert result is None

    def test_returns_recurrent_expense_for_owner(
        self, db, test_household, test_template
    ):
        result = recurrent_expense_service.get_recurrent_expense_by_id(
            db, str(test_template.id), str(test_household.id)
        )
        assert result is not None
        assert result.id == test_template.id


class TestCreateRecurrentExpense:
    def test_create_success(self, db, test_household, test_payment_method, test_user):
        data = RecurrentExpenseCreate(
            description="Rent",
            currency=CurrencyCode.USD,
            payment_method_id=test_payment_method.id,
            base_amount=Decimal("1200.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        recurrent_expense = recurrent_expense_service.create_recurrent_expense(
            db, data, str(test_household.id), actor=test_user
        )
        assert recurrent_expense.description == "Rent"
        assert recurrent_expense.active is True

    def test_raises_when_payment_method_not_owned(
        self, db, test_household, other_payment_method, test_user
    ):
        data = RecurrentExpenseCreate(
            description="Rent",
            currency=CurrencyCode.USD,
            payment_method_id=other_payment_method.id,
            base_amount=Decimal("1200.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        with pytest.raises(PaymentMethodNotFoundExceptionError):
            recurrent_expense_service.create_recurrent_expense(
                db, data, str(test_household.id), actor=test_user
            )

    def test_raises_when_payment_method_nonexistent(
        self, db, test_household, test_user
    ):
        data = RecurrentExpenseCreate(
            description="Rent",
            currency=CurrencyCode.USD,
            payment_method_id=uuid.uuid4(),
            base_amount=Decimal("1200.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        with pytest.raises(PaymentMethodNotFoundExceptionError):
            recurrent_expense_service.create_recurrent_expense(
                db, data, str(test_household.id), actor=test_user
            )


class TestUpdateRecurrentExpense:
    def test_partial_update(self, db, test_household, test_template, test_user):
        data = RecurrentExpenseUpdate(description="Updated Groceries")
        updated = recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )
        assert updated.description == "Updated Groceries"
        assert updated.category == test_template.category

    def test_update_recurrence_config_validates_against_existing_type(
        self, db, test_household, test_template, test_user
    ):
        # test_template has recurrence_type=weekly; send invalid config for weekly
        data = RecurrentExpenseUpdate(recurrence_config={"interval_days": 14})
        with pytest.raises(InvalidRecurrenceConfigExceptionError):
            recurrent_expense_service.update_recurrent_expense(
                db, test_template, data, str(test_household.id), actor=test_user
            )

    def test_update_both_recurrence_fields(
        self, db, test_household, test_template, test_user
    ):
        data = RecurrentExpenseUpdate(
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 15},
        )
        updated = recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )
        assert updated.recurrence_type == RecurrenceType.MONTHLY
        assert updated.recurrence_config == {"day_of_month": 15}


class TestDeleteRecurrentExpense:
    def test_soft_delete_sets_active_false(self, db, test_template, test_user):
        assert test_template.active is True
        recurrent_expense_service.delete_recurrent_expense(
            db, test_template, actor=test_user
        )
        db.refresh(test_template)
        assert test_template.active is False

    def test_soft_delete_does_not_remove_record(self, db, test_template, test_user):
        recurrent_expense_id = test_template.id
        recurrent_expense_service.delete_recurrent_expense(
            db, test_template, actor=test_user
        )
        record = (
            db.query(RecurrentExpense)
            .filter(RecurrentExpense.id == recurrent_expense_id)
            .first()
        )
        assert record is not None
        assert record.active is False


# ---------------------------------------------------------------------------
# Helpers for propagation tests
# ---------------------------------------------------------------------------


def _make_cycle(
    db: Session,
    household: Household,
    status: CycleStatus = CycleStatus.ACTIVE,
    active: bool = True,
) -> Cycle:
    cycle = Cycle(
        household_id=household.id,
        name=f"Cycle {uuid.uuid4().hex[:6]}",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        remaining_balance=Decimal("0"),
        status=status,
        active=active,
    )
    db.add(cycle)
    db.flush()
    return cycle


def _make_cycle_expense(
    db: Session,
    cycle: Cycle,
    template: RecurrentExpense,
    payment_method: PaymentMethod,
    paid: bool = False,
    active: bool = True,
) -> CycleExpense:
    expense = CycleExpense(
        cycle_id=cycle.id,
        template_id=template.id,
        payment_method_id=payment_method.id,
        description=template.description,
        currency=CycleCurrencyCode.USD,
        amount=template.base_amount,
        amount_usd=template.base_amount,
        due_date=date(2025, 1, 15),
        category=template.category,
        autopay=template.autopay,
        paid=paid,
        active=active,
    )
    db.add(expense)
    db.flush()
    return expense


# ---------------------------------------------------------------------------
# Propagation tests
# ---------------------------------------------------------------------------


class TestPropagatToOpenCycles:
    """Tests for propagate_to_open_cycles behaviour in update_recurrent_expense."""

    def test_no_propagation_when_flag_false(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        """Default behaviour: cycle expenses are NOT changed."""
        cycle = _make_cycle(db, test_household)
        expense = _make_cycle_expense(db, cycle, test_template, test_payment_method)
        db.commit()

        data = RecurrentExpenseUpdate(description="New Name")
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.description == "Groceries"  # original, unchanged

    def test_propagates_description_to_unpaid_expenses(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        cycle = _make_cycle(db, test_household)
        expense = _make_cycle_expense(db, cycle, test_template, test_payment_method)
        db.commit()

        data = RecurrentExpenseUpdate(
            description="New Groceries",
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.description == "New Groceries"

    def test_propagates_autopay_to_unpaid_expenses(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        cycle = _make_cycle(db, test_household)
        expense = _make_cycle_expense(db, cycle, test_template, test_payment_method)
        db.commit()
        assert expense.autopay is False

        data = RecurrentExpenseUpdate(
            autopay=True,
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.autopay is True

    def test_propagates_amount_and_recalculates_amount_usd(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        cycle = _make_cycle(db, test_household)
        expense = _make_cycle_expense(db, cycle, test_template, test_payment_method)
        db.commit()

        data = RecurrentExpenseUpdate(
            base_amount=Decimal("200.00"),
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        # USD → USD rate is 1; amount_usd should equal the new amount
        assert expense.amount == Decimal("200.00")
        assert expense.amount_usd == Decimal("200.00")

    def test_does_not_touch_paid_expenses(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        cycle = _make_cycle(db, test_household)
        paid_expense = _make_cycle_expense(
            db, cycle, test_template, test_payment_method, paid=True
        )
        db.commit()

        data = RecurrentExpenseUpdate(
            description="Should Not Apply",
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(paid_expense)
        assert paid_expense.description == "Groceries"  # unchanged

    def test_does_not_touch_expenses_in_completed_cycles(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        completed_cycle = _make_cycle(db, test_household, status=CycleStatus.COMPLETED)
        expense = _make_cycle_expense(
            db, completed_cycle, test_template, test_payment_method
        )
        db.commit()

        data = RecurrentExpenseUpdate(
            description="Should Not Apply",
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.description == "Groceries"  # unchanged

    def test_does_not_touch_expenses_in_draft_cycles_false(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        """DRAFT cycles are open (not completed) — expenses SHOULD be updated."""
        draft_cycle = _make_cycle(db, test_household, status=CycleStatus.DRAFT)
        expense = _make_cycle_expense(
            db, draft_cycle, test_template, test_payment_method
        )
        db.commit()

        data = RecurrentExpenseUpdate(
            description="Draft Cycle Update",
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.description == "Draft Cycle Update"

    def test_propagates_payment_method(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        cycle = _make_cycle(db, test_household)
        expense = _make_cycle_expense(db, cycle, test_template, test_payment_method)
        db.commit()

        # Create a second payment method in the same household
        new_pm = PaymentMethod(
            household_id=test_household.id,
            name="New Card",
            method_type=PaymentMethodType.CREDIT,
            default_currency=PMCurrencyCode.USD,
        )
        db.add(new_pm)
        db.commit()

        data = RecurrentExpenseUpdate(
            payment_method_id=new_pm.id,
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.payment_method_id == new_pm.id

    def test_non_propagatable_fields_are_not_applied(
        self,
        db,
        test_household,
        test_template,
        test_payment_method,
        test_user,
    ):
        """category and currency are template-only; cycle expenses stay unchanged."""
        cycle = _make_cycle(db, test_household)
        expense = _make_cycle_expense(db, cycle, test_template, test_payment_method)
        original_category = expense.category
        db.commit()

        data = RecurrentExpenseUpdate(
            category=ExpenseCategory.EXTRA,
            propagate_to_open_cycles=True,
        )
        recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id), actor=test_user
        )

        db.refresh(expense)
        assert expense.category == original_category
