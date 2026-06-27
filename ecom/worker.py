"""Async event worker.

Standalone process (not part of the API) that consumes domain events from the
event bus and performs side effects asynchronously and idempotently:

  - ``payment.succeeded`` -> decrement inventory for the order's items, write an
    inventory audit log, and "send" an order-confirmation email (logged here).

Delivery is at-least-once, so every handler is idempotent: the bus records each
processed event id (Redis ``SET NX``), and inventory changes are guarded against
double-application. In Azure this same loop maps onto a Service Bus queue
consumer with KEDA-based scaling; only ``app.services.events`` changes.

Run with::

    python -m worker
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket

from sqlalchemy import select

from app.config import settings
from app.db import DatabaseManager
from app.models import InventoryLog, OrderItem, Product
from app.services.events import EventBus

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [worker] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

# Topics this worker subscribes to.
TOPICS = ["payment.succeeded"]

_shutdown = asyncio.Event()


def _request_shutdown(*_args: object) -> None:
    logger.info("Shutdown signal received; finishing in-flight work...")
    _shutdown.set()


async def _handle_payment_succeeded(event: dict) -> None:
    """Idempotently fulfil a paid order: decrement stock + audit + confirm email."""
    data = event.get("data", {})
    order_id = data.get("order_id")
    order_number = data.get("order_number")
    if not order_id:
        logger.warning("payment.succeeded missing order_id; skipping event=%s", event.get("id"))
        return

    session_factory = DatabaseManager.get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        items = result.scalars().all()

        if not items:
            logger.info("No order items for order_id=%s; nothing to fulfil", order_id)
        else:
            for item in items:
                product = await session.get(Product, item.product_id)
                if product is None:
                    logger.warning("Product %s not found for order %s", item.product_id, order_id)
                    continue
                # Guard against negative inventory under concurrent fulfilment.
                decrement = min(item.quantity, product.stock_qty or 0)
                product.stock_qty = (product.stock_qty or 0) - decrement
                session.add(
                    InventoryLog(
                        product_id=product.id,
                        change_qty=-decrement,
                        reason="sale",
                        details={
                            "order_id": order_id,
                            "order_number": order_number,
                            "event_id": event.get("id"),
                            "requested_qty": item.quantity,
                        },
                    )
                )
                logger.info(
                    "Inventory -%s for product=%s (order=%s) new_stock=%s",
                    decrement,
                    product.id,
                    order_number,
                    product.stock_qty,
                )
            await session.commit()

    # Email side effect — logged here; a real deployment would call an email
    # provider (SendGrid/ACS). Kept inside the handler so a delivery retry resends.
    logger.info("Order confirmation email queued for order=%s", order_number or order_id)


HANDLERS = {
    "payment.succeeded": _handle_payment_succeeded,
}


async def _process_topic(bus: EventBus, topic: str, group: str, consumer: str) -> None:
    """Read and dispatch a batch from one topic."""
    messages = await bus.read(topic, group, consumer, count=10, block_ms=5000)
    for message_id, event in messages:
        event_id = event.get("id", "")
        try:
            if await bus.is_processed(event_id):
                logger.info("Duplicate event ignored id=%s topic=%s", event_id, topic)
                await bus.ack(topic, group, message_id)
                continue

            handler = HANDLERS.get(event.get("type"))
            if handler is None:
                logger.info("No handler for event type=%s; acking", event.get("type"))
                await bus.ack(topic, group, message_id)
                continue

            await handler(event)
            await bus.ack(topic, group, message_id)
            logger.info("Processed event id=%s type=%s", event_id, event.get("type"))
        except Exception as exc:
            # Release the idempotency marker so the redelivery can retry. Leaving the
            # message unacked means it stays in the consumer group's pending list.
            await bus.unmark_processed(event_id)
            logger.error("Failed to process event id=%s: %s", event_id, exc, exc_info=True)


async def main() -> None:
    if not settings.redis_url:
        logger.error("REDIS_URL is not set; the worker requires a Redis event bus. Exiting.")
        return

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown)
        except NotImplementedError:  # Windows fallback
            signal.signal(sig, _request_shutdown)

    await DatabaseManager.initialize()

    bus = EventBus(settings.redis_url)
    await bus.connect()

    group = settings.events_consumer_group
    consumer = f"{socket.gethostname()}-{os.getpid()}"
    for topic in TOPICS:
        await bus.ensure_group(topic, group)

    logger.info("Worker started group=%s consumer=%s topics=%s", group, consumer, TOPICS)

    try:
        while not _shutdown.is_set():
            for topic in TOPICS:
                if _shutdown.is_set():
                    break
                await _process_topic(bus, topic, group, consumer)
    finally:
        await bus.close()
        await DatabaseManager.close()
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
