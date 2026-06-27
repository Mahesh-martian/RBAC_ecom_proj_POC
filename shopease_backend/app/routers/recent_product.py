"""Recent product routes — /api/v1/recent-products."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.response import send_response
from app.database import get_db
from app.deps import require_roles
from app.schemas import RecentProductRequest
from app.serializers import serialize_recent_product

router = APIRouter(prefix="/recent-products", tags=["recent-products"])

customer_only = require_roles("CUSTOMER")


@router.post("")
async def save_recent_products(
    payload: RecentProductRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(customer_only),
):
    user_id = user["id"]
    for product_id in payload.products:
        db.add(models.RecentProduct(userId=user_id, productId=product_id))
    await db.commit()
    return send_response(status_code=201, message="Recent products saved successfully.", data="")


@router.get("")
async def get_recent_products(db: AsyncSession = Depends(get_db), user=Depends(customer_only)):
    result = await db.execute(
        select(models.RecentProduct)
        .where(models.RecentProduct.userId == user["id"])
        .options(selectinload(models.RecentProduct.product))
        .order_by(models.RecentProduct.visitedAt.desc())
        .limit(10)
    )
    recents = [serialize_recent_product(r) for r in result.scalars().all()]
    return send_response(status_code=201, message="Recent products fetched successfully.", data=recents)
