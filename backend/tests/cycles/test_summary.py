"""Tests for GET /api/v1/cycles/{cycle_id}/summary."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.auth.models import User
from app.cycles.models import Cycle


def get_auth_headers(client: TestClient, user: User) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetCycleSummary:
    def test_requires_auth(self, client: TestClient, test_cycle: Cycle) -> None:
        response = client.get(f"/api/v1/cycles/{test_cycle.id}/summary")
        assert response.status_code == 401

    def test_returns_404_for_unknown_cycle(
        self, client: TestClient, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            "/api/v1/cycles/00000000-0000-0000-0000-000000000000/summary",
            headers=headers,
        )
        assert response.status_code == 404

    def test_returns_404_for_other_users_cycle(
        self,
        client: TestClient,
        other_user: User,
        test_cycle: Cycle,
    ) -> None:
        headers = get_auth_headers(client, other_user)
        response = client.get(
            f"/api/v1/cycles/{test_cycle.id}/summary", headers=headers
        )
        assert response.status_code == 404

    def test_empty_cycle_returns_zero_totals(
        self, client: TestClient, test_user: User, test_cycle: Cycle
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/cycles/{test_cycle.id}/summary", headers=headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["cycle"]["id"] == str(test_cycle.id)
        assert data["cycle"]["name"] == test_cycle.name
        assert Decimal(data["financial"]["total_expenses_usd"]) == Decimal("0")
        assert Decimal(data["financial"]["net_balance"]) == Decimal("5000.00")
        assert data["by_payment_method"] == []
        assert data["by_currency"] == {}
        assert data["status_breakdown"] == {
            "pending": 0,
            "paid": 0,
            "overdue": 0,
            "cancelled": 0,
        }

    def test_financial_totals_exclude_cancelled(
        self, client: TestClient, test_user: User, cycle_with_expenses: Cycle
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/cycles/{cycle_with_expenses.id}/summary", headers=headers
        )
        assert response.status_code == 200
        financial = response.json()["financial"]

        # 1200 (rent USD) + 300 (groceries USD) + 100 (gas MXN→USD) = 1600
        # cancelled (10 USD) should NOT be included
        assert Decimal(financial["total_expenses_usd"]) == Decimal("1600.00")
        assert Decimal(financial["fixed_expenses_usd"]) == Decimal("1200.00")
        assert Decimal(financial["variable_expenses_usd"]) == Decimal("400.00")
        assert Decimal(financial["usa_expenses_usd"]) == Decimal("1500.00")
        assert Decimal(financial["mexico_expenses_usd"]) == Decimal("100.00")
        assert Decimal(financial["net_balance"]) == Decimal("3400.00")

    def test_by_currency_separates_usd_and_mxn(
        self, client: TestClient, test_user: User, cycle_with_expenses: Cycle
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/cycles/{cycle_with_expenses.id}/summary", headers=headers
        )
        assert response.status_code == 200
        by_currency = response.json()["by_currency"]

        assert "USD" in by_currency
        assert "MXN" in by_currency

        usd = by_currency["USD"]
        assert Decimal(usd["total_amount"]) == Decimal("1500.00")
        assert usd["total_amount_usd"] is None  # not present for USD
        assert usd["expense_count"] == 2

        mxn = by_currency["MXN"]
        assert Decimal(mxn["total_amount"]) == Decimal("2000.00")
        assert Decimal(mxn["total_amount_usd"]) == Decimal("100.00")
        assert mxn["expense_count"] == 1

    def test_by_payment_method_breakdown(
        self,
        client: TestClient,
        test_user: User,
        cycle_with_expenses: Cycle,
        usd_payment_method,
        mxn_payment_method,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/cycles/{cycle_with_expenses.id}/summary", headers=headers
        )
        assert response.status_code == 200
        by_pm = response.json()["by_payment_method"]

        pm_by_id = {item["payment_method"]["id"]: item for item in by_pm}

        chase = pm_by_id[str(usd_payment_method.id)]
        # Rent (1200, paid) + Groceries (300, pending) — cancelled excluded
        assert Decimal(chase["total_amount"]) == Decimal("1500.00")
        assert Decimal(chase["paid_amount"]) == Decimal("1200.00")
        assert Decimal(chase["pending_amount"]) == Decimal("300.00")
        assert chase["expense_count"] == 2

        bbva = pm_by_id[str(mxn_payment_method.id)]
        assert Decimal(bbva["total_amount"]) == Decimal("100.00")
        assert Decimal(bbva["paid_amount"]) == Decimal("0.00")
        assert Decimal(bbva["pending_amount"]) == Decimal("100.00")
        assert bbva["expense_count"] == 1

    def test_status_breakdown_counts_all_active_expenses(
        self, client: TestClient, test_user: User, cycle_with_expenses: Cycle
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/cycles/{cycle_with_expenses.id}/summary", headers=headers
        )
        assert response.status_code == 200
        breakdown = response.json()["status_breakdown"]

        assert breakdown["paid"] == 1
        assert breakdown["pending"] == 1
        assert breakdown["overdue"] == 1
        assert breakdown["cancelled"] == 1

    def test_cycle_info_fields_are_present(
        self, client: TestClient, test_user: User, test_cycle: Cycle
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/cycles/{test_cycle.id}/summary", headers=headers
        )
        assert response.status_code == 200
        cycle_info = response.json()["cycle"]

        assert cycle_info["id"] == str(test_cycle.id)
        assert cycle_info["name"] == "January 2025"
        assert cycle_info["start_date"] == "2025-01-01"
        assert cycle_info["end_date"] == "2025-02-11"
        assert Decimal(cycle_info["income_amount"]) == Decimal("5000.00")
