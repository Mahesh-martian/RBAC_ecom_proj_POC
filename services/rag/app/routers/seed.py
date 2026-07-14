"""
Admin endpoint for seeding database with sample products
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models import Category, Product

router = APIRouter(prefix="/admin/seed", tags=["admin"])

# Sample products data
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

CATEGORIES = {
    "Apparel": "Clothing and outerwear",
    "Accessories": "Bags, belts, and accessories",
    "Footwear": "Shoes and footwear",
    "Perfume": "Fragrances and perfumes"
}


@router.post("/products")
async def seed_products(session: AsyncSession = Depends(get_db_session)):
    """
    Seed database with sample products
    WARNING: Only use in development environment
    """
    try:
        # Create categories
        categories_map = {}
        
        for cat_name, cat_desc in CATEGORIES.items():
            stmt = select(Category).where(Category.name == cat_name)
            result = await session.execute(stmt)
            existing_cat = result.scalar_one_or_none()
            
            if existing_cat:
                categories_map[cat_name] = existing_cat
            else:
                category = Category(
                    name=cat_name,
                    slug=cat_name.lower().replace(" ", "-"),
                    description=cat_desc,
                )
                session.add(category)
                await session.flush()
                categories_map[cat_name] = category
        
        # Create products
        created_count = 0
        skipped_count = 0
        
        for prod in PRODUCTS_DATA["products"]:
            stmt = select(Product).where(Product.sku == prod["productID"])
            result = await session.execute(stmt)
            existing_prod = result.scalar_one_or_none()
            
            if existing_prod:
                skipped_count += 1
                continue
            
            category = categories_map.get(prod["category"])
            if not category:
                continue
            
            # Price conversion
            price = prod["price"] / 100 if prod["price"] > 1000 else prod["price"]
            
            product = Product(
                sku=prod["productID"],
                name=prod["productName"],
                description=prod["Description"],
                category_id=category.id,
                price=price,
                cost=price * 0.4,
                currency="USD",
                stock_qty=100,
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
            created_count += 1
        
        await session.commit()
        
        return {
            "status": "success",
            "message": "Database seeded with sample products",
            "created": created_count,
            "skipped": skipped_count,
            "total": len(PRODUCTS_DATA["products"])
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
