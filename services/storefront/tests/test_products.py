"""Product endpoint tests: public listing envelope + role guards."""

from __future__ import annotations


async def test_list_products_returns_paginated_envelope(client):
    resp = await client.get("/api/v1/products")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert "meta" in body
    assert {"page", "limit", "total"} <= set(body["meta"].keys())


async def test_create_product_without_auth_is_rejected(client):
    # No Authorization header -> get_current_user raises 401 before role check.
    resp = await client.post("/api/v1/products", data={"data": "{}"})
    assert resp.status_code == 401
    assert resp.json()["success"] is False
