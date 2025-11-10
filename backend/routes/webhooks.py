"""
Stripe Webhook Routes for WWMAA Backend

Provides secure webhook endpoints for Stripe payment events.
All webhooks are protected with HMAC signature verification.

Webhook Endpoint: POST /api/webhooks/stripe

Security:
- Signature verification using stripe.Webhook.construct_event()
- Idempotent processing (duplicate events are detected and rejected)
- Fast response times (< 5 seconds) to avoid Stripe retries
- Comprehensive logging and error handling

Supported Events:
- checkout.session.completed
- invoice.paid
- invoice.payment_failed
- customer.subscription.updated
- customer.subscription.deleted
- charge.refunded
"""

import logging
import stripe
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

from backend.config import settings
from backend.services.webhook_service import (
    get_webhook_service,
    DuplicateEventError,
    WebhookProcessingError
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/webhooks",
    tags=["webhooks"]
)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """
    Stripe webhook endpoint

    Receives and processes Stripe webhook events with signature verification.
    Responds quickly (< 5 seconds) to avoid Stripe retries.

    Args:
        request: FastAPI request object containing raw body
        stripe_signature: Stripe signature header for verification

    Returns:
        Success response with 200 OK

    Raises:
        HTTPException: For signature verification failures or processing errors
    """
    webhook_service = get_webhook_service()

    # Get raw request body for signature verification
    try:
        payload = await request.body()
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body"
        )

    # Verify webhook signature
    if not stripe_signature:
        logger.error("Missing Stripe signature header")
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe-Signature header"
        )

    try:
        # Construct and verify event using Stripe's library
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )

        logger.info(f"Webhook signature verified for event {event.id}")

    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )

    # Extract event data
    event_id = event.id
    event_type = event.type
    event_data = event.to_dict()

    logger.info(f"Processing webhook event: {event_type} (ID: {event_id})")

    # Process webhook event
    try:
        result = webhook_service.process_webhook_event(
            event_id=event_id,
            event_type=event_type,
            event_data=event_data
        )

        logger.info(f"Webhook event {event_id} processed successfully")

        # Return 200 OK to Stripe immediately
        return {
            "status": "success",
            "event_id": event_id,
            "event_type": event_type,
            "result": result
        }

    except DuplicateEventError as e:
        # Event already processed - return 200 OK to prevent Stripe retries
        logger.warning(f"Duplicate event {event_id}: {e}")
        return {
            "status": "duplicate",
            "event_id": event_id,
            "message": "Event already processed"
        }

    except WebhookProcessingError as e:
        # Processing error - log but return 200 OK to prevent retries
        # (event is stored in ZeroDB for manual replay if needed)
        logger.error(f"Webhook processing error for event {event_id}: {e}")
        return {
            "status": "error",
            "event_id": event_id,
            "message": "Event stored for manual processing"
        }

    except Exception as e:
        # Unexpected error - log and return 500
        logger.error(f"Unexpected error processing webhook {event_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/stripe/health")
async def webhook_health_check():
    """
    Webhook health check endpoint

    Returns:
        Health status of webhook service
    """
    return {
        "status": "healthy",
        "service": "stripe_webhooks",
        "webhook_secret_configured": bool(settings.STRIPE_WEBHOOK_SECRET)
    }
