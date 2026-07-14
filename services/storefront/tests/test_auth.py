"""Auth flow integration tests (register, login, duplicate, bad credentials)."""

from __future__ import annotations

from tests.conftest import login_user, register_user


async def test_register_returns_201_without_password(client):
    resp = await register_user(client, email="alice@example.com")
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == "alice@example.com"
    assert "password" not in body["data"]


async def test_register_duplicate_email_returns_400(client):
    await register_user(client, email="dupe@example.com")
    resp = await register_user(client, email="dupe@example.com")
    assert resp.status_code == 400
    assert resp.json()["success"] is False


async def test_login_returns_tokens_and_user(client):
    await register_user(client, email="bob@example.com", role="VENDOR")
    resp = await login_user(client, email="bob@example.com")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["accessToken"]
    assert data["refreshToken"]
    user = data["userWithoutPassword"]
    assert user["email"] == "bob@example.com"
    assert user["role"] == "VENDOR"
    # access-token payload embeds the nested vendor object
    assert user.get("vendor") is not None
    assert "password" not in user


async def test_login_wrong_password_returns_401(client):
    await register_user(client, email="carol@example.com")
    resp = await login_user(client, email="carol@example.com", password="wrong-password")
    assert resp.status_code == 401
    assert resp.json()["success"] is False


async def test_login_unknown_user_returns_404(client):
    resp = await login_user(client, email="nobody@example.com")
    assert resp.status_code == 404
