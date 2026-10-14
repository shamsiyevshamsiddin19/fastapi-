from passlib.context import CryptContext

# Bcrypt xashlash konteksti
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Parolni xavfsiz bcrypt orqali xashlaydi."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiritilgan ochiq parolni xashlangan parol bilan solishtiradi."""
    return pwd_context.verify(plain_password, hashed_password)
