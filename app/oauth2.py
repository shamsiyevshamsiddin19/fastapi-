from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from . import models, schemas
from .config import settings
from .database import get_db

# Token qayerdan kelishini aytamiz (Swagger UI dagi Authorize tugmasi uchun)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ─── ACCESS TOKEN YARATISH ────────────────────
def create_access_token(data: dict) -> str:
    """Qisqa muddatli access token yaratish (odatda 30 daqiqa)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


# ─── REFRESH TOKEN YARATISH (Uy vazifasi 1) ───
def create_refresh_token(data: dict) -> str:
    """Uzoq muddatli refresh token yaratish (7 kun)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "scope": "refresh_token"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


# ─── TOKENNI TEKSHIRISH ───────────────────────
def verify_access_token(token: str, credentials_exception):
    """JWT tokenni decode qilib tekshirish va user_id ni olish."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=str(user_id))
    except JWTError:
        raise credentials_exception

    return token_data


# ─── JORIY FOYDALANUVCHINI OLISH ─────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Himoyalangan endpointlar uchun dependency.
    Authorization header dan Bearer tokenni olib, DB dagi user ni qaytaradi.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tokenni tekshirib bo'lmadi",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_access_token(token, credentials_exception)

    user = db.query(models.User).filter(
        models.User.id == int(token_data.id)
    ).first()

    if user is None:
        raise credentials_exception

    return user
