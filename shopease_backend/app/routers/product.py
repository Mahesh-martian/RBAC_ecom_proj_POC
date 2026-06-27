"""Product routes — /api/v1/products."""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.cloudinary_helper import upload_multiple_to_cloudinary
from app.core.errors import ApiError
from app.core.pagination import calculate_pagination
from app.core.response import model_to_dict, send_response
from app.database import get_db
from app.deps import require_roles, vendor_id_of
from app.schemas import CreateProductRequest, UpdateProductRequest
from app.serializers import serialize_product

router = APIRouter(prefix="/products", tags=["products"])

vendor_only = require_roles("VENDOR")


@router.post("")
async def create_product(
    data: str = Form(...),
    images: List[UploadFile] = File(default_factory=list),
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_only),
):
    if not images:
        raise ApiError(400, "At least one image is required")

    payload = CreateProductRequest(**json.loads(data))
    vendor_id = vendor_id_of(user)

    shop_result = await db.execute(select(models.Shop).where(models.Shop.vendorId == vendor_id))
    shop = shop_result.scalar_one_or_none()
    if shop is None:
        raise ApiError(404, "Shop not found")

    image_urls = await upload_multiple_to_cloudinary(images)

    product = models.Product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        discount=payload.discount or 0,
        categoryId=payload.categoryId,
        inventory=payload.inventory,
        image=image_urls,
        vendorId=vendor_id,
        shopId=shop.id,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return send_response(status_code=201, message="Product created successfully", data=model_to_dict(product))


@router.get("")
async def get_all_products(
    db: AsyncSession = Depends(get_db),
    categoryId: Optional[str] = None,
    name: Optional[str] = None,
    price: Optional[float] = None,
    discount: Optional[float] = None,
    searchTerm: Optional[str] = None,
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    conditions = [models.Product.deletedAt.is_(None)]
    if searchTerm:
        like = f"%{searchTerm}%"
        conditions.append(or_(models.Product.name.ilike(like), models.Product.description.ilike(like)))
    if categoryId:
        conditions.append(models.Product.categoryId == categoryId)
    if name:
        conditions.append(models.Product.name == name)
    if price is not None:
        conditions.append(models.Product.price == price)
    if discount is not None:
        conditions.append(models.Product.discount == discount)

    base = select(models.Product).where(*conditions)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    column = getattr(models.Product, pg.sortBy, None) or models.Product.createdAt
    ordering = column.desc() if pg.sortOrder == "desc" else column.asc()
    result = await db.execute(base.order_by(ordering).offset(pg.skip).limit(pg.limit))
    products = [model_to_dict(p) for p in result.scalars().all()]
    return send_response(
        message="Products fetched successfully",
        data=products,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )


@router.get("/vendor-product")
async def get_vendor_products(
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_only),
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    vendor_id = vendor_id_of(user)
    base = select(models.Product).where(
        models.Product.vendorId == vendor_id, models.Product.deletedAt.is_(None)
    )
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    column = getattr(models.Product, pg.sortBy, None) or models.Product.createdAt
    ordering = column.desc() if pg.sortOrder == "desc" else column.asc()
    result = await db.execute(
        base.options(selectinload(models.Product.category)).order_by(ordering).offset(pg.skip).limit(pg.limit)
    )
    products = [serialize_product(p, category_name=True) for p in result.scalars().all()]
    return send_response(
        message="Products fetched successfully",
        data=products,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )


@router.get("/{product_id}")
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Product)
        .where(models.Product.id == product_id)
        .options(
            selectinload(models.Product.reviews).selectinload(models.Review.customer),
            selectinload(models.Product.shop),
            selectinload(models.Product.category),
        )
    )
    product = result.scalar_one_or_none()
    if product is None or product.deletedAt is not None:
        raise ApiError(404, "Product not found")
    return send_response(
        message="Product fetched successfully",
        data=serialize_product(product, with_reviews=True, with_shop=True, with_category=True),
    )


@router.post("/duplicate/{product_id}")
async def duplicate_product(product_id: str, db: AsyncSession = Depends(get_db), user=Depends(vendor_only)):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise ApiError(404, "Product not found")

    # A vendor may only duplicate their own products.
    vendor_id = vendor_id_of(user)
    if product.vendorId != vendor_id:
        raise ApiError(403, "Forbidden")

    new_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        discount=product.discount,
        categoryId=product.categoryId,
        inventory=product.inventory,
        image=list(product.image or []),
        vendorId=vendor_id,
        shopId=product.shopId,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return send_response(message="Product duplicated successfully", data=model_to_dict(new_product))


@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    data: str = Form(...),
    images: List[UploadFile] = File(default_factory=list),
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_only),
):
    payload = UpdateProductRequest(**json.loads(data))
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise ApiError(404, "Product not found")

    # A vendor may only update their own products.
    if product.vendorId != vendor_id_of(user):
        raise ApiError(403, "Forbidden")

    new_urls = await upload_multiple_to_cloudinary(images) if images else []
    kept_images = payload.image if payload.image is not None else list(product.image or [])
    product.image = [*kept_images, *new_urls]

    if payload.name is not None:
        product.name = payload.name
    if payload.description is not None:
        product.description = payload.description
    if payload.price is not None:
        product.price = payload.price
    if payload.discount is not None:
        product.discount = payload.discount
    if payload.inventory is not None:
        product.inventory = payload.inventory

    await db.commit()
    await db.refresh(product)
    return send_response(message="Product updated successfully", data=model_to_dict(product))
