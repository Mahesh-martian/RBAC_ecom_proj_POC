"""Authentication flow tests against an in-memory database."""


def test_register_returns_created_user(client):
    resp = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "password": "StrongPass123",
            "name": "New User",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_register_rejects_weak_password(client):
    # Too short / missing uppercase+digit -> 422 from schema validation.
    resp = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short", "name": "Weak"},
    )
    assert resp.status_code == 422


def test_register_duplicate_email_conflicts(client):
    payload = {
        "email": "dupe@example.com",
        "password": "StrongPass123",
        "name": "Dupe User",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_login_returns_token(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPass123",
            "name": "Login User",
        },
    )
    resp = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "StrongPass123"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["expires_in"] > 0


def test_login_wrong_password_unauthorized(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpw@example.com",
            "password": "StrongPass123",
            "name": "Wrong PW",
        },
    )
    resp = client.post(
        "/auth/login",
        json={"email": "wrongpw@example.com", "password": "NotThePass123"},
    )
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_profile_with_token(registered_user, client):
    resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == registered_user["credentials"]["email"]
