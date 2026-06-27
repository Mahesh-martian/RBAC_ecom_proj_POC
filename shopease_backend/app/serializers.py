"""Composable serializers that reproduce the Node API's nested JSON shapes.

All rely on `model_to_dict`, which emits camelCase keys matching Prisma columns.
Routers must eager-load (selectinload) any relationships used here.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.response import model_to_dict
from app import models


def serialize_user(user: models.User) -> dict[str, Any]:
    """User without password, with nested vendor & customer (admin omitted).

    This is the exact payload embedded in the JWT and returned by auth routes.
    """
    data = model_to_dict(user, exclude=("password",)) or {}
    data["vendor"] = model_to_dict(getattr(user, "vendor", None))
    data["customer"] = model_to_dict(getattr(user, "customer", None))
    return data


def serialize_category(category: Optional[models.Category]) -> Optional[dict]:
    return model_to_dict(category)


def serialize_customer_public(customer: Optional[models.Customer]) -> Optional[dict]:
    if customer is None:
        return None
    return {"name": customer.name, "profilePhoto": customer.profilePhoto}


def serialize_review(review: models.Review, *, with_customer: bool = False) -> dict[str, Any]:
    data = model_to_dict(review) or {}
    if with_customer:
        data["customer"] = serialize_customer_public(getattr(review, "customer", None))
    return data


def serialize_product(
    product: models.Product,
    *,
    with_reviews: bool = False,
    with_shop: bool = False,
    with_category: bool = False,
    category_name: bool = False,
) -> dict[str, Any]:
    data = model_to_dict(product) or {}
    if with_reviews:
        reviews = getattr(product, "reviews", []) or []
        data["reviews"] = [serialize_review(r, with_customer=True) for r in reviews]
    if with_shop:
        data["shop"] = model_to_dict(getattr(product, "shop", None))
    if with_category:
        data["category"] = model_to_dict(getattr(product, "category", None))
    if category_name:
        cat = getattr(product, "category", None)
        data["categoryName"] = cat.name if cat else None
    return data


def serialize_shop(shop: models.Shop, *, detailed: bool = False) -> dict[str, Any]:
    data = model_to_dict(shop) or {}
    if detailed:
        products = getattr(shop, "products", []) or []
        data["products"] = [serialize_product(p, with_reviews=True) for p in products]
        vendor = getattr(shop, "vendor", None)
        vendor_data = model_to_dict(vendor)
        if vendor_data is not None and vendor is not None:
            follows = getattr(vendor, "follows", []) or []
            vendor_data["follows"] = [model_to_dict(f) for f in follows]
        data["vendor"] = vendor_data
    return data


def serialize_order_item(item: models.OrderItem) -> dict[str, Any]:
    return model_to_dict(item) or {}


def serialize_order(order: models.Order, *, with_parties: bool = False) -> dict[str, Any]:
    data = model_to_dict(order) or {}
    items = getattr(order, "order_items", []) or []
    data["order_items"] = [serialize_order_item(i) for i in items]
    if with_parties:
        data["customer"] = model_to_dict(getattr(order, "customer", None))
        data["vendor"] = model_to_dict(getattr(order, "vendor", None))
    return data


def serialize_payment(payment: models.Payment) -> dict[str, Any]:
    return model_to_dict(payment) or {}


def serialize_flash_sale(flash_sale: models.FlashSale, *, with_product: bool = False) -> dict[str, Any]:
    data = model_to_dict(flash_sale) or {}
    if with_product:
        data["product"] = model_to_dict(getattr(flash_sale, "product", None))
    return data


def serialize_recent_product(recent: models.RecentProduct) -> dict[str, Any]:
    data = model_to_dict(recent) or {}
    data["product"] = model_to_dict(getattr(recent, "product", None))
    return data


def serialize_review_admin(review: models.Review) -> dict[str, Any]:
    """Review with product and full customer (vendor/admin listing)."""
    data = model_to_dict(review) or {}
    data["product"] = model_to_dict(getattr(review, "product", None))
    data["customer"] = model_to_dict(getattr(review, "customer", None))
    return data
