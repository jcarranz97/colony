import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_tokens.models import ApiToken
from app.api_tokens.service import _hash_token
from app.auth.models import User

from .conftest import get_auth_headers

BASE = "/api/v1/api-tokens"


class TestCreateApiToken:
    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.post(BASE + "/", json={"name": "My MCP"})
        assert resp.status_code == 401

    def test_create_returns_one_time_secret(
        self, client: TestClient, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_user)
        resp = client.post(BASE + "/", json={"name": "My MCP"}, headers=headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "My MCP"
        assert body["token"].startswith("colony_pat_")
        assert body["prefix"] == body["token"][:16]
        assert body["active"] is True

    def test_create_rejects_blank_name(
        self, client: TestClient, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_user)
        resp = client.post(BASE + "/", json={"name": "   "}, headers=headers)
        assert resp.status_code == 422


class TestListApiTokens:
    def test_requires_auth(self, client: TestClient) -> None:
        assert client.get(BASE + "/").status_code == 401

    def test_list_returns_metadata_without_secret(
        self, client: TestClient, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_user)
        client.post(BASE + "/", json={"name": "My MCP"}, headers=headers)
        resp = client.get(BASE + "/", headers=headers)
        assert resp.status_code == 200
        tokens = resp.json()
        assert len(tokens) == 1
        assert "token" not in tokens[0]

    def test_list_isolates_other_users(
        self, client: TestClient, test_user: User, other_user: User
    ) -> None:
        client.post(
            BASE + "/",
            json={"name": "Mine"},
            headers=get_auth_headers(client, test_user),
        )
        resp = client.get(BASE + "/", headers=get_auth_headers(client, other_user))
        assert resp.status_code == 200
        assert resp.json() == []


class TestRevokeApiToken:
    def test_revoke_removes_token(self, client: TestClient, test_user: User) -> None:
        headers = get_auth_headers(client, test_user)
        created = client.post(
            BASE + "/", json={"name": "My MCP"}, headers=headers
        ).json()
        resp = client.delete(f"{BASE}/{created['id']}", headers=headers)
        assert resp.status_code == 204
        assert client.get(BASE + "/", headers=headers).json() == []

    def test_revoke_unknown_token_is_not_found(
        self, client: TestClient, test_user: User
    ) -> None:
        headers = get_auth_headers(client, test_user)
        resp = client.delete(f"{BASE}/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404

    def test_cannot_revoke_other_users_token(
        self, client: TestClient, test_user: User, other_user: User
    ) -> None:
        created = client.post(
            BASE + "/",
            json={"name": "Mine"},
            headers=get_auth_headers(client, test_user),
        ).json()
        resp = client.delete(
            f"{BASE}/{created['id']}",
            headers=get_auth_headers(client, other_user),
        )
        assert resp.status_code == 404


class TestPatAuthentication:
    """A PAT must authenticate the API just like a JWT."""

    def test_pat_authenticates_protected_endpoint(
        self, client: TestClient, test_user: User
    ) -> None:
        token = client.post(
            BASE + "/",
            json={"name": "My MCP"},
            headers=get_auth_headers(client, test_user),
        ).json()["token"]
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == test_user.username

    def test_revoked_pat_is_rejected(self, client: TestClient, test_user: User) -> None:
        headers = get_auth_headers(client, test_user)
        created = client.post(
            BASE + "/", json={"name": "My MCP"}, headers=headers
        ).json()
        client.delete(f"{BASE}/{created['id']}", headers=headers)
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {created['token']}"},
        )
        assert resp.status_code == 401

    def test_unknown_pat_is_rejected(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer colony_pat_does_not_exist"},
        )
        assert resp.status_code == 401

    def test_expired_pat_is_rejected(
        self, client: TestClient, db: Session, test_user: User
    ) -> None:
        raw = "colony_pat_expired_token_value"
        db.add(
            ApiToken(
                user_id=test_user.id,
                name="Expired",
                token_hash=_hash_token(raw),
                prefix=raw[:16],
                expires_at=datetime.utcnow() - timedelta(days=1),  # noqa: DTZ003
            )
        )
        db.commit()
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {raw}"})
        assert resp.status_code == 401


class TestApiTokenHealth:
    def test_health(self, client: TestClient) -> None:
        resp = client.get(BASE + "/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
