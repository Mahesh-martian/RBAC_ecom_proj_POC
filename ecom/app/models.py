"""
SQLAlchemy ORM models for e-commerce database.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, ForeignKey, JSON, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class User(Base):
    """User/Customer model."""
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(JSON, nullable=True)  # {street, city, state, zip, country}
    preferences = Column(JSON, nullable=True)  # {currency, language, notifications}
    subscription_tier = Column(String(50), default="free")  # free, premium, vip
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    orders = relationship("Order", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user")
    carts = relationship("Cart", back_populates="user")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_created_at", "created_at"),
    )


class Category(Base):
    """Product category model."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="category")
    __table_args__ = (
        Index("idx_categories_slug", "slug"),
    )


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_products_category_id", "category_id"),
        Index("idx_products_sku", "sku"),
        Index("idx_products_created_at", "created_at"),
        Index("idx_products_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True)
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    price = Column(Float, nullable=False)  # Selling price
    cost = Column(Float, nullable=True)  # Cost price for margin calculation
    currency = Column(String(3), default="USD")
    stock_qty = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    images = Column(JSON, nullable=True)  # [{url, alt_text, order}, ...]
    tags = Column(JSON, nullable=True)  # ["tag1", "tag2", ...]
    product_metadata = Column(JSON, nullable=True)  # {color, size, material, etc.}
    rating = Column(Float, default=0.0)  # Denormalized average rating
    rating_count = Column(Integer, default=0)  # Count of reviews
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    wishlist_items = relationship("Wishlist", back_populates="product")
    inventory_logs = relationship("InventoryLog", back_populates="product")


class ProductReview(Base):
    """Product review model."""
    __tablename__ = "product_reviews"
    __table_args__ = (
        Index("idx_reviews_product_id", "product_id"),
        Index("idx_reviews_user_id", "user_id"),
        Index("idx_reviews_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    helpful_count = Column(Integer, default=0)
    unhelpful_count = Column(Integer, default=0)
    is_verified_purchase = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class Cart(Base):
    """Shopping cart model."""
    __tablename__ = "carts"
    __table_args__ = (
        Index("idx_carts_user_id", "user_id"),
        Index("idx_carts_session_id", "session_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for guest carts
    session_id = Column(String(255), nullable=True)  # UUID for guest tracking
    items = Column(JSON, nullable=True)  # [{product_id, quantity, variant_options}, ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For guest carts (7 days)

    user = relationship("User", back_populates="carts")


class Order(Base):
    """Order model."""
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_order_number", "order_number"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_number = Column(String(50), unique=True, nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Pricing
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    shipping = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment info
    payment_intent_id = Column(String(255), nullable=True)  # Stripe PaymentIntent ID
    payment_method = Column(String(50), nullable=True)  # stripe, paypal, etc.
    
    # Shipping info
    shipping_address = Column(JSON, nullable=False)  # {street, city, state, zip, country}
    tracking_number = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Individual item in an order."""
    __tablename__ = "order_items"
    __table_args__ = (
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
    )

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    variant_options = Column(JSON, nullable=True)  # {color, size, etc.}
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Wishlist(Base):
    """User wishlist/saved items."""
    __tablename__ = "wishlists"
    __table_args__ = (
        Index("idx_wishlists_user_id", "user_id"),
        Index("idx_wishlists_product_id", "product_id"),
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="wishlist")
    product = relationship("Product", back_populates="wishlist_items")


class InventoryLog(Base):
    """Audit log for inventory changes."""
    __tablename__ = "inventory_logs"
    __table_args__ = (
        Index("idx_inventory_logs_product_id", "product_id"),
        Index("idx_inventory_logs_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_qty = Column(Integer, nullable=False)  # Positive or negative
    reason = Column(String(100), nullable=False)  # sale, restock, adjustment, return, damage
    details = Column(JSON, nullable=True)  # Additional metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="inventory_logs")


class AnalyticsEvent(Base):
    """Analytics event tracking."""
    __tablename__ = "analytics_events"
    __table_args__ = (
        Index("idx_analytics_events_user_id", "user_id"),
        Index("idx_analytics_events_session_id", "session_id"),
        Index("idx_analytics_events_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=False)  # view, click, add_to_cart, checkout, etc.
    event_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
