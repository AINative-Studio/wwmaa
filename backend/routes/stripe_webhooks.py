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


@router.post("/cloudflare/recordings")
async def cloudflare_recording_webhook(request: Request):
    """
    Cloudflare webhook endpoint for recording events (US-046)

    Receives and processes Cloudflare Calls/Stream webhook events for:
    - recording.started: Recording has started
    - recording.complete: Recording uploaded to Stream and ready
    - recording.failed: Recording failed

    Args:
        request: FastAPI request object containing webhook payload

    Returns:
        Success response with 200 OK

    Raises:
        HTTPException: For processing errors
    """
    from backend.services.recording_service import get_recording_service
    from backend.services.email_service import get_email_service
    from backend.services.zerodb_service import get_zerodb_client

    # Get raw request body
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body"
        )

    event_type = payload.get("event")
    event_data = payload.get("data", {})

    logger.info(f"Processing Cloudflare webhook event: {event_type}")

    # TODO: Add webhook signature verification for security
    # For now, processing without verification

    try:
        recording_service = get_recording_service()
        email_service = get_email_service()
        db_service = get_zerodb_client()

        if event_type == "recording.complete":
            # Recording has been uploaded to Stream and is ready
            recording_id = event_data.get("recordingId")
            stream_id = event_data.get("streamId")
            stream_url = event_data.get("streamUrl")
            duration_seconds = event_data.get("duration")
            file_size_bytes = event_data.get("fileSize")
            room_id = event_data.get("roomId")

            logger.info(f"Recording complete for recording {recording_id}, stream {stream_id}")

            # Find session by room_id
            session_result = db_service.query_documents(
                collection="training_sessions",
                filters={"cloudflare_room_id": room_id},
                limit=1
            )

            sessions = session_result.get("documents", [])
            if not sessions:
                logger.error(f"No session found for room {room_id}")
                return {
                    "status": "error",
                    "message": f"No session found for room {room_id}"
                }

            session = sessions[0].get("data", {})
            session_id = session.get("id")

            # Attach recording to session
            recording_service.attach_recording(
                session_id=session_id,
                stream_id=stream_id,
                stream_url=stream_url,
                duration_seconds=duration_seconds,
                file_size_bytes=file_size_bytes
            )

            # Send notification emails
            try:
                # Get instructor info
                instructor_id = session.get("instructor_id")
                instructor_result = db_service.get_document("users", str(instructor_id))
                instructor = instructor_result.get("data", {})

                # Send instructor notification
                if instructor:
                    email_service.send_recording_ready_email_instructor(
                        email=instructor.get("email"),
                        instructor_name=instructor.get("first_name", "Instructor"),
                        session_title=session.get("title"),
                        session_date=session.get("session_date"),
                        duration_minutes=duration_seconds // 60 if duration_seconds else None,
                        view_url=f"{settings.PYTHON_BACKEND_URL}/training/sessions/{session_id}"
                    )

                # Get registered participants and send notifications
                # TODO: Query RSVPs/attendance records and send participant emails

            except Exception as e:
                logger.error(f"Failed to send notification emails: {e}")
                # Don't fail webhook if email fails

            logger.info(f"Recording webhook processed successfully for session {session_id}")

            return {
                "status": "success",
                "event": event_type,
                "session_id": str(session_id),
                "stream_id": stream_id
            }

        elif event_type == "recording.failed":
            # Recording failed
            recording_id = event_data.get("recordingId")
            error_message = event_data.get("error", "Unknown error")
            room_id = event_data.get("roomId")

            logger.error(f"Recording failed for recording {recording_id}: {error_message}")

            # Find session by room_id
            session_result = db_service.query_documents(
                collection="training_sessions",
                filters={"cloudflare_room_id": room_id},
                limit=1
            )

            sessions = session_result.get("documents", [])
            if sessions:
                session = sessions[0].get("data", {})
                session_id = session.get("id")

                # Update session with failure status
                db_service.update_document(
                    "training_sessions",
                    str(session_id),
                    {
                        "recording_status": "failed",
                        "recording_error": error_message
                    }
                )

                logger.info(f"Updated session {session_id} with recording failure")

            return {
                "status": "error",
                "event": event_type,
                "recording_id": recording_id,
                "error": error_message
            }

        else:
            logger.warning(f"Unhandled Cloudflare event type: {event_type}")
            return {
                "status": "ignored",
                "event": event_type,
                "message": "Event type not handled"
            }

    except Exception as e:
        logger.error(f"Error processing Cloudflare webhook: {e}")
        # Return 200 OK to prevent Cloudflare retries
        # Log error for manual investigation
        return {
            "status": "error",
            "event": event_type,
            "message": str(e)
        }


@router.get("/cloudflare/health")
async def cloudflare_webhook_health_check():
    """
    Cloudflare webhook health check endpoint

    Returns:
        Health status of Cloudflare webhook service
    """
    return {
        "status": "healthy",
        "service": "cloudflare_webhooks",
        "cloudflare_account_configured": bool(settings.CLOUDFLARE_ACCOUNT_ID)
    }
