"""SQLAlchemy ORM models mirroring the ShopEase Prisma schema.

Column names are kept camelCase and table names match Prisma `@@map` values so
the JSON the API emits is identical to the original Node backend (and so this
app can bind to an existing Prisma-migrated database).
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deletedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    admin: Mapped["Admin | None"] = relationship(back_populates="user", uselist=False)
    vendor: Mapped["Vendor | None"] = relationship(back_populates="user", uselist=False)
    customer: Mapped["Customer | None"] = relationship(back_populates="user", uselist=False)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, ForeignKey("users.email"), unique=True, nullable=False)
    profilePhoto: Mapped[str | None] = mapped_column(String, nullable=True)
    isDeleted: Mapped[bool] = mapped_column(Boolean, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="admin")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, ForeignKey("users.email"), unique=True, nullable=False)
    profilePhoto: Mapped[str | None] = mapped_column(String, nullable=True)
    isDeleted: Mapped[bool] = mapped_column(Boolean, default=False)
    isSuspended: Mapped[bool] = mapped_column(Boolean, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="vendor")
    shop: Mapped["Shop | None"] = relationship(back_populates="vendor", uselist=False)
    products: Mapped[list["Product"]] = relationship(back_populates="vendor")
    follows: Mapped[list["Follow"]] = relationship(back_populates="vendor")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, ForeignKey("users.email"), unique=True, nullable=False)
    profilePhoto: Mapped[str | None] = mapped_column(String, nullable=True)
    isDeleted: Mapped[bool] = mapped_column(Boolean, default=False)
    isSuspended: Mapped[bool] = mapped_column(Boolean, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="customer")


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    logo: Mapped[str | None] = mapped_column(String, nullable=True)
    vendorId: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), unique=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deletedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    isBlackListed: Mapped[bool] = mapped_column(Boolean, default=False)

    vendor: Mapped["Vendor"] = relationship(back_populates="shop")
    products: Mapped[list["Product"]] = relationship(back_populates="shop")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, default=0)
    categoryId: Mapped[str] = mapped_column(String, ForeignKey("categories.id"), nullable=False)
    inventory: Mapped[int] = mapped_column(Integer, nullable=False)
    image: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    vendorId: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    shopId: Mapped[str] = mapped_column(String, ForeignKey("shops.id"), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deletedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    vendor: Mapped["Vendor"] = relationship(back_populates="products")
    shop: Mapped["Shop"] = relationship(back_populates="products")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deletedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customerId: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    vendorId: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    totalAmount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deletedAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    payment: Mapped["Payment | None"] = relationship(back_populates="order", uselist=False)
    customer: Mapped["Customer"] = relationship()
    vendor: Mapped["Vendor"] = relationship()


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    orderId: Mapped[str] = mapped_column(String, ForeignKey("orders.id"), nullable=False)
    productId: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, default=0)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship(back_populates="order_items")
    product: Mapped["Product"] = relationship()


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customerId: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    productId: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customerId: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    productId: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship(back_populates="reviews")
    customer: Mapped["Customer"] = relationship()


class Follow(Base):
    __tablename__ = "follows"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    customerId: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    vendorId: Mapped[str] = mapped_column(String, ForeignKey("vendors.id"), nullable=False)
    isDeleted: Mapped[bool] = mapped_column(Boolean, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vendor: Mapped["Vendor"] = relationship(back_populates="follows")


class FlashSale(Base):
    __tablename__ = "flash_sales"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    productId: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    discount: Mapped[float] = mapped_column(Float, nullable=False)
    startTime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    endTime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship()


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    orderId: Mapped[str] = mapped_column(String, ForeignKey("orders.id"), unique=True, nullable=False)
    customerId: Mapped[str] = mapped_column(String, ForeignKey("customers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paymentMethod: Mapped[str] = mapped_column(String, default="CARD")
    transactionId: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship(back_populates="payment")
    customer: Mapped["Customer"] = relationship()


class RecentProduct(Base):
    __tablename__ = "recent_products"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    userId: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    productId: Mapped[str] = mapped_column(String, ForeignKey("products.id"), nullable=False)
    visitedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship()


class Chat(Base):
    __tablename__ = "Chat"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    userId: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
