"""
Order service for order management and fulfillment.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from app.models import Order, OrderItem, Cart, Product, OrderStatus, User, AnalyticsEvent
from app.schemas import OrderCreateRequest, OrderResponse
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


class OrderService:
    """Order management service."""
    
    @staticmethod
    def generate_order_number() -> str:
        """
        Generate unique order number.
        Format: ORD-YYYYMMDD-XXXXXXXX (e.g., ORD-20240623-a1b2c3d4)
        """
        now = datetime.utcnow()
        date_part = now.strftime("%Y%m%d")
        random_part = str(uuid.uuid4())[:8]
        return f"ORD-{date_part}-{random_part}"
    
    @staticmethod
    async def get_order_by_id(
        order_id: int,
        session: AsyncSession
    ) -> Optional[Order]:
        """Get order by ID with items."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.user),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_order_by_number(
        order_number: str,
        session: AsyncSession
    ) -> Optional[Order]:
        """Get order by order number."""
        stmt = select(Order).where(Order.order_number == order_number)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_user_orders(
        user_id: int,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Order], int]:
        """
        Get user's orders with pagination.
        
        Returns:
            Tuple of (orders, total_count)
        """
        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(Order)
            .where(Order.user_id == user_id)
        )
        result = await session.execute(count_stmt)
        total = result.scalar() or 0
        
        # Get paginated results
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .options(selectinload(Order.items))
        )
        result = await session.execute(stmt)
        orders = result.scalars().all()
        
        return orders, total
    
    @staticmethod
    async def create_order(
        user_id: int,
        cart: Cart,
        request: OrderCreateRequest,
        session: AsyncSession
    ) -> Order:
        """
        Create order from cart.
        
        Args:
            user_id: User ID
            cart: Cart object with items
            request: Order creation request (shipping address)
            session: Database session
            
        Returns:
            Created Order object
        """
        if not cart.items or len(cart.items) == 0:
            raise ValueError("Cart is empty")
        
        # Calculate totals
        subtotal = 0.0
        order_items = []
        
        for item in cart.items:
            product = await ProductService.get_product_by_id(item["product_id"], session)
            if not product:
                raise ValueError(f"Product {item['product_id']} not found")
            
            if product.stock_qty < item["quantity"]:
                raise ValueError(f"Insufficient stock for {product.name}")
            
            line_total = product.price * item["quantity"]
            subtotal += line_total
            
            order_item = OrderItem(
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=product.price,
                subtotal=line_total,
                variant_options=item.get("variant_options"),
            )
            order_items.append({
                "item": order_item,
                "product": product
            })
        
        # Calculate shipping and tax (simplified - in production, use real tax service)
        tax = subtotal * 0.1  # 10% tax (simplified)
        shipping = 10.0 if subtotal < 50 else 0.0  # Free shipping over $50
        total = subtotal + tax + shipping
        
        # Create order
        order = Order(
            user_id=user_id,
            order_number=OrderService.generate_order_number(),
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            discount=0.0,
            total=total,
            currency="USD",
            shipping_address=request.shipping_address,
        )
        
        # Add order items
        for item_data in order_items:
            order.items.append(item_data["item"])
            
            # Reduce stock
            await ProductService.update_stock(
                item_data["product"].id,
                -item_data["item"].quantity,
                "sale",
                session,
                details={"order_id": order.id}
            )
        
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        # Log analytics event
        analytics_event = AnalyticsEvent(
            user_id=user_id,
            event_type="order_created",
            event_data={
                "order_id": order.id,
                "order_number": order.order_number,
                "total": total,
                "item_count": len(order_items)
            }
        )
        session.add(analytics_event)
        await session.commit()
        
        logger.info(f"Order created: {order.order_number} for user {user_id}")
        return order
    
    @staticmethod
    async def update_order_status(
        order_id: int,
        new_status: OrderStatus,
        session: AsyncSession,
        tracking_number: Optional[str] = None
    ) -> Order:
        """
        Update order status.
        
        Args:
            order_id: Order ID
            new_status: New status
            session: Database session
            tracking_number: Optional tracking number
            
        Returns:
            Updated Order
        """
        order = await OrderService.get_order_by_id(order_id, session)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        old_status = order.status
        order.status = new_status
        
        if new_status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.utcnow()
            if tracking_number:
                order.tracking_number = tracking_number
        
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(order)
        
        logger.info(f"Order status changed: {order.order_number} {old_status} -> {new_status}")
        return order
    
    @staticmethod
    async def cancel_order(
        order_id: int,
        reason: Optional[str],
        session: AsyncSession
    ) -> Order:
        """
        Cancel order and reverse inventory.
        
        Args:
            order_id: Order ID
            reason: Cancellation reason
            session: Database session
            
        Returns:
            Cancelled Order
        """
        order = await OrderService.get_order_by_id(order_id, session)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Can only cancel pending or paid orders
        if order.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            raise ValueError(f"Cannot cancel order with status {order.status}")
        
        # Reverse inventory
        for item in order.items:
            await ProductService.update_stock(
                item.product_id,
                item.quantity,
                "order_canceled",
                session,
                details={"order_id": order_id, "reason": reason}
            )
        
        order.status = OrderStatus.CANCELED
        await session.commit()
        await session.refresh(order)
        
        logger.info(f"Order canceled: {order.order_number}, Reason: {reason}")
        return order
    
    @staticmethod
    async def mark_payment_received(
        order_id: int,
        payment_intent_id: str,
        session: AsyncSession
    ) -> Order:
        """
        Mark order as paid (called after payment success).
        
        Args:
            order_id: Order ID
            payment_intent_id: Stripe PaymentIntent ID
            session: Database session
            
        Returns:
            Updated Order
        """
        order = await OrderService.get_order_by_id(order_id, session)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.status = OrderStatus.PAID
        order.payment_intent_id = payment_intent_id
        order.payment_method = "stripe"
        
        await session.commit()
        await session.refresh(order)
        
        logger.info(f"Order marked paid: {order.order_number}")
        return order
    
    @staticmethod
    async def get_dashboard_stats(
        session: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics for admin.
        
        Args:
            session: Database session
            days: Number of days to calculate stats for
            
        Returns:
            Dictionary of statistics
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total revenue
        revenue_stmt = (
            select(func.sum(Order.total))
            .where(
                (Order.created_at >= cutoff_date) &
                (Order.status == OrderStatus.PAID)
            )
        )
        result = await session.execute(revenue_stmt)
        total_revenue = float(result.scalar() or 0)
        
        # Total orders
        orders_stmt = (
            select(func.count())
            .select_from(Order)
            .where(Order.created_at >= cutoff_date)
        )
        result = await session.execute(orders_stmt)
        total_orders = result.scalar() or 0
        
        # Average order value
        aov = (total_revenue / total_orders) if total_orders > 0 else 0
        
        # Total customers
        customers_stmt = (
            select(func.count(func.distinct(Order.user_id)))
            .select_from(Order)
            .where(Order.created_at >= cutoff_date)
        )
        result = await session.execute(customers_stmt)
        total_customers = result.scalar() or 0
        
        # New customers today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_customers_stmt = (
            select(func.count())
            .select_from(User)
            .where(User.created_at >= today_start)
        )
        result = await session.execute(new_customers_stmt)
        new_customers_today = result.scalar() or 0
        
        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": aov,
            "total_customers": total_customers,
            "new_customers_today": new_customers_today,
        }
