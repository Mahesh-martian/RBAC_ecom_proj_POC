"""Product catalog endpoint tests."""


def test_list_products_empty(client):
    resp = client.get("/products")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 20


def test_list_products_rejects_invalid_limit(client):
    # limit is constrained to 1..100 by the query validator.
    resp = client.get("/products", params={"limit": 0})
    assert resp.status_code == 422
