from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, oauth2, schemas
from ..database import get_db
from ..utils.email import send_welcome_email, write_log
from ..utils.hashing import hash_password, verify_password

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# ─── CREATE USER ──────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Yangi foydalanuvchini ro'yxatdan o'tkazish.

    - **email**: Valid elektron pochta (EmailStr)
    - **password**: Kamida 8 ta belgili parol (bcrypt orqali xashlanadi)
    - **Returns**: Ro'yxatdan o'tgan foydalanuvchi ma'lumotlari (parolsiz)
    """
    # Email allaqachon borligini tekshirish
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email allaqachon ro'yxatdan o'tgan"
        )

    # Parolni xashlash
    hashed_pwd = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Fonda email yuborish — foydalanuvchi kutmaydi!
    background_tasks.add_task(
        send_welcome_email,
        email=new_user.email,
        username=new_user.username,
    )

    # Fonda log yozish
    background_tasks.add_task(
        write_log,
        action="user_created",
        user_id=new_user.id,
        details=f"email={new_user.email}",
    )

    return new_user



# ─── GET ALL USERS ────────────────────────────
@router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """
    Barcha foydalanuvchilar ro'yxatini olish.
    """
    users = db.query(models.User).all()
    return users


# ─── JORIY FOYDALANUVCHINI OLISH (Amaliy mashq 2) ───
@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Joriy tizimga kirgan foydalanuvchi ma'lumotlarini olish ("Men" endpoint).
    """
    return current_user


# ─── PAROLNI O'ZGARTIRISH (Uy vazifasi 3) ─────
@router.put("/me/password")
def change_password(
    passwords: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Joriy foydalanuvchining parolini o'zgartirish.

    - **old_password**: Amaldagi eski parol
    - **new_password**: Yangi parol (kamida 8 ta belgi)
    """
    # 1. Eski parolni tekshirish
    if not verify_password(passwords.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eski parol noto'g'ri"
        )

    # 2. Yangi parolni xashlash va saqlash
    current_user.password = hash_password(passwords.new_password)
    db.commit()
    return {"xabar": "Parol muvaffaqiyatli o'zgartirildi"}


# ─── GET USER BY ID ───────────────────────────
@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Bitta foydalanuvchini ID raqami orqali olish.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={user_id} bo'lgan foydalanuvchi topilmadi"
        )
    return user
