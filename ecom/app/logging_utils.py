"""Structured logging helpers with request-id correlation.

Provides:
* a ``request_id`` :class:`contextvars.ContextVar` set by the telemetry middleware
  so every log emitted while handling a request carries the same correlation id,
* a JSON log formatter (used when ``settings.log_format == "json"``) that folds the
  request id and any structured ``extra`` fields into a single JSON line, and
* :func:`log_step`, a small helper for emitting one structured per-step RAG log
  (embed / retrieve / prompt / llm) that is gated behind ``settings.rag_step_logging``
  or DEBUG level so it can be disabled in production.
"""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

# Correlation id for the in-flight request. Empty string when outside a request
# (e.g. background tasks / startup) so logs still format cleanly.
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

# Reserved LogRecord attributes we must not treat as user-supplied "extra" fields.
_RESERVED_RECORD_KEYS = set(
    logging.makeLogRecord({}).__dict__.keys()
) | {"message", "asctime", "request_id"}


def get_request_id() -> str:
    """Return the current request correlation id, or an empty string if unset."""
    return request_id_ctx.get()


class RequestIdFilter(logging.Filter):
    """Attach the current ``request_id`` to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - stdlib name
        if not getattr(record, "request_id", None):
            record.request_id = request_id_ctx.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """Render log records as single-line JSON including structured extra fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "") or request_id_ctx.get(),
        }

        # Fold any structured fields passed via ``extra={...}`` into the payload.
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_KEYS or key in payload:
                continue
            if key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def log_step(
    logger: logging.Logger,
    step: str,
    *,
    enabled: bool,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Emit one structured per-step log line for a RAG pipeline stage.

    ``step`` names the stage (e.g. ``"embed_query"``, ``"retrieve"``, ``"prompt"``,
    ``"llm"``). Extra keyword ``fields`` are attached as structured attributes so the
    JSON formatter surfaces them (and they remain readable in plain-text mode).

    The call is skipped entirely when neither ``enabled`` (the ``rag_step_logging``
    flag) is set nor the logger is enabled for DEBUG, so production stays quiet.
    """
    if not enabled and not logger.isEnabledFor(logging.DEBUG):
        return
    # When only DEBUG enabled it (not the flag), demote to DEBUG.
    effective_level = level if enabled else logging.DEBUG
    logger.log(
        effective_level,
        "rag_step %s",
        step,
        extra={"event": "rag_step", "step": step, **fields},
    )
