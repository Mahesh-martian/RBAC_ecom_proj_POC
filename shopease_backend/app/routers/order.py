"""Order routes — /api/v1/orders."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.core.pagination import calculate_pagination
from app.core.response import send_response
from app.database import get_db
from app.deps import customer_id_of, require_roles, vendor_id_of
from app.schemas import CreateOrderRequest
from app.serializers import serialize_order

router = APIRouter(prefix="/orders", tags=["orders"])

customer_only = require_roles("CUSTOMER")
any_role = require_roles("CUSTOMER", "VENDOR", "ADMIN", "SUPER_ADMIN")


@router.post("")
async def create_order(
    payload: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(customer_only),
):
    order = models.Order(
        customerId=customer_id_of(user),
        vendorId=payload.vendorId,
        totalAmount=payload.totalAmount,
        status="PENDING",
    )
    db.add(order)
    await db.flush()

    for item in payload.products:
        db.add(
            models.OrderItem(
                orderId=order.id,
                productId=item.productId,
                quantity=item.quantity,
                price=item.price,
                discount=item.discount,
            )
        )

    await db.commit()
    result = await db.execute(
        select(models.Order)
        .where(models.Order.id == order.id)
        .options(selectinload(models.Order.order_items))
    )
    created = result.scalar_one()
    return send_response(status_code=201, message="Order created successfully", data=serialize_order(created))


@router.get("")
async def get_orders(
    db: AsyncSession = Depends(get_db),
    user=Depends(any_role),
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    role = user.get("role")

    base = select(models.Order).options(selectinload(models.Order.order_items))
    with_parties = False
    if role == "CUSTOMER":
        base = base.where(models.Order.customerId == customer_id_of(user))
    elif role == "VENDOR":
        base = base.where(models.Order.vendorId == vendor_id_of(user))
    else:  # ADMIN / SUPER_ADMIN
        base = base.where(models.Order.deletedAt.is_(None)).options(
            selectinload(models.Order.customer), selectinload(models.Order.vendor)
        )
        with_parties = True

    total = await db.scalar(select(func.count()).select_from(base.order_by(None).subquery()))
    column = getattr(models.Order, pg.sortBy, None) or models.Order.createdAt
    ordering = column.desc() if pg.sortOrder == "desc" else column.asc()
    result = await db.execute(base.order_by(ordering).offset(pg.skip).limit(pg.limit))
    orders = [serialize_order(o, with_parties=with_parties) for o in result.scalars().unique().all()]
    return send_response(
        message="Orders fetched successfully",
        data=orders,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )
