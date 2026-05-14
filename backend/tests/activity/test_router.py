from app.activity.constants import EntityType
from app.activity.service import comment_service

from .conftest import get_auth_headers


class TestActivityFeedEndpoint:
    def test_requires_auth(self, client):
        response = client.get("/api/v1/activity/")
        assert response.status_code == 401

    def test_returns_empty_without_scope(self, client, test_user):
        headers = get_auth_headers(client, test_user)
        response = client.get("/api/v1/activity/", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_entity_scope_returns_events(
        self, client, db, test_household, test_payment_method, test_user
    ):
        # Trigger an event by creating a comment via the service.
        comment_service.create(
            db,
            household_id=test_household.id,
            entity_type=EntityType.PAYMENT_METHOD,
            entity_id=test_payment_method.id,
            body="hello",
            actor=test_user,
        )
        headers = get_auth_headers(client, test_user)
        response = client.get(
            "/api/v1/activity/",
            params={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
            },
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["action"] == "commented"
        assert body[0]["actor"]["id"] == str(test_user.id)


class TestCommentsCrudEndpoint:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/comments/",
            json={
                "entity_type": "payment_method",
                "entity_id": "00000000-0000-0000-0000-000000000000",
                "body": "hi",
            },
        )
        assert response.status_code == 401

    def test_create_returns_comment(self, client, test_payment_method, test_user):
        headers = get_auth_headers(client, test_user)
        response = client.post(
            "/api/v1/comments/",
            headers=headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "first comment",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["body"] == "first comment"
        assert body["author"]["id"] == str(test_user.id)
        assert body["edited_at"] is None

    def test_create_rejects_invalid_entity(self, client, test_user):
        headers = get_auth_headers(client, test_user)
        response = client.post(
            "/api/v1/comments/",
            headers=headers,
            json={
                "entity_type": "payment_method",
                "entity_id": "00000000-0000-0000-0000-000000000000",
                "body": "x",
            },
        )
        assert response.status_code == 404

    def test_edit_by_author(self, client, test_payment_method, test_user):
        headers = get_auth_headers(client, test_user)
        create = client.post(
            "/api/v1/comments/",
            headers=headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "original",
            },
        )
        comment_id = create.json()["id"]
        response = client.patch(
            f"/api/v1/comments/{comment_id}",
            headers=headers,
            json={"body": "edited"},
        )
        assert response.status_code == 200
        assert response.json()["body"] == "edited"
        assert response.json()["edited_at"] is not None

    def test_edit_by_other_user_forbidden(
        self, client, test_payment_method, test_user, other_user
    ):
        author_headers = get_auth_headers(client, test_user)
        create = client.post(
            "/api/v1/comments/",
            headers=author_headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "mine",
            },
        )
        comment_id = create.json()["id"]
        other_headers = get_auth_headers(client, other_user)
        response = client.patch(
            f"/api/v1/comments/{comment_id}",
            headers=other_headers,
            json={"body": "hostile"},
        )
        assert response.status_code == 403

    def test_delete_by_author(self, client, test_payment_method, test_user):
        headers = get_auth_headers(client, test_user)
        create = client.post(
            "/api/v1/comments/",
            headers=headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "to delete",
            },
        )
        comment_id = create.json()["id"]
        response = client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
        assert response.status_code == 204

        list_response = client.get(
            "/api/v1/comments/",
            params={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
            },
            headers=headers,
        )
        assert list_response.status_code == 200
        assert list_response.json() == []

    def test_delete_by_admin(self, client, test_payment_method, test_user, admin_user):
        author_headers = get_auth_headers(client, test_user)
        create = client.post(
            "/api/v1/comments/",
            headers=author_headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "moderate me",
            },
        )
        comment_id = create.json()["id"]
        admin_headers = get_auth_headers(client, admin_user)
        response = client.delete(
            f"/api/v1/comments/{comment_id}", headers=admin_headers
        )
        assert response.status_code == 204

    def test_delete_by_other_user_forbidden(
        self, client, test_payment_method, test_user, other_user
    ):
        author_headers = get_auth_headers(client, test_user)
        create = client.post(
            "/api/v1/comments/",
            headers=author_headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "mine",
            },
        )
        comment_id = create.json()["id"]
        other_headers = get_auth_headers(client, other_user)
        response = client.delete(
            f"/api/v1/comments/{comment_id}", headers=other_headers
        )
        assert response.status_code == 403

    def test_list_filters_by_entity(self, client, test_payment_method, test_user):
        headers = get_auth_headers(client, test_user)
        client.post(
            "/api/v1/comments/",
            headers=headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "one",
            },
        )
        client.post(
            "/api/v1/comments/",
            headers=headers,
            json={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
                "body": "two",
            },
        )
        response = client.get(
            "/api/v1/comments/",
            params={
                "entity_type": "payment_method",
                "entity_id": str(test_payment_method.id),
            },
            headers=headers,
        )
        assert response.status_code == 200
        bodies = [c["body"] for c in response.json()]
        assert sorted(bodies) == ["one", "two"]
