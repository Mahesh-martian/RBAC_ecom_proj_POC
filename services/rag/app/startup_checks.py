"""Startup validation checks for production-like safety."""

from __future__ import annotations

from app.config import Settings


_ALLOWED_ENVIRONMENTS = {"development", "staging", "production"}
_PLACEHOLDER_TOKENS = {
    "change-in-production",
    "your-secret",
    "your-super-secret",
    "your-openai-key",
    "your-search-admin-key",
    "change-me-admin-key",
    "instrumentationkey=...",
}


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    lowered = value.lower()
    return any(token in lowered for token in _PLACEHOLDER_TOKENS)


def validate_startup_settings(settings: Settings) -> None:
    """Raise ValueError when unsafe or incomplete settings are detected."""
    errors: list[str] = []

    if settings.environment not in _ALLOWED_ENVIRONMENTS:
        errors.append("ENVIRONMENT must be one of development|staging|production")

    production_like = settings.environment in {"staging", "production"}

    if production_like:
        if settings.debug:
            errors.append("DEBUG must be false in staging/production")

        if len(settings.jwt_secret or "") < 32 or _is_placeholder(settings.jwt_secret):
            errors.append("JWT_SECRET must be at least 32 chars and not a placeholder")

        if any(origin.startswith("http://localhost") for origin in settings.cors_origins):
            errors.append("CORS_ORIGINS must not include localhost in staging/production")

        if any(not origin.startswith("https://") for origin in settings.cors_origins):
            errors.append("CORS_ORIGINS must use https:// in staging/production")

        if "*" in settings.cors_methods:
            errors.append("CORS_METHODS must not include '*' in staging/production")

        if "*" in settings.cors_headers:
            errors.append("CORS_HEADERS must not include '*' in staging/production")

        lowered_db_url = (settings.database_url or "").lower()
        if "localhost" not in lowered_db_url and "sslmode=require" not in lowered_db_url:
            errors.append("DATABASE_URL must include sslmode=require for non-local staging/production")

        if not settings.rag_admin_api_key or len(settings.rag_admin_api_key) < 32 or _is_placeholder(settings.rag_admin_api_key):
            errors.append("RAG_ADMIN_API_KEY must be set to a strong non-placeholder value")

        if settings.app_insights_enabled and _is_placeholder(settings.app_insights_connection_string):
            errors.append("APP_INSIGHTS_CONNECTION_STRING is required when APP_INSIGHTS_ENABLED=true")

        if settings.rag_provider in {"azure", "hybrid"} and not settings.azure_rag_configured:
            errors.append("Azure RAG settings are incomplete for RAG_PROVIDER=azure|hybrid")

    if settings.rag_chat_api_url and not settings.rag_chat_api_key:
        errors.append("RAG_CHAT_API_KEY is required when RAG_CHAT_API_URL is set")

    if settings.request_max_body_mb <= 0:
        errors.append("REQUEST_MAX_BODY_MB must be greater than 0")

    if settings.auth_request_max_body_kb <= 0:
        errors.append("AUTH_REQUEST_MAX_BODY_KB must be greater than 0")

    if settings.stripe_readiness_url and not settings.stripe_readiness_url.startswith(("http://", "https://")):
        errors.append("STRIPE_READINESS_URL must start with http:// or https://")

    if production_like and settings.rag_chat_api_url and not settings.rag_chat_api_url.startswith("https://"):
        errors.append("RAG_CHAT_API_URL must use https:// in staging/production")

    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Startup settings validation failed: {joined}")
