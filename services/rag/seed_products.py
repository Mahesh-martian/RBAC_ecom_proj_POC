#!/usr/bin/env python3
"""
Seed script to populate database with sample products from apparels.json
Run this after docker-compose is up and database is initialized
"""

import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base, Category, Product
from app.config import settings

# Product data from knowledge_source
PRODUCTS_DATA = {
    "products": [
        {
            "productID": "0000001",
            "manufacturer": "Zara",
            "img": "https://static.zara.net/photos///2023/I/0/2/p/5320/355/800/2/w/563/5320355800_1_1_1.jpg?ts=1697787915583",
            "productName": "PINSTRIPE COAT",
            "Description": "Oversize-fit coat made of a viscose blend fabric. Notch lapel collar and long sleeves with buttoned cuffs.",
            "price": 4900,
            "category": "Apparel"
        },
        {
            "productID": "0000002",
            "manufacturer": "Zara",
            "img": "https://static.zara.net/photos///2023/I/0/2/p/7380/687/711/2/w/563/7380687711_1_1_1.jpg?ts=1694174968069",
            "productName": "OVERSIZED TECHNICAL TRENCH COAT",
            "Description": "Trench coat made of technical fabric with a velvety finish. Notch lapel collar and long sleeves.",
            "price": 4900,
            "category": "Apparel"
        },
        {
            "productID": "0000003",
            "manufacturer": "Zara",
            "img": "https://static.zara.net/photos///2023/I/0/2/p/3918/611/508/2/w/563/3918611508_1_1_1.jpg?ts=1696405613738",
            "productName": "PADDED TECHNICAL PARKA",
            "Description": "Parka made of technical fabric, padded on inside. High neck with a hood and long sleeves with elasticated cuffs.",
            "price": 5900,
            "category": "Apparel"
        },
        {
            "productID": "0000004",
            "manufacturer": "Zara",
            "img": "https://static.zara.net/photos///2022/I/2/2/p/0210/585/999/2/w/563/0210585999_6_1_1.jpg?ts=1663836779877",
            "productName": "BOGOSS VIBRANT LEATHER 100 ML / 3.38 OZ",
            "Description": "The first Vibrant Leather for le benjamin with its fruity hint of pineapple that gives it modernity, accompanied by cedar notes, adding a woody touch of rejuvenation.",
            "price": 1900,
            "category": "Perfume"
        },
        {
            "productID": "0000005",
            "manufacturer": "Zara",
            "img": "https://static.zara.net/photos///2023/I/1/2/p/3213/220/203/2/w/563/3213220203_2_1_1.jpg?ts=1687421823150",
            "productName": "MULTICOLOURED NYLON BACKPACK",
            "Description": "Multicoloured backpack. Soft construction. Featuring one main zip pocket and a medium-sized zip pocket on the inside.",
            "price": 2490,
            "category": "Accessories"
        },
        {
            "productID": "0000006",
            "manufacturer": "Nike",
            "img": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop",
            "productName": "CLASSIC WHITE SNEAKERS",
            "Description": "Comfortable and durable white sneakers for everyday wear. Perfect for casual outfits.",
            "price": 6999,
            "category": "Footwear"
        },
        {
            "productID": "0000007",
            "manufacturer": "Adidas",
            "img": "https://images.unsplash.com/photo-1542221066-7557bdc37fcf?w=500&h=500&fit=crop",
            "productName": "BLACK RUNNING SHOES",
            "Description": "High-performance running shoes with advanced cushioning technology for maximum comfort.",
            "price": 7999,
            "category": "Footwear"
        },
        {
            "productID": "0000008",
            "manufacturer": "Gucci",
            "img": "https://images.unsplash.com/photo-1548690596-f40c3c3f4f0a?w=500&h=500&fit=crop",
            "productName": "LEATHER CROSSBODY BAG",
            "Description": "Elegant leather crossbody bag in black with gold chain strap. Perfect for all occasions.",
            "price": 12999,
            "category": "Accessories"
        },
        {
            "productID": "0000009",
            "manufacturer": "Calvin Klein",
            "img": "https://images.unsplash.com/photo-1552347827-d12cf5cd1ac4?w=500&h=500&fit=crop",
            "productName": "CASUAL BLUE DENIM JACKET",
            "Description": "Classic blue denim jacket with perfect fit. A wardrobe essential for any style.",
            "price": 3999,
            "category": "Apparel"
        },
        {
            "productID": "0000010",
            "manufacturer": "Tommy Hilfiger",
            "img": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500&h=500&fit=crop",
            "productName": "STRIPED POLO SHIRT",
            "Description": "Classic striped polo shirt in navy and white. Breathable cotton material.",
            "price": 2499,
            "category": "Apparel"
        }
    ]
}

# Categories mapping
CATEGORIES = {
    "Apparel": "Clothing and outerwear",
    "Accessories": "Bags, belts, and accessories",
    "Footwear": "Shoes and footwear",
    "Perfume": "Fragrances and perfumes"
}


async def seed_database():
    """Seed the database with sample products"""
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True,
    )
    
    # Create async session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        try:
            # Create categories
            print("Creating categories...")
            categories_map = {}
            
            for cat_name, cat_desc in CATEGORIES.items():
                # Check if category exists
                from sqlalchemy import select
                stmt = select(Category).where(Category.name == cat_name)
                result = await session.execute(stmt)
                existing_cat = result.scalar_one_or_none()
                
                if existing_cat:
                    categories_map[cat_name] = existing_cat
                    print(f"  ✓ Category '{cat_name}' already exists (ID: {existing_cat.id})")
                else:
                    category = Category(
                        name=cat_name,
                        slug=cat_name.lower().replace(" ", "-"),
                        description=cat_desc,
                    )
                    session.add(category)
                    await session.flush()
                    categories_map[cat_name] = category
                    print(f"  ✓ Created category '{cat_name}' (ID: {category.id})")
            
            # Create products
            print("\nCreating products...")
            from sqlalchemy import select
            
            for prod in PRODUCTS_DATA["products"]:
                # Check if product already exists
                stmt = select(Product).where(Product.sku == prod["productID"])
                result = await session.execute(stmt)
                existing_prod = result.scalar_one_or_none()
                
                if existing_prod:
                    print(f"  ✓ Product '{prod['productName']}' already exists (SKU: {prod['productID']})")
                    continue
                
                category = categories_map.get(prod["category"])
                if not category:
                    print(f"  ✗ Category '{prod['category']}' not found, skipping product")
                    continue
                
                # Price is in cents (or whole number), convert to USD
                price = prod["price"] / 100 if prod["price"] > 1000 else prod["price"]
                
                product = Product(
                    sku=prod["productID"],
                    name=prod["productName"],
                    description=prod["Description"],
                    category_id=category.id,
                    price=price,
                    cost=price * 0.4,  # Assume 40% cost margin
                    currency="USD",
                    stock_qty=100,  # Default stock
                    reorder_level=10,
                    images=[{"url": prod["img"], "alt_text": prod["productName"]}],
                    tags=[prod["category"].lower(), prod["manufacturer"].lower()],
                    product_metadata={
                        "manufacturer": prod["manufacturer"],
                        "sku": prod["productID"],
                    },
                    is_active=True,
                )
                session.add(product)
                print(f"  ✓ Created product '{prod['productName']}' (SKU: {prod['productID']})")
            
            # Commit all changes
            await session.commit()
            print("\n✅ Database seeded successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error seeding database: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
