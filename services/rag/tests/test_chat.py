"""Chat endpoint request-validation tests.

These exercise FastAPI request validation only (which runs before the handler), so
they need no Azure/RAG backends.
"""


def test_chat_query_requires_query_field(client):
    resp = client.post("/chat/query", json={})
    assert resp.status_code == 422


def test_chat_query_rejects_empty_query(client):
    resp = client.post("/chat/query", json={"query": ""})
    assert resp.status_code == 422


def test_chat_query_rejects_overlong_query(client):
    resp = client.post("/chat/query", json={"query": "x" * 501})
    assert resp.status_code == 422
