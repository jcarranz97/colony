import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.recurrent_expenses.constants import RecurrenceType
from app.recurrent_expenses.schemas import (
    RecurrentExpenseCreate,
    RecurrentExpenseUpdate,
)

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


class TestRecurrentExpenseCreate:
    def test_valid_monthly(self):
        schema = RecurrentExpenseCreate(**BASE_VALID)
        assert schema.description == "Rent"
        assert schema.base_amount == Decimal("1200.00")

    def test_valid_weekly(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "weekly",
            "recurrence_config": {"day_of_week": 6},
        }
        schema = RecurrentExpenseCreate(**data)
        assert schema.recurrence_config == {"day_of_week": 6}

    def test_valid_bi_weekly(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "bi_weekly",
            "recurrence_config": {"interval_days": 14},
        }
        schema = RecurrentExpenseCreate(**data)
        assert schema.recurrence_config == {"interval_days": 14}

    def test_valid_custom(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "custom",
            "recurrence_config": {"interval": 3, "unit": "months"},
        }
        schema = RecurrentExpenseCreate(**data)
        assert schema.recurrence_config["unit"] == "months"

    def test_base_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            RecurrentExpenseCreate(**{**BASE_VALID, "base_amount": "0"})

    def test_base_amount_negative_raises(self):
        with pytest.raises(ValidationError):
            RecurrentExpenseCreate(**{**BASE_VALID, "base_amount": "-10.00"})

    def test_description_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            RecurrentExpenseCreate(**{**BASE_VALID, "description": "   "})

    def test_description_stripped(self):
        schema = RecurrentExpenseCreate(**{**BASE_VALID, "description": "  Rent  "})
        assert schema.description == "Rent"

    def test_weekly_missing_day_of_week_raises(self):
        data = {**BASE_VALID, "recurrence_type": "weekly", "recurrence_config": {}}
        with pytest.raises(ValidationError, match="day_of_week"):
            RecurrentExpenseCreate(**data)

    def test_weekly_invalid_day_of_week_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "weekly",
            "recurrence_config": {"day_of_week": 7},
        }
        with pytest.raises(ValidationError, match="day_of_week"):
            RecurrentExpenseCreate(**data)

    def test_bi_weekly_missing_interval_days_raises(self):
        data = {**BASE_VALID, "recurrence_type": "bi_weekly", "recurrence_config": {}}
        with pytest.raises(ValidationError, match="interval_days"):
            RecurrentExpenseCreate(**data)

    def test_monthly_missing_day_of_month_raises(self):
        data = {**BASE_VALID, "recurrence_type": "monthly", "recurrence_config": {}}
        with pytest.raises(ValidationError, match="day_of_month"):
            RecurrentExpenseCreate(**data)

    def test_monthly_day_of_month_out_of_range_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "monthly",
            "recurrence_config": {"day_of_month": 32},
        }
        with pytest.raises(ValidationError, match="day_of_month"):
            RecurrentExpenseCreate(**data)

    def test_custom_invalid_unit_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "custom",
            "recurrence_config": {"interval": 3, "unit": "quarters"},
        }
        with pytest.raises(ValidationError, match="unit"):
            RecurrentExpenseCreate(**data)

    def test_custom_missing_interval_raises(self):
        data = {
            **BASE_VALID,
            "recurrence_type": "custom",
            "recurrence_config": {"unit": "months"},
        }
        with pytest.raises(ValidationError, match="interval"):
            RecurrentExpenseCreate(**data)

    def test_invalid_currency_raises(self):
        with pytest.raises(ValidationError):
            RecurrentExpenseCreate(**{**BASE_VALID, "currency": "EUR"})

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError):
            RecurrentExpenseCreate(**{**BASE_VALID, "category": "unknown"})


class TestRecurrentExpenseUpdate:
    def test_empty_update_valid(self):
        # All fields optional — empty update is valid
        schema = RecurrentExpenseUpdate()
        assert schema.description is None

    def test_partial_update_valid(self):
        schema = RecurrentExpenseUpdate(description="New Description")
        assert schema.description == "New Description"

    def test_both_recurrence_fields_validated(self):
        # Both provided and mismatched config raises
        with pytest.raises(ValidationError, match="day_of_week"):
            RecurrentExpenseUpdate(
                recurrence_type=RecurrenceType.WEEKLY,
                recurrence_config={"interval_days": 14},  # wrong for weekly
            )

    def test_only_recurrence_config_skips_schema_validation(self):
        # Only config updated — schema skips validation (service validates against DB)
        schema = RecurrentExpenseUpdate(recurrence_config={"day_of_week": 5})
        assert schema.recurrence_config == {"day_of_week": 5}

    def test_only_recurrence_type_valid(self):
        schema = RecurrentExpenseUpdate(recurrence_type=RecurrenceType.MONTHLY)
        assert schema.recurrence_type is not None

    def test_clear_autopay_info(self):
        # Setting autopay_info=None explicitly means the field IS set and should
        # appear in the dump with None, so a PATCH request can clear the field.
        schema = RecurrentExpenseUpdate(autopay_info=None)
        dumped = schema.model_dump(exclude_unset=True)
        assert "autopay_info" in dumped
        assert dumped["autopay_info"] is None

    def test_base_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            RecurrentExpenseUpdate(base_amount=Decimal("0"))
