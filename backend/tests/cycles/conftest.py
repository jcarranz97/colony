import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.cycles.constants import (
    CurrencyCode,
    CycleStatus,
    ExpenseCategory,
    ExpenseStatus,
)
from app.cycles.models import Cycle, CycleExpense, ExchangeRate
from app.payment_methods.constants import (
    CurrencyCode as PMCurrencyCode,
    PaymentMethodType,
)
from app.payment_methods.models import PaymentMethod


@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        preferred_currency="USD",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db: Session) -> User:
    user = User(
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Other",
        last_name="User",
        preferred_currency="USD",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def usd_payment_method(db: Session, test_user: User) -> PaymentMethod:
    pm = PaymentMethod(
        user_id=test_user.id,
        name="Chase Debit",
        method_type=PaymentMethodType.DEBIT,
        default_currency=PMCurrencyCode.USD,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


@pytest.fixture
def mxn_payment_method(db: Session, test_user: User) -> PaymentMethod:
    pm = PaymentMethod(
        user_id=test_user.id,
        name="BBVA MXN",
        method_type=PaymentMethodType.DEBIT,
        default_currency=PMCurrencyCode.MXN,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


@pytest.fixture
def mxn_exchange_rate(db: Session) -> ExchangeRate:
    rate = ExchangeRate(
        from_currency=CurrencyCode.MXN,
        to_currency=CurrencyCode.USD,
        rate=Decimal("0.050000"),
        rate_date=date(2025, 1, 1),
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@pytest.fixture
def test_cycle(db: Session, test_user: User) -> Cycle:
    cycle = Cycle(
        user_id=test_user.id,
        name="January 2025",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 2, 11),
        income_amount=Decimal("5000.00"),
        remaining_balance=Decimal("5000.00"),
        status=CycleStatus.ACTIVE,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


@pytest.fixture
def cycle_with_expenses(
    db: Session,
    test_cycle: Cycle,
    usd_payment_method: PaymentMethod,
    mxn_payment_method: PaymentMethod,
) -> Cycle:
    """Cycle pre-populated with a mix of USD and MXN expenses in various statuses."""
    expenses = [
        CycleExpense(
            cycle_id=test_cycle.id,
            payment_method_id=usd_payment_method.id,
            description="Rent",
            currency=CurrencyCode.USD,
            amount=Decimal("1200.00"),
            amount_usd=Decimal("1200.00"),
            due_date=date(2025, 1, 1),
            category=ExpenseCategory.FIXED,
            status=ExpenseStatus.PAID,
            paid=True,
        ),
        CycleExpense(
            cycle_id=test_cycle.id,
            payment_method_id=usd_payment_method.id,
            description="Groceries",
            currency=CurrencyCode.USD,
            amount=Decimal("300.00"),
            amount_usd=Decimal("300.00"),
            due_date=date(2025, 1, 15),
            category=ExpenseCategory.VARIABLE,
            status=ExpenseStatus.PENDING,
            paid=False,
        ),
        CycleExpense(
            cycle_id=test_cycle.id,
            payment_method_id=mxn_payment_method.id,
            description="Gas MXN",
            currency=CurrencyCode.MXN,
            amount=Decimal("2000.00"),
            amount_usd=Decimal("100.00"),
            due_date=date(2025, 1, 20),
            category=ExpenseCategory.VARIABLE,
            status=ExpenseStatus.OVERDUE,
            paid=False,
        ),
        CycleExpense(
            cycle_id=test_cycle.id,
            payment_method_id=usd_payment_method.id,
            description="Cancelled sub",
            currency=CurrencyCode.USD,
            amount=Decimal("10.00"),
            amount_usd=Decimal("10.00"),
            due_date=date(2025, 1, 5),
            category=ExpenseCategory.FIXED,
            status=ExpenseStatus.CANCELLED,
            paid=False,
        ),
    ]
    for e in expenses:
        db.add(e)
    db.commit()
    db.refresh(test_cycle)
    return test_cycle
