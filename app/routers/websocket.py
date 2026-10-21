from datetime import datetime
import json
import logging
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from .. import models
from ..config import settings



logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


# ─── CONNECTION MANAGER ───────────────────────
class ConnectionManager:
    def __init__(self) -> None:
        # {room_id: [websocket1, websocket2, ...]}
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str) -> None:
        """Ulanishni qabul qilish va xonaga qo'shish."""
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)
        logger.info(f"Yangi WebSocket ulanish: {room} | Jami: {len(self.active_connections[room])}")

    def disconnect(self, websocket: WebSocket, room: str) -> None:
        """Ulanishni xonadan chiqarish va xona bo'sh bo'lsa o'chirish."""
        if room in self.active_connections:
            if websocket in self.active_connections[room]:
                self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]
        logger.info(f"WebSocket uzildi: {room}")

    async def send_personal(self, message: str, websocket: WebSocket) -> None:
        """Faqat bitta clientga xabar yuborish."""
        await websocket.send_text(message)

    async def broadcast(self, message: str, room: str) -> None:
        """Xonadagi barcha clientlarga xabar yuborish."""
        if room in self.active_connections:
            for connection in list(self.active_connections[room]):
                try:
                    await connection.send_text(message)
                except Exception as exc:
                    logger.debug(f"Broadcast yuborishda xatolik: {exc}")

    async def broadcast_except(self, message: str, room: str, exclude: WebSocket) -> None:
        """O'zidan boshqa barcha clientlarga xabar yuborish."""
        if room in self.active_connections:
            for connection in list(self.active_connections[room]):
                if connection != exclude:
                    try:
                        await connection.send_text(message)
                    except Exception as exc:
                        logger.debug(f"Broadcast_except xatolik: {exc}")

    def get_room_count(self, room: str) -> int:
        """Xonadagi ulanishlar soni."""
        return len(self.active_connections.get(room, []))

    def get_all_rooms(self) -> dict[str, int]:
        """Barcha faol xonalar va ulardagi a'zolar soni."""
        return {room: len(conns) for room, conns in self.active_connections.items()}


manager = ConnectionManager()


# ─── JWT AUTH HELPER ──────────────────────────
async def get_ws_user(token: Optional[str]) -> Optional[models.User]:
    """WebSocket uchun JWT tokenni tekshirib foydalanuvchini olish."""
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = payload.get("user_id")
        if not user_id:
            return None
    except JWTError:
        return None

    from ..database import SessionLocal, get_db
    from ..main import app

    if get_db in app.dependency_overrides:
        gen = app.dependency_overrides[get_db]()
        db = next(gen)
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        return user

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        return user
    finally:
        db.close()



# ─── 1. ODDIY WEBSOCKET (Echo test) ───────────
@router.websocket("/ws")
async def websocket_echo_endpoint(websocket: WebSocket) -> None:
    """Oddiy echo WebSocket endpoint (ws_test.html uchun)."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Siz yubordingiz: {data}")
    except WebSocketDisconnect:
        logger.info("Oddiy WebSocket client uzildi")


# ─── 2. OCHIQ XONA CHAT (Username bilan) ───────
@router.websocket("/ws/chat/{room}/{username}")
async def chat_open_endpoint(
    websocket: WebSocket,
    room: str,
    username: str,
) -> None:
    """Xona va foydalanuvchi nomi orqali chat qilish."""
    await manager.connect(websocket, room)

    join_message = json.dumps({
        "type": "system",
        "message": f"{username} xonaga kirdi!",
        "room": room,
        "users_count": manager.get_room_count(room),
        "timestamp": datetime.now().strftime("%H:%M"),
    })
    await manager.broadcast(join_message, room)

    try:
        while True:
            data = await websocket.receive_text()
            # JSON yoki oddiy matnni tekshirish
            try:
                parsed = json.loads(data)
                msg_type = parsed.get("type", "message")
                msg_text = parsed.get("message", data)
            except Exception:
                msg_type = "message"
                msg_text = data

            if msg_type == "typing":
                # "Ali yozmoqda..." amaliy mashqi
                typing_payload = json.dumps({
                    "type": "typing",
                    "username": username,
                    "room": room,
                    "message": f"{username} yozmoqda...",
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
                await manager.broadcast_except(typing_payload, room, exclude=websocket)
            else:
                out_message = json.dumps({
                    "type": "message",
                    "username": username,
                    "message": msg_text,
                    "room": room,
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
                await manager.broadcast(out_message, room)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        leave_message = json.dumps({
            "type": "system",
            "message": f"{username} xonadan chiqdi",
            "room": room,
            "users_count": manager.get_room_count(room),
            "timestamp": datetime.now().strftime("%H:%M"),
        })
        await manager.broadcast(leave_message, room)


# ─── 3. HIMOYALANGAN CHAT (JWT Token bilan) ───
@router.websocket("/ws/chat/{room}")
@router.websocket("/ws/secure/{room}")
async def chat_secure_endpoint(
    websocket: WebSocket,
    room: str,
    token: Optional[str] = Query(None),
) -> None:
    """JWT token orqali autentifikatsiya qilingan WebSocket chat."""
    user = await get_ws_user(token)

    if not token or not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    username = user.username
    await manager.connect(websocket, room)

    join_message = json.dumps({
        "type": "system",
        "message": f"{username} joined",
        "room": room,
        "users_count": manager.get_room_count(room),
        "timestamp": datetime.now().strftime("%H:%M"),
    })
    await manager.broadcast(join_message, room)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                msg_type = parsed.get("type", "message")
                msg_text = parsed.get("message", data)
            except Exception:
                msg_type = "message"
                msg_text = data

            if msg_type == "typing":
                typing_payload = json.dumps({
                    "type": "typing",
                    "username": username,
                    "room": room,
                    "message": f"{username} yozmoqda...",
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
                await manager.broadcast_except(typing_payload, room, exclude=websocket)
            else:
                out_message = json.dumps({
                    "type": "message",
                    "username": username,
                    "message": msg_text,
                    "room": room,
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
                await manager.broadcast(out_message, room)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        leave_message = json.dumps({
            "type": "system",
            "message": f"{username} left",
            "room": room,
            "users_count": manager.get_room_count(room),
            "timestamp": datetime.now().strftime("%H:%M"),
        })
        await manager.broadcast(leave_message, room)


# ─── 4. FAOL XONALAR RO'YXATI ─────────────────
@router.get("/ws/rooms")
def get_active_rooms():
    """Barcha faol chat xonalari va ulanishlar sonini qaytarish."""
    return {"rooms": manager.get_all_rooms()}


# ─── 5. ONLINE FOYDALANUVCHILAR XULOSASI ──────
@router.get("/ws/online")
def get_online_summary():
    """Hozirda WebSocket ga ulangan barcha foydalanuvchilar statistikasi."""
    rooms = manager.get_all_rooms()
    return {
        "total_online": sum(rooms.values()),
        "rooms": rooms,
    }
