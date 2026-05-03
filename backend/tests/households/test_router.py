"""Tests for the /api/v1/households/ endpoints."""

import uuid

from fastapi.testclient import TestClient

from app.auth.models import User
from app.households.models import Household, UserHouseholdMembership

from .conftest import get_auth_headers


class TestCreateHousehold:
    def test_requires_auth(self, client: TestClient) -> None:
        response = client.post("/api/v1/households/", json={"name": "Smith Family"})
        assert response.status_code == 401

    def test_requires_admin(self, client: TestClient, test_user: User) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.post(
            "/api/v1/households/", json={"name": "Smith Family"}, headers=headers
        )
        assert response.status_code == 403

    def test_admin_can_create(self, client: TestClient, test_admin: User) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.post(
            "/api/v1/households/", json={"name": "Smith Family"}, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Smith Family"
        assert data["active"] is True

    def test_duplicate_name_returns_409(
        self, client: TestClient, test_admin: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.post(
            "/api/v1/households/",
            json={"name": test_household.name},
            headers=headers,
        )
        assert response.status_code == 409


class TestListHouseholds:
    def test_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/v1/households/")
        assert response.status_code == 401

    def test_requires_admin(self, client: TestClient, test_user: User) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/households/", headers=headers)
        assert response.status_code == 403

    def test_admin_gets_all_households(
        self,
        client: TestClient,
        test_admin: User,
        test_household: Household,
        other_household: Household,
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.get("/api/v1/households/", headers=headers)
        assert response.status_code == 200
        ids = [h["id"] for h in response.json()]
        assert str(test_household.id) in ids
        assert str(other_household.id) in ids


class TestGetHousehold:
    def test_requires_auth(self, client: TestClient, test_household: Household) -> None:
        response = client.get(f"/api/v1/households/{test_household.id}")
        assert response.status_code == 401

    def test_requires_admin(
        self, client: TestClient, test_user: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get(
            f"/api/v1/households/{test_household.id}", headers=headers
        )
        assert response.status_code == 403

    def test_admin_can_get(
        self, client: TestClient, test_admin: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.get(
            f"/api/v1/households/{test_household.id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(test_household.id)

    def test_not_found(self, client: TestClient, test_admin: User) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.get(f"/api/v1/households/{uuid.uuid4()}", headers=headers)
        assert response.status_code == 404


class TestUpdateHousehold:
    def test_requires_auth(self, client: TestClient, test_household: Household) -> None:
        response = client.put(
            f"/api/v1/households/{test_household.id}", json={"name": "Renamed"}
        )
        assert response.status_code == 401

    def test_requires_admin(
        self, client: TestClient, test_user: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.put(
            f"/api/v1/households/{test_household.id}",
            json={"name": "Renamed"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_admin_can_update(
        self, client: TestClient, test_admin: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.put(
            f"/api/v1/households/{test_household.id}",
            json={"name": "Renamed Household"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Household"

    def test_not_found(self, client: TestClient, test_admin: User) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.put(
            f"/api/v1/households/{uuid.uuid4()}",
            json={"name": "X"},
            headers=headers,
        )
        assert response.status_code == 404


class TestDeleteHousehold:
    def test_requires_auth(self, client: TestClient, test_household: Household) -> None:
        response = client.delete(f"/api/v1/households/{test_household.id}")
        assert response.status_code == 401

    def test_requires_admin(
        self, client: TestClient, test_user: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.delete(
            f"/api/v1/households/{test_household.id}", headers=headers
        )
        assert response.status_code == 403

    def test_admin_soft_deletes(
        self,
        client: TestClient,
        test_admin: User,
        other_household: Household,
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.delete(
            f"/api/v1/households/{other_household.id}", headers=headers
        )
        assert response.status_code == 204


class TestAddMember:
    def test_requires_auth(
        self, client: TestClient, test_household: Household, test_user: User
    ) -> None:
        response = client.post(
            f"/api/v1/households/{test_household.id}/members",
            json={"user_id": str(test_user.id)},
        )
        assert response.status_code == 401

    def test_requires_admin(
        self, client: TestClient, test_user: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.post(
            f"/api/v1/households/{test_household.id}/members",
            json={"user_id": str(test_user.id)},
            headers=headers,
        )
        assert response.status_code == 403

    def test_admin_can_add_member(
        self,
        client: TestClient,
        test_admin: User,
        test_household: Household,
        other_user: User,
        db,
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.post(
            f"/api/v1/households/{test_household.id}/members",
            json={"user_id": str(other_user.id)},
            headers=headers,
        )
        assert response.status_code == 201
        membership = (
            db.query(UserHouseholdMembership)
            .filter(
                UserHouseholdMembership.user_id == other_user.id,
                UserHouseholdMembership.household_id == test_household.id,
            )
            .first()
        )
        assert membership is not None

    def test_duplicate_member_returns_409(
        self,
        client: TestClient,
        test_admin: User,
        test_household: Household,
        test_user: User,
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.post(
            f"/api/v1/households/{test_household.id}/members",
            json={"user_id": str(test_user.id)},
            headers=headers,
        )
        assert response.status_code == 409

    def test_household_not_found_returns_404(
        self, client: TestClient, test_admin: User, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.post(
            f"/api/v1/households/{uuid.uuid4()}/members",
            json={"user_id": str(test_user.id)},
            headers=headers,
        )
        assert response.status_code == 404


class TestRemoveMember:
    def test_requires_auth(
        self, client: TestClient, test_household: Household, test_user: User
    ) -> None:
        response = client.delete(
            f"/api/v1/households/{test_household.id}/members/{test_user.id}"
        )
        assert response.status_code == 401

    def test_requires_admin(
        self, client: TestClient, test_user: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.delete(
            f"/api/v1/households/{test_household.id}/members/{test_user.id}",
            headers=headers,
        )
        assert response.status_code == 403

    def test_admin_can_remove_member(
        self,
        client: TestClient,
        test_admin: User,
        test_household: Household,
        test_user: User,
        db,
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.delete(
            f"/api/v1/households/{test_household.id}/members/{test_user.id}",
            headers=headers,
        )
        assert response.status_code == 204
        membership = (
            db.query(UserHouseholdMembership)
            .filter(
                UserHouseholdMembership.user_id == test_user.id,
                UserHouseholdMembership.household_id == test_household.id,
            )
            .first()
        )
        assert membership is None

    def test_user_not_in_household_returns_404(
        self, client: TestClient, test_admin: User, test_household: Household
    ) -> None:
        headers = get_auth_headers(client, test_admin)
        response = client.delete(
            f"/api/v1/households/{test_household.id}/members/{uuid.uuid4()}",
            headers=headers,
        )
        assert response.status_code == 404


class TestGetMyHouseholds:
    def test_requires_auth(self, client: TestClient) -> None:
        response = client.get("/api/v1/households/me")
        assert response.status_code == 401

    def test_returns_user_households(
        self,
        client: TestClient,
        test_user: User,
        test_household: Household,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/households/me", headers=headers)
        assert response.status_code == 200
        ids = [h["id"] for h in response.json()]
        assert str(test_household.id) in ids

    def test_does_not_return_other_households(
        self,
        client: TestClient,
        test_user: User,
        other_household: Household,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/households/me", headers=headers)
        assert response.status_code == 200
        ids = [h["id"] for h in response.json()]
        assert str(other_household.id) not in ids


class TestSetActiveHousehold:
    def test_requires_auth(self, client: TestClient, test_household: Household) -> None:
        response = client.put(
            "/api/v1/households/me/active",
            json={"household_id": str(test_household.id)},
        )
        assert response.status_code == 401

    def test_switches_active_household(
        self,
        client: TestClient,
        test_user: User,
        test_household: Household,
        other_household: Household,
        db,
    ) -> None:
        db.add(
            UserHouseholdMembership(
                user_id=test_user.id, household_id=other_household.id
            )
        )
        db.commit()

        headers = get_auth_headers(client, test_user)
        response = client.put(
            "/api/v1/households/me/active",
            json={"household_id": str(other_household.id)},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(other_household.id)

    def test_returns_404_if_not_member(
        self,
        client: TestClient,
        test_user: User,
        other_household: Household,
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.put(
            "/api/v1/households/me/active",
            json={"household_id": str(other_household.id)},
            headers=headers,
        )
        assert response.status_code == 404

    def test_returns_404_if_household_nonexistent(
        self, client: TestClient, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_user)
        response = client.put(
            "/api/v1/households/me/active",
            json={"household_id": str(uuid.uuid4())},
            headers=headers,
        )
        assert response.status_code == 404
