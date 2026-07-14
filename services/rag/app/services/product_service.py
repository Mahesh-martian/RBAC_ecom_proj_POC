"""
Product service for catalog management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
import logging

from app.models import Product, Category, ProductReview
from app.schemas import ProductCreateRequest, ProductUpdateRequest, ProductResponse, ProductListParams

logger = logging.getLogger(__name__)


class ProductService:
    """Product management service."""
    
    @staticmethod
    async def get_product_by_id(
        product_id: int,
        session: AsyncSession
    ) -> Optional[Product]:
        """
        Get product by ID with related data.
        
        Args:
            product_id: Product ID
            session: Database session
            
        Returns:
            Product object or None
        """
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.reviews),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_product_by_sku(
        sku: str,
        session: AsyncSession
    ) -> Optional[Product]:
        """Get product by SKU."""
        stmt = select(Product).where(Product.sku == sku)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_products(
        params: ProductListParams,
        session: AsyncSession
    ) -> Tuple[List[Product], int]:
        """
        List products with filtering and pagination.
        
        Args:
            params: Query parameters
            session: Database session
            
        Returns:
            Tuple of (products list, total count)
        """
        # Build base query
        stmt = select(Product).where(Product.is_active == True)
        
        # Apply filters
        if params.category_id:
            stmt = stmt.where(Product.category_id == params.category_id)
        
        if params.min_price is not None:
            stmt = stmt.where(Product.price >= params.min_price)
        
        if params.max_price is not None:
            stmt = stmt.where(Product.price <= params.max_price)
        
        if params.in_stock_only:
            stmt = stmt.where(Product.stock_qty > 0)
        
        if params.search:
            search_term = f"%{params.search}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term),
                )
            )
        
        # Get total count
        count_stmt = select(func.count()).select_from(Product)
        # Apply same filters to count
        if params.category_id:
            count_stmt = count_stmt.where(Product.category_id == params.category_id)
        if params.min_price is not None:
            count_stmt = count_stmt.where(Product.price >= params.min_price)
        if params.max_price is not None:
            count_stmt = count_stmt.where(Product.price <= params.max_price)
        if params.in_stock_only:
            count_stmt = count_stmt.where(Product.stock_qty > 0)
        
        result = await session.execute(count_stmt)
        total = result.scalar() or 0
        
        # Apply sorting
        sort_column = getattr(Product, params.sort_by, Product.created_at)
        if params.sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_column.asc())
        else:
            stmt = stmt.order_by(sort_column.desc())
        
        # Apply pagination
        stmt = stmt.offset(params.skip).limit(params.limit)
        
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        return products, total
    
    @staticmethod
    async def create_product(
        request: ProductCreateRequest,
        session: AsyncSession
    ) -> Product:
        """
        Create new product.
        
        Args:
            request: Product creation request
            session: Database session
            
        Returns:
            Created Product object
        """
        # Check if SKU already exists
        existing = await ProductService.get_product_by_sku(request.sku, session)
        if existing:
            logger.warning(f"SKU already exists: {request.sku}")
            raise ValueError(f"Product with SKU {request.sku} already exists")
        
        product = Product(
            sku=request.sku,
            name=request.name,
            description=request.description,
            category_id=request.category_id,
            price=request.price,
            cost=request.cost,
            currency=request.currency,
            stock_qty=request.stock_qty,
            reorder_level=request.reorder_level,
            images=request.images,
            tags=request.tags,
            metadata=request.metadata,
        )
        
        session.add(product)
        await session.commit()
        await session.refresh(product)
        
        logger.info(f"Product created: {product.id} - {product.name}")
        return product
    
    @staticmethod
    async def update_product(
        product_id: int,
        request: ProductUpdateRequest,
        session: AsyncSession
    ) -> Product:
        """
        Update existing product.
        
        Args:
            product_id: Product ID
            request: Update request data
            session: Database session
            
        Returns:
            Updated Product object
        """
        product = await ProductService.get_product_by_id(product_id, session)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Update only provided fields
        if request.name is not None:
            product.name = request.name
        if request.description is not None:
            product.description = request.description
        if request.price is not None:
            product.price = request.price
        if request.cost is not None:
            product.cost = request.cost
        if request.stock_qty is not None:
            product.stock_qty = request.stock_qty
        if request.reorder_level is not None:
            product.reorder_level = request.reorder_level
        if request.images is not None:
            product.images = request.images
        if request.tags is not None:
            product.tags = request.tags
        if request.metadata is not None:
            product.metadata = request.metadata
        if request.is_active is not None:
            product.is_active = request.is_active
        
        await session.commit()
        await session.refresh(product)
        
        logger.info(f"Product updated: {product_id}")
        return product
    
    @staticmethod
    async def delete_product(
        product_id: int,
        session: AsyncSession,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete product (soft delete by default).
        
        Args:
            product_id: Product ID
            session: Database session
            soft_delete: If True, set is_active=False; if False, hard delete
            
        Returns:
            True if deleted, False if not found
        """
        product = await ProductService.get_product_by_id(product_id, session)
        if not product:
            return False
        
        if soft_delete:
            product.is_active = False
            await session.commit()
            logger.info(f"Product soft-deleted: {product_id}")
        else:
            await session.delete(product)
            await session.commit()
            logger.info(f"Product hard-deleted: {product_id}")
        
        return True
    
    @staticmethod
    async def update_stock(
        product_id: int,
        quantity_change: int,
        reason: str,
        session: AsyncSession,
        details: Optional[dict] = None
    ) -> Product:
        """
        Update product stock and log change.
        
        Args:
            product_id: Product ID
            quantity_change: Quantity to add (positive) or remove (negative)
            reason: Reason for change (sale, restock, adjustment, return, damage)
            session: Database session
            details: Optional metadata
            
        Returns:
            Updated Product object
        """
        from app.models import InventoryLog
        
        product = await ProductService.get_product_by_id(product_id, session)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        new_stock = product.stock_qty + quantity_change
        if new_stock < 0:
            raise ValueError(f"Cannot reduce stock below 0. Current: {product.stock_qty}, Change: {quantity_change}")
        
        product.stock_qty = new_stock
        
        # Log inventory change
        log = InventoryLog(
            product_id=product_id,
            change_qty=quantity_change,
            reason=reason,
            details=details,
        )
        
        session.add(log)
        await session.commit()
        await session.refresh(product)
        
        logger.info(f"Stock updated for product {product_id}: {quantity_change} ({reason})")
        return product
    
    @staticmethod
    async def get_low_stock_products(
        session: AsyncSession,
        limit: int = 10
    ) -> List[Product]:
        """
        Get products with stock below reorder level.
        
        Args:
            session: Database session
            limit: Maximum results
            
        Returns:
            List of products needing restock
        """
        stmt = (
            select(Product)
            .where(
                and_(
                    Product.stock_qty <= Product.reorder_level,
                    Product.is_active == True
                )
            )
            .order_by(Product.stock_qty.asc())
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def update_product_rating(
        product_id: int,
        session: AsyncSession
    ) -> None:
        """
        Recalculate and update product rating from reviews.
        
        Args:
            product_id: Product ID
            session: Database session
        """
        # Calculate average rating
        stmt = select(
            func.avg(ProductReview.rating),
            func.count(ProductReview.id)
        ).where(ProductReview.product_id == product_id)
        
        result = await session.execute(stmt)
        avg_rating, count = result.one()
        
        product = await ProductService.get_product_by_id(product_id, session)
        if product:
            product.rating = float(avg_rating or 0)
            product.rating_count = int(count or 0)
            await session.commit()
