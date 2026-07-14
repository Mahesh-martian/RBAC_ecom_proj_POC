"""ShopEase FastAPI application entrypoint.

Replicates the Node/Express backend: same `/api/v1` mount, same response and
error envelopes, same routes. Run with:

    uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models  # noqa: F401  (register ORM metadata)
from app.config import settings
from app.core.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.database import Base, engine
from app.routers import (
    admin,
    auth,
    chatbot,
    flash_sale,
    follows,
    order,
    payment,
    product,
    recent_product,
    reviews,
    shop,
)
from app.seed import seed_admin_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_admin_account()
    logger.info("Server is running on port %s", settings.port)
    yield


app = FastAPI(title="ShopEase API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

API_PREFIX = "/api/v1"
for module in (auth, admin, shop, product, order, flash_sale, payment, follows, reviews, recent_product, chatbot):
    app.include_router(module.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {"Message": "ShopEase server is running correctly"}


@app.get("/health", tags=["health"])
async def health():
    """Liveness probe: process is up. Fast, no external dependencies."""
    return {"status": "ok", "service": "shopease-api"}


@app.get("/ready", tags=["health"])
async def ready():
    """Readiness probe: verifies the database is reachable."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised via integration
        logger.warning("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "down"},
        )
    return {"status": "ready", "database": "up"}
