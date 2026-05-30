"""Tests for PUT /api/v1/cycles/{cycle_id}/expenses/{expense_id}.

Focused on changing the payment method of an expense already in a cycle.
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.cycles.models import Cycle, CycleExpense
from app.households.models import Household
from app.payment_methods.constants import (
    CurrencyCode as PMCurrencyCode,
    PaymentMethodType,
)
from app.payment_methods.models import PaymentMethod


def get_auth_headers(client: TestClient, user: User) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": "testpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _first_expense(cycle: Cycle) -> CycleExpense:
    """Return a pending USD expense from the seeded cycle."""
    return next(e for e in cycle.expenses if e.description == "Groceries")


class TestUpdateExpensePaymentMethod:
    def test_requires_auth(
        self, client: TestClient, cycle_with_expenses: Cycle
    ) -> None:
        expense = _first_expense(cycle_with_expenses)
        response = client.put(
            f"/api/v1/cycles/{cycle_with_expenses.id}/expenses/{expense.id}",
            json={"payment_method_id": str(uuid.uuid4())},
        )
        assert response.status_code == 401

    def test_changes_payment_method(
        self,
        client: TestClient,
        test_user: User,
        cycle_with_expenses: Cycle,
        mxn_payment_method: PaymentMethod,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        expense = _first_expense(cycle_with_expenses)
        assert expense.payment_method_id != mxn_payment_method.id

        response = client.put(
            f"/api/v1/cycles/{cycle_with_expenses.id}/expenses/{expense.id}",
            headers=headers,
            json={"payment_method_id": str(mxn_payment_method.id)},
        )

        assert response.status_code == 200
        data = response.json()
        # The response must echo the new id at the top level so the UI can
        # re-initialize its dropdown after save (regression: it previously
        # only returned the nested payment_method object).
        assert data["payment_method_id"] == str(mxn_payment_method.id)
        assert data["payment_method"]["id"] == str(mxn_payment_method.id)

    def test_unknown_payment_method_rejected(
        self,
        client: TestClient,
        test_user: User,
        cycle_with_expenses: Cycle,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        expense = _first_expense(cycle_with_expenses)

        response = client.put(
            f"/api/v1/cycles/{cycle_with_expenses.id}/expenses/{expense.id}",
            headers=headers,
            json={"payment_method_id": str(uuid.uuid4())},
        )

        assert response.status_code == 404

    def test_other_household_payment_method_rejected(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        cycle_with_expenses: Cycle,
        other_household: Household,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        expense = _first_expense(cycle_with_expenses)
        foreign_pm = PaymentMethod(
            household_id=other_household.id,
            name="Foreign Card",
            method_type=PaymentMethodType.CREDIT,
            default_currency=PMCurrencyCode.USD,
        )
        db.add(foreign_pm)
        db.commit()
        db.refresh(foreign_pm)

        response = client.put(
            f"/api/v1/cycles/{cycle_with_expenses.id}/expenses/{expense.id}",
            headers=headers,
            json={"payment_method_id": str(foreign_pm.id)},
        )

        assert response.status_code == 404

    def test_change_is_recorded_in_activity_log(
        self,
        client: TestClient,
        test_user: User,
        cycle_with_expenses: Cycle,
        usd_payment_method: PaymentMethod,
        mxn_payment_method: PaymentMethod,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        expense = _first_expense(cycle_with_expenses)

        update = client.put(
            f"/api/v1/cycles/{cycle_with_expenses.id}/expenses/{expense.id}",
            headers=headers,
            json={"payment_method_id": str(mxn_payment_method.id)},
        )
        assert update.status_code == 200

        activity = client.get(
            "/api/v1/activity/",
            headers=headers,
            params={"entity_type": "cycle_expense", "entity_id": str(expense.id)},
        )
        assert activity.status_code == 200
        entries = activity.json()
        pm_change = next(e for e in entries if "payment_method_id" in e["changes"])
        diff = pm_change["changes"]["payment_method_id"]
        assert diff["from"] == str(usd_payment_method.id)
        assert diff["to"] == str(mxn_payment_method.id)
