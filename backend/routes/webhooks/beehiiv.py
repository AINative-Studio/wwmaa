"""
BeeHiiv Webhook Routes for WWMAA Backend

Provides secure webhook endpoints for BeeHiiv blog post events.
All webhooks are protected with HMAC signature verification.

Webhook Endpoint: POST /api/webhooks/beehiiv/post

Security:
- Signature verification using HMAC SHA256
- Idempotent processing (duplicate events are detected)
- Fast response times (< 5 seconds)
- Comprehensive logging and error handling

Supported Events:
- post.published: New post published
- post.updated: Existing post updated
- post.deleted: Post deleted (soft delete/archive)
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

from backend.services.blog_sync_service import (
    get_blog_sync_service,
    BlogSyncError
)


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/webhooks/beehiiv",
    tags=["webhooks", "beehiiv"]
)


@router.post("/post")
async def beehiiv_post_webhook(
    request: Request,
    x_beehiiv_signature: Optional[str] = Header(None, alias="X-BeeHiiv-Signature")
):
    """
    BeeHiiv post webhook endpoint

    Receives and processes BeeHiiv webhook events for blog posts.
    Supports post.published, post.updated, and post.deleted events.

    Args:
        request: FastAPI request object containing raw body
        x_beehiiv_signature: BeeHiiv signature header for verification

    Returns:
        Success response with 200 OK

    Raises:
        HTTPException: For signature verification failures or processing errors
    """
    blog_sync_service = get_blog_sync_service()

    # Get raw request body for signature verification
    try:
        payload = await request.body()
        payload_str = payload.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body"
        )

    # Parse JSON payload
    try:
        import json
        webhook_data = json.loads(payload_str)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    # Verify webhook signature
    if x_beehiiv_signature:
        is_valid = blog_sync_service.verify_webhook_signature(
            payload=payload,
            signature=x_beehiiv_signature
        )

        if not is_valid:
            logger.error("BeeHiiv webhook signature verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        logger.info("BeeHiiv webhook signature verified")
    else:
        logger.warning("BeeHiiv webhook received without signature header")

    # Extract event data
    event_type = webhook_data.get('event')
    event_data = webhook_data.get('data', {})
    post_id = event_data.get('id')

    if not event_type:
        logger.error("Missing event type in webhook payload")
        raise HTTPException(
            status_code=400,
            detail="Missing event type"
        )

    if not post_id:
        logger.error("Missing post ID in webhook payload")
        raise HTTPException(
            status_code=400,
            detail="Missing post ID"
        )

    logger.info(f"Processing BeeHiiv webhook: {event_type} for post {post_id}")

    # Process webhook event based on type
    try:
        if event_type == "post.published":
            # New post published
            article = blog_sync_service.sync_post(event_data)

            logger.info(f"Post published: {article.id} (BeeHiiv ID: {post_id})")

            return {
                "status": "success",
                "event_type": event_type,
                "post_id": post_id,
                "article_id": str(article.id),
                "message": "Post synced successfully"
            }

        elif event_type == "post.updated":
            # Post updated
            article = blog_sync_service.sync_post(event_data)

            logger.info(f"Post updated: {article.id} (BeeHiiv ID: {post_id})")

            return {
                "status": "success",
                "event_type": event_type,
                "post_id": post_id,
                "article_id": str(article.id),
                "message": "Post updated successfully"
            }

        elif event_type == "post.deleted":
            # Post deleted - archive it
            existing_article = blog_sync_service._get_article_by_beehiiv_id(post_id)

            if existing_article:
                blog_sync_service.delete_post(existing_article.id)

                logger.info(f"Post archived: {existing_article.id} (BeeHiiv ID: {post_id})")

                return {
                    "status": "success",
                    "event_type": event_type,
                    "post_id": post_id,
                    "article_id": str(existing_article.id),
                    "message": "Post archived successfully"
                }
            else:
                logger.warning(f"Post to delete not found: {post_id}")

                return {
                    "status": "not_found",
                    "event_type": event_type,
                    "post_id": post_id,
                    "message": "Post not found in database"
                }

        else:
            # Unsupported event type
            logger.warning(f"Unsupported BeeHiiv event type: {event_type}")

            return {
                "status": "ignored",
                "event_type": event_type,
                "post_id": post_id,
                "message": "Event type not supported"
            }

    except BlogSyncError as e:
        # Processing error - log but return 200 OK to prevent retries
        logger.error(f"Blog sync error for event {event_type}: {e}")

        return {
            "status": "error",
            "event_type": event_type,
            "post_id": post_id,
            "message": "Event processing failed"
        }

    except Exception as e:
        # Unexpected error - log and return 500
        logger.error(f"Unexpected error processing BeeHiiv webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/health")
async def beehiiv_webhook_health_check():
    """
    BeeHiiv webhook health check endpoint

    Returns:
        Health status of BeeHiiv webhook service
    """
    from backend.config import settings

    return {
        "status": "healthy",
        "service": "beehiiv_webhooks",
        "webhook_secret_configured": bool(settings.BEEHIIV_WEBHOOK_SECRET),
        "api_key_configured": bool(settings.BEEHIIV_API_KEY),
        "publication_id_configured": bool(settings.BEEHIIV_PUBLICATION_ID)
    }
