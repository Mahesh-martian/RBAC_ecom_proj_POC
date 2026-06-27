"""Pytest fixtures for the shopease-api integration tests.

The ShopEase ORM models use Postgres-specific column types (ARRAY on
``Product.image`` and JSONB on ``Payment.metadata``), so the suite runs against a
real Postgres instance. Point ``TEST_DATABASE_URL`` at a throwaway database; if
none is reachable, the whole suite is skipped so ``pytest`` still passes on a
machine without Postgres. CI provides a Postgres service container.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/shopease_test",
)


@pytest_asyncio.fixture
async def _engine():
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.connect():
            pass
    except Exception:  # noqa: BLE001 - any connection failure means skip
        await engine.dispose()
        pytest.skip(
            f"No Postgres reachable at {TEST_DATABASE_URL}; set TEST_DATABASE_URL to run integration tests."
        )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(_engine) -> AsyncGenerator[AsyncClient, None]:
    """Fresh schema per test + an HTTP client wired to the test database."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_user(client: AsyncClient, *, email: str, role: str = "CUSTOMER", password: str = "Passw0rd!"):
    return await client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": password, "role": role},
    )


async def login_user(client: AsyncClient, *, email: str, password: str = "Passw0rd!"):
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})
