from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


# ─── CREATE CATEGORY ──────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """
    Yangi kategoriya yaratish.

    - **name**: Kategoriya nomi (takrorlanmasligi kerak)
    - **description**: Tavsif
    """
    existing = db.query(models.Category).filter(models.Category.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ushbu nomdagi kategoriya allaqachon mavjud"
        )

    new_cat = models.Category(**category.model_dump())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


# ─── GET ALL CATEGORIES ───────────────────────
@router.get("/", response_model=List[schemas.CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Maksimal kategoriyalar soni"),
    skip: int = Query(0, ge=0, description="Tashlab o'tiladigan elementlar soni")
):
    """
    Barcha kategoriyalar ro'yxatini sahifalash (pagination) bilan olish.
    """
    categories = db.query(models.Category).limit(limit).offset(skip).all()
    return categories


# ─── GET CATEGORY BY ID ───────────────────────
@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    Bitta kategoriyani ID raqami orqali olish.
    """
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={category_id} bo'lgan kategoriya topilmadi"
        )
    return cat


# ─── UPDATE CATEGORY ──────────────────────────
@router.put("/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    updated_category: schemas.CategoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Kategoriya ma'lumotlarini yangilash.
    """
    cat_query = db.query(models.Category).filter(models.Category.id == category_id)
    cat = cat_query.first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={category_id} bo'lgan kategoriya topilmadi"
        )

    cat_query.update(updated_category.model_dump(exclude_unset=True), synchronize_session=False)
    db.commit()
    return cat_query.first()


# ─── DELETE CATEGORY ──────────────────────────
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Kategoriyani ID raqami bo'yicha o'chirish.
    """
    cat_query = db.query(models.Category).filter(models.Category.id == category_id)
    cat = cat_query.first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID={category_id} bo'lgan kategoriya topilmadi"
        )

    cat_query.delete(synchronize_session=False)
    db.commit()
    return None
