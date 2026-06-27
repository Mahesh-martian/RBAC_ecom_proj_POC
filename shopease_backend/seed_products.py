"""Seed sample catalog data into the ShopEase database.

Inserts a demo vendor + shop, a few categories, and a handful of products with
real image URLs (so the storefront UI renders them and the RAG chatbot can
return real recommendations). Idempotent: re-running it is a no-op once seeded.

Run from the host against the compose Postgres (published on :5432)::

    cd shopease_backend
    $env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/shopease"
    python seed_products.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app import models
from app.core.security import hash_password
from app.database import SessionLocal

VENDOR_EMAIL = "vendor@shopease.com"
VENDOR_PASSWORD = "Vendor1234"

CATEGORIES = [
    ("Apparel", "Clothing for men and women"),
    ("Footwear", "Shoes, sneakers and sandals"),
    ("Accessories", "Bags, watches and more"),
]

# (name, description, price, discount%, inventory, category, [images])
PRODUCTS = [
    (
        "Classic Cotton T-Shirt",
        "Soft 100% cotton crew-neck tee, breathable everyday wear.",
        19.99, 10, 120, "Apparel",
        ["https://images.unsplash.com/photo-1521572163474-6864f9cf17ab"],
    ),
    (
        "Slim-Fit Denim Jeans",
        "Stretch denim with a modern slim fit and durable stitching.",
        49.99, 15, 80, "Apparel",
        ["https://images.unsplash.com/photo-1542272604-787c3835535d"],
    ),
    (
        "Hooded Sweatshirt",
        "Fleece-lined pullover hoodie, warm and comfortable.",
        39.99, 0, 60, "Apparel",
        ["https://images.unsplash.com/photo-1556821840-3a63f95609a7"],
    ),
    (
        "Running Sneakers",
        "Lightweight cushioned running shoes with breathable mesh.",
        79.99, 20, 45, "Footwear",
        ["https://images.unsplash.com/photo-1542291026-7eec264c27ff"],
    ),
    (
        "Leather Ankle Boots",
        "Genuine leather boots with a non-slip rubber sole.",
        119.99, 5, 30, "Footwear",
        ["https://images.unsplash.com/photo-1520639888713-7851133b1ed0"],
    ),
    (
        "Canvas Backpack",
        "Water-resistant canvas backpack with laptop compartment.",
        59.99, 10, 50, "Accessories",
        ["https://images.unsplash.com/photo-1553062407-98eeb64c6a62"],
    ),
    (
        "Minimalist Wrist Watch",
        "Stainless steel analog watch with a leather strap.",
        89.99, 0, 25, "Accessories",
        ["https://images.unsplash.com/photo-1524592094714-0f0654e20314"],
    ),
    (
        "Polarized Sunglasses",
        "UV400 polarized lenses with a lightweight metal frame.",
        29.99, 25, 70, "Accessories",
        ["https://images.unsplash.com/photo-1511499767150-a48a237f0083"],
    ),
]


async def seed() -> None:
    async with SessionLocal() as db:
        # Already seeded? bail out.
        existing = await db.scalar(select(models.Product).limit(1))
        if existing is not None:
            print("Catalog already has products; nothing to seed.")
            return

        # Vendor user + vendor profile.
        vendor_user = await db.scalar(select(models.User).where(models.User.email == VENDOR_EMAIL))
        if vendor_user is None:
            vendor_user = models.User(
                name="Demo Vendor",
                email=VENDOR_EMAIL,
                password=hash_password(VENDOR_PASSWORD),
                role="VENDOR",
            )
            db.add(vendor_user)
            await db.flush()

        vendor = await db.scalar(select(models.Vendor).where(models.Vendor.email == VENDOR_EMAIL))
        if vendor is None:
            vendor = models.Vendor(name="Demo Vendor", email=VENDOR_EMAIL)
            db.add(vendor)
            await db.flush()

        # Shop.
        shop = await db.scalar(select(models.Shop).where(models.Shop.vendorId == vendor.id))
        if shop is None:
            shop = models.Shop(
                name="Demo Storefront",
                description="A sample shop seeded for demos and RAG recommendations.",
                logo="https://images.unsplash.com/photo-1441986300917-64674bd600d8",
                vendorId=vendor.id,
            )
            db.add(shop)
            await db.flush()

        # Categories.
        cat_by_name: dict[str, models.Category] = {}
        for name, desc in CATEGORIES:
            cat = await db.scalar(select(models.Category).where(models.Category.name == name))
            if cat is None:
                cat = models.Category(name=name, description=desc)
                db.add(cat)
                await db.flush()
            cat_by_name[name] = cat

        # Products.
        for name, desc, price, discount, inventory, category, images in PRODUCTS:
            db.add(
                models.Product(
                    name=name,
                    description=desc,
                    price=price,
                    discount=discount,
                    inventory=inventory,
                    categoryId=cat_by_name[category].id,
                    image=images,
                    vendorId=vendor.id,
                    shopId=shop.id,
                )
            )

        await db.commit()
        print(f"Seeded {len(PRODUCTS)} products across {len(CATEGORIES)} categories.")
        print(f"Vendor login: {VENDOR_EMAIL} / {VENDOR_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
