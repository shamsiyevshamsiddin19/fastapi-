import json
from app.main import app
from fastapi.testclient import TestClient
import pytest
from starlette.websockets import WebSocketDisconnect


def test_websocket_echo():
    with TestClient(app) as client, client.websocket_connect("/ws") as websocket:
        websocket.send_text("Salom WebSocket")
        data = websocket.receive_text()
        assert data == "Siz yubordingiz: Salom WebSocket"


def test_websocket_chat_open():
    with TestClient(app) as client, client.websocket_connect("/ws/chat/general/Ali") as ws1:
        # Join xabari
        join_msg = ws1.receive_text()
        data = json.loads(join_msg)
        assert data["type"] == "system"
        assert "Ali xonaga kirdi!" in data["message"]

        # Xabar yuborish
        ws1.send_text("Hammaga salom!")
        chat_msg = ws1.receive_text()
        chat_data = json.loads(chat_msg)
        assert chat_data["type"] == "message"
        assert chat_data["username"] == "Ali"
        assert chat_data["message"] == "Hammaga salom!"


def test_websocket_chat_typing_indicator():
    with TestClient(app) as client, \
         client.websocket_connect("/ws/chat/general/Ali") as ws1:
        ws1.receive_text()  # join message
        with client.websocket_connect("/ws/chat/general/Vali") as ws2:
            ws1.receive_text()  # Vali join message in ws1
            ws2.receive_text()  # Vali join message in ws2

            # Ali typing yuboradi
            ws1.send_text(json.dumps({"type": "typing"}))

            # Vali buni qabul qiladi
            typing_msg = ws2.receive_text()
            data = json.loads(typing_msg)
            assert data["type"] == "typing"
            assert data["username"] == "Ali"


def test_websocket_secure_without_token():
    with TestClient(app) as client, pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/chat/secret"):
            pass


def test_websocket_secure_with_valid_token(client, token, test_user):
    with client.websocket_connect(f"/ws/chat/secret?token={token}") as ws:
        join_msg = ws.receive_text()
        data = json.loads(join_msg)
        assert data["type"] == "system"
        assert f"{test_user['username']} joined" in data["message"]

        ws.send_text("Maxfiy xabar")
        msg = ws.receive_text()
        msg_data = json.loads(msg)
        assert msg_data["message"] == "Maxfiy xabar"
        assert msg_data["username"] == test_user["username"]


def test_websocket_rooms_and_online(client):
    response = client.get("/ws/rooms")
    assert response.status_code == 200
    assert "rooms" in response.json()

    online_resp = client.get("/ws/online")
    assert online_resp.status_code == 200
    assert "total_online" in online_resp.json()
