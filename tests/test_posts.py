from app import models
from app.utils.hashing import hash_password


def test_get_all_posts(client, test_posts):
    response = client.get("/posts/")
    assert response.status_code == 200
    assert len(response.json()) == len(test_posts)


def test_get_post(client, test_posts):
    response = client.get(f"/posts/{test_posts[0].id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_posts[0].id
    assert response.json()["title"] == test_posts[0].title


def test_get_post_not_found(client):
    assert client.get("/posts/99999").status_code == 404


def test_create_post(authorized_client):
    response = authorized_client.post(
        "/posts/",
        json={"title": "Yangi post", "content": "Yangi kontent", "published": True},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Yangi post"
    assert data["content"] == "Yangi kontent"
    assert data["published"] is True
    assert data["owner_id"]


def test_create_post_default_published(authorized_client):
    response = authorized_client.post(
        "/posts/",
        json={"title": "Post", "content": "Kontent"},
    )
    assert response.status_code == 201
    assert response.json()["published"] is True


def test_update_post(authorized_client, test_posts):
    response = authorized_client.put(
        f"/posts/{test_posts[0].id}",
        json={
            "title": "Yangilangan sarlavha",
            "content": "Yangilangan kontent",
            "published": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Yangilangan sarlavha"
    assert response.json()["content"] == "Yangilangan kontent"


def test_update_other_user_post_forbidden(authorized_client, db):
    other_user = models.User(
        username="other",
        email="other@example.com",
        password=hash_password("password123"),
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    other_post = models.Post(
        title="Boshqaning posti",
        content="Kontent",
        owner_id=other_user.id,
    )
    db.add(other_post)
    db.commit()
    db.refresh(other_post)

    response = authorized_client.put(
        f"/posts/{other_post.id}",
        json={"title": "O'zgartirish", "content": "Kontent", "published": True},
    )
    assert response.status_code == 403


def test_delete_post(authorized_client, test_posts):
    post_id = test_posts[0].id
    response = authorized_client.delete(f"/posts/{post_id}")
    assert response.status_code == 204
    assert authorized_client.get(f"/posts/{post_id}").status_code == 404


def test_delete_post_not_found(authorized_client):
    assert authorized_client.delete("/posts/99999").status_code == 404


def test_delete_other_user_post_forbidden(authorized_client, db):
    other_user = models.User(
        username="other2",
        email="other2@example.com",
        password=hash_password("password123"),
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    other_post = models.Post(
        title="Boshqaning posti",
        content="Kontent",
        owner_id=other_user.id,
    )
    db.add(other_post)
    db.commit()
    db.refresh(other_post)

    response = authorized_client.delete(f"/posts/{other_post.id}")
    assert response.status_code == 403


def test_get_posts_pagination(client, test_posts):
    first_page = client.get("/posts/?limit=2&skip=0")
    second_page = client.get("/posts/?limit=2&skip=2")

    assert first_page.status_code == 200
    assert len(first_page.json()) == 2
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1


def test_get_posts_search(client, test_posts):
    response = client.get("/posts/?search=Birinchi")
    assert response.status_code == 200
    assert [post["title"] for post in response.json()] == ["Birinchi post"]
