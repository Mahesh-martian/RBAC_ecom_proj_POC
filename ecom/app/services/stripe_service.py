"""
Stripe payment integration service.
"""

import stripe
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_api_key
stripe.api_version = settings.stripe_api_version


class StripeService:
    """Stripe payment processing service."""
    
    @staticmethod
    async def create_payment_intent(
        amount_cents: int,
        currency: str = "usd",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent.
        
        Args:
            amount_cents: Amount in cents (e.g., $10.50 = 1050)
            currency: Currency code (usd, eur, etc.)
            metadata: Custom metadata to attach
            
        Returns:
            PaymentIntent object
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
            )
            logger.info(f"Created PaymentIntent: {intent.id}")
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment processing error: {str(e)}"
            )
    
    @staticmethod
    async def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a Stripe PaymentIntent.
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            
        Returns:
            PaymentIntent object
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "payment_intent_id": intent.id,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "charges": intent.charges.data,
                "client_secret": intent.client_secret,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving PaymentIntent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve payment intent"
            )
    
    @staticmethod
    async def confirm_payment_intent(
        payment_intent_id: str,
        payment_method_id: str,
    ) -> Dict[str, Any]:
        """
        Confirm a payment (optional, can also confirm client-side).
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            payment_method_id: Stripe PaymentMethod ID
            
        Returns:
            Confirmed PaymentIntent
        """
        try:
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id,
            )
            logger.info(f"Confirmed PaymentIntent: {intent.id}, Status: {intent.status}")
            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "client_secret": intent.client_secret,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment confirmation failed: {str(e)}"
            )
    
    @staticmethod
    async def refund_payment(
        payment_intent_id: str,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """
        Refund a successful payment.
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            reason: Refund reason
            
        Returns:
            Refund object
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not intent.charges.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No charges to refund"
                )
            
            charge_id = intent.charges.data[0].id
            
            refund = stripe.Refund.create(
                charge=charge_id,
                reason=reason,
            )
            
            logger.info(f"Refund created: {refund.id} for charge: {charge_id}")
            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount,
                "reason": refund.reason,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund failed: {str(e)}"
            )
    
    @staticmethod
    def verify_webhook_signature(body: str, signature: str) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature and return event.
        
        Args:
            body: Raw webhook body
            signature: Stripe-Signature header
            
        Returns:
            Parsed event object
            
        Raises:
            HTTPException: If signature invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                body,
                signature,
                settings.stripe_webhook_secret
            )
            return event
        except ValueError:
            logger.error("Invalid webhook payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload"
            )
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
    
    @staticmethod
    def handle_charge_succeeded(charge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle charge.succeeded webhook event.
        
        Args:
            charge: Charge object from webhook
            
        Returns:
            Event summary
        """
        payment_intent_id = charge.get("payment_intent")
        amount = charge.get("amount")
        metadata = charge.get("metadata", {})
        
        logger.info(
            f"Charge succeeded: {charge['id']}, "
            f"Amount: {amount}, "
            f"PaymentIntent: {payment_intent_id}"
        )
        
        return {
            "event_type": "charge.succeeded",
            "charge_id": charge["id"],
            "payment_intent_id": payment_intent_id,
            "amount": amount,
            "metadata": metadata,
        }
    
    @staticmethod
    def handle_charge_failed(charge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle charge.failed webhook event.
        
        Args:
            charge: Charge object from webhook
            
        Returns:
            Event summary
        """
        payment_intent_id = charge.get("payment_intent")
        failure_code = charge.get("failure_code")
        failure_message = charge.get("failure_message")
        
        logger.warning(
            f"Charge failed: {charge['id']}, "
            f"Code: {failure_code}, "
            f"Message: {failure_message}"
        )
        
        return {
            "event_type": "charge.failed",
            "charge_id": charge["id"],
            "payment_intent_id": payment_intent_id,
            "failure_code": failure_code,
            "failure_message": failure_message,
        }
    
    @staticmethod
    def handle_charge_refunded(charge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle charge.refunded webhook event.
        
        Args:
            charge: Charge object from webhook
            
        Returns:
            Event summary
        """
        logger.info(f"Charge refunded: {charge['id']}, Amount: {charge.get('amount_refunded')}")
        
        return {
            "event_type": "charge.refunded",
            "charge_id": charge["id"],
            "payment_intent_id": charge.get("payment_intent"),
            "amount_refunded": charge.get("amount_refunded"),
        }
