"""Application configuration mirroring the Node `src/config/index.ts`."""

from __future__ import annotations

from typing import Annotated, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings (loaded from .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    port: int = Field(default=5002, alias="PORT")
    node_env: str = Field(default="development", alias="NODE_ENV")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/shopease",
        alias="DATABASE_URL",
    )

    # JWT
    jwt_secret: str = Field(default="change-me-access-secret", alias="JWT_SECRET")
    jwt_expires_in: str = Field(default="7d", alias="JWT_EXPIRES_IN")
    jwt_refresh_token_secret: str = Field(
        default="change-me-refresh-secret", alias="JWT_REFRESH_TOKEN_SECRET"
    )
    jwt_refresh_token_expires_in: str = Field(
        default="30d", alias="JWT_REFRESH_TOKEN_EXPIRES_IN"
    )
    jwt_reset_pass_token: str = Field(
        default="change-me-reset-secret", alias="JWT_RESET_PASS_TOKEN"
    )
    jwt_reset_pass_token_expires_in: str = Field(
        default="15m", alias="JWT_RESET_PASS_TOKEN_EXPIRES_IN"
    )
    reset_pass_link: str = Field(
        default="http://localhost:3000/reset-password", alias="RESET_PASS_LINK"
    )

    # Cloudinary
    cloudinary_name: Optional[str] = Field(default=None, alias="CLOUDINARY_NAME")
    cloudinary_api_key: Optional[str] = Field(default=None, alias="CLOUDINARY_API_KEY")
    cloudinary_secret: Optional[str] = Field(default=None, alias="CLOUDINARY_SECRET")

    # Email
    nodemailer_email: Optional[str] = Field(default=None, alias="NODEMAILER_EMAIL")
    nodemailer_app_pass: Optional[str] = Field(default=None, alias="NODEMAILER_APP_PASS")

    # Stripe
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")

    # Seed admin
    admin_email: str = Field(default="admin@shopease.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="Admin1234", alias="ADMIN_PASSWORD")

    # Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # RAG service (ecom) — powers the shopping-assistant chatbot without external keys.
    rag_service_url: str = Field(default="http://localhost:8000", alias="RAG_SERVICE_URL")

    # CORS
    cors_origins: Annotated[List[str], NoDecode] = Field(
        default=["http://localhost:3000", "https://shop-ease-8a83-fe.vercel.app"],
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
