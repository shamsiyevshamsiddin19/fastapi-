import io



def test_upload_image_unauthorized(client):
    file_content = b"fake image content"
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}
    response = client.post("/upload/image", files=files)
    assert response.status_code == 401


def test_upload_image_success(authorized_client):
    file_content = b"\x89PNG\r\n\x1a\nfake_image_bytes"
    files = {"file": ("avatar.png", io.BytesIO(file_content), "image/png")}
    response = authorized_client.post("/upload/image", files=files)

    assert response.status_code == 201
    data = response.json()
    assert "filename" in data
    assert "url" in data
    assert data["content_type"] == "image/png"
    assert data["uploaded_by"] == "testuser"

    # Statik fayl tekshiruvi
    static_resp = authorized_client.get(data["url"])
    assert static_resp.status_code == 200
    assert static_resp.content == file_content


def test_upload_image_invalid_type(authorized_client):
    file_content = b"not an image text content"
    files = {"file": ("doc.txt", io.BytesIO(file_content), "text/plain")}
    response = authorized_client.post("/upload/image", files=files)
    assert response.status_code == 400
    assert "Faqat rasm formatlariga" in response.json()["detail"]


def test_upload_multiple_images(authorized_client):
    files = [
        ("files", ("img1.jpg", io.BytesIO(b"img1"), "image/jpeg")),
        ("files", ("img2.png", io.BytesIO(b"img2"), "image/png")),
    ]
    response = authorized_client.post("/upload/images", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 2
    assert len(data["uploaded"]) == 2


def test_upload_avatar(authorized_client):
    file_content = b"\x89PNGavatar"
    files = {"file": ("profile.png", io.BytesIO(file_content), "image/png")}
    response = authorized_client.post("/upload/avatar", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "avatar_url" in data
    assert data["uploaded_by"] == "testuser"


def test_upload_pdf_file(authorized_client):
    pdf_content = b"%PDF-1.4 test document content"
    files = {"file": ("document.pdf", io.BytesIO(pdf_content), "application/pdf")}
    response = authorized_client.post("/upload/file", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["content_type"] == "application/pdf"
