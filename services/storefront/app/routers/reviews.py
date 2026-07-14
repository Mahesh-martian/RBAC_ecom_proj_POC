"""Review routes — /api/v1/reviews."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.errors import ApiError
from app.core.pagination import calculate_pagination
from app.core.response import model_to_dict, send_response
from app.database import get_db
from app.deps import customer_id_of, require_roles, vendor_id_of
from app.schemas import CreateReviewRequest
from app.serializers import serialize_review_admin

router = APIRouter(prefix="/reviews", tags=["reviews"])

customer_only = require_roles("CUSTOMER")
vendor_or_admin = require_roles("VENDOR", "ADMIN", "SUPER_ADMIN")


@router.post("")
async def create_review(
    payload: CreateReviewRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(customer_only),
):
    customer_id = customer_id_of(user)

    purchased = await db.execute(
        select(models.OrderItem.id)
        .join(models.Order, models.Order.id == models.OrderItem.orderId)
        .where(
            models.Order.customerId == customer_id,
            models.Order.status == "COMPLETED",
            models.OrderItem.productId == payload.productId,
        )
        .limit(1)
    )
    if purchased.first() is None:
        raise ApiError(400, "You can only review products you have purchased")

    existing = await db.execute(
        select(models.Review).where(
            models.Review.customerId == customer_id,
            models.Review.productId == payload.productId,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ApiError(400, "You have already reviewed this product")

    review = models.Review(
        customerId=customer_id,
        productId=payload.productId,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return send_response(status_code=201, message="Review Created Successfully.", data=model_to_dict(review))


@router.get("")
async def get_reviews(
    db: AsyncSession = Depends(get_db),
    user=Depends(vendor_or_admin),
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    base = select(models.Review).options(
        selectinload(models.Review.product), selectinload(models.Review.customer)
    )
    if user.get("role") == "VENDOR":
        base = base.join(models.Product, models.Product.id == models.Review.productId).where(
            models.Product.vendorId == vendor_id_of(user)
        )

    total = await db.scalar(select(func.count()).select_from(base.order_by(None).subquery()))
    column = getattr(models.Review, pg.sortBy, None) or models.Review.createdAt
    ordering = column.desc() if pg.sortOrder == "desc" else column.asc()
    result = await db.execute(base.order_by(ordering).offset(pg.skip).limit(pg.limit))
    reviews = [serialize_review_admin(r) for r in result.scalars().unique().all()]
    return send_response(
        message="Reviews fetched successfully",
        data=reviews,
        meta={"total": total or 0, "page": pg.page, "limit": pg.limit},
    )
