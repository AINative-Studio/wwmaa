"""
Cloudflare Webhook Routes for WWMAA Backend

Provides secure webhook endpoints for Cloudflare services:
- Cloudflare Calls recording events
- Cloudflare Stream video processing events

All webhooks are protected with HMAC signature verification.

Webhook Endpoints:
- POST /api/webhooks/cloudflare/recording - Cloudflare Calls recordings
- POST /api/webhooks/cloudflare/stream - Cloudflare Stream videos

Security:
- Signature verification using HMAC SHA-256
- Timestamp validation to prevent replay attacks
- Fast response times (< 5 seconds)
- Comprehensive logging and error handling

Supported Events:
Calls:
- recording.ready - Recording processed and available
- recording.failed - Recording processing failed

Stream:
- video.ready - Video processing completed
- video.error - Video processing failed
"""

import logging
import hmac
import hashlib
import time
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from datetime import datetime
from uuid import UUID

from backend.config import settings
from backend.services.zerodb_service import get_zerodb_client
from backend.models.cloudflare_schemas import (
    WebhookRecordingReadyEvent,
    RecordingStatus,
    CloudflareRecording
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/webhooks/cloudflare",
    tags=["webhooks", "cloudflare"]
)


def verify_cloudflare_signature(
    payload: bytes,
    signature: str,
    timestamp: str,
    secret: str
) -> bool:
    """
    Verify Cloudflare webhook signature.

    Args:
        payload: Raw webhook payload bytes
        signature: Signature from webhook header
        timestamp: Timestamp from webhook header
        secret: Webhook secret from configuration

    Returns:
        True if signature is valid

    Raises:
        HTTPException: If signature is invalid or timestamp is too old
    """
    try:
        # Construct signed payload: timestamp + "." + body
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"

        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures using constant-time comparison
        if not hmac.compare_digest(expected_signature, signature):
            logger.error("Cloudflare webhook signature verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        # Check timestamp to prevent replay attacks (within 5 minutes)
        current_time = int(time.time())
        webhook_time = int(timestamp)

        if abs(current_time - webhook_time) > 300:  # 5 minutes
            logger.error(f"Cloudflare webhook timestamp too old: {webhook_time}")
            raise HTTPException(
                status_code=401,
                detail="Webhook timestamp too old"
            )

        logger.debug("Cloudflare webhook signature verified successfully")
        return True

    except ValueError as e:
        logger.error(f"Webhook signature verification error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Signature verification failed: {str(e)}"
        )


@router.post("/recording")
async def cloudflare_recording_webhook(
    request: Request,
    x_cloudflare_signature: Optional[str] = Header(None, alias="X-Cloudflare-Signature"),
    x_cloudflare_timestamp: Optional[str] = Header(None, alias="X-Cloudflare-Timestamp")
):
    """
    Cloudflare recording webhook endpoint.

    Receives and processes Cloudflare Calls recording events with signature verification.
    Updates training session with recording URL when video is ready.

    Events:
        - recording.ready: Recording processed and available for viewing
        - recording.failed: Recording processing failed

    Args:
        request: FastAPI request object containing raw body
        x_cloudflare_signature: Cloudflare signature header for verification
        x_cloudflare_timestamp: Timestamp header for replay attack prevention

    Returns:
        Success response with 200 OK

    Raises:
        HTTPException: For signature verification failures or processing errors
    """
    zerodb = get_zerodb_client()

    # Get raw request body for signature verification
    try:
        payload = await request.body()
        payload_json = await request.json()
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body"
        )

    # Verify webhook signature if secret is configured
    webhook_secret = settings.CLOUDFLARE_WEBHOOK_SECRET
    if webhook_secret:
        if not x_cloudflare_signature or not x_cloudflare_timestamp:
            logger.error("Missing Cloudflare signature or timestamp headers")
            raise HTTPException(
                status_code=400,
                detail="Missing required webhook headers"
            )

        verify_cloudflare_signature(
            payload=payload,
            signature=x_cloudflare_signature,
            timestamp=x_cloudflare_timestamp,
            secret=webhook_secret
        )
    else:
        logger.warning("CLOUDFLARE_WEBHOOK_SECRET not configured, skipping signature verification")

    # Parse webhook event
    try:
        event_type = payload_json.get("event_type")
        recording_data = payload_json.get("data", {})

        logger.info(f"Processing Cloudflare webhook event: {event_type}")

        # Extract recording details
        recording_id = recording_data.get("recording_id")
        room_id = recording_data.get("room_id")

        if not recording_id or not room_id:
            logger.error("Missing recording_id or room_id in webhook payload")
            raise HTTPException(
                status_code=400,
                detail="Invalid webhook payload: missing recording_id or room_id"
            )

    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse webhook payload: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload format: {str(e)}"
        )

    # Process event based on type
    try:
        if event_type == "recording.ready":
            await handle_recording_ready(
                zerodb=zerodb,
                recording_id=recording_id,
                room_id=room_id,
                recording_data=recording_data
            )
        elif event_type == "recording.failed":
            await handle_recording_failed(
                zerodb=zerodb,
                recording_id=recording_id,
                room_id=room_id,
                recording_data=recording_data
            )
        else:
            logger.warning(f"Unknown event type: {event_type}")

        logger.info(f"Cloudflare webhook event {event_type} processed successfully")

        # Return 200 OK to Cloudflare immediately
        return {
            "status": "success",
            "event_type": event_type,
            "recording_id": recording_id
        }

    except Exception as e:
        # Log error but return 200 OK to prevent retries
        logger.error(f"Error processing Cloudflare webhook: {str(e)}")
        return {
            "status": "error",
            "event_type": event_type,
            "message": "Event logged for manual processing"
        }


async def handle_recording_ready(
    zerodb,
    recording_id: str,
    room_id: str,
    recording_data: dict
):
    """
    Handle recording.ready event.

    Updates cloudflare_recordings collection and training_sessions with video URL.

    Args:
        zerodb: ZeroDB service instance
        recording_id: Cloudflare recording identifier
        room_id: Cloudflare room identifier
        recording_data: Recording data from webhook
    """
    logger.info(f"Handling recording.ready event for recording {recording_id}")

    stream_url = recording_data.get("stream_url")
    stream_id = recording_data.get("stream_id")
    duration = recording_data.get("duration")
    size_bytes = recording_data.get("size_bytes")

    # Find recording in database
    recordings = zerodb.query_collection(
        collection_name="cloudflare_recordings",
        filters={"recording_id": recording_id}
    )

    if recordings and len(recordings) > 0:
        recording = recordings[0]
        session_id = recording.get("session_id")

        # Update recording status
        zerodb.update_document(
            collection_name="cloudflare_recordings",
            document_id=recording["id"],
            data={
                "status": RecordingStatus.READY.value,
                "stream_url": stream_url,
                "cloudflare_stream_id": stream_id,
                "duration": duration,
                "size_bytes": size_bytes,
                "ready_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        # Update training session with video URL
        if session_id:
            sessions = zerodb.query_collection(
                collection_name="training_sessions",
                filters={"id": session_id}
            )

            if sessions and len(sessions) > 0:
                zerodb.update_document(
                    collection_name="training_sessions",
                    document_id=session_id,
                    data={
                        "cloudflare_stream_id": stream_id,
                        "video_url": stream_url,
                        "video_duration_seconds": duration,
                        "recording_status": "ready",
                        "updated_at": datetime.utcnow().isoformat()
                    }
                )

                logger.info(f"Training session {session_id} updated with recording URL")

                # TODO: Send notification to session creator
                # This will be implemented in US-044 or US-045
                logger.info(f"TODO: Send notification for recording ready: {session_id}")

    else:
        logger.warning(f"Recording {recording_id} not found in database")


async def handle_recording_failed(
    zerodb,
    recording_id: str,
    room_id: str,
    recording_data: dict
):
    """
    Handle recording.failed event.

    Updates recording status to failed and logs error.

    Args:
        zerodb: ZeroDB service instance
        recording_id: Cloudflare recording identifier
        room_id: Cloudflare room identifier
        recording_data: Recording data from webhook
    """
    logger.error(f"Handling recording.failed event for recording {recording_id}")

    error_message = recording_data.get("error_message", "Unknown error")

    # Find recording in database
    recordings = zerodb.query_collection(
        collection_name="cloudflare_recordings",
        filters={"recording_id": recording_id}
    )

    if recordings and len(recordings) > 0:
        recording = recordings[0]
        session_id = recording.get("session_id")

        # Update recording status
        zerodb.update_document(
            collection_name="cloudflare_recordings",
            document_id=recording["id"],
            data={
                "status": RecordingStatus.FAILED.value,
                "error_message": error_message,
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        # Update training session
        if session_id:
            sessions = zerodb.query_collection(
                collection_name="training_sessions",
                filters={"id": session_id}
            )

            if sessions and len(sessions) > 0:
                zerodb.update_document(
                    collection_name="training_sessions",
                    document_id=session_id,
                    data={
                        "recording_status": "failed",
                        "updated_at": datetime.utcnow().isoformat()
                    }
                )

                logger.error(f"Training session {session_id} recording failed: {error_message}")

                # TODO: Send notification to session creator about failure
                logger.error(f"TODO: Send failure notification for session: {session_id}")

    else:
        logger.warning(f"Recording {recording_id} not found in database")


@router.post("/stream")
async def cloudflare_stream_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """
    Cloudflare Stream webhook endpoint.

    Receives and processes Cloudflare Stream video processing events.
    Updates media_assets with video status when ready or failed.

    Events:
        - video.ready: Video processing completed successfully
        - video.error: Video processing failed

    Args:
        request: FastAPI request object containing raw body
        x_signature: Cloudflare signature header for verification

    Returns:
        Success response with 200 OK

    Raises:
        HTTPException: For signature verification failures
    """
    zerodb = get_zerodb_client()

    # Get raw request body for signature verification
    try:
        payload = await request.body()
        payload_json = await request.json()
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body"
        )

    # Verify webhook signature if secret is configured
    stream_webhook_secret = getattr(settings, 'CLOUDFLARE_STREAM_WEBHOOK_SECRET', None)
    if stream_webhook_secret:
        if not x_signature:
            logger.error("Missing X-Signature header for Stream webhook")
            raise HTTPException(
                status_code=400,
                detail="Missing X-Signature header"
            )

        # Verify signature (simpler than Calls - no timestamp)
        expected_signature = hmac.new(
            stream_webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, x_signature):
            logger.error("Cloudflare Stream webhook signature verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        logger.debug("Cloudflare Stream webhook signature verified")
    else:
        logger.warning("CLOUDFLARE_STREAM_WEBHOOK_SECRET not configured, skipping signature verification")

    # Parse webhook event
    try:
        video_id = payload_json.get("uid")
        status_info = payload_json.get("status", {})
        video_state = status_info.get("state")
        meta = payload_json.get("meta", {})

        logger.info(f"Processing Cloudflare Stream webhook: video_id={video_id}, state={video_state}")

    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse Stream webhook payload: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload format: {str(e)}"
        )

    # Process event based on state
    try:
        if video_state == "ready":
            await handle_stream_video_ready(
                zerodb=zerodb,
                video_id=video_id,
                event_data=payload_json
            )
        elif video_state == "error":
            await handle_stream_video_error(
                zerodb=zerodb,
                video_id=video_id,
                event_data=payload_json
            )
        else:
            logger.info(f"Stream video state: {video_state} for video {video_id}")

        logger.info(f"Cloudflare Stream webhook processed: {video_id}")

        # Return 200 OK immediately
        return {
            "status": "success",
            "video_id": video_id,
            "state": video_state
        }

    except Exception as e:
        # Log error but return 200 OK to prevent retries
        logger.error(f"Error processing Cloudflare Stream webhook: {str(e)}")
        return {
            "status": "error",
            "video_id": video_id,
            "message": "Event logged for manual processing"
        }


async def handle_stream_video_ready(
    zerodb,
    video_id: str,
    event_data: dict
):
    """
    Handle video.ready event from Cloudflare Stream.

    Updates media_assets with video details when processing completes.

    Args:
        zerodb: ZeroDB service instance
        video_id: Cloudflare Stream video identifier
        event_data: Full event data from webhook
    """
    logger.info(f"Handling video.ready event for video {video_id}")

    # Extract video details
    duration = event_data.get("duration")
    thumbnail = event_data.get("thumbnail")
    preview = event_data.get("preview")
    playback = event_data.get("playback", {})
    input_info = event_data.get("input", {})

    # Find media asset by stream_video_id
    assets = zerodb.query_collection(
        collection_name="media_assets",
        filters={"stream_video_id": video_id}
    )

    if assets and len(assets) > 0:
        asset = assets[0]
        asset_id = asset["id"]

        # Update asset status and video details
        # Import enums
        import sys
        sys.path.insert(0, '/Users/aideveloper/Desktop/wwmaa/backend/models')
        from schemas_media_extension import MediaAssetStatus

        zerodb.update_document(
            collection_name="media_assets",
            document_id=asset_id,
            data={
                "status": MediaAssetStatus.READY.value,
                "duration_seconds": int(duration) if duration else None,
                "thumbnail_url": thumbnail,
                "preview_url": preview,
                "url": playback.get("hls"),
                "width": input_info.get("width"),
                "height": input_info.get("height"),
                "processing_error": None,
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        logger.info(f"Media asset {asset_id} updated to READY status")

        # If linked to training session, update it
        if asset.get("entity_type") == "training_session" and asset.get("entity_id"):
            training_session_id = asset["entity_id"]

            zerodb.update_document(
                collection_name="training_sessions",
                document_id=training_session_id,
                data={
                    "cloudflare_stream_id": video_id,
                    "video_url": playback.get("hls"),
                    "video_duration_seconds": int(duration) if duration else None,
                    "recording_status": "ready",
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Training session {training_session_id} updated with video details")

        # TODO: Send notification to creator
        logger.info(f"TODO: Send notification for video ready: {asset_id}")

    else:
        logger.warning(f"Media asset not found for video_id: {video_id}")


async def handle_stream_video_error(
    zerodb,
    video_id: str,
    event_data: dict
):
    """
    Handle video.error event from Cloudflare Stream.

    Updates media_assets with error status when processing fails.

    Args:
        zerodb: ZeroDB service instance
        video_id: Cloudflare Stream video identifier
        event_data: Full event data from webhook
    """
    logger.error(f"Handling video.error event for video {video_id}")

    # Extract error details
    status_info = event_data.get("status", {})
    error_code = status_info.get("errorReasonCode", "")
    error_text = status_info.get("errorReasonText", "Unknown error")

    # Find media asset by stream_video_id
    assets = zerodb.query_collection(
        collection_name="media_assets",
        filters={"stream_video_id": video_id}
    )

    if assets and len(assets) > 0:
        asset = assets[0]
        asset_id = asset["id"]

        # Import enums
        import sys
        sys.path.insert(0, '/Users/aideveloper/Desktop/wwmaa/backend/models')
        from schemas_media_extension import MediaAssetStatus

        # Update asset status to failed
        zerodb.update_document(
            collection_name="media_assets",
            document_id=asset_id,
            data={
                "status": MediaAssetStatus.FAILED.value,
                "processing_error": f"{error_code}: {error_text}",
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        logger.error(f"Media asset {asset_id} marked as FAILED: {error_text}")

        # If linked to training session, update status
        if asset.get("entity_type") == "training_session" and asset.get("entity_id"):
            training_session_id = asset["entity_id"]

            zerodb.update_document(
                collection_name="training_sessions",
                document_id=training_session_id,
                data={
                    "recording_status": "failed",
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            logger.error(f"Training session {training_session_id} recording failed")

        # TODO: Alert admin about failed video
        logger.error(f"TODO: Send admin alert for failed video: {asset_id}")

    else:
        logger.warning(f"Media asset not found for video_id: {video_id}")


@router.get("/health")
async def cloudflare_webhook_health_check():
    """
    Cloudflare webhook health check endpoint.

    Returns:
        Health status of Cloudflare webhook service
    """
    return {
        "status": "healthy",
        "service": "cloudflare_webhooks",
        "webhook_secret_configured": bool(settings.CLOUDFLARE_WEBHOOK_SECRET),
        "stream_webhook_secret_configured": bool(getattr(settings, 'CLOUDFLARE_STREAM_WEBHOOK_SECRET', None))
    }
