from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from .. import models, oauth2, schemas
from ..database import get_db
from ..utils.email import send_post_notification

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


# ─── CREATE POST ──────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Yangi post yaratish va bazaga saqlash.

    - **title**: Post sarlavhasi
    - **content**: Post matni
    - **published**: Chop etilganlik holati
    - **category_id**: Kategoriya ID si (ixtiyoriy)
    - **owner_id**: Avtomatik ravishda token orqali aniqlangan foydalanuvchi ID si
    """
    post_data = post.model_dump()
    # Agar Swagger defaulti bo'yicha 0 kelgan bo'lsa yoki mavjud bo'lmasa
    if post_data.get("category_id") == 0:
        post_data["category_id"] = None
    elif post_data.get("category_id"):
        category = db.query(models.Category).filter(models.Category.id == post_data["category_id"]).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID={post_data['category_id']} bo'lgan kategoriya topilmadi"
            )

    new_post = models.Post(
        owner_id=current_user.id,
        **post_data
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Fonda post bildirishi yuborish
    background_tasks.add_task(
        send_post_notification,
        author_email=current_user.email,
        title=new_post.title,
    )

    return new_post



# ─── READ ALL POSTS (Qidiruv + Pagination) ────
@router.get("/", response_model=List[schemas.PostWithOwner])
def get_all_posts(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Olinadigan postlar soni"),
    skip: int = Query(0, ge=0, description="Tashlab o'tiladigan postlar soni"),
    search: Optional[str] = Query("", description="Sarlavha yoki matn bo'yicha qidiruv so'zi")
):
    """
    Barcha postlar ro'yxatini qidiruv va sahifalash bilan olish (Ommaviy).

    - **limit**: Maksimal nechta post (default: 10)
    - **skip**: Nechta post tashlab o'tish (default: 0)
    - **search**: Qidirilayotgan so'z
    """
    query = db.query(models.Post)
    if search:
        query = query.filter(
            models.Post.title.ilike(f"%{search}%") | models.Post.content.ilike(f"%{search}%")
        )
    posts = query.limit(limit).offset(skip).all()
    return posts


# ─── FAQAT O'Z POSTLARINI KO'RISH (Amaliy mashq 3) ───
@router.get("/my", response_model=List[schemas.PostResponse])
def get_my_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Faqat joriy tizimga kirgan foydalanuvchiga tegishli postlar ro'yxatini olish.
    """
    posts = db.query(models.Post).filter(
        models.Post.owner_id == current_user.id
    ).all()
    return posts


# ─── FOYDALANUVCHI POSTLARINI OLISH ───────────
@router.get("/user/{user_id}/posts", response_model=List[schemas.PostResponse])
def get_user_posts(user_id: int, db: Session = Depends(get_db)):
    """
    Muayyan foydalanuvchiga tegishli barcha postlarni olish.

    - **user_id**: Foydalanuvchi ID si
    """
    posts = db.query(models.Post).filter(models.Post.owner_id == user_id).all()
    return posts


# ─── READ ONE POST ────────────────────────────
@router.get("/{post_id}", response_model=schemas.PostWithOwner)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    Bitta postni ID raqami orqali olish (egasi va kategoriyasi bilan). Ommaviy.
    """
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={post_id} bo'lgan post topilmadi"
        )
    return post


# ─── UPDATE POST (PUT) ────────────────────────
@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: int,
    updated_post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Mavjud post ma'lumotlarini to'liq yangilash (Faqat post egasi).
    """
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={post_id} bo'lgan post topilmadi"
        )

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz bu postni yangilay olmaysiz"
        )

    update_data = updated_post.model_dump(exclude_unset=True)
    if update_data.get("category_id") == 0:
        update_data["category_id"] = None
    elif update_data.get("category_id"):
        category = db.query(models.Category).filter(models.Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID={update_data['category_id']} bo'lgan kategoriya topilmadi"
            )

    post_query.update(update_data, synchronize_session=False)
    db.commit()
    return post_query.first()


# ─── PARTIAL UPDATE POST (PATCH) ──────────────
@router.patch("/{post_id}", response_model=schemas.PostResponse)
def partial_update_post(
    post_id: int,
    post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Postni qisman yangilash (Faqat post egasi).
    """
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    existing_post = post_query.first()
    if not existing_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={post_id} bo'lgan post topilmadi"
        )

    if existing_post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz bu postni yangilay olmaysiz"
        )

    update_data = post.model_dump(exclude_unset=True)
    if update_data.get("category_id") == 0:
        update_data["category_id"] = None
    elif update_data.get("category_id"):
        category = db.query(models.Category).filter(models.Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID={update_data['category_id']} bo'lgan kategoriya topilmadi"
            )

    if update_data:
        post_query.update(update_data, synchronize_session=False)
        db.commit()
    return post_query.first()


# ─── DELETE POST ──────────────────────────────
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Postni ID bo'yicha o'chirish (Faqat post egasi).
    """
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={post_id} bo'lgan post topilmadi"
        )

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Siz bu postni o'chira olmaysiz"
        )

    post_query.delete(synchronize_session=False)
    db.commit()
    return None
