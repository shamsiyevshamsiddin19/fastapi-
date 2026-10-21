def test_create_user(client):
    response = client.post(
        "/users/",
        json={
            "username": "ali",
            "email": "ali@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ali@example.com"
    assert data["username"] == "ali"
    assert "password" not in data
    assert "id" in data
    assert "created_at" in data


def test_create_user_duplicate_email(client):
    user = {
        "username": "ali",
        "email": "ali@example.com",
        "password": "password123",
    }
    assert client.post("/users/", json=user).status_code == 201

    response = client.post(
        "/users/",
        json={**user, "username": "vali", "password": "password456"},
    )
    assert response.status_code == 400
    assert "allaqachon" in response.json()["detail"]


def test_create_user_invalid_email(client):
    response = client.post(
        "/users/",
        json={
            "username": "ali",
            "email": "bu-email-emas",
            "password": "password123",
        },
    )
    assert response.status_code == 422


def test_create_user_short_password(client):
    response = client.post(
        "/users/",
        json={"username": "ali", "email": "ali@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_get_user(client, test_user):
    response = client.get(f"/users/{test_user['id']}")

    assert response.status_code == 200
    assert response.json()["email"] == test_user["email"]
    assert response.json()["username"] == test_user["username"]


def test_get_user_not_found(client):
    response = client.get("/users/99999")
    assert response.status_code == 404
