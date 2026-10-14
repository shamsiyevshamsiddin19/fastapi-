from fastapi import FastAPI
from .routers import auth, categories, posts, users

# DIQQAT: models.Base.metadata.create_all(bind=engine) olib tashlandi!
# Chunki endi jadvallar va ularning o'zgarishlarini Alembic boshqaradi.

app = FastAPI(
    title="Blog API",
    description="FastAPI + PostgreSQL + JWT + Alembic",
    version="4.0.0"
)

# Routerlarni ulash
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(categories.router)


@app.get("/")
def root():
    """
    Bosh sahifa - Blog API holati.
    """
    return {"xabar": "Blog API v5.0 — Alembic bilan!"}