"""Simple in-memory rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit requests per client IP over a rolling window."""

    def __init__(self, app, requests: int, period_seconds: int):
        super().__init__(app)
        self.requests = max(1, requests)
        self.period_seconds = max(1, period_seconds)
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _prune(self, entries: deque[float], now: float) -> None:
        cutoff = now - self.period_seconds
        while entries and entries[0] < cutoff:
            entries.popleft()

    async def dispatch(self, request: Request, call_next) -> Response:
        key = self._client_key(request)
        now = time.time()

        with self._lock:
            entries = self._events[key]
            self._prune(entries, now)
            if len(entries) >= self.requests:
                retry_after = max(1, int(self.period_seconds - (now - entries[0])))
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limited",
                        "message": "Too many requests. Please retry later.",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            entries.append(now)

        return await call_next(request)
