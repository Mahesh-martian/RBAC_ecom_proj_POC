"""
Order management API endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.schemas import (
    OrderCreateRequest, OrderResponse, OrderCancelRequest, OrderListResponse
)
from app.services.order_service import OrderService
from app.dependencies import CurrentUserDep, AdminUserDep, DBSessionDep
from app.models import Cart, OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart"
)
async def create_order(
    request: OrderCreateRequest,
    current_user: CurrentUserDep,
    session: DBSessionDep,
) -> OrderResponse:
    """
    Create new order from shopping cart.
    
    Request body:
    - **cart_id**: ID of cart to convert to order
    - **shipping_address**: Address object {street, city, state, zip, country}
    - **shipping_method**: Shipping method (standard, express, overnight)
    
    Returns: Created Order with items
    """
    from sqlalchemy import select
    
    # Get cart
    stmt = select(Cart).where(Cart.id == request.cart_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    if cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create order from another user's cart"
        )
    
    try:
        order = await OrderService.create_order(current_user.id, cart, request, session)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=dict,
    summary="Get user's orders"
)
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user: CurrentUserDep = None,
    session: DBSessionDep = None,
) -> dict:
    """
    Get current user's order history with pagination.
    """
    orders, total = await OrderService.list_user_orders(
        current_user.id, session, skip=skip, limit=limit
    )
    
    return {
        "items": [OrderListResponse.model_validate(o) for o in orders],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details"
)
async def get_order(
    order_id: int,
    current_user: CurrentUserDep,
    session: DBSessionDep,
) -> OrderResponse:
    """
    Get detailed order information.
    Users can only view their own orders.
    """
    order = await OrderService.get_order_by_id(order_id, session)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another user's order"
        )
    
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order"
)
async def cancel_order(
    order_id: int,
    request: OrderCancelRequest,
    current_user: CurrentUserDep,
    session: DBSessionDep,
) -> OrderResponse:
    """
    Cancel order and reverse inventory.
    Can only cancel pending or paid orders.
    Users can only cancel their own orders.
    """
    order = await OrderService.get_order_by_id(order_id, session)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot cancel another user's order"
        )
    
    try:
        order = await OrderService.cancel_order(
            order_id, request.reason, session
        )
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============ Admin Endpoints ============

@router.get(
    "/admin/all",
    response_model=dict,
    summary="Get all orders (Admin only)"
)
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    current_user: AdminUserDep = None,
    session: DBSessionDep = None,
) -> dict:
    """
    Get all orders. Admin only. Supports filtering by status.
    """
    from sqlalchemy import select, func
    
    stmt = select(Order).order_by(Order.created_at.desc())
    
    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
            stmt = stmt.where(Order.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    # Get count
    count_stmt = select(func.count()).select_from(Order)
    if status_filter:
        count_stmt = count_stmt.where(Order.status == OrderStatus(status_filter))
    
    result = await session.execute(count_stmt)
    total = result.scalar() or 0
    
    # Get paginated results
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    orders = result.scalars().all()
    
    return {
        "items": [OrderListResponse.model_validate(o) for o in orders],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status (Admin only)"
)
async def update_order_status(
    order_id: int,
    new_status: str,
    tracking_number: Optional[str] = None,
    current_user: AdminUserDep = None,
    session: DBSessionDep = None,
) -> OrderResponse:
    """
    Update order status. Admin only.
    Valid statuses: pending, paid, shipped, delivered, canceled, refunded
    """
    try:
        status_enum = OrderStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {new_status}"
        )
    
    try:
        order = await OrderService.update_order_status(
            order_id, status_enum, session, tracking_number
        )
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/admin/stats",
    summary="Get dashboard statistics (Admin only)"
)
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: AdminUserDep = None,
    session: DBSessionDep = None,
) -> dict:
    """
    Get dashboard statistics for admin dashboard.
    """
    stats = await OrderService.get_dashboard_stats(session, days)
    return stats


# Import Order model for use in admin endpoints
from app.models import Order
