"""
Configuration management using Pydantic Settings.
Environment variables and Azure Key Vault integration.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment and Key Vault."""
    
    # Environment
    environment: str = Field(default="development", description="development|staging|production")
    debug: bool = Field(default=False)
    
    # API Configuration
    api_title: str = Field(default="E-Commerce API")
    api_version: str = Field(default="1.0.0")
    api_docs_url: str = Field(default="/docs")
    api_openapi_url: str = Field(default="/openapi.json")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)
    
    # Database Configuration
    database_url: str = Field(default="postgresql+asyncpg://user:password@localhost/ecommerce")
    database_pool_size: int = Field(default=20)
    database_pool_recycle: int = Field(default=3600)
    database_echo: bool = Field(default=False)
    
    # JWT/Authentication
    jwt_secret: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)
    jwt_refresh_expiration_days: int = Field(default=30)

    # Shared secret used by the ShopEase storefront to sign access tokens. The RAG
    # service verifies the storefront token with this secret to derive the caller's
    # authoritative role (customer/vendor/admin) for RBAC-scoped policy retrieval.
    shopease_jwt_secret: Optional[str] = Field(default=None)
    
    # CORS
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(default=True)
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    cors_headers: List[str] = Field(default=["Authorization", "Content-Type", "X-Request-Id"])
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_period_seconds: int = Field(default=60)
    request_max_body_mb: int = Field(default=2)
    auth_request_max_body_kb: int = Field(default=64)
    
    # Stripe Configuration
    stripe_api_key: str = Field(default="sk_test_...")
    stripe_webhook_secret: str = Field(default="whsec_...")
    stripe_api_version: str = Field(default="2024-04-10")
    stripe_readiness_url: Optional[str] = Field(default=None)
    
    # Azure Configuration
    azure_subscription_id: str = Field(default="")
    azure_resource_group: str = Field(default="")
    azure_keyvault_url: Optional[str] = Field(default=None)
    
    # Azure Blob Storage
    azure_storage_account_name: str = Field(default="")
    azure_storage_account_key: str = Field(default="")
    azure_storage_container_products: str = Field(default="product-images")
    
    # Azure OpenAI (for future AI features)
    azure_openai_api_key: Optional[str] = Field(default=None)
    azure_openai_endpoint: Optional[str] = Field(default=None)
    azure_openai_deployment: Optional[str] = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-10-21")
    azure_openai_chat_deployment: Optional[str] = Field(default=None)
    azure_openai_embedding_deployment: Optional[str] = Field(default=None)

    # Azure AI Search (RAG vector retrieval)
    azure_search_endpoint: Optional[str] = Field(default=None)
    azure_search_admin_key: Optional[str] = Field(default=None)
    azure_search_index_name: str = Field(default="support-policies-index")
    azure_search_semantic_config: str = Field(default="support-semantic")
    azure_search_vector_dimensions: int = Field(default=1536)

    # Dedicated embedding endpoint (Azure AI Foundry / Azure AI Inference) for models
    # not served by Azure OpenAI, e.g. Cohere ``embed-v-4-0``. When both are set, all
    # embedding calls use this endpoint instead of the Azure OpenAI resource.
    azure_embedding_endpoint: Optional[str] = Field(default=None)
    azure_embedding_api_key: Optional[str] = Field(default=None)

    # RAG behavior
    rag_provider: str = Field(default="local", description="local|azure|hybrid")
    rag_top_k: int = Field(default=3)
    rag_min_local_score: int = Field(default=2)
    rag_min_azure_score: float = Field(default=0.8)

    # Admin security for operational endpoints
    rag_admin_api_key: Optional[str] = Field(default=None)

    # Prompt versioning / registry
    prompt_registry_provider: str = Field(
        default="yaml",
        description="yaml | langfuse | composite (langfuse first, YAML fallback)",
    )
    prompt_cache_ttl_seconds: int = Field(default=300)

    # Langfuse (external prompt registry + LLM tracing)
    langfuse_public_key: Optional[str] = Field(default=None)
    langfuse_secret_key: Optional[str] = Field(default=None)
    langfuse_host: Optional[str] = Field(
        default=None,
        description="e.g. https://cloud.langfuse.com or a self-hosted URL",
    )

    # RAGAS evaluation
    ragas_enabled: bool = Field(default=False)
    # Metrics computed offline / on demand: comma-separated subset of
    # faithfulness, answer_relevancy, context_precision, context_recall, answer_similarity
    ragas_metrics: str = Field(
        default="faithfulness,answer_relevancy,context_precision,context_recall,answer_similarity",
    )
    # Judge model (defaults to azure_openai_chat_deployment when unset).
    ragas_judge_deployment: Optional[str] = Field(default=None)
    # Threshold below which a metric is treated as a failure in CI.
    ragas_min_faithfulness: float = Field(default=0.7)
    ragas_min_answer_relevancy: float = Field(default=0.7)
    ragas_min_context_precision: float = Field(default=0.6)
    ragas_min_context_recall: float = Field(default=0.6)
    # Online sampling — fraction of prod /chat/query requests to score in-band.
    ragas_online_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Redis / event bus (async worker transport; maps to Azure Service Bus in prod)
    redis_url: Optional[str] = Field(default=None)
    events_consumer_group: str = Field(default="ecom-workers")

    # Application Insights (Observability)
    app_insights_connection_string: Optional[str] = Field(default=None)
    app_insights_enabled: bool = Field(default=True)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json or text
    # When true, emit verbose per-step RAG logs (embed/retrieve/prompt/llm) at INFO.
    # When false, those step logs are only emitted if the logger is at DEBUG level,
    # so production stays quiet by default.
    rag_step_logging: bool = Field(default=False)
    
    # Email/Notifications
    email_provider: str = Field(default="sendgrid")  # sendgrid or azure_communication_services
    email_api_key: str = Field(default="")
    email_from_address: str = Field(default="noreply@fashionstore.com")
    email_from_name: str = Field(default="Fashion Store")
    
    # Business Settings
    product_images_max_size_mb: int = Field(default=5)
    product_images_allowed_types: List[str] = Field(default=["image/jpeg", "image/png", "image/webp"])
    cart_expiration_days: int = Field(default=7)
    
    # RAG Chat API
    rag_chat_api_url: Optional[str] = Field(default=None)
    rag_chat_api_key: Optional[str] = Field(default=None)
    rag_chat_timeout_seconds: float = Field(default=12.0)
    rag_chat_search_mode: str = Field(default="keyword", description="hybrid|keyword|vector")

    # ShopEase storefront catalog (external product source for chat recommendations)
    shopease_products_enabled: bool = Field(
        default=False,
        description="When true, chat product recommendations come from the ShopEase product API instead of the local DB.",
    )
    shopease_api_url: Optional[str] = Field(
        default=None,
        description="ShopEase backend base URL including /api/v1, e.g. http://localhost:5002/api/v1",
    )
    shopease_api_timeout_seconds: float = Field(default=8.0)
    shopease_default_currency: str = Field(default="INR")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    @property
    def database_url_masked(self) -> str:
        """Return database URL with password masked for logging."""
        try:
            # postgresql+asyncpg://user:password@host/db -> postgresql+asyncpg://user:***@host/db
            if "@" in self.database_url:
                before_at, after_at = self.database_url.rsplit("@", 1)
                scheme_and_user = before_at.rsplit(":", 1)[0]
                return f"{scheme_and_user}:***@{after_at}"
            return self.database_url
        except Exception:
            return "***"

    @property
    def azure_rag_configured(self) -> bool:
        """True if required Azure RAG settings are present."""
        return bool(
            self.azure_openai_api_key
            and self.azure_openai_endpoint
            and self.azure_openai_embedding_deployment
            and self.azure_openai_chat_deployment
            and self.azure_search_endpoint
            and self.azure_search_admin_key
            and self.azure_search_index_name
        )

    @property
    def keyvault_configured(self) -> bool:
        """True if an Azure Key Vault URL is configured."""
        return bool(self.azure_keyvault_url)


def get_settings() -> Settings:
    """Get settings instance. Singleton pattern."""
    if not hasattr(get_settings, "_instance"):
        # Overlay any secrets stored in Azure Key Vault onto the environment
        # before Settings reads them. No-op when AZURE_KEYVAULT_URL is unset or
        # when the Azure SDK / vault is unavailable (fails soft).
        from app.services.keyvault import load_keyvault_secrets

        load_keyvault_secrets(os.environ.get("AZURE_KEYVAULT_URL"))
        get_settings._instance = Settings()
    return get_settings._instance


# Load settings on module import
settings = get_settings()
