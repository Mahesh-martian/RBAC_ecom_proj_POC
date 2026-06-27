"""Flash sale routes — /api/v1/flash-sale."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.errors import ApiError
from app.core.pagination import calculate_pagination
from app.core.response import model_to_dict, send_response
from app.database import get_db
from app.deps import require_roles, vendor_id_of
from app.schemas import CreateFlashSaleRequest, UpdateFlashSaleRequest
from app.serializers import serialize_flash_sale

router = APIRouter(prefix="/flash-sale", tags=["flash-sale"])

vendor_only = require_roles("VENDOR")


@router.post("")
async def create_flash_sale(
    payload: CreateFlashSaleRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_only),
):
    # A vendor may only put their own products on flash sale.
    product_result = await db.execute(
        select(models.Product).where(models.Product.id == payload.productId)
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        raise ApiError(404, "Product not found")
    if product.vendorId != vendor_id_of(user):
        raise ApiError(403, "Forbidden")

    flash_sale = models.FlashSale(
        productId=payload.productId,
        discount=payload.discount if payload.discount is not None else 0,
        startTime=payload.startTime,
        endTime=payload.endTime,
    )
    db.add(flash_sale)
    await db.commit()
    await db.refresh(flash_sale)
    return send_response(status_code=201, message="Flash Sale created successfully", data=model_to_dict(flash_sale))


@router.get("")
async def get_flash_sales(
    db: AsyncSession = Depends(get_db),
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    now = datetime.now(timezone.utc)
    active = and_(models.FlashSale.startTime <= now, models.FlashSale.endTime >= now)
    upcoming = models.FlashSale.startTime > now

    base = select(models.FlashSale).where(or_(active, upcoming)).options(
        selectinload(models.FlashSale.product)
    )
    total = await db.scalar(
        select(func.count()).select_from(select(models.FlashSale).where(active).subquery())
    )
    result = await db.execute(
        base.order_by(models.FlashSale.startTime.desc()).offset(pg.skip).limit(pg.limit)
    )
    flash_sales = [serialize_flash_sale(f, with_product=True) for f in result.scalars().all()]
    return send_response(
        message="Flash Sales fetched successfully",
        data=flash_sales,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )


@router.get("/{flash_sale_id}")
async def get_flash_sale(flash_sale_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.FlashSale).where(models.FlashSale.id == flash_sale_id))
    flash_sale = result.scalar_one_or_none()
    if flash_sale is None:
        raise ApiError(404, "Flash Sale not found")
    return send_response(message="Flash Sale fetched successfully", data=model_to_dict(flash_sale))


@router.patch("/{flash_sale_id}")
async def update_flash_sale(
    flash_sale_id: str,
    payload: UpdateFlashSaleRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_only),
):
    result = await db.execute(select(models.FlashSale).where(models.FlashSale.id == flash_sale_id))
    flash_sale = result.scalar_one_or_none()
    if flash_sale is None:
        raise ApiError(404, "Flash Sale not found")

    # A vendor may only update flash sales for their own products.
    product_result = await db.execute(
        select(models.Product).where(models.Product.id == flash_sale.productId)
    )
    product = product_result.scalar_one_or_none()
    if product is None or product.vendorId != vendor_id_of(user):
        raise ApiError(403, "Forbidden")

    if payload.discount is not None:
        flash_sale.discount = payload.discount
    if payload.startTime is not None:
        flash_sale.startTime = payload.startTime
    if payload.endTime is not None:
        flash_sale.endTime = payload.endTime

    await db.commit()
    await db.refresh(flash_sale)
    return send_response(message="Flash Sale updated successfully", data=model_to_dict(flash_sale))
