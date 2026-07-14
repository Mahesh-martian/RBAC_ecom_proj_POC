"""Admin routes — /api/v1/admin (ADMIN only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.errors import ApiError
from app.core.pagination import calculate_pagination
from app.core.response import model_to_dict, send_response
from app.database import get_db
from app.deps import require_roles
from app.schemas import (
    BlacklistShopRequest,
    CreateCategoryRequest,
    UpdateCategoryRequest,
    UpdateUserRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])

admin_only = require_roles("ADMIN", "SUPER_ADMIN")


def _order_by(model, sort_by: str, sort_order: str):
    column = getattr(model, sort_by, None) or model.createdAt
    return column.desc() if sort_order == "desc" else column.asc()


@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
    searchTerm: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    conditions = [models.User.deletedAt.is_(None)]
    if searchTerm:
        like = f"%{searchTerm}%"
        conditions.append(or_(models.User.name.ilike(like), models.User.email.ilike(like)))
    if name:
        conditions.append(models.User.name == name)
    if email:
        conditions.append(models.User.email == email)

    base = select(models.User).where(*conditions)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(_order_by(models.User, pg.sortBy, pg.sortOrder)).offset(pg.skip).limit(pg.limit)
    )
    users = [model_to_dict(u, exclude=("password",)) for u in result.scalars().all()]
    return send_response(
        message="Users fetched successfully",
        data=users,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )


@router.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(admin_only)):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or user.deletedAt is not None:
        raise ApiError(404, "User Not Found")
    return send_response(message="User fetched successfully", data=model_to_dict(user, exclude=("password",)))


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
        .options(selectinload(models.User.vendor), selectinload(models.User.customer))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ApiError(404, "User Not Found")

    if user.role == "VENDOR" and user.vendor:
        user.vendor.isSuspended = payload.isSuspended
    elif user.role == "CUSTOMER" and user.customer:
        user.customer.isSuspended = payload.isSuspended

    await db.commit()
    return send_response(message="User Data Updated Successfully", data=None)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(admin_only)):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
        .options(selectinload(models.User.vendor), selectinload(models.User.customer))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ApiError(404, "User Not Found")

    if user.role == "VENDOR" and user.vendor:
        user.vendor.isDeleted = True
    elif user.role == "CUSTOMER" and user.customer:
        user.customer.isDeleted = True
    user.deletedAt = datetime.now(timezone.utc)

    await db.commit()
    return send_response(message="User successfully deleted", data=None)


@router.patch("/shop/{shop_id}")
async def blacklist_shop(
    shop_id: str,
    payload: BlacklistShopRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
):
    result = await db.execute(select(models.Shop).where(models.Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if shop is None:
        raise ApiError(404, "Shop not found")
    shop.isBlackListed = payload.isBlackListed
    await db.commit()
    return send_response(message="Vendor shop blacklisted successfully", data=None)


@router.post("/categories")
async def create_category(
    payload: CreateCategoryRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
):
    existing = await db.execute(select(models.Category).where(models.Category.name == payload.name))
    if existing.scalar_one_or_none() is not None:
        raise ApiError(400, "Category with this name already exists")
    category = models.Category(name=payload.name, description=payload.description)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return send_response(message="Category created successfully", data=model_to_dict(category))


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
    page: Optional[int] = None,
    limit: Optional[int] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    base = select(models.Category).where(models.Category.deletedAt.is_(None))
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(_order_by(models.Category, pg.sortBy, pg.sortOrder)).offset(pg.skip).limit(pg.limit)
    )
    categories = [model_to_dict(c) for c in result.scalars().all()]
    return send_response(
        message="Categories fetched successfully",
        data=categories,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )


@router.get("/categories/{category_id}")
async def get_category(category_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(admin_only)):
    result = await db.execute(select(models.Category).where(models.Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise ApiError(404, "Category not found")
    return send_response(message="Category fetched successfully", data=model_to_dict(category))


@router.patch("/categories/{category_id}")
async def update_category(
    category_id: str,
    payload: UpdateCategoryRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
):
    result = await db.execute(select(models.Category).where(models.Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise ApiError(404, "Category not found")

    if payload.name is not None:
        clash = await db.execute(
            select(models.Category).where(
                models.Category.name == payload.name, models.Category.id != category_id
            )
        )
        if clash.scalar_one_or_none() is not None:
            raise ApiError(400, "Category with this name already exists")
        category.name = payload.name
    if payload.description is not None:
        category.description = payload.description

    await db.commit()
    await db.refresh(category)
    return send_response(message="Category updated successfully", data=model_to_dict(category))


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(admin_only)):
    result = await db.execute(select(models.Category).where(models.Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise ApiError(404, "Category not found")
    category.deletedAt = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(category)
    return send_response(message="Category deleted successfully", data=model_to_dict(category))
