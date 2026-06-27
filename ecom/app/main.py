"""
Main FastAPI application entry point.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response, status
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.config import settings
from app.db import DatabaseManager
from app.middleware.body_size_limit import BodySizeLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.telemetry import TelemetryMiddleware
from app.routers import auth, products, orders, payments, carts, seed, chat, rag_admin
from app.schemas import HealthCheckResponse, ErrorResponse
from app.startup_checks import validate_startup_settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _stripe_status() -> str:
    if not settings.stripe_api_key or settings.stripe_api_key == "sk_test_...":
        return "degraded"

    # In local development we avoid external readiness checks.
    if settings.is_development:
        return "ok"

    if settings.stripe_readiness_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(settings.stripe_readiness_url)
            if response.status_code >= 500:
                return "error"
            if response.status_code >= 400:
                return "degraded"
        except Exception:
            return "error"

    return "ok"


async def _rag_status() -> str:
    if settings.rag_provider == "local":
        return "ok"

    if settings.rag_chat_api_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{settings.rag_chat_api_url.rstrip('/')}/health")
            if response.status_code >= 500:
                return "error"
            if response.status_code >= 400:
                return "degraded"
            return "ok"
        except Exception:
            return "error"

    if settings.rag_provider in {"azure", "hybrid"}:
        return "ok" if settings.azure_rag_configured else "error"
    return "degraded"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info(f"Starting E-Commerce API v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    
    try:
        # Fail fast on unsafe production-like configuration.
        validate_startup_settings(settings)

        # Initialize database
        await DatabaseManager.initialize()
        logger.info("Database initialized")
        
        # Create tables (idempotent)
        await DatabaseManager.create_tables()
        logger.info("Database tables ready")
        
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        sys.exit(1)
    
    yield
    
    # Shutdown
    logger.info("Shutting down E-Commerce API")
    await DatabaseManager.close()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Production-grade e-commerce API with RAG chatbot integration",
    docs_url=settings.api_docs_url if settings.environment != "production" else None,
    openapi_url=settings.api_openapi_url if settings.environment != "production" else None,
    lifespan=lifespan,
)

# ============ Middleware Setup ============

# Security headers first so every response receives baseline protections.
app.add_middleware(SecurityHeadersMiddleware)

# Request body size limit to reduce abuse risk on large payload endpoints.
app.add_middleware(
    BodySizeLimitMiddleware,
    max_body_bytes=settings.request_max_body_mb * 1024 * 1024,
    per_path_max_bytes={
        "/auth": settings.auth_request_max_body_kb * 1024,
    },
)

# Basic global API rate limiting.
app.add_middleware(
    RateLimitMiddleware,
    requests=settings.rate_limit_requests,
    period_seconds=settings.rate_limit_period_seconds,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Telemetry middleware (after CORS to capture all requests)
app.add_middleware(TelemetryMiddleware)


# ============ Exception Handlers ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.headers.get("X-Request-Id"),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.headers.get("X-Request-Id"),
        }
    )


# ============ Health Check Endpoints ============

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Health check endpoint"
)
async def health_check() -> HealthCheckResponse:
    """
    Check API and dependency health status.
    """
    database = "ok" if await DatabaseManager.ping() else "error"
    stripe = await _stripe_status()
    rag = await _rag_status()
    overall = "ok" if database == "ok" and stripe != "error" and rag != "error" else "degraded"

    return HealthCheckResponse(
        status=overall,
        version=settings.api_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        database=database,
        stripe=stripe,
        rag=rag,
    )


@app.get(
    "/ready",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Readiness check endpoint"
)
async def readiness_check(response: Response) -> HealthCheckResponse:
    """Readiness probe for dependency availability.

    Returns HTTP 503 when critical dependencies are unavailable.
    """
    database = "ok" if await DatabaseManager.ping() else "error"
    stripe = await _stripe_status()
    rag = await _rag_status()

    ready = database == "ok" and rag != "error"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthCheckResponse(
        status="ok" if ready else "error",
        version=settings.api_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        database=database,
        stripe=stripe,
        rag=rag,
    )


@app.get(
    "/info",
    tags=["info"],
    summary="API information"
)
async def api_info() -> dict:
    """
    Get API metadata and version information.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============ Router Registration ============

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(carts.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(seed.router)
app.include_router(chat.router)
app.include_router(rag_admin.router)


# ============ Root Endpoint ============

@app.get("/", tags=["root"], summary="Welcome endpoint")
async def root() -> dict:
    """Welcome message with API info."""
    return {
        "message": "Welcome to E-Commerce API",
        "version": settings.api_version,
        "docs_url": settings.api_docs_url if settings.environment != "production" else None,
        "health_url": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
