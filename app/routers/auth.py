from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, oauth2, schemas
from ..database import get_db
from ..oauth2 import create_access_token, create_refresh_token, verify_access_token
from ..utils.hashing import verify_password

router = APIRouter(
    tags=["Authentication"]
)


# ─── LOGIN ENDPOINT (7-Qism) ──────────────────
@router.post("/login", response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Foydalanuvchi tizimga kirishi (Login).

    - **username**: Foydalanuvchi emaili (OAuth2 standarti bo'yicha username deb nomlanadi)
    - **password**: Maxfiy parol
    - **Returns**: JWT Access Token
    """
    # 1. Foydalanuvchini email yoki username orqali topish
    user = db.query(models.User).filter(
        (models.User.email == user_credentials.username) |
        (models.User.username == user_credentials.username)
    ).first()

    # 2 & 3. Foydalanuvchi borligi va parolni tekshirish (Xavfsizlik: xato xabari bir xil)
    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Noto'g'ri email yoki parol"
        )

    # 4. Foydalanuvchi faolligini tekshirish (Uy vazifasi 2)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hisobingiz faol emas"
        )

    # 5. Access token yaratish
    access_token = create_access_token(data={"user_id": user.id})

    # 6. Tokenni qaytarish
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ─── REFRESH TOKEN (Uy vazifasi 1) ─────────────
@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    payload: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Uzoq muddatli Refresh Token orqali yangi Access Token olish.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token yaroqsiz yoki muddati tugagan",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_access_token(payload.refresh_token, credentials_exception)

    user = db.query(models.User).filter(models.User.id == int(token_data.id)).first()
    if not user:
        raise credentials_exception

    new_access_token = create_access_token(data={"user_id": user.id})
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
