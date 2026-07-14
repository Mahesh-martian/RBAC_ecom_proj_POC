"""Shop routes — /api/v1/shop."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.cloudinary_helper import upload_to_cloudinary
from app.core.errors import ApiError
from app.core.pagination import calculate_pagination
from app.core.response import send_response
from app.database import get_db
from app.deps import require_roles, vendor_id_of
from app.schemas import CreateShopRequest
from app.serializers import serialize_shop

router = APIRouter(prefix="/shop", tags=["shop"])

vendor_only = require_roles("VENDOR")

_DETAIL_OPTIONS = (
    selectinload(models.Shop.products).selectinload(models.Product.reviews).selectinload(models.Review.customer),
    selectinload(models.Shop.vendor).selectinload(models.Vendor.follows),
)


@router.post("")
async def create_shop(
    data: str = Form(...),
    file: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_only),
):
    payload = CreateShopRequest(**json.loads(data))
    logo = payload.logo
    if file is not None:
        uploaded = await upload_to_cloudinary(file)
        if uploaded:
            logo = uploaded

    shop = models.Shop(
        name=payload.name,
        description=payload.description,
        logo=logo,
        vendorId=vendor_id_of(user),
    )
    db.add(shop)
    await db.commit()
    await db.refresh(shop)
    return send_response(status_code=201, message="Shop Created Successfully.", data=serialize_shop(shop))


@router.get("")
async def get_my_shop(db: AsyncSession = Depends(get_db), user=Depends(vendor_only)):
    result = await db.execute(select(models.Shop).where(models.Shop.vendorId == vendor_id_of(user)))
    shop = result.scalar_one_or_none()
    if shop is None:
        raise ApiError(404, "Shop not found")
    return send_response(message="Shop fetched successfully", data=serialize_shop(shop))


@router.get("/single/{shop_id}")
async def get_single_shop(shop_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Shop).where(models.Shop.id == shop_id).options(*_DETAIL_OPTIONS)
    )
    shop = result.scalar_one_or_none()
    if shop is None:
        raise ApiError(404, "Shop not found")
    return send_response(message="Shop detail fetched successfully", data=serialize_shop(shop, detailed=True))


@router.get("/all")
async def get_all_shops(
    db: AsyncSession = Depends(get_db),
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    base = select(models.Shop).where(models.Shop.isBlackListed.is_(False))
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    column = getattr(models.Shop, pg.sortBy, None) or models.Shop.createdAt
    ordering = column.desc() if pg.sortOrder == "desc" else column.asc()
    result = await db.execute(base.options(*_DETAIL_OPTIONS).order_by(ordering).offset(pg.skip).limit(pg.limit))
    shops = [serialize_shop(s, detailed=True) for s in result.scalars().unique().all()]
    return send_response(
        message="Shops fetched successfully",
        data=shops,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )
