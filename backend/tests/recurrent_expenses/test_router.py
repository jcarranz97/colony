import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.auth.models import User
from app.recurrent_expenses.constants import (
    CurrencyCode,
    ExpenseCategory,
    RecurrenceType,
)
from app.recurrent_expenses.models import RecurrentExpense


def get_auth_headers(client: TestClient, user: User) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


RECURRENT_EXPENSE_PAYLOAD = {
    "description": "Netflix",
    "currency": "USD",
    "base_amount": "15.99",
    "category": "fixed",
    "recurrence_type": "monthly",
    "recurrence_config": {"day_of_month": 1},
    "reference_date": "2024-12-01",
}


class TestGetRecurrentExpenses:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/recurrent-expenses/")
        assert response.status_code == 401

    def test_list_returns_empty_for_new_user(
        self, client, test_user, test_payment_method
    ):
        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/recurrent-expenses/", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_user_recurrent_expenses(
        self, client, test_user, test_template
    ):
        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/recurrent-expenses/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Groceries"

    def test_list_filter_by_active(self, client, test_user, test_template):
        headers = get_auth_headers(client, test_user)
        response = client.get(
            "/api/v1/recurrent-expenses/?active=true", headers=headers
        )
        assert response.status_code == 200
        assert all(t["active"] for t in response.json())

    def test_list_does_not_include_other_users_recurrent_expenses(
        self,
        client,
        test_user,
        other_user,
        test_template,
        other_payment_method,
        db,
    ):
        other_recurrent_expense = RecurrentExpense(
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
        db.add(other_recurrent_expense)
        db.commit()

        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/recurrent-expenses/", headers=headers)
        descriptions = [t["description"] for t in response.json()]
        assert "Other Template" not in descriptions


class TestCreateRecurrentExpense:
    def test_create_requires_auth(self, client, test_payment_method):
        payload = {
            **RECURRENT_EXPENSE_PAYLOAD,
            "payment_method_id": str(test_payment_method.id),
        }
        response = client.post("/api/v1/recurrent-expenses/", json=payload)
        assert response.status_code == 401

    def test_create_success(self, client, test_user, test_payment_method):
        headers = get_auth_headers(client, test_user)
        payload = {
            **RECURRENT_EXPENSE_PAYLOAD,
            "payment_method_id": str(test_payment_method.id),
        }
        response = client.post(
            "/api/v1/recurrent-expenses/", json=payload, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Netflix"
        assert data["active"] is True
        assert "payment_method" in data
        assert data["payment_method"]["name"] == "Chase Debit"

    def test_create_returns_422_for_invalid_recurrence_config(
        self, client, test_user, test_payment_method
    ):
        headers = get_auth_headers(client, test_user)
        payload = {
            **RECURRENT_EXPENSE_PAYLOAD,
            "payment_method_id": str(test_payment_method.id),
            "recurrence_config": {},  # missing day_of_month for monthly
        }
        response = client.post(
            "/api/v1/recurrent-expenses/", json=payload, headers=headers
        )
        assert response.status_code == 422

    def test_create_returns_404_for_wrong_payment_method(
        self, client, test_user, other_payment_method
    ):
        headers = get_auth_headers(client, test_user)
        payload = {
            **RECURRENT_EXPENSE_PAYLOAD,
            "payment_method_id": str(other_payment_method.id),
        }
        response = client.post(
            "/api/v1/recurrent-expenses/", json=payload, headers=headers
        )
        assert response.status_code == 404


class TestGetRecurrentExpenseById:
    def test_get_requires_auth(self, client, test_template):
        response = client.get(f"/api/v1/recurrent-expenses/{test_template.id}")
        assert response.status_code == 401

    def test_get_success(self, client, test_user, test_template):
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/recurrent-expenses/{test_template.id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_template.id)

    def test_get_returns_404_for_other_users_recurrent_expense(
        self, client, other_user, test_template
    ):
        headers = get_auth_headers(client, other_user)
        response = client.get(
            f"/api/v1/recurrent-expenses/{test_template.id}", headers=headers
        )
        assert response.status_code == 404

    def test_get_returns_404_for_nonexistent_id(self, client, test_user):
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/recurrent-expenses/{uuid.uuid4()}", headers=headers
        )
        assert response.status_code == 404


class TestUpdateRecurrentExpense:
    def test_update_requires_auth(self, client, test_template):
        response = client.put(f"/api/v1/recurrent-expenses/{test_template.id}", json={})
        assert response.status_code == 401

    def test_partial_update_success(self, client, test_user, test_template):
        headers = get_auth_headers(client, test_user)
        response = client.put(
            f"/api/v1/recurrent-expenses/{test_template.id}",
            json={"description": "Updated Groceries"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated Groceries"

    def test_update_returns_404_for_other_users_recurrent_expense(
        self, client, other_user, test_template
    ):
        headers = get_auth_headers(client, other_user)
        response = client.put(
            f"/api/v1/recurrent-expenses/{test_template.id}",
            json={"description": "Hacked"},
            headers=headers,
        )
        assert response.status_code == 404


class TestDeleteRecurrentExpense:
    def test_delete_requires_auth(self, client, test_template):
        response = client.delete(f"/api/v1/recurrent-expenses/{test_template.id}")
        assert response.status_code == 401

    def test_delete_returns_204(self, client, test_user, test_template):
        headers = get_auth_headers(client, test_user)
        response = client.delete(
            f"/api/v1/recurrent-expenses/{test_template.id}", headers=headers
        )
        assert response.status_code == 204

    def test_deleted_recurrent_expense_returns_inactive(
        self, client, test_user, test_template
    ):
        headers = get_auth_headers(client, test_user)
        client.delete(f"/api/v1/recurrent-expenses/{test_template.id}", headers=headers)
        response = client.get(
            f"/api/v1/recurrent-expenses/{test_template.id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["active"] is False

    def test_delete_returns_404_for_other_users_recurrent_expense(
        self, client, other_user, test_template
    ):
        headers = get_auth_headers(client, other_user)
        response = client.delete(
            f"/api/v1/recurrent-expenses/{test_template.id}", headers=headers
        )
        assert response.status_code == 404


class TestHealthCheck:
    def test_health_check_no_auth_required(self, client):
        response = client.get("/api/v1/recurrent-expenses/health")
        assert response.status_code == 200
        assert response.json()["domain"] == "recurrent_expenses"
