"""Follow routes — /api/v1/follows."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.errors import ApiError
from app.core.response import model_to_dict, send_response
from app.database import get_db
from app.deps import customer_id_of, require_roles, vendor_id_of
from app.schemas import FollowRequest

router = APIRouter(prefix="/follows", tags=["follows"])

customer_only = require_roles("CUSTOMER")
vendor_only = require_roles("VENDOR")


@router.post("")
async def follow_vendor(
    payload: FollowRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(customer_only),
):
    customer_id = customer_id_of(user)
    existing = await db.execute(
        select(models.Follow).where(
            models.Follow.customerId == customer_id,
            models.Follow.vendorId == payload.vendorId,
            models.Follow.isDeleted.is_(False),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ApiError(400, "You are already following this vendor")

    follow = models.Follow(customerId=customer_id, vendorId=payload.vendorId)
    db.add(follow)
    await db.commit()
    await db.refresh(follow)
    return send_response(status_code=201, message="Vendor followed successfully", data=model_to_dict(follow))


@router.get("")
async def my_follower_count(db: AsyncSession = Depends(get_db), user=Depends(vendor_only)):
    count = await db.scalar(
        select(func.count()).select_from(models.Follow).where(models.Follow.vendorId == vendor_id_of(user))
    )
    return send_response(message="Follower count fetched successfully", data=count or 0)


@router.get("/{vendor_id}")
async def follower_count(vendor_id: str, db: AsyncSession = Depends(get_db)):
    count = await db.scalar(
        select(func.count())
        .select_from(models.Follow)
        .where(models.Follow.vendorId == vendor_id, models.Follow.isDeleted.is_(False))
    )
    return send_response(message="Follower count fetched successfully", data=count or 0)


@router.delete("/{vendor_id}")
async def unfollow_vendor(vendor_id: str, db: AsyncSession = Depends(get_db), user=Depends(customer_only)):
    customer_id = customer_id_of(user)
    result = await db.execute(
        select(models.Follow).where(
            models.Follow.vendorId == vendor_id,
            models.Follow.customerId == customer_id,
            models.Follow.isDeleted.is_(False),
        )
    )
    follow = result.scalar_one_or_none()
    if follow is None:
        raise ApiError(400, "You are not following this vendor")
    follow.isDeleted = True
    await db.commit()
    await db.refresh(follow)
    return send_response(message="Vendor unfollowed successfully", data=model_to_dict(follow))
