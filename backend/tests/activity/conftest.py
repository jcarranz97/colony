import uuid

import pytest
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.households.models import Household, UserHouseholdMembership
from app.payment_methods.constants import CurrencyCode, PaymentMethodType
from app.payment_methods.models import PaymentMethod


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
        username=f"author_{uuid.uuid4().hex[:8]}",
        password_hash=get_password_hash("testpassword123"),
        first_name="Author",
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
def other_user(db: Session, test_household: Household) -> User:
    """A second user in the SAME household (used for permission checks)."""
    user = User(
        username=f"viewer_{uuid.uuid4().hex[:8]}",
        password_hash=get_password_hash("testpassword123"),
        first_name="Viewer",
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
def admin_user(db: Session, test_household: Household) -> User:
    user = User(
        username=f"admin_{uuid.uuid4().hex[:8]}",
        password_hash=get_password_hash("testpassword123"),
        first_name="Admin",
        last_name="User",
        preferred_currency="USD",
        role="admin",
        active_household_id=test_household.id,
    )
    db.add(user)
    db.flush()
    db.add(UserHouseholdMembership(user_id=user.id, household_id=test_household.id))
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_payment_method(db: Session, test_household: Household) -> PaymentMethod:
    pm = PaymentMethod(
        household_id=test_household.id,
        name="Test Card",
        method_type=PaymentMethodType.DEBIT,
        default_currency=CurrencyCode.USD,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)
    return pm


def get_auth_headers(client, user) -> dict[str, str]:
    """Helper to log in and return Authorization headers."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": "testpassword123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
