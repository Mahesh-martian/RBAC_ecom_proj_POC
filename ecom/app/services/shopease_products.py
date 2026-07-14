"""Adapter that sources product recommendations from the ShopEase storefront API.

ShopEase exposes its catalog at ``GET {shopease_api_url}/products`` and wraps the
payload as ``{ "success": bool, "message": str, "meta": {...}, "data": [Product] }``.
A ShopEase ``Product`` looks like::

    {
        "id": "uuid-string",
        "name": "...",
        "description": "...",
        "price": 49.99,
        "discount": 10,            # percentage off, defaults to 0
        "categoryId": "uuid",
        "inventory": 12,
        "image": ["https://...", ...],
        "vendorId": "uuid",
        "shopId": "uuid"
    }

The adapter normalizes those records into :class:`ChatRecommendation` instances so
the chat endpoint can serve ShopEase products without touching the local database.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.config import settings
from app.schemas import ChatRecommendation

logger = logging.getLogger(__name__)


def _normalize_product(raw: dict[str, Any]) -> Optional[ChatRecommendation]:
    """Convert a ShopEase product record into a ChatRecommendation, or None if invalid."""
    product_id = raw.get("id")
    name = raw.get("name")
    price = raw.get("price")
    if product_id is None or not name or price is None:
        return None

    # ShopEase stores ``discount`` as a percentage; apply it so the shown price is final.
    try:
        base_price = float(price)
        discount = float(raw.get("discount") or 0)
    except (TypeError, ValueError):
        return None
    if discount > 0:
        base_price = round(base_price * (1 - min(discount, 100) / 100), 2)

    image_url: Optional[str] = None
    images = raw.get("image")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, str) and first.strip():
            image_url = first

    sku = str(product_id)[:8]

    return ChatRecommendation(
        id=str(product_id),
        name=str(name),
        sku=sku,
        price=base_price,
        currency=settings.shopease_default_currency,
        image_url=image_url,
    )


async def _search_once(
    *,
    search_term: str,
    category: Optional[str],
    limit: int,
    max_price: Optional[float] = None,
) -> list[ChatRecommendation]:
    """Run a single ShopEase ``/products`` query for one search term."""
    base_url = settings.shopease_api_url
    if not base_url:
        return []

    params: dict[str, Any] = {"limit": max(limit * 4, limit), "page": 1}
    if search_term:
        params["searchTerm"] = search_term

    url = f"{base_url.rstrip('/')}/products"
    try:
        async with httpx.AsyncClient(timeout=settings.shopease_api_timeout_seconds) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("shopease_products unreachable url=%s error=%s", url, exc)
        return []

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []

    wanted_category = category.lower().strip() if category else None
    recommendations: list[ChatRecommendation] = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        # ShopEase filters by searchTerm server-side; optionally narrow by category name.
        if wanted_category:
            cat = raw.get("category")
            cat_name = cat.get("name") if isinstance(cat, dict) else None
            if cat_name and wanted_category not in str(cat_name).lower():
                continue
        rec = _normalize_product(raw)
        if rec is None:
            continue
        # Honor a budget ceiling ("under 100") against the final, discounted price.
        if max_price is not None and rec.price > max_price:
            continue
        recommendations.append(rec)
        if len(recommendations) >= limit:
            break

    return recommendations


async def search_products(
    *,
    search_terms: list[str],
    category: Optional[str] = None,
    limit: int = 3,
    max_price: Optional[float] = None,
) -> list[ChatRecommendation]:
    """Query the ShopEase catalog for each search term and merge unique results.

    ShopEase performs a single substring match per request, so multi-word natural
    language ("I need a backpack") misses products. Searching one keyword at a time
    and de-duplicating by id gives relevant hits for conversational queries.

    Returns an empty list (never raises) when ShopEase is unreachable or returns an
    unexpected payload, so the chat endpoint can degrade gracefully.
    """
    terms = [t for t in (term.strip() for term in search_terms) if t]
    if not terms:
        terms = [""]  # empty term lists the catalog (used for category-only browsing)

    merged: list[ChatRecommendation] = []
    seen_ids: set[str] = set()
    for term in terms:
        for rec in await _search_once(
            search_term=term, category=category, limit=limit, max_price=max_price
        ):
            if rec.id in seen_ids:
                continue
            seen_ids.add(rec.id)
            merged.append(rec)
            if len(merged) >= limit:
                return merged

    return merged
