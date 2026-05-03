import uuid
from datetime import date
from decimal import Decimal

import pytest

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
    def test_create_success(self, db, test_household, test_payment_method):
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
            db, data, str(test_household.id)
        )
        assert recurrent_expense.description == "Rent"
        assert recurrent_expense.active is True

    def test_raises_when_payment_method_not_owned(
        self, db, test_household, other_payment_method
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
                db, data, str(test_household.id)
            )

    def test_raises_when_payment_method_nonexistent(self, db, test_household):
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
                db, data, str(test_household.id)
            )


class TestUpdateRecurrentExpense:
    def test_partial_update(self, db, test_household, test_template):
        data = RecurrentExpenseUpdate(description="Updated Groceries")
        updated = recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id)
        )
        assert updated.description == "Updated Groceries"
        assert updated.category == test_template.category

    def test_update_recurrence_config_validates_against_existing_type(
        self, db, test_household, test_template
    ):
        # test_template has recurrence_type=weekly; send invalid config for weekly
        data = RecurrentExpenseUpdate(recurrence_config={"interval_days": 14})
        with pytest.raises(InvalidRecurrenceConfigExceptionError):
            recurrent_expense_service.update_recurrent_expense(
                db, test_template, data, str(test_household.id)
            )

    def test_update_both_recurrence_fields(self, db, test_household, test_template):
        data = RecurrentExpenseUpdate(
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 15},
        )
        updated = recurrent_expense_service.update_recurrent_expense(
            db, test_template, data, str(test_household.id)
        )
        assert updated.recurrence_type == RecurrenceType.MONTHLY
        assert updated.recurrence_config == {"day_of_month": 15}


class TestDeleteRecurrentExpense:
    def test_soft_delete_sets_active_false(self, db, test_template):
        assert test_template.active is True
        recurrent_expense_service.delete_recurrent_expense(db, test_template)
        db.refresh(test_template)
        assert test_template.active is False

    def test_soft_delete_does_not_remove_record(self, db, test_template):
        recurrent_expense_id = test_template.id
        recurrent_expense_service.delete_recurrent_expense(db, test_template)
        record = (
            db.query(RecurrentExpense)
            .filter(RecurrentExpense.id == recurrent_expense_id)
            .first()
        )
        assert record is not None
        assert record.active is False
