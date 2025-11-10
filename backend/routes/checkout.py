"""
Checkout Routes for WWMAA Backend

Handles Stripe checkout session creation and payment processing
for membership subscriptions.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field, EmailStr
from backend.services.stripe_service import get_stripe_service, CheckoutSessionError, StripeServiceError
from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/checkout",
    tags=["checkout"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateCheckoutSessionRequest(BaseModel):
    """Request model for creating a checkout session"""
    application_id: str = Field(..., description="Application ID for the membership")
    tier_id: str = Field(..., description="Subscription tier (basic, premium, lifetime)")
    success_url: Optional[str] = Field(None, description="Custom success URL (optional)")
    cancel_url: Optional[str] = Field(None, description="Custom cancel URL (optional)")


class CheckoutSessionResponse(BaseModel):
    """Response model for checkout session creation"""
    session_id: str = Field(..., description="Stripe checkout session ID")
    url: str = Field(..., description="Checkout session URL")
    amount: int = Field(..., description="Payment amount in cents")
    currency: str = Field(..., description="Payment currency")
    tier: str = Field(..., description="Subscription tier")
    mode: str = Field(..., description="Payment mode (payment or subscription)")
    expires_at: int = Field(..., description="Session expiration timestamp")


class RetrieveSessionRequest(BaseModel):
    """Request model for retrieving a checkout session"""
    session_id: str = Field(..., description="Stripe checkout session ID")


class RetrieveSessionResponse(BaseModel):
    """Response model for checkout session retrieval"""
    id: str
    payment_status: str
    customer_email: Optional[str] = None
    amount_total: Optional[int] = None
    currency: Optional[str] = None
    status: str


class ProcessPaymentRequest(BaseModel):
    """Request model for processing a successful payment"""
    session_id: str = Field(..., description="Stripe checkout session ID")


class ProcessPaymentResponse(BaseModel):
    """Response model for payment processing"""
    success: bool
    user_id: str
    application_id: str
    subscription_id: Optional[str] = None
    tier: str
    amount: float


# ============================================================================
# ROUTES
# ============================================================================

@router.post(
    "/create-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe Checkout Session",
    description="Creates a Stripe checkout session for membership payment"
)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session for membership payment

    This endpoint creates a hosted Stripe Checkout session for a user to complete
    their membership payment after application approval.

    Flow:
    1. Validate user owns the application
    2. Validate application is approved
    3. Create Stripe checkout session
    4. Return checkout URL for redirection

    Args:
        request: Checkout session creation request
        current_user: Authenticated user from JWT

    Returns:
        CheckoutSessionResponse with session details

    Raises:
        HTTPException 400: Invalid request data
        HTTPException 403: User doesn't own application
        HTTPException 404: Application not found
        HTTPException 500: Stripe API error
    """
    try:
        user_id = current_user.get("user_id")

        # Initialize services
        stripe_service = get_stripe_service()
        db = ZeroDBClient()

        # Validate application exists and belongs to user
        try:
            app_result = db.get_document("applications", request.application_id)
            application = app_result.get("data", {})

            if not application:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found"
                )

            # Check ownership
            if str(application.get("user_id")) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to access this application"
                )

            # Check if application is approved
            app_status = application.get("status")
            if app_status != "approved":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Application must be approved before payment. Current status: {app_status}"
                )

            # Check if payment already completed
            if application.get("payment_completed"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment already completed for this application"
                )

        except ZeroDBNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        # Get user email for checkout
        try:
            user_result = db.get_document("users", user_id)
            user = user_result.get("data", {})
            customer_email = user.get("email") or application.get("email")
        except Exception:
            customer_email = application.get("email")

        # Create checkout session
        try:
            session_data = stripe_service.create_checkout_session(
                user_id=user_id,
                application_id=request.application_id,
                tier_id=request.tier_id,
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                customer_email=customer_email
            )

            logger.info(
                f"Checkout session created for user {user_id}, "
                f"application {request.application_id}, tier {request.tier_id}"
            )

            return CheckoutSessionResponse(**session_data)

        except CheckoutSessionError as e:
            logger.error(f"Checkout session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create checkout session: {str(e)}"
            )
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/retrieve-session",
    response_model=RetrieveSessionResponse,
    summary="Retrieve Checkout Session",
    description="Retrieves checkout session details by session ID"
)
async def retrieve_checkout_session(
    request: RetrieveSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve a Stripe checkout session by ID

    Allows users to check the status of their checkout session.

    Args:
        request: Session retrieval request
        current_user: Authenticated user from JWT

    Returns:
        RetrieveSessionResponse with session details

    Raises:
        HTTPException 404: Session not found
        HTTPException 500: Stripe API error
    """
    try:
        stripe_service = get_stripe_service()

        session_data = stripe_service.retrieve_checkout_session(request.session_id)

        logger.info(f"Checkout session retrieved: {request.session_id}")

        return RetrieveSessionResponse(**session_data)

    except CheckoutSessionError as e:
        logger.error(f"Session retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/process-payment",
    response_model=ProcessPaymentResponse,
    summary="Process Successful Payment",
    description="Processes a successful payment and creates subscription"
)
async def process_payment(
    request: ProcessPaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process a successful payment from checkout session

    This endpoint is called after a successful payment to:
    1. Verify payment completed
    2. Create subscription in database
    3. Update application status

    Args:
        request: Payment processing request
        current_user: Authenticated user from JWT

    Returns:
        ProcessPaymentResponse with subscription details

    Raises:
        HTTPException 400: Payment not completed
        HTTPException 404: Session not found
        HTTPException 500: Processing error
    """
    try:
        stripe_service = get_stripe_service()

        # Process the payment
        result = stripe_service.process_successful_payment(request.session_id)

        # Verify user owns this session
        user_id = current_user.get("user_id")
        if str(result.get("user_id")) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to process this payment"
            )

        logger.info(
            f"Payment processed for user {user_id}, "
            f"session {request.session_id}"
        )

        return ProcessPaymentResponse(**result)

    except StripeServiceError as e:
        logger.error(f"Payment processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/tier-pricing/{tier_id}",
    summary="Get Tier Pricing",
    description="Get pricing information for a subscription tier"
)
async def get_tier_pricing(tier_id: str):
    """
    Get pricing information for a subscription tier

    Public endpoint to fetch tier pricing without authentication.

    Args:
        tier_id: Subscription tier ID (basic, premium, lifetime)

    Returns:
        Dict with pricing information

    Raises:
        HTTPException 400: Invalid tier ID
    """
    try:
        stripe_service = get_stripe_service()
        pricing = stripe_service.get_tier_pricing(tier_id)

        return pricing

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting tier pricing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/health",
    summary="Checkout Service Health Check",
    description="Check if checkout service is operational"
)
async def health_check():
    """
    Health check endpoint for checkout service

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "checkout",
        "stripe_configured": bool(get_stripe_service().api_key)
    }
