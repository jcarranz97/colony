import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.expense_templates.constants import RecurrenceType
from app.expense_templates.schemas import ExpenseTemplateCreate, ExpenseTemplateUpdate

BASE_VALID = {
    "description": "Rent",
    "currency": "USD",
    "payment_method_id": str(uuid.uuid4()),
    "base_amount": "1200.00",
    "category": "fixed",
    "recurrence_type": "monthly",
    "recurrence_config": {"day_of_month": 1},
    "reference_date": "2024-12-01",
}


class TestExpenseTemplateCreate:
    def test_valid_monthly(self):
        schema = ExpenseTemplateCreate(**BASE_VALID)
        assert schema.description == "Rent"
        assert schema.base_amount == Decimal("1200.00")

    def test_valid_weekly(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "weekly",
            "recurrence_config": {"day_of_week": 6},
        }
        schema = ExpenseTemplateCreate(**data)
        assert schema.recurrence_config == {"day_of_week": 6}

    def test_valid_bi_weekly(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "bi_weekly",
            "recurrence_config": {"interval_days": 14},
        }
        schema = ExpenseTemplateCreate(**data)
        assert schema.recurrence_config == {"interval_days": 14}

    def test_valid_custom(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "custom",
            "recurrence_config": {"interval": 3, "unit": "months"},
        }
        schema = ExpenseTemplateCreate(**data)
        assert schema.recurrence_config["unit"] == "months"

    def test_base_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            ExpenseTemplateCreate(**{**BASE_VALID, "base_amount": "0"})

    def test_base_amount_negative_raises(self):
        with pytest.raises(ValidationError):
            ExpenseTemplateCreate(**{**BASE_VALID, "base_amount": "-10.00"})

    def test_description_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            ExpenseTemplateCreate(**{**BASE_VALID, "description": "   "})

    def test_description_stripped(self):
        schema = ExpenseTemplateCreate(**{**BASE_VALID, "description": "  Rent  "})
        assert schema.description == "Rent"

    def test_weekly_missing_day_of_week_raises(self):
        data = {**BASE_VALID, "recurrence_type": "weekly", "recurrence_config": {}}
        with pytest.raises(ValidationError, match="day_of_week"):
            ExpenseTemplateCreate(**data)

    def test_weekly_invalid_day_of_week_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "weekly",
            "recurrence_config": {"day_of_week": 7},
        }
        with pytest.raises(ValidationError, match="day_of_week"):
            ExpenseTemplateCreate(**data)

    def test_bi_weekly_missing_interval_days_raises(self):
        data = {**BASE_VALID, "recurrence_type": "bi_weekly", "recurrence_config": {}}
        with pytest.raises(ValidationError, match="interval_days"):
            ExpenseTemplateCreate(**data)

    def test_monthly_missing_day_of_month_raises(self):
        data = {**BASE_VALID, "recurrence_type": "monthly", "recurrence_config": {}}
        with pytest.raises(ValidationError, match="day_of_month"):
            ExpenseTemplateCreate(**data)

    def test_monthly_day_of_month_out_of_range_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "monthly",
            "recurrence_config": {"day_of_month": 32},
        }
        with pytest.raises(ValidationError, match="day_of_month"):
            ExpenseTemplateCreate(**data)

    def test_custom_invalid_unit_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "custom",
            "recurrence_config": {"interval": 3, "unit": "quarters"},
        }
        with pytest.raises(ValidationError, match="unit"):
            ExpenseTemplateCreate(**data)

    def test_custom_missing_interval_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "custom",
            "recurrence_config": {"unit": "months"},
        }
        with pytest.raises(ValidationError, match="interval"):
            ExpenseTemplateCreate(**data)

    def test_invalid_currency_raises(self):
        with pytest.raises(ValidationError):
            ExpenseTemplateCreate(**{**BASE_VALID, "currency": "EUR"})

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError):
            ExpenseTemplateCreate(**{**BASE_VALID, "category": "unknown"})


class TestExpenseTemplateUpdate:
    def test_empty_update_valid(self):
        # All fields optional — empty update is valid
        schema = ExpenseTemplateUpdate()
        assert schema.description is None

    def test_partial_update_valid(self):
        schema = ExpenseTemplateUpdate(description="New Description")
        assert schema.description == "New Description"

    def test_both_recurrence_fields_validated(self):
        # Both provided and mismatched config raises
        with pytest.raises(ValidationError, match="day_of_week"):
            ExpenseTemplateUpdate(
                recurrence_type=RecurrenceType.WEEKLY,
                recurrence_config={"interval_days": 14},  # wrong for weekly
            )

    def test_only_recurrence_config_skips_schema_validation(self):
        # Only config updated — schema skips validation (service validates against DB)
        schema = ExpenseTemplateUpdate(recurrence_config={"day_of_week": 5})
        assert schema.recurrence_config == {"day_of_week": 5}

    def test_only_recurrence_type_valid(self):
        schema = ExpenseTemplateUpdate(recurrence_type=RecurrenceType.MONTHLY)
        assert schema.recurrence_type is not None

    def test_clear_autopay_info(self):
        # Should be able to set autopay_info to None explicitly
        schema = ExpenseTemplateUpdate(autopay_info=None)
        dumped = schema.model_dump(exclude_unset=True)
        # autopay_info not in exclude_unset since it was not explicitly set
        assert "autopay_info" not in dumped

    def test_base_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            ExpenseTemplateUpdate(base_amount=Decimal("0"))
