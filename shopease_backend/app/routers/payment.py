"""Payment routes — /api/v1/payment."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.config import settings
from app.core.errors import ApiError
from app.core.pagination import calculate_pagination
from app.core.response import send_response
from app.database import get_db
from app.deps import customer_id_of, require_roles
from app.schemas import CreatePaymentIntentRequest, PaymentConfirmRequest
from app.serializers import serialize_payment

router = APIRouter(prefix="/payment", tags=["payment"])

admin_only = require_roles("ADMIN", "SUPER_ADMIN")
customer_only = require_roles("CUSTOMER")

stripe.api_key = settings.stripe_secret_key


@router.post("/create-payment-intent")
async def create_payment_intent(
    payload: CreatePaymentIntentRequest,
    _customer=Depends(customer_only),
):
    if not settings.stripe_secret_key:
        raise ApiError(500, "Stripe is not configured")

    def _create():
        return stripe.PaymentIntent.create(
            amount=int(payload.amount * 100),
            currency="usd",
            payment_method_types=["card"],
        )

    try:
        intent = await asyncio.to_thread(_create)
    except stripe.error.StripeError as exc:  # type: ignore[attr-defined]
        raise ApiError(400, getattr(exc, "user_message", None) or str(exc))

    return send_response(
        status_code=201,
        message="Payment Intent Created Successfully.",
        data=json.loads(str(intent)),
    )


@router.post("/payment-confirm")
async def confirm_payment(
    payload: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current=Depends(customer_only),
):
    # Customers may only record payments against their own customer profile.
    if payload.customerId != customer_id_of(current):
        raise ApiError(403, "Forbidden")

    payment = models.Payment(
        orderId=payload.orderId,
        customerId=payload.customerId,
        amount=payload.amount,
        transactionId=payload.transactionId,
        status=payload.status,
        metadata_=payload.metadata,
    )
    db.add(payment)

    if payload.status == "SUCCESS":
        order_result = await db.execute(
            select(models.Order)
            .where(models.Order.id == payload.orderId)
            .options(selectinload(models.Order.order_items))
        )
        order = order_result.scalar_one_or_none()
        if order is None:
            raise ApiError(404, "Order not found")
        order.status = "COMPLETED"

        for item in order.order_items:
            product_result = await db.execute(
                select(models.Product).where(models.Product.id == item.productId)
            )
            product = product_result.scalar_one_or_none()
            if product is not None:
                product.inventory = max(0, product.inventory - item.quantity)

    await db.commit()
    await db.refresh(payment)
    return send_response(status_code=201, message="Payment Saved Successfully.", data=serialize_payment(payment))


@router.get("")
async def get_payments(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_only),
    page: Optional[int] = Query(default=None),
    limit: Optional[int] = Query(default=None),
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
):
    pg = calculate_pagination(page, limit, sortBy, sortOrder)
    base = select(models.Payment).where(models.Payment.status == "SUCCESS")
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    column = getattr(models.Payment, pg.sortBy, None) or models.Payment.createdAt
    ordering = column.desc() if pg.sortOrder == "desc" else column.asc()
    result = await db.execute(base.order_by(ordering).offset(pg.skip).limit(pg.limit))
    payments = [serialize_payment(p) for p in result.scalars().all()]
    return send_response(
        message="Payments fetched successfully",
        data=payments,
        meta={"page": pg.page, "limit": pg.limit, "total": total or 0},
    )
