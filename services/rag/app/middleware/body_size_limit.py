"""Request body size limiting middleware."""

from __future__ import annotations

from typing import Dict

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests that exceed the configured maximum body size."""

    def __init__(self, app, max_body_bytes: int, per_path_max_bytes: Dict[str, int] | None = None):
        super().__init__(app)
        self.max_body_bytes = max(1024, max_body_bytes)
        normalized: dict[str, int] = {}
        for path, value in (per_path_max_bytes or {}).items():
            normalized[path] = max(1024, int(value))
        self.per_path_max_bytes = normalized

    def _resolve_limit(self, path: str) -> int:
        for prefix in sorted(self.per_path_max_bytes.keys(), key=len, reverse=True):
            if path.startswith(prefix):
                return self.per_path_max_bytes[prefix]
        return self.max_body_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        max_body_bytes = self._resolve_limit(request.url.path)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_body_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "request_too_large",
                            "message": f"Request body exceeds limit of {max_body_bytes} bytes",
                        },
                    )
            except ValueError:
                # Ignore malformed header and continue to application handling.
                pass

        return await call_next(request)
