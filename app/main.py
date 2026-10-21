import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import auth, categories, posts, upload, users, websocket

# Uploads papkasini mount qilishdan oldin yaratish
os.makedirs("uploads", exist_ok=True)

# Asosiy loggerni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Blog API",
    description="FastAPI + PostgreSQL + JWT + Alembic + WebSockets + BackgroundTasks",
    version="6.0.0",
)

# CORS sozlamalari (WebSockets va frontend integratsiyasi uchun)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list if settings.origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik fayllarni serve qilish
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routerlarni ulash
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(upload.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    """
    Bosh sahifa - Blog API holati va versiyasi.
    """
    return {"xabar": "Blog API v6.0 — WebSocket va Background Tasks bilan!"}


@app.get("/health")
def health():
    """
    Server sog'lomlik tekshiruvi.
    """
    return {"status": "ok"}