import pytest
from app import models
from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def test_user(client):
    response = client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    user = response.json()
    user["password"] = "password123"
    return user


@pytest.fixture()
def token(client, test_user):
    response = client.post(
        "/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def authorized_client(client, token):
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture()
def test_posts(db, test_user):
    posts = [
        models.Post(
            title="Birinchi post",
            content="Birinchi kontent",
            published=True,
            owner_id=test_user["id"],
        ),
        models.Post(
            title="Ikkinchi post",
            content="Ikkinchi kontent",
            published=True,
            owner_id=test_user["id"],
        ),
        models.Post(
            title="Uchinchi post",
            content="Uchinchi kontent",
            published=False,
            owner_id=test_user["id"],
        ),
    ]
    db.add_all(posts)
    db.commit()
    for post in posts:
        db.refresh(post)
    return posts
