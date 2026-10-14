from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ==========================================
# TOKEN SCHEMAS (6-Qism)
# ==========================================
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==========================================
# USER SCHEMAS
# ==========================================
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Parol kamida 8 ta belgi bo'lishi kerak")
        return v


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Yangi parol kamida 8 ta belgi bo'lishi kerak")
        return v


# ==========================================
# OWNER INFO SCHEMA (14-Qism)
# ==========================================
class OwnerInfo(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CATEGORY SCHEMAS
# ==========================================
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# POST SCHEMAS
# ==========================================
class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


class PostCreate(PostBase):
    category_id: Optional[int] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published: Optional[bool] = None
    rating: Optional[int] = None
    category_id: Optional[int] = None


class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    owner: Optional[OwnerInfo] = None
    category_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PostWithOwner(PostResponse):
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)