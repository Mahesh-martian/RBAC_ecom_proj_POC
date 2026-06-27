"""
Payment processing API endpoints (Stripe integration).
"""

from collections import OrderedDict

from fastapi import APIRouter, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.schemas import PaymentIntentRequest, PaymentIntentResponse, PaymentWebhookEvent
from app.services.stripe_service import StripeService
from app.services.order_service import OrderService
from app.services.events import event_bus
from app.dependencies import CurrentUserDep, DBSessionDep
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

# In-process idempotency guard for Stripe's at-least-once delivery. Stripe retries
# webhooks, so we must not re-apply the same event. This bounded cache short-circuits
# duplicate event ids. NOTE: for multi-instance deployments replace with a shared
# store (Redis SETNX or a processed_events table) so dedupe holds across replicas.
_PROCESSED_EVENT_IDS: "OrderedDict[str, None]" = OrderedDict()
_PROCESSED_EVENTS_MAX = 5000


def _already_processed(event_id: str) -> bool:
    """Return True if this event id was already handled; otherwise record it."""
    if not event_id:
        return False
    if event_id in _PROCESSED_EVENT_IDS:
        return True
    _PROCESSED_EVENT_IDS[event_id] = None
    if len(_PROCESSED_EVENT_IDS) > _PROCESSED_EVENTS_MAX:
        _PROCESSED_EVENT_IDS.popitem(last=False)  # evict oldest
    return False


@router.post(
    "/intent",
    response_model=PaymentIntentResponse,
    summary="Create Stripe PaymentIntent"
)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: CurrentUserDep,
    session: DBSessionDep,
) -> PaymentIntentResponse:
    """
    Create Stripe PaymentIntent for order payment.
    
    Response includes:
    - **client_secret**: Use this with Stripe.js on frontend
    - **amount**: Amount in cents
    - **currency**: Currency code
    """
    # Get order
    order = await OrderService.get_order_by_id(request.order_id, session)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create payment for another user's order"
        )
    
    if order.status.value != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create payment for order with status {order.status}"
        )
    
    # Create Stripe PaymentIntent
    amount_cents = int(order.total * 100)  # Convert to cents
    
    result = await StripeService.create_payment_intent(
        amount_cents=amount_cents,
        currency="usd",
        metadata={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "user_id": str(order.user_id),
        }
    )
    
    return PaymentIntentResponse(
        client_secret=result["client_secret"],
        order_id=order.id,
        amount=order.total,
        currency="USD",
    )


@router.post(
    "/confirm",
    summary="Confirm payment"
)
async def confirm_payment(
    order_id: int,
    payment_intent_id: str,
    current_user: CurrentUserDep,
    session: DBSessionDep,
) -> dict:
    """
    Confirm payment status.
    In production, payment confirmation typically happens client-side via Stripe.js,
    and this endpoint can be called for additional verification or webhook fallback.
    """
    # Get order
    order = await OrderService.get_order_by_id(order_id, session)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot confirm payment for another user's order"
        )
    
    # Retrieve PaymentIntent to check status
    pi_data = await StripeService.retrieve_payment_intent(payment_intent_id)
    
    if pi_data["status"] == "succeeded":
        # Mark order as paid
        order = await OrderService.mark_payment_received(order_id, payment_intent_id, session)
        return {
            "status": "success",
            "message": "Payment confirmed",
            "order_id": order.id,
            "order_number": order.order_number,
        }
    else:
        return {
            "status": "pending",
            "message": f"Payment status: {pi_data['status']}",
            "order_id": order.id,
        }


@router.post(
    "/webhook",
    summary="Stripe webhook handler"
)
async def handle_webhook(
    request: Request,
    session: DBSessionDep,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
) -> dict:
    """
    Handle Stripe webhook events.
    Stripe sends events here: charge.succeeded, charge.failed, charge.refunded, etc.

    Production hardening:
    - Reads the RAW request body (required for signature verification).
    - Verifies the Stripe-Signature header against STRIPE_WEBHOOK_SECRET.
    - De-duplicates retried deliveries by event id (idempotency).
    - Returns 200 for handled/ignored/duplicate events so Stripe stops retrying;
      returns 5xx only on transient processing failures so Stripe retries.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header"
        )

    # Raw bytes are required; Stripe computes the HMAC over the exact payload.
    raw_body = await request.body()

    # Verify webhook signature and parse event (raises 400/403 on failure).
    event = StripeService.verify_webhook_signature(raw_body, stripe_signature)

    event_id = event.get("id", "")
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    # Idempotency: skip events we have already applied.
    if _already_processed(event_id):
        logger.info("Duplicate webhook ignored: id=%s type=%s", event_id, event_type)
        return {"status": "duplicate", "event_id": event_id, "event_type": event_type}

    logger.info("Webhook received: id=%s type=%s", event_id, event_type)

    try:
        if event_type == "charge.succeeded":
            StripeService.handle_charge_succeeded(event_data)

            # Update order status if available
            payment_intent_id = event_data.get("payment_intent")
            order_number = event_data.get("metadata", {}).get("order_number")
            if payment_intent_id and order_number:
                order = await OrderService.get_order_by_number(order_number, session)
                # mark_payment_received is a no-op if already paid, keeping this idempotent.
                if order and order.status.value == "pending":
                    await OrderService.mark_payment_received(
                        order.id, payment_intent_id, session
                    )
                    # Emit a domain event so downstream consumers (inventory, email,
                    # fulfilment) react asynchronously. Fail-soft: a bus outage must
                    # not roll back a completed payment. Reuse the Stripe event id so
                    # the worker's dedupe aligns with Stripe's at-least-once delivery.
                    await event_bus.publish(
                        "payment.succeeded",
                        {
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "payment_intent_id": payment_intent_id,
                            "amount": float(order.total),
                            "user_id": order.user_id,
                        },
                        event_id=f"stripe:{event_id}",
                    )
            return {"status": "processed", "event_id": event_id, "event_type": event_type}

        elif event_type == "charge.failed":
            result = StripeService.handle_charge_failed(event_data)
            logger.warning(f"Payment failed: {result}")
            return {"status": "processed", "event_id": event_id, "event_type": event_type}

        elif event_type == "charge.refunded":
            result = StripeService.handle_charge_refunded(event_data)
            logger.info(f"Charge refunded: {result}")
            return {"status": "processed", "event_id": event_id, "event_type": event_type}

        else:
            logger.info(f"Unhandled webhook event: {event_type}")
            return {"status": "ignored", "event_id": event_id, "event_type": event_type}

    except Exception as e:
        # Roll back our idempotency record so Stripe's retry can re-attempt this event.
        _PROCESSED_EVENT_IDS.pop(event_id, None)
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing error"
        )


@router.post(
    "/{order_id}/refund",
    summary="Request refund for order"
)
async def request_refund(
    order_id: int,
    reason: Optional[str] = None,
    current_user: CurrentUserDep = None,
    session: DBSessionDep = None,
) -> dict:
    """
    Request refund for completed order.
    Admin would typically process this after review.
    """
    # Get order
    order = await OrderService.get_order_by_id(order_id, session)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot request refund for another user's order"
        )
    
    if not order.payment_intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No payment found for this order"
        )
    
    try:
        refund = await StripeService.refund_payment(
            order.payment_intent_id,
            reason=reason or "requested_by_customer"
        )
        
        # Update order status
        from app.models import OrderStatus
        order = await OrderService.update_order_status(
            order_id, OrderStatus.REFUNDED, session
        )
        
        return {
            "status": "refund_processed",
            "refund_id": refund["refund_id"],
            "amount": refund["amount"] / 100,  # Convert from cents
            "order_id": order.id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Refund processing failed"
        )
