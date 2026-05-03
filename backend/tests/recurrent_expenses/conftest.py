import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.households.models import Household, UserHouseholdMembership
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
from app.recurrent_expenses.models import RecurrentExpense


@pytest.fixture
def test_household(db: Session) -> Household:
    household = Household(name=f"Test Household {uuid.uuid4().hex[:8]}")
    db.add(household)
    db.commit()
    db.refresh(household)
    return household


@pytest.fixture
def other_household(db: Session) -> Household:
    household = Household(name=f"Other Household {uuid.uuid4().hex[:8]}")
    db.add(household)
    db.commit()
    db.refresh(household)
    return household


@pytest.fixture
def test_user(db: Session, test_household: Household) -> User:
    user = User(
        username=f"test_{uuid.uuid4().hex[:8]}",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        preferred_currency="USD",
        active_household_id=test_household.id,
    )
    db.add(user)
    db.flush()
    db.add(UserHouseholdMembership(user_id=user.id, household_id=test_household.id))
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db: Session, other_household: Household) -> User:
    user = User(
        username=f"other_{uuid.uuid4().hex[:8]}",
        password_hash=get_password_hash("testpassword123"),
        first_name="Other",
        last_name="User",
        preferred_currency="USD",
        active_household_id=other_household.id,
    )
    db.add(user)
    db.flush()
    db.add(UserHouseholdMembership(user_id=user.id, household_id=other_household.id))
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_payment_method(db: Session, test_household: Household) -> PaymentMethod:
    pm = PaymentMethod(
        household_id=test_household.id,
        name="Chase Debit",
        method_type=PaymentMethodType.DEBIT,
        default_currency=PMCurrencyCode.USD,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


@pytest.fixture
def other_payment_method(db: Session, other_household: Household) -> PaymentMethod:
    pm = PaymentMethod(
        household_id=other_household.id,
        name="Other Card",
        method_type=PaymentMethodType.CREDIT,
        default_currency=PMCurrencyCode.USD,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


@pytest.fixture
def test_template(
    db: Session,
    test_household: Household,
    test_payment_method: PaymentMethod,
) -> RecurrentExpense:
    recurrent_expense = RecurrentExpense(
        household_id=test_household.id,
        payment_method_id=test_payment_method.id,
        description="Groceries",
        currency=CurrencyCode.USD,
        base_amount=Decimal("150.00"),
        category=ExpenseCategory.VARIABLE,
        recurrence_type=RecurrenceType.WEEKLY,
        recurrence_config={"day_of_week": 6},
        reference_date=date(2024, 12, 21),
    )
    db.add(recurrent_expense)
    db.commit()
    db.refresh(recurrent_expense)
    return recurrent_expense
