"""Azure Key Vault secret loading.

Overlays secrets stored in Azure Key Vault onto the process environment before
application settings are constructed. Uses managed identity when running in
Azure and falls back to local developer credentials (``az login``, environment,
Visual Studio, etc.) via :class:`DefaultAzureCredential`.

Design goals:
- **Least privilege**: only ``get`` permission on an explicit allowlist of
  secret names is required (no ``list``).
- **Fail soft**: if the SDK is missing or the vault is unreachable, log a
  warning and continue with environment/.env values so local development and
  non-Azure deployments are unaffected.
- **Authoritative in prod**: when a vault URL is configured, Key Vault values
  override existing environment values for the mapped secrets by default.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Map Key Vault secret names (kebab-case) -> environment variable names.
# Pydantic settings read these env vars case-insensitively (e.g. JWT_SECRET ->
# Settings.jwt_secret). Add new sensitive fields here as the app grows.
SECRET_TO_ENV: dict[str, str] = {
    "jwt-secret": "JWT_SECRET",
    "database-url": "DATABASE_URL",
    "stripe-api-key": "STRIPE_API_KEY",
    "stripe-webhook-secret": "STRIPE_WEBHOOK_SECRET",
    "azure-openai-api-key": "AZURE_OPENAI_API_KEY",
    "azure-search-admin-key": "AZURE_SEARCH_ADMIN_KEY",
    "azure-storage-account-key": "AZURE_STORAGE_ACCOUNT_KEY",
    "rag-admin-api-key": "RAG_ADMIN_API_KEY",
    "email-api-key": "EMAIL_API_KEY",
}


def load_keyvault_secrets(vault_url: str | None, *, override: bool = True) -> int:
    """Load mapped secrets from Key Vault into ``os.environ``.

    Args:
        vault_url: The Key Vault URI, e.g. ``https://my-kv.vault.azure.net/``.
            When falsy, this is a no-op (returns 0).
        override: When True (default), Key Vault values replace any existing
            environment values for mapped keys. When False, only missing keys
            are populated.

    Returns:
        The number of secrets successfully loaded.
    """
    if not vault_url:
        return 0

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
    except ImportError:
        logger.warning(
            "AZURE_KEYVAULT_URL is set but azure-identity/azure-keyvault-secrets "
            "are not installed; skipping Key Vault load."
        )
        return 0

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
    except Exception as exc:  # noqa: BLE001 - never block startup on KV init
        logger.warning("Failed to initialize Key Vault client for %s: %r", vault_url, exc)
        return 0

    # Fail fast: probe for a token once. If no Azure credential is available
    # (e.g. running locally in a container without managed identity, az login,
    # or a service principal), bail out immediately instead of retrying the
    # full credential chain for every secret, which would stall startup.
    try:
        credential.get_token("https://vault.azure.net/.default")
    except Exception as exc:  # noqa: BLE001 - fall back to env/.env values
        logger.warning(
            "Key Vault authentication unavailable for %s; falling back to "
            "environment/.env values. (%s)",
            vault_url,
            type(exc).__name__,
        )
        return 0

    loaded = 0
    for secret_name, env_var in SECRET_TO_ENV.items():
        if not override and os.environ.get(env_var):
            continue
        try:
            secret = client.get_secret(secret_name)
        except Exception as exc:  # noqa: BLE001 - a missing secret is non-fatal
            logger.debug("Key Vault secret '%s' not loaded: %r", secret_name, exc)
            continue
        if secret.value is not None:
            os.environ[env_var] = secret.value
            loaded += 1

    logger.info("Loaded %d secret(s) from Key Vault %s", loaded, vault_url)
    return loaded
