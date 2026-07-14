"""
Shopping cart API endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import logging

from app.schemas import CartItemRequest, CartResponse, CartItemResponse
from app.dependencies import CurrentUserDep, OptionalUserDep, DBSessionDep
from app.models import Cart, Product
from app.services.product_service import ProductService
from sqlalchemy import select
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/carts", tags=["cart"])


async def get_or_create_cart(
    user_id: Optional[int],
    session_id: Optional[str],
    session: AsyncSession,
) -> Cart:
    """Helper to get or create cart based on user_id or session_id."""
    if user_id:
        stmt = select(Cart).where(Cart.user_id == user_id)
    else:
        stmt = select(Cart).where(Cart.session_id == session_id)
    
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        cart = Cart(
            user_id=user_id,
            session_id=session_id or str(uuid.uuid4()),
            items=[],
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        session.add(cart)
        await session.commit()
        await session.refresh(cart)
    
    return cart


async def format_cart_response(cart: Cart, session: AsyncSession) -> CartResponse:
    """Format cart data for response with calculated totals."""
    items_response = []
    subtotal = 0.0
    
    if cart.items:
        for item in cart.items:
            product = await ProductService.get_product_by_id(item["product_id"], session)
            if product:
                line_total = product.price * item["quantity"]
                subtotal += line_total
                
                items_response.append(CartItemResponse(
                    product_id=product.id,
                    quantity=item["quantity"],
                    variant_options=item.get("variant_options"),
                    price=product.price,
                    subtotal=line_total,
                    product_name=product.name,
                    product_image=product.images[0]["url"] if product.images else None,
                ))
    
    # Calculate tax and shipping
    tax = subtotal * 0.1  # 10% tax
    shipping = 10.0 if subtotal < 50 else 0.0  # Free shipping over $50
    total = subtotal + tax + shipping
    
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=items_response,
        subtotal=subtotal,
        tax=tax,
        shipping=shipping,
        total=total,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create cart"
)
async def create_cart(
    current_user: OptionalUserDep = None,
    session: DBSessionDep = None,
) -> CartResponse:
    """
    Create new shopping cart.
    For authenticated users, uses user_id.
    For guests, generates session_id.
    """
    user_id = current_user.id if current_user else None
    session_id = str(uuid.uuid4()) if not current_user else None
    
    cart = await get_or_create_cart(user_id, session_id, session)
    
    logger.info(f"Cart created: {cart.id} (user: {user_id}, session: {session_id})")
    
    return await format_cart_response(cart, session)


@router.get(
    "/{cart_id}",
    response_model=CartResponse,
    summary="Get cart"
)
async def get_cart(
    cart_id: int,
    current_user: OptionalUserDep = None,
    session: DBSessionDep = None,
) -> CartResponse:
    """
    Get cart contents with calculated totals.
    """
    stmt = select(Cart).where(Cart.id == cart_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    # Verify ownership
    if current_user and cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's cart"
        )
    
    return await format_cart_response(cart, session)


@router.post(
    "/{cart_id}/items",
    response_model=CartResponse,
    summary="Add item to cart"
)
async def add_to_cart(
    cart_id: int,
    request: CartItemRequest,
    current_user: OptionalUserDep = None,
    session: DBSessionDep = None,
) -> CartResponse:
    """
    Add product to cart.
    If product already in cart, update quantity.
    """
    stmt = select(Cart).where(Cart.id == cart_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    if current_user and cart.user_id is not None and cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's cart"
        )

    # Adopt an unowned guest cart for the authenticated user.
    if current_user and cart.user_id is None:
        cart.user_id = current_user.id
    
    # Verify product exists
    product = await ProductService.get_product_by_id(request.product_id, session)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product.stock_qty < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {product.stock_qty}"
        )
    
    # Update cart items
    if not cart.items:
        cart.items = []
    
    # Check if product already in cart
    existing_item = None
    for item in cart.items:
        if item["product_id"] == request.product_id:
            existing_item = item
            break
    
    if existing_item:
        existing_item["quantity"] += request.quantity
        if existing_item["quantity"] > product.stock_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity exceeds stock. Available: {product.stock_qty}"
            )
    else:
        cart.items.append({
            "product_id": request.product_id,
            "quantity": request.quantity,
            "variant_options": request.variant_options,
        })
    
    cart.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(cart)
    
    logger.info(f"Item added to cart {cart_id}: product {request.product_id}, qty {request.quantity}")
    
    return await format_cart_response(cart, session)


@router.patch(
    "/{cart_id}/items/{item_index}",
    response_model=CartResponse,
    summary="Update cart item quantity"
)
async def update_cart_item(
    cart_id: int,
    item_index: int,
    quantity: int = Query(ge=1),
    current_user: OptionalUserDep = None,
    session: DBSessionDep = None,
) -> CartResponse:
    """
    Update quantity of item in cart.
    """
    stmt = select(Cart).where(Cart.id == cart_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    if current_user and cart.user_id is not None and cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's cart"
        )

    # Adopt an unowned guest cart for the authenticated user.
    if current_user and cart.user_id is None:
        cart.user_id = current_user.id
    
    if not cart.items or item_index >= len(cart.items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    # Verify stock
    product = await ProductService.get_product_by_id(
        cart.items[item_index]["product_id"], session
    )
    if product.stock_qty < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {product.stock_qty}"
        )
    
    cart.items[item_index]["quantity"] = quantity
    cart.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(cart)
    
    return await format_cart_response(cart, session)


@router.delete(
    "/{cart_id}/items/{item_index}",
    response_model=CartResponse,
    summary="Remove item from cart"
)
async def remove_from_cart(
    cart_id: int,
    item_index: int,
    current_user: OptionalUserDep = None,
    session: DBSessionDep = None,
) -> CartResponse:
    """
    Remove item from cart.
    """
    stmt = select(Cart).where(Cart.id == cart_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    if current_user and cart.user_id is not None and cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's cart"
        )

    # Adopt an unowned guest cart for the authenticated user.
    if current_user and cart.user_id is None:
        cart.user_id = current_user.id
    
    if not cart.items or item_index >= len(cart.items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    removed_item = cart.items.pop(item_index)
    cart.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(cart)
    
    logger.info(f"Item removed from cart {cart_id}: product {removed_item['product_id']}")
    
    return await format_cart_response(cart, session)


@router.delete(
    "/{cart_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear cart"
)
async def clear_cart(
    cart_id: int,
    current_user: OptionalUserDep = None,
    session: DBSessionDep = None,
) -> None:
    """
    Clear all items from cart.
    """
    stmt = select(Cart).where(Cart.id == cart_id)
    result = await session.execute(stmt)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    
    if current_user and cart.user_id is not None and cart.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another user's cart"
        )

    # Adopt an unowned guest cart for the authenticated user.
    if current_user and cart.user_id is None:
        cart.user_id = current_user.id
    
    cart.items = []
    cart.updated_at = datetime.utcnow()
    await session.commit()
    
    logger.info(f"Cart cleared: {cart_id}")
