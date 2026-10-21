import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from .. import models, oauth2

router = APIRouter(prefix="/upload", tags=["Upload"])

# Fayllar saqlanadigan asosiy papka
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Ruxsat etilgan rasm formatlari va limitlar
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Ruxsat etilgan barcha fayl formatlari (Uy vazifasi 3)
ALLOWED_ALL_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "video/mp4",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024       # 5 MB
MAX_DOC_SIZE = 20 * 1024 * 1024        # 20 MB (PDF)
MAX_VIDEO_SIZE = 100 * 1024 * 1024     # 100 MB (MP4)


# ─── 1. BITTA RASM YUKLASH ─────────────────────
@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """
    Bitta rasm yuklash (JPEG, PNG, GIF, WebP).
    Maksimal hajm: 5 MB.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faqat rasm formatlariga ruxsat berilgan: {sorted(list(ALLOWED_IMAGE_TYPES))}",
        )

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl hajmi 5 MB dan oshmasligi kerak",
        )

    extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    return {
        "filename": filename,
        "url": f"/uploads/{filename}",
        "size": len(contents),
        "content_type": file.content_type,
        "uploaded_by": current_user.username,
    }


# ─── 2. BIR NECHTA RASM YUKLASH ───────────────
@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_multiple_images(
    files: list[UploadFile] = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """
    Bir vaqtning o'zida maksimal 5 tagacha rasm yuklash.
    """
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bir vaqtda ko'pi bilan 5 ta fayl yuklash mumkin",
        )

    results = []
    for file in files:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            continue

        contents = await file.read()
        if len(contents) > MAX_IMAGE_SIZE:
            continue

        extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{extension}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(contents)

        results.append({
            "filename": filename,
            "url": f"/uploads/{filename}",
            "size": len(contents),
            "content_type": file.content_type,
        })

    return {"uploaded": results, "count": len(results)}


# ─── 3. AVATAR YUKLASH (Amaliy mashq 3) ────────
@router.post("/avatar", status_code=status.HTTP_201_CREATED)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """
    Foydalanuvchi profil rasmini (avatar) yuklash.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar faqat rasm formatida bo'lishi kerak",
        )

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar hajmi 5 MB dan oshmasligi kerak",
        )

    extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    return {
        "filename": filename,
        "avatar_url": f"/uploads/{filename}",
        "uploaded_by": current_user.username,
    }


# ─── 4. KENGAYTIRILGAN FAYL YUKLASH (Uy vazifasi 3) ───
@router.post("/file", status_code=status.HTTP_201_CREATED)
async def upload_any_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """
    Rasm, PDF yoki MP4 video fayllarni yuklash.
    Hajm chegaralari:
    - Rasm: 5 MB
    - PDF: 20 MB
    - Video: 100 MB
    """
    if file.content_type not in ALLOWED_ALL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruxsat etilgan turlar: rasmlar, application/pdf, video/mp4. Kelgan tur: {file.content_type}",
        )

    contents = await file.read()

    max_size = MAX_IMAGE_SIZE
    if file.content_type == "application/pdf":
        max_size = MAX_DOC_SIZE
    elif file.content_type == "video/mp4":
        max_size = MAX_VIDEO_SIZE

    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fayl hajmi ruxsat etilgan limitdan ({max_size // (1024 * 1024)} MB) oshmasligi kerak",
        )

    extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
    filename = f"{uuid.uuid4().hex}.{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    return {
        "filename": filename,
        "url": f"/uploads/{filename}",
        "size": len(contents),
        "content_type": file.content_type,
        "uploaded_by": current_user.username,
    }
