"""
Newsletter Subscription Routes (US-058)

Public API endpoints for newsletter subscription management:
- POST /api/newsletter/subscribe - Create new subscription with double opt-in
- GET /api/newsletter/confirm - Confirm email subscription
- POST /api/newsletter/unsubscribe - Unsubscribe from newsletter
- GET /api/newsletter/status/{email} - Check subscription status
- PUT /api/newsletter/preferences - Update preferences

Implements:
- Double opt-in flow with email confirmation
- GDPR compliance (consent tracking, IP hashing)
- Rate limiting for subscription endpoints
- Email validation
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, Query, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from backend.services.newsletter_service import (
    NewsletterService,
    get_newsletter_service,
    NewsletterServiceError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/newsletter", tags=["Newsletter"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class NewsletterSubscribeRequest(BaseModel):
    """Newsletter subscription request"""
    email: EmailStr = Field(..., description="Subscriber email address")
    name: Optional[str] = Field(None, max_length=200, description="Subscriber name")
    interests: Optional[List[str]] = Field(
        default=None,
        description="Interests (e.g., ['events', 'training', 'articles', 'news'])"
    )
    consent: bool = Field(..., description="GDPR consent checkbox (must be true)")


class NewsletterPreferencesRequest(BaseModel):
    """Newsletter preferences update request"""
    email: EmailStr = Field(..., description="Subscriber email address")
    name: Optional[str] = Field(None, max_length=200, description="Updated name")
    interests: Optional[List[str]] = Field(
        None,
        description="Updated interests"
    )


class NewsletterUnsubscribeRequest(BaseModel):
    """Newsletter unsubscribe request"""
    email: EmailStr = Field(..., description="Subscriber email address")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for unsubscribing")


class NewsletterResponse(BaseModel):
    """Newsletter API response"""
    message: str
    status: str
    email: Optional[str] = None
    subscription_id: Optional[str] = None


# ============================================================================
# PUBLIC NEWSLETTER ENDPOINTS
# ============================================================================

@router.post("/subscribe", response_model=NewsletterResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_to_newsletter(
    request: Request,
    data: NewsletterSubscribeRequest,
    newsletter_service: NewsletterService = Depends(get_newsletter_service)
) -> NewsletterResponse:
    """
    Subscribe to newsletter with double opt-in (US-058)

    Requires:
    - Valid email address
    - GDPR consent checkbox

    Process:
    1. Validates email and consent
    2. Creates pending subscription record
    3. Sends confirmation email
    4. Returns success message

    Returns:
        - 201: Subscription created, confirmation email sent
        - 400: Invalid email or missing consent
        - 409: Email already subscribed
        - 429: Too many requests
    """
    try:
        # Validate consent
        if not data.consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GDPR consent is required to subscribe"
            )

        # Get client IP and user agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Subscribe
        result = await newsletter_service.public_subscribe(
            email=data.email,
            name=data.name,
            interests=data.interests or [],
            ip_address=client_ip,
            user_agent=user_agent,
            source="website"
        )

        # Check if already subscribed
        if result.get("status") == "already_subscribed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result["message"]
            )

        logger.info(f"Newsletter subscription created: {data.email}")

        return NewsletterResponse(
            message=result["message"],
            status=result["status"],
            email=data.email,
            subscription_id=result.get("subscription_id")
        )

    except HTTPException:
        raise
    except NewsletterServiceError as e:
        logger.error(f"Newsletter subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in newsletter subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process subscription"
        )


@router.get("/confirm")
async def confirm_newsletter_subscription(
    request: Request,
    token: str = Query(..., description="Confirmation token from email"),
    newsletter_service: NewsletterService = Depends(get_newsletter_service)
) -> RedirectResponse:
    """
    Confirm newsletter subscription (US-058)

    Validates confirmation token and activates subscription.
    Adds subscriber to BeeHiiv General list.

    Args:
        token: JWT confirmation token from email link

    Returns:
        - Redirect to thank you page on success
        - Redirect to error page on failure
    """
    try:
        # Confirm subscription
        result = await newsletter_service.confirm_public_subscription(token)

        logger.info(f"Newsletter subscription confirmed: {result.get('email')}")

        # Redirect to thank you page
        frontend_url = "http://localhost:3000"  # TODO: Use settings
        return RedirectResponse(
            url=f"{frontend_url}/newsletter/thank-you?email={result.get('email')}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    except NewsletterServiceError as e:
        logger.warning(f"Newsletter confirmation failed: {str(e)}")
        frontend_url = "http://localhost:3000"
        return RedirectResponse(
            url=f"{frontend_url}/newsletter/error?message={str(e)}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Unexpected error in newsletter confirmation: {str(e)}")
        frontend_url = "http://localhost:3000"
        return RedirectResponse(
            url=f"{frontend_url}/newsletter/error?message=Confirmation failed",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.post("/unsubscribe", response_model=NewsletterResponse)
async def unsubscribe_from_newsletter(
    data: NewsletterUnsubscribeRequest,
    newsletter_service: NewsletterService = Depends(get_newsletter_service)
) -> NewsletterResponse:
    """
    Unsubscribe from newsletter (US-058)

    Removes subscriber from BeeHiiv General list and updates database.

    Args:
        data: Unsubscribe request with email and optional reason

    Returns:
        - 200: Successfully unsubscribed
        - 404: Email not found in subscribers
    """
    try:
        result = await newsletter_service.public_unsubscribe(
            email=data.email,
            reason=data.reason
        )

        logger.info(f"Newsletter unsubscribe: {data.email}")

        return NewsletterResponse(
            message=result["message"],
            status=result["status"],
            email=data.email
        )

    except NewsletterServiceError as e:
        logger.error(f"Newsletter unsubscribe error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in newsletter unsubscribe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process unsubscribe request"
        )


@router.get("/status/{email}", response_model=dict)
async def get_subscription_status(
    email: EmailStr,
    newsletter_service: NewsletterService = Depends(get_newsletter_service)
) -> dict:
    """
    Get newsletter subscription status (US-058)

    Check if email is subscribed and get subscription details.

    Args:
        email: Email address to check

    Returns:
        - 200: Subscription status and details
    """
    try:
        result = await newsletter_service.get_public_subscription_status(email)

        return result

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription status"
        )


@router.put("/preferences", response_model=dict)
async def update_newsletter_preferences(
    data: NewsletterPreferencesRequest,
    newsletter_service: NewsletterService = Depends(get_newsletter_service)
) -> dict:
    """
    Update newsletter preferences (US-058)

    Update subscriber name and interests.

    Args:
        data: Preferences update request

    Returns:
        - 200: Preferences updated successfully
        - 404: Subscriber not found
        - 400: Cannot update inactive subscription
    """
    try:
        result = await newsletter_service.update_public_preferences(
            email=data.email,
            name=data.name,
            interests=data.interests
        )

        logger.info(f"Newsletter preferences updated: {data.email}")

        return result

    except NewsletterServiceError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating newsletter preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def newsletter_health_check() -> dict:
    """
    Newsletter service health check

    Returns:
        - 200: Service is healthy
    """
    return {
        "status": "healthy",
        "service": "newsletter",
        "endpoints": [
            "POST /api/newsletter/subscribe",
            "GET /api/newsletter/confirm",
            "POST /api/newsletter/unsubscribe",
            "GET /api/newsletter/status/{email}",
            "PUT /api/newsletter/preferences"
        ]
    }
