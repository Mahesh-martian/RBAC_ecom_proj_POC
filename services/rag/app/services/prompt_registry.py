"""Versioned prompt registry with YAML-on-disk and Langfuse backends.

The registry is the single entry point for every prompt used by the RAG pipeline
(system prompt, per-role personas, help texts, and the semantic router's intent
anchors). Prompts live in ``services/rag/prompts/<id>[/<variant>]/vN.yaml`` and
are always resolvable locally. When Langfuse credentials are configured and the
provider is set to ``composite`` (or ``langfuse``), the registry tries Langfuse
first and transparently falls back to YAML on any error.

Design goals:
* Never break on missing Langfuse creds or a network outage — YAML always wins as
  the fallback so the service stays up.
* Provide a stable ``PromptTemplate`` object every caller can rely on, whose
  ``label`` (``id@vN``) is emitted alongside the answer for auditability.
* Support both plain-string templates and structured payloads (intent anchors)
  through a single object.
* Cache aggressively: prompts don't change per request; loading YAML off disk on
  every chat call would be wasteful.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional, Protocol

logger = logging.getLogger(__name__)


class PromptNotFoundError(LookupError):
    """Raised when a requested (id, version, variant) cannot be resolved."""


@dataclass(frozen=True)
class PromptTemplate:
    """A single prompt version.

    ``template`` holds a plain-string payload (typical LLM prompts). When the
    prompt is a structured payload (e.g. router intent anchors), ``structured``
    carries the parsed data and ``template`` is empty.
    """

    id: str
    version: str
    template: str = ""
    structured: Any = None
    variant: Optional[str] = None
    variables: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "yaml"  # "yaml" | "langfuse"

    @property
    def label(self) -> str:
        """Short identifier for logs, response payloads, and eval reports."""
        base = f"{self.id}@v{self.version}"
        return f"{base}:{self.variant}" if self.variant else base

    def render(self, **variables: Any) -> str:
        """Render a plain-string template with ``{var}``-style substitutions.

        Passing extra kwargs not declared in ``variables`` is allowed; missing
        declared variables raise ``KeyError`` from ``str.format``.
        """
        if not self.template:
            raise ValueError(
                f"Prompt {self.label} has no string template (structured payload only)"
            )
        return self.template.format(**variables) if variables else self.template


class PromptRegistry(Protocol):
    """Interface implemented by every backend."""

    def get(
        self,
        prompt_id: str,
        *,
        version: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> PromptTemplate: ...


# --------------------------------------------------------------------- YAML backend


_VERSION_FILE_RE = re.compile(r"^v(?P<num>\d+)\.ya?ml$", re.IGNORECASE)


class YamlPromptRegistry:
    """Read prompt YAMLs from ``prompts/<id>[/<variant>]/vN.yaml``.

    The active version defaults to the highest ``N`` in the folder unless
    ``PROMPT_<ID>_VERSION`` (upper-cased) is set — for example
    ``PROMPT_SUPPORT_SYSTEM_VERSION=2``.
    """

    def __init__(self, prompts_dir: Path | str | None = None, cache_ttl_seconds: int = 300):
        base = Path(__file__).resolve().parents[2]
        self._dir = Path(prompts_dir) if prompts_dir is not None else (base / "prompts")
        self._cache: dict[str, tuple[float, PromptTemplate]] = {}
        self._ttl = max(0, cache_ttl_seconds)
        self._lock = threading.Lock()

    @property
    def prompts_dir(self) -> Path:
        return self._dir

    # -- Cache helpers -----------------------------------------------------
    def _cache_key(self, prompt_id: str, variant: Optional[str], version: Optional[str]) -> str:
        return f"{prompt_id}::{variant or ''}::{version or 'active'}"

    def _cache_get(self, key: str) -> Optional[PromptTemplate]:
        with self._lock:
            hit = self._cache.get(key)
        if not hit:
            return None
        ts, value = hit
        if self._ttl and (time.time() - ts) > self._ttl:
            return None
        return value

    def _cache_put(self, key: str, value: PromptTemplate) -> None:
        with self._lock:
            self._cache[key] = (time.time(), value)

    # -- Version resolution ------------------------------------------------
    def _folder_for(self, prompt_id: str, variant: Optional[str]) -> Path:
        folder = self._dir / prompt_id
        if variant:
            folder = folder / variant
        return folder

    def _list_versions(self, folder: Path) -> list[tuple[int, Path]]:
        if not folder.is_dir():
            return []
        versions: list[tuple[int, Path]] = []
        for entry in folder.iterdir():
            if not entry.is_file():
                continue
            match = _VERSION_FILE_RE.match(entry.name)
            if not match:
                continue
            versions.append((int(match.group("num")), entry))
        return sorted(versions, key=lambda x: x[0])

    def _resolve_active_version(self, prompt_id: str) -> Optional[str]:
        env_key = f"PROMPT_{prompt_id.upper()}_VERSION"
        pinned = os.environ.get(env_key)
        return pinned.strip() if pinned else None

    # -- Public API --------------------------------------------------------
    def get(
        self,
        prompt_id: str,
        *,
        version: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> PromptTemplate:
        # Env-var pin takes precedence over caller-supplied version.
        pinned = self._resolve_active_version(prompt_id)
        effective_version = pinned or version

        cache_key = self._cache_key(prompt_id, variant, effective_version)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        folder = self._folder_for(prompt_id, variant)
        versions = self._list_versions(folder)
        if not versions:
            raise PromptNotFoundError(
                f"No prompt files found for id={prompt_id} variant={variant} at {folder}"
            )

        if effective_version:
            match = next(
                (path for num, path in versions if str(num) == str(effective_version)),
                None,
            )
            if match is None:
                raise PromptNotFoundError(
                    f"Prompt {prompt_id} version {effective_version} not found "
                    f"(available: {[n for n, _ in versions]})"
                )
            path = match
        else:
            # Highest numeric version wins by default.
            path = versions[-1][1]

        template = self._load_file(path, prompt_id, variant)
        self._cache_put(cache_key, template)
        return template

    def _load_file(
        self,
        path: Path,
        expected_id: str,
        expected_variant: Optional[str],
    ) -> PromptTemplate:
        try:
            import yaml  # local import so PyYAML is only required when this backend is used
        except ImportError as exc:  # pragma: no cover - handled by requirements pin
            raise RuntimeError(
                "PyYAML is required for the YAML prompt registry. Install via 'pip install PyYAML'."
            ) from exc

        try:
            with path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
        except Exception as exc:  # noqa: BLE001 - surface any parse error clearly
            raise RuntimeError(f"Failed to load prompt file {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise RuntimeError(f"Prompt file {path} must be a YAML mapping")

        file_id = str(raw.get("id") or expected_id)
        if file_id != expected_id:
            logger.warning(
                "prompt_registry file id mismatch: %s declared id=%s but is in folder %s",
                path,
                file_id,
                expected_id,
            )

        variant = raw.get("variant")
        if variant is not None and expected_variant is not None and variant != expected_variant:
            logger.warning(
                "prompt_registry variant mismatch in %s: declared=%s folder=%s",
                path,
                variant,
                expected_variant,
            )

        version_field = raw.get("version")
        if version_field is None:
            match = _VERSION_FILE_RE.match(path.name)
            version_field = match.group("num") if match else "1"
        version = str(version_field)

        template_text = raw.get("template", "") or ""
        if template_text and not isinstance(template_text, str):
            raise RuntimeError(
                f"Prompt {path}: 'template' must be a string (got {type(template_text).__name__})"
            )

        structured = raw.get("structured")

        variables_raw = raw.get("variables") or []
        if isinstance(variables_raw, str):
            variables_raw = [variables_raw]
        variables = tuple(str(v) for v in variables_raw)

        metadata = {
            "path": str(path),
            "description": raw.get("description"),
        }

        return PromptTemplate(
            id=expected_id,
            version=version,
            template=str(template_text).rstrip("\n"),
            structured=structured,
            variant=expected_variant if expected_variant else raw.get("variant"),
            variables=variables,
            metadata=metadata,
            source="yaml",
        )

    def invalidate(self, prompt_id: Optional[str] = None) -> None:
        """Drop cached entries — call after editing files on disk."""
        with self._lock:
            if prompt_id is None:
                self._cache.clear()
                return
            prefix = f"{prompt_id}::"
            for key in list(self._cache.keys()):
                if key.startswith(prefix):
                    del self._cache[key]


# --------------------------------------------------------------------- Langfuse backend


class LangfusePromptRegistry:
    """Fetch prompts from Langfuse. Falls back to raising when unavailable.

    Prompts registered in Langfuse should be named as ``{id}`` or
    ``{id}/{variant}`` (Langfuse names allow slashes). The active version is
    Langfuse's "production" label unless a specific ``version`` (int) is passed.
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        self._ttl = max(0, cache_ttl_seconds)
        self._cache: dict[str, tuple[float, PromptTemplate]] = {}
        self._lock = threading.Lock()
        self._client = None
        self._available = False
        self._init_error: Optional[str] = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from langfuse import Langfuse  # type: ignore
        except ImportError as exc:
            self._init_error = f"langfuse package not installed: {exc}"
            return

        from app.config import settings

        if not (settings.langfuse_public_key and settings.langfuse_secret_key):
            self._init_error = "Langfuse credentials not configured"
            return

        try:
            self._client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host or "https://cloud.langfuse.com",
            )
            self._available = True
        except Exception as exc:  # noqa: BLE001 - keep service up even if init fails
            self._init_error = f"Langfuse client init failed: {exc}"
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def _cache_key(self, name: str, version: Optional[str]) -> str:
        return f"{name}::{version or 'production'}"

    def get(
        self,
        prompt_id: str,
        *,
        version: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> PromptTemplate:
        if not self._available or self._client is None:
            raise PromptNotFoundError(
                f"Langfuse unavailable ({self._init_error or 'not initialized'})"
            )

        name = f"{prompt_id}/{variant}" if variant else prompt_id
        cache_key = self._cache_key(name, version)
        with self._lock:
            hit = self._cache.get(cache_key)
        if hit and (not self._ttl or (time.time() - hit[0]) <= self._ttl):
            return hit[1]

        try:
            fetch_kwargs: dict[str, Any] = {"name": name}
            if version is not None:
                try:
                    fetch_kwargs["version"] = int(version)
                except ValueError:
                    fetch_kwargs["label"] = version
            prompt_obj = self._client.get_prompt(**fetch_kwargs)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001 - fallback is the caller's job
            raise PromptNotFoundError(f"Langfuse fetch failed for {name}: {exc}") from exc

        template_text = getattr(prompt_obj, "prompt", None) or ""
        version_str = str(getattr(prompt_obj, "version", version or "1"))

        template = PromptTemplate(
            id=prompt_id,
            version=version_str,
            template=str(template_text),
            structured=None,
            variant=variant,
            variables=tuple(getattr(prompt_obj, "variables", ()) or ()),
            metadata={"langfuse_labels": list(getattr(prompt_obj, "labels", []) or [])},
            source="langfuse",
        )
        with self._lock:
            self._cache[cache_key] = (time.time(), template)
        return template


# --------------------------------------------------------------------- Composite


class CompositePromptRegistry:
    """Try one registry first, fall back to the next on ``PromptNotFoundError``."""

    def __init__(self, primary: PromptRegistry, fallback: PromptRegistry):
        self._primary = primary
        self._fallback = fallback

    def get(
        self,
        prompt_id: str,
        *,
        version: Optional[str] = None,
        variant: Optional[str] = None,
    ) -> PromptTemplate:
        try:
            return self._primary.get(prompt_id, version=version, variant=variant)
        except PromptNotFoundError as exc:
            logger.debug(
                "prompt_registry primary miss for %s (%s); falling back to secondary",
                prompt_id,
                exc,
            )
            return self._fallback.get(prompt_id, version=version, variant=variant)


# --------------------------------------------------------------------- Factory


_registry_singleton: Optional[PromptRegistry] = None
_registry_lock = threading.Lock()


def get_prompt_registry() -> PromptRegistry:
    """Return the process-wide prompt registry configured via settings."""
    global _registry_singleton
    if _registry_singleton is not None:
        return _registry_singleton

    with _registry_lock:
        if _registry_singleton is not None:
            return _registry_singleton

        from app.config import settings

        yaml_backend = YamlPromptRegistry(cache_ttl_seconds=settings.prompt_cache_ttl_seconds)
        provider = (settings.prompt_registry_provider or "yaml").lower()

        if provider == "yaml":
            _registry_singleton = yaml_backend
        elif provider == "langfuse":
            langfuse_backend = LangfusePromptRegistry(
                cache_ttl_seconds=settings.prompt_cache_ttl_seconds
            )
            if not langfuse_backend.available:
                logger.warning(
                    "prompt_registry provider=langfuse but backend unavailable; using YAML fallback"
                )
                _registry_singleton = yaml_backend
            else:
                _registry_singleton = langfuse_backend
        elif provider == "composite":
            langfuse_backend = LangfusePromptRegistry(
                cache_ttl_seconds=settings.prompt_cache_ttl_seconds
            )
            if langfuse_backend.available:
                _registry_singleton = CompositePromptRegistry(
                    primary=langfuse_backend, fallback=yaml_backend
                )
            else:
                logger.info(
                    "prompt_registry composite: Langfuse unavailable, using YAML backend only"
                )
                _registry_singleton = yaml_backend
        else:
            logger.warning(
                "prompt_registry unknown provider=%s; defaulting to YAML", provider
            )
            _registry_singleton = yaml_backend

        return _registry_singleton


def reset_prompt_registry() -> None:
    """Test helper: drop the singleton so the next call rebuilds it."""
    global _registry_singleton
    with _registry_lock:
        _registry_singleton = None


def collect_prompt_labels(templates: Iterable[PromptTemplate]) -> dict[str, str]:
    """Return an ``{id: label}`` dict, useful for embedding into response payloads."""
    out: dict[str, str] = {}
    for tpl in templates:
        key = f"{tpl.id}:{tpl.variant}" if tpl.variant else tpl.id
        out[key] = tpl.label
    return out
