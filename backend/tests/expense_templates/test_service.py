import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.expense_templates.constants import (
    CurrencyCode,
    ExpenseCategory,
    RecurrenceType,
)
from app.expense_templates.exceptions import (
    InvalidRecurrenceConfigExceptionError,
    PaymentMethodNotFoundExceptionError,
)
from app.expense_templates.models import ExpenseTemplate
from app.expense_templates.schemas import ExpenseTemplateCreate, ExpenseTemplateUpdate
from app.expense_templates.service import expense_template_service


class TestGetExpenseTemplates:
    def test_returns_only_user_templates(
        self, db, test_user, other_user, test_payment_method, other_payment_method
    ):
        t1 = ExpenseTemplate(
            user_id=test_user.id,
            payment_method_id=test_payment_method.id,
            description="My Template",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        t2 = ExpenseTemplate(
            user_id=other_user.id,
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

        results = expense_template_service.get_expense_templates(db, str(test_user.id))
        assert len(results) == 1
        assert results[0].description == "My Template"

    def test_filter_by_active(self, db, test_user, test_payment_method):
        active_t = ExpenseTemplate(
            user_id=test_user.id,
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
        inactive_t = ExpenseTemplate(
            user_id=test_user.id,
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

        results = expense_template_service.get_expense_templates(
            db, str(test_user.id), active=True
        )
        assert all(t.active for t in results)
        assert len(results) == 1

    def test_filter_by_category(self, db, test_user, test_payment_method):
        fixed_t = ExpenseTemplate(
            user_id=test_user.id,
            payment_method_id=test_payment_method.id,
            description="Fixed",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        variable_t = ExpenseTemplate(
            user_id=test_user.id,
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

        results = expense_template_service.get_expense_templates(
            db, str(test_user.id), category="fixed"
        )
        assert len(results) == 1
        assert results[0].description == "Fixed"


class TestGetExpenseTemplateById:
    def test_returns_none_for_other_user(
        self, db, test_user, other_user, test_payment_method
    ):
        template = ExpenseTemplate(
            user_id=test_user.id,
            payment_method_id=test_payment_method.id,
            description="Mine",
            currency=CurrencyCode.USD,
            base_amount=Decimal("100.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        db.add(template)
        db.commit()

        result = expense_template_service.get_expense_template_by_id(
            db, str(template.id), str(other_user.id)
        )
        assert result is None

    def test_returns_template_for_owner(self, db, test_user, test_template):
        result = expense_template_service.get_expense_template_by_id(
            db, str(test_template.id), str(test_user.id)
        )
        assert result is not None
        assert result.id == test_template.id


class TestCreateExpenseTemplate:
    def test_create_success(self, db, test_user, test_payment_method):
        data = ExpenseTemplateCreate(
            description="Rent",
            currency=CurrencyCode.USD,
            payment_method_id=test_payment_method.id,
            base_amount=Decimal("1200.00"),
            category=ExpenseCategory.FIXED,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            reference_date=date(2024, 12, 1),
        )
        template = expense_template_service.create_expense_template(
            db, data, str(test_user.id)
        )
        assert template.description == "Rent"
        assert template.active is True

    def test_raises_when_payment_method_not_owned(
        self, db, test_user, other_payment_method
    ):
        data = ExpenseTemplateCreate(
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
            expense_template_service.create_expense_template(
                db, data, str(test_user.id)
            )

    def test_raises_when_payment_method_nonexistent(self, db, test_user):
        data = ExpenseTemplateCreate(
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
            expense_template_service.create_expense_template(
                db, data, str(test_user.id)
            )


class TestUpdateExpenseTemplate:
    def test_partial_update(self, db, test_user, test_template):
        data = ExpenseTemplateUpdate(description="Updated Groceries")
        updated = expense_template_service.update_expense_template(
            db, test_template, data, str(test_user.id)
        )
        assert updated.description == "Updated Groceries"
        assert updated.category == test_template.category

    def test_update_recurrence_config_validates_against_existing_type(
        self, db, test_user, test_template
    ):
        # test_template has recurrence_type=weekly; send invalid config for weekly
        data = ExpenseTemplateUpdate(recurrence_config={"interval_days": 14})
        with pytest.raises(InvalidRecurrenceConfigExceptionError):
            expense_template_service.update_expense_template(
                db, test_template, data, str(test_user.id)
            )

    def test_update_both_recurrence_fields(self, db, test_user, test_template):
        data = ExpenseTemplateUpdate(
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 15},
        )
        updated = expense_template_service.update_expense_template(
            db, test_template, data, str(test_user.id)
        )
        assert updated.recurrence_type == RecurrenceType.MONTHLY
        assert updated.recurrence_config == {"day_of_month": 15}


class TestDeleteExpenseTemplate:
    def test_soft_delete_sets_active_false(self, db, test_template):
        assert test_template.active is True
        expense_template_service.delete_expense_template(db, test_template)
        db.refresh(test_template)
        assert test_template.active is False

    def test_soft_delete_does_not_remove_record(self, db, test_template):
        template_id = test_template.id
        expense_template_service.delete_expense_template(db, test_template)
        record = (
            db.query(ExpenseTemplate)
            .filter(ExpenseTemplate.id == template_id)
            .first()
        )
        assert record is not None
        assert record.active is False
