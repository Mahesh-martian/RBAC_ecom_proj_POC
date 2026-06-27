"""Lightweight async event bus for decoupled, at-least-once processing.

Transport is **Redis Streams** (consumer groups give at-least-once delivery with
explicit acks). When ``REDIS_URL`` is unset the bus degrades to a no-op publisher
so request paths never fail just because the bus is unavailable.

The publish/consume surface mirrors a queue broker, so moving to **Azure Service
Bus** in production only requires swapping this module's implementation — callers
(producers in the API, the consumer in worker.py) stay the same.

Event envelope::

    {"id": "evt_...", "type": "payment.succeeded", "occurred_at": "<iso>", "data": {...}}
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

STREAM_PREFIX = "stream:"
PROCESSED_KEY_PREFIX = "processed:"
PROCESSED_TTL_SECONDS = 7 * 24 * 3600  # remember handled events for a week


def make_event(event_type: str, data: dict[str, Any], event_id: Optional[str] = None) -> dict[str, Any]:
    """Build a normalized event envelope."""
    return {
        "id": event_id or f"evt_{uuid.uuid4().hex}",
        "type": event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


class EventBus:
    """Redis Streams event bus with a no-op fallback when Redis is not configured."""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self._redis_url = redis_url if redis_url is not None else settings.redis_url
        self._client: Any = None  # redis.asyncio.Redis, created lazily

    @property
    def enabled(self) -> bool:
        return bool(self._redis_url)

    async def connect(self) -> None:
        """Create the Redis client lazily (idempotent)."""
        if self._client is not None or not self._redis_url:
            return
        # Imported lazily so the package is only required where the bus is used.
        from redis import asyncio as aioredis

        self._client = aioredis.from_url(self._redis_url, decode_responses=True)
        logger.info("EventBus connected to Redis")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _stream(event_type: str) -> str:
        return f"{STREAM_PREFIX}{event_type}"

    async def publish(self, event_type: str, data: dict[str, Any], event_id: Optional[str] = None) -> Optional[str]:
        """Publish an event. Fail-soft: never raises into the caller's request path."""
        event = make_event(event_type, data, event_id)
        if not self._redis_url:
            logger.info("EventBus disabled (no REDIS_URL); dropping event type=%s", event_type)
            return None
        try:
            await self.connect()
            message_id = await self._client.xadd(
                self._stream(event_type), {"payload": json.dumps(event)}
            )
            logger.info("Published event type=%s id=%s stream_msg=%s", event_type, event["id"], message_id)
            return message_id
        except Exception as exc:  # transport problems must not break the API request
            logger.error("EventBus publish failed type=%s error=%s", event_type, exc)
            return None

    async def ensure_group(self, event_type: str, group: str) -> None:
        """Create the consumer group (and stream) if it does not already exist."""
        await self.connect()
        try:
            await self._client.xgroup_create(
                name=self._stream(event_type), groupname=group, id="0", mkstream=True
            )
            logger.info("Created consumer group=%s stream=%s", group, self._stream(event_type))
        except Exception as exc:
            # BUSYGROUP means the group already exists — that is fine.
            if "BUSYGROUP" not in str(exc):
                raise

    async def read(
        self,
        event_type: str,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 5000,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Read undelivered messages for this consumer. Returns [(message_id, event)]."""
        await self.connect()
        response = await self._client.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={self._stream(event_type): ">"},
            count=count,
            block=block_ms,
        )
        messages: list[tuple[str, dict[str, Any]]] = []
        for _stream_name, entries in response or []:
            for message_id, fields in entries:
                try:
                    event = json.loads(fields.get("payload", "{}"))
                except json.JSONDecodeError:
                    event = {}
                messages.append((message_id, event))
        return messages

    async def ack(self, event_type: str, group: str, message_id: str) -> None:
        await self._client.xack(self._stream(event_type), group, message_id)

    async def is_processed(self, event_id: str) -> bool:
        """Idempotency check via SET NX. Returns True if the event was already handled."""
        if not event_id:
            return False
        await self.connect()
        # SET key 1 NX EX ttl -> returns True if newly set, None if it already existed.
        created = await self._client.set(
            f"{PROCESSED_KEY_PREFIX}{event_id}", "1", nx=True, ex=PROCESSED_TTL_SECONDS
        )
        return created is None

    async def unmark_processed(self, event_id: str) -> None:
        """Remove the idempotency marker so a failed event can be retried."""
        if event_id and self._client is not None:
            await self._client.delete(f"{PROCESSED_KEY_PREFIX}{event_id}")


# Module-level singleton used by API producers.
event_bus = EventBus()
