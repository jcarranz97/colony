"""Tests for the optional ``household_id`` query param (multi-household).

Data endpoints default to the user's active household, but accept an
explicit ``household_id`` so multi-household clients (the MCP server) can
target — or aggregate across — any household the user belongs to.
"""

import uuid

from app.households.models import UserHouseholdMembership

from .conftest import get_auth_headers


def _add_membership(db, user, household) -> None:
    db.add(UserHouseholdMembership(user_id=user.id, household_id=household.id))
    db.commit()


def _make_cycle(client, headers, name="May 2026") -> dict:
    resp = client.post(
        "/api/v1/cycles/",
        json={
            "name": name,
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


class TestTargetHouseholdScoping:
    def test_list_cycles_defaults_to_active_household(self, client, test_user):
        resp = client.get(
            "/api/v1/cycles/", headers=get_auth_headers(client, test_user)
        )
        assert resp.status_code == 200

    def test_member_household_id_is_allowed(self, client, test_user, test_household):
        resp = client.get(
            f"/api/v1/cycles/?household_id={test_household.id}",
            headers=get_auth_headers(client, test_user),
        )
        assert resp.status_code == 200

    def test_non_member_household_id_is_forbidden(
        self, client, test_user, other_household
    ):
        resp = client.get(
            f"/api/v1/cycles/?household_id={other_household.id}",
            headers=get_auth_headers(client, test_user),
        )
        assert resp.status_code == 403

    def test_unknown_household_id_is_not_found(self, client, test_user):
        resp = client.get(
            f"/api/v1/cycles/?household_id={uuid.uuid4()}",
            headers=get_auth_headers(client, test_user),
        )
        assert resp.status_code == 404

    def test_payment_methods_non_member_household_is_forbidden(
        self, client, test_user, other_household
    ):
        resp = client.get(
            f"/api/v1/payment-methods/?household_id={other_household.id}",
            headers=get_auth_headers(client, test_user),
        )
        assert resp.status_code == 403

    def test_recurrent_expenses_non_member_household_is_forbidden(
        self, client, test_user, other_household
    ):
        resp = client.get(
            f"/api/v1/recurrent-expenses/?household_id={other_household.id}",
            headers=get_auth_headers(client, test_user),
        )
        assert resp.status_code == 403

    def test_household_id_scopes_results(
        self, client, db, test_user, test_household, other_household
    ):
        """A cycle created in one household is invisible to the other."""
        _add_membership(db, test_user, other_household)
        headers = get_auth_headers(client, test_user)
        _make_cycle(client, headers)

        in_test = client.get(
            f"/api/v1/cycles/?household_id={test_household.id}", headers=headers
        ).json()
        assert len(in_test["cycles"]) == 1

        in_other = client.get(
            f"/api/v1/cycles/?household_id={other_household.id}", headers=headers
        ).json()
        assert in_other["cycles"] == []

    def test_member_of_two_households_can_query_both(
        self, client, db, test_user, test_household, other_household
    ):
        _add_membership(db, test_user, other_household)
        headers = get_auth_headers(client, test_user)
        for household_id in (test_household.id, other_household.id):
            resp = client.get(
                f"/api/v1/cycles/?household_id={household_id}", headers=headers
            )
            assert resp.status_code == 200
