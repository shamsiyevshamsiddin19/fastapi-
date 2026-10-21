from unittest.mock import patch


def test_user_creation_triggers_background_tasks(client):
    with patch("app.routers.users.send_welcome_email") as mock_welcome, \
         patch("app.routers.users.write_log") as mock_log:
        response = client.post(
            "/users/",
            json={
                "username": "bguser",
                "email": "bguser@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        assert mock_welcome.called
        assert mock_welcome.call_args.kwargs["email"] == "bguser@example.com"
        assert mock_welcome.call_args.kwargs["username"] == "bguser"
        assert mock_log.called


def test_post_creation_triggers_background_task(authorized_client):
    with patch("app.routers.posts.send_post_notification") as mock_notify:
        response = authorized_client.post(
            "/posts/",
            json={
                "title": "Post with Background Notification",
                "content": "Kontent matni",
                "published": True,
            },
        )
        assert response.status_code == 201
        assert mock_notify.called
        assert mock_notify.call_args.kwargs["title"] == "Post with Background Notification"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_status(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "WebSocket" in response.json()["xabar"]
