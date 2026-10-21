from app.config import settings
from jose import jwt


def test_login(client, test_user):
    response = client.post(
        "/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


def test_login_token_contains_user_id(client, test_user):
    response = client.post(
        "/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    payload = jwt.decode(
        response.json()["access_token"],
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    assert payload["user_id"] == test_user["id"]


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/login",
        data={"username": test_user["email"], "password": "wrong-password"},
    )
    assert response.status_code == 403


def test_login_unknown_email(client):
    response = client.post(
        "/login",
        data={"username": "missing@example.com", "password": "password123"},
    )
    assert response.status_code == 403


def test_create_post_without_token(client):
    response = client.post(
        "/posts/",
        json={"title": "Test post", "content": "Kontent"},
    )
    assert response.status_code == 401
