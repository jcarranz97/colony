import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_password_hash
from app.households.models import Household, UserHouseholdMembership

RAW_PASSWORD = "testpassword123"


def _make_user(
    db: Session,
    *,
    role: str = "user",
    household: Household | None = None,
) -> User:
    user = User(
        username=f"user_{uuid.uuid4().hex[:8]}",
        password_hash=get_password_hash(RAW_PASSWORD),
        preferred_currency="USD",
        role=role,
        active_household_id=household.id if household else None,
    )
    db.add(user)
    db.flush()
    if household:
        db.add(UserHouseholdMembership(user_id=user.id, household_id=household.id))
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(client: TestClient, user: User) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": RAW_PASSWORD},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def test_household(db: Session) -> Household:
    h = Household(name=f"Test Household {uuid.uuid4().hex[:8]}")
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@pytest.fixture
def other_household(db: Session) -> Household:
    h = Household(name=f"Other Household {uuid.uuid4().hex[:8]}")
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@pytest.fixture
def test_admin(db: Session, test_household: Household) -> User:
    return _make_user(db, role="admin", household=test_household)


@pytest.fixture
def test_user(db: Session, test_household: Household) -> User:
    return _make_user(db, role="user", household=test_household)


@pytest.fixture
def other_user(db: Session, other_household: Household) -> User:
    return _make_user(db, role="user", household=other_household)
