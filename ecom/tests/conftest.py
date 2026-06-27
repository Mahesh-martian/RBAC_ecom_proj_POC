"""Shared pytest fixtures for the e-commerce / RAG service.

Tests run fully self-contained: no Postgres, Azure, or Stripe credentials needed.
The database dependency is overridden with an in-memory SQLite engine, and the
app lifespan (which would connect to Postgres) is intentionally not started — the
``TestClient`` is created without its context manager.
"""

import os

# Environment must be configured BEFORE importing the app, because app.config
# instantiates its Settings singleton at import time. These override any values
# in a local .env file (environment variables take precedence in pydantic-settings).
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["JWT_SECRET"] = "test-jwt-secret-value-at-least-32-characters-long"
os.environ["RAG_PROVIDER"] = "local"
os.environ["STRIPE_API_KEY"] = "sk_test_dummy"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["RATE_LIMIT_REQUESTS"] = "100000"
os.environ["APP_INSIGHTS_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import get_db_session
from app.main import app
from app.models import Base
from app.routers import auth as auth_router


@pytest.fixture
def client():
    """A TestClient backed by a fresh in-memory SQLite database per test.

    Tables are created lazily inside the dependency override so they live in the
    same event loop that serves the request (required for StaticPool + aiosqlite).
    """
    # The auth router keeps a process-global per-IP rate-limit counter; since every
    # TestClient request shares the IP "testclient", reset it so tests are isolated.
    auth_router._auth_events.clear()

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    state = {"initialized": False}

    async def override_get_db():
        if not state["initialized"]:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            state["initialized"] = True
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db
    # No `with` block: skip the app lifespan so it never dials Postgres.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def registered_user(client):
    """Register a user and return its credentials plus an access token."""
    credentials = {
        "email": "tester@example.com",
        "password": "TestPass1234",
        "name": "Test User",
    }
    resp = client.post("/auth/register", json=credentials)
    assert resp.status_code == 201, resp.text

    login = client.post(
        "/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"credentials": credentials, "token": token}
