"""
Product catalog API endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.schemas import (
    ProductCreateRequest, ProductUpdateRequest, ProductResponse, 
    ProductListParams, ReviewResponse
)
from app.services.product_service import ProductService
from app.dependencies import CurrentUserDep, AdminUserDep, DBSessionDep, OptionalUserDep
from app.models import User, ProductReview

router = APIRouter(prefix="/products", tags=["products"])


@router.get(
    "",
    response_model=dict,
    summary="List products"
)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    in_stock_only: bool = False,
    session: DBSessionDep = None,
) -> dict:
    """
    List products with filtering and pagination.
    
    Query parameters:
    - **skip**: Number of results to skip (default: 0)
    - **limit**: Number of results to return (default: 20, max: 100)
    - **category_id**: Filter by category
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **search**: Search term (searches name, description, SKU)
    - **sort_by**: Sort column (created_at, price, rating, name)
    - **sort_order**: asc or desc (default: desc)
    - **in_stock_only**: Only show in-stock products
    """
    params = ProductListParams(
        skip=skip,
        limit=limit,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        in_stock_only=in_stock_only,
    )
    
    products, total = await ProductService.list_products(params, session)
    
    return {
        "items": [ProductResponse.model_validate(p) for p in products],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product details"
)
async def get_product(
    product_id: int,
    session: DBSessionDep,
) -> ProductResponse:
    """
    Get detailed product information including reviews and ratings.
    """
    product = await ProductService.get_product_by_id(product_id, session)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}/reviews",
    response_model=List[ReviewResponse],
    summary="Get product reviews"
)
async def get_product_reviews(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    session: DBSessionDep = None,
) -> List[ReviewResponse]:
    """
    Get reviews for a product with pagination.
    """
    from sqlalchemy import select
    
    product = await ProductService.get_product_by_id(product_id, session)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get reviews
    stmt = (
        select(ProductReview)
        .where(ProductReview.product_id == product_id)
        .order_by(ProductReview.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    reviews = result.scalars().all()
    
    return [ReviewResponse.model_validate(r) for r in reviews]


@router.post(
    "/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product review"
)
async def create_review(
    product_id: int,
    request: dict,
    current_user: CurrentUserDep,
    session: DBSessionDep,
) -> ReviewResponse:
    """
    Post a review for a purchased product.
    Requires authentication.
    """
    from app.models import Order, OrderItem
    from sqlalchemy import select, and_
    
    product = await ProductService.get_product_by_id(product_id, session)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user purchased this product (verified purchase)
    stmt = (
        select(OrderItem)
        .join(Order)
        .where(
            and_(
                Order.user_id == current_user.id,
                OrderItem.product_id == product_id,
            )
        )
    )
    result = await session.execute(stmt)
    purchased = result.scalar_one_or_none() is not None
    
    # Create review
    review = ProductReview(
        product_id=product_id,
        user_id=current_user.id,
        rating=request.get("rating"),
        title=request.get("title"),
        content=request.get("content"),
        is_verified_purchase=purchased,
    )
    
    session.add(review)
    await session.commit()
    await session.refresh(review)
    
    # Update product rating
    await ProductService.update_product_rating(product_id, session)
    
    return ReviewResponse.model_validate(review)


# ============ Admin Endpoints ============

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product (Admin only)"
)
async def create_product(
    request: ProductCreateRequest,
    current_user: AdminUserDep,
    session: DBSessionDep,
) -> ProductResponse:
    """
    Create new product. Admin only.
    """
    try:
        product = await ProductService.create_product(request, session)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product (Admin only)"
)
async def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    current_user: AdminUserDep,
    session: DBSessionDep,
) -> ProductResponse:
    """
    Update product details. Admin only.
    """
    try:
        product = await ProductService.update_product(product_id, request, session)
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product (Admin only)"
)
async def delete_product(
    product_id: int,
    current_user: AdminUserDep,
    session: DBSessionDep,
) -> None:
    """
    Delete product (soft delete). Admin only.
    """
    deleted = await ProductService.delete_product(product_id, session, soft_delete=True)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
