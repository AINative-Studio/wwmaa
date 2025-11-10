"""
Event RSVP Routes for WWMAA Backend

Handles all event RSVP operations including:
- Creating RSVPs for free events
- Creating Stripe checkout for paid events
- Canceling RSVPs with refund logic
- Checking RSVP status
- Managing waitlist

US-032: Event RSVP System
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Path
from pydantic import BaseModel, Field, EmailStr

from backend.services.rsvp_service import (
    get_rsvp_service,
    RSVPServiceError,
    EventFullError,
    DuplicateRSVPError,
    CancellationError
)
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import RSVPStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/events",
    tags=["event_rsvps"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateFreeRSVPRequest(BaseModel):
    """Request model for creating free event RSVP"""
    user_name: str = Field(..., min_length=1, description="User's full name")
    user_email: EmailStr = Field(..., description="User's email address")
    user_phone: Optional[str] = Field(None, description="User's phone number")


class CreateFreeRSVPResponse(BaseModel):
    """Response model for free event RSVP creation"""
    rsvp_id: str = Field(..., description="RSVP UUID")
    status: str = Field(..., description="RSVP status (confirmed)")
    event_id: str = Field(..., description="Event UUID")
    event_title: str = Field(..., description="Event title")
    event_date: str = Field(..., description="Event start date/time")
    qr_code: str = Field(..., description="Base64-encoded QR code PNG")
    message: str = Field(..., description="Success message")


class CreatePaidRSVPCheckoutRequest(BaseModel):
    """Request model for creating paid event checkout"""
    success_url: Optional[str] = Field(None, description="Custom success URL")
    cancel_url: Optional[str] = Field(None, description="Custom cancel URL")


class CreatePaidRSVPCheckoutResponse(BaseModel):
    """Response model for paid event checkout creation"""
    session_id: str = Field(..., description="Stripe checkout session ID")
    url: str = Field(..., description="Checkout URL")
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(..., description="Currency code")
    event_title: str = Field(..., description="Event title")
    expires_at: int = Field(..., description="Checkout expiration timestamp")


class CancelRSVPRequest(BaseModel):
    """Request model for canceling RSVP"""
    reason: Optional[str] = Field(None, description="Cancellation reason")


class CancelRSVPResponse(BaseModel):
    """Response model for RSVP cancellation"""
    success: bool = Field(..., description="Cancellation success")
    refund_issued: bool = Field(..., description="Whether refund was issued")
    refund_amount: Optional[float] = Field(None, description="Refund amount")
    hours_until_event: float = Field(..., description="Hours until event starts")
    message: str = Field(..., description="Cancellation message")


class RSVPStatusResponse(BaseModel):
    """Response model for RSVP status"""
    has_rsvp: bool = Field(..., description="User has RSVP for event")
    rsvp_id: Optional[str] = Field(None, description="RSVP UUID")
    status: Optional[str] = Field(None, description="RSVP status")
    rsvp_date: Optional[str] = Field(None, description="RSVP date")
    payment_status: Optional[str] = Field(None, description="Payment status")
    check_in_status: Optional[bool] = Field(None, description="Check-in status")
    can_rsvp: Optional[bool] = Field(None, description="User can RSVP")
    event_full: Optional[bool] = Field(None, description="Event is full")
    waitlist_available: Optional[bool] = Field(None, description="Waitlist available")
    available_spots: Optional[int] = Field(None, description="Available spots")


class AddToWaitlistRequest(BaseModel):
    """Request model for adding to waitlist"""
    user_name: str = Field(..., min_length=1, description="User's full name")
    user_email: EmailStr = Field(..., description="User's email address")
    user_phone: Optional[str] = Field(None, description="User's phone number")


class AddToWaitlistResponse(BaseModel):
    """Response model for waitlist addition"""
    rsvp_id: str = Field(..., description="Waitlist entry UUID")
    status: str = Field(..., description="Status (waitlist)")
    message: str = Field(..., description="Success message")


# ============================================================================
# ROUTES
# ============================================================================

@router.post(
    "/{event_id}/rsvp",
    response_model=CreateFreeRSVPResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create RSVP for Free Event",
    description="Creates an RSVP for a free event with immediate confirmation"
)
async def create_free_event_rsvp(
    event_id: str = Path(..., description="Event UUID"),
    request: CreateFreeRSVPRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Create RSVP for free event

    Flow:
    1. Verify user is authenticated (members only)
    2. Check for duplicate RSVP
    3. Check event capacity
    4. Create RSVP with confirmed status
    5. Update event attendee count
    6. Generate QR code for check-in
    7. Send confirmation email
    8. Return RSVP details

    Args:
        event_id: Event UUID
        request: RSVP creation request
        current_user: Authenticated user from JWT

    Returns:
        CreateFreeRSVPResponse with RSVP details and QR code

    Raises:
        HTTPException 400: Event full or duplicate RSVP
        HTTPException 404: Event not found
        HTTPException 500: Service error
    """
    try:
        user_id = current_user.get("user_id")
        rsvp_service = get_rsvp_service()

        result = rsvp_service.create_free_event_rsvp(
            event_id=event_id,
            user_id=user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            user_phone=request.user_phone
        )

        logger.info(f"Created free event RSVP for user {user_id}, event {event_id}")

        return CreateFreeRSVPResponse(**result)

    except DuplicateRSVPError as e:
        logger.warning(f"Duplicate RSVP attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EventFullError as e:
        logger.warning(f"Event full: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RSVPServiceError as e:
        logger.error(f"RSVP service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create RSVP: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating RSVP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{event_id}/rsvp/checkout",
    response_model=CreatePaidRSVPCheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Stripe Checkout for Paid Event",
    description="Creates Stripe checkout session for paid event RSVP"
)
async def create_paid_event_checkout(
    event_id: str = Path(..., description="Event UUID"),
    request: CreatePaidRSVPCheckoutRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Create Stripe checkout session for paid event

    RSVP is created after successful payment via webhook handler.

    Flow:
    1. Verify user is authenticated
    2. Check for duplicate RSVP
    3. Check event capacity
    4. Create Stripe checkout session
    5. Return checkout URL for redirection

    Args:
        event_id: Event UUID
        request: Checkout creation request
        current_user: Authenticated user from JWT

    Returns:
        CreatePaidRSVPCheckoutResponse with Stripe checkout URL

    Raises:
        HTTPException 400: Event full or duplicate RSVP
        HTTPException 404: Event not found
        HTTPException 500: Stripe or service error
    """
    try:
        user_id = current_user.get("user_id")
        user_email = current_user.get("email")
        rsvp_service = get_rsvp_service()

        result = rsvp_service.create_paid_event_checkout(
            event_id=event_id,
            user_id=user_id,
            user_email=user_email,
            success_url=request.success_url if request else None,
            cancel_url=request.cancel_url if request else None
        )

        logger.info(f"Created paid event checkout for user {user_id}, event {event_id}")

        return CreatePaidRSVPCheckoutResponse(**result)

    except DuplicateRSVPError as e:
        logger.warning(f"Duplicate RSVP attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EventFullError as e:
        logger.warning(f"Event full: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RSVPServiceError as e:
        logger.error(f"RSVP service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating checkout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete(
    "/{event_id}/rsvp",
    response_model=CancelRSVPResponse,
    summary="Cancel RSVP",
    description="Cancels RSVP with refund logic for paid events"
)
async def cancel_rsvp(
    event_id: str = Path(..., description="Event UUID"),
    request: CancelRSVPRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel RSVP with refund logic

    Refund Policy:
    - >24 hours before event: Full refund
    - <24 hours before event: No refund

    Flow:
    1. Verify user is authenticated
    2. Find user's RSVP for event
    3. Check if within cancellation window
    4. Issue refund if applicable
    5. Update RSVP status to canceled
    6. Update event attendee count
    7. Promote from waitlist if available
    8. Send cancellation confirmation email

    Args:
        event_id: Event UUID
        request: Cancellation request
        current_user: Authenticated user from JWT

    Returns:
        CancelRSVPResponse with cancellation details

    Raises:
        HTTPException 403: User doesn't own RSVP
        HTTPException 404: RSVP not found
        HTTPException 500: Service error
    """
    try:
        user_id = current_user.get("user_id")
        rsvp_service = get_rsvp_service()

        # First, get the user's RSVP ID
        status_result = rsvp_service.get_rsvp_status(event_id, user_id)

        if not status_result.get("has_rsvp"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No RSVP found for this event"
            )

        rsvp_id = status_result.get("rsvp_id")
        reason = request.reason if request else None

        result = rsvp_service.cancel_rsvp(
            rsvp_id=rsvp_id,
            user_id=user_id,
            reason=reason
        )

        logger.info(f"Canceled RSVP for user {user_id}, event {event_id}")

        return CancelRSVPResponse(**result)

    except CancellationError as e:
        logger.warning(f"Cancellation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except RSVPServiceError as e:
        logger.error(f"RSVP service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel RSVP: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error canceling RSVP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{event_id}/rsvp/status",
    response_model=RSVPStatusResponse,
    summary="Get RSVP Status",
    description="Gets user's RSVP status for an event"
)
async def get_rsvp_status(
    event_id: str = Path(..., description="Event UUID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's RSVP status for event

    Returns:
    - If user has RSVP: Full RSVP details
    - If no RSVP: Availability information (can RSVP, event full, etc.)

    Args:
        event_id: Event UUID
        current_user: Authenticated user from JWT

    Returns:
        RSVPStatusResponse with status information

    Raises:
        HTTPException 404: Event not found
        HTTPException 500: Service error
    """
    try:
        user_id = current_user.get("user_id")
        rsvp_service = get_rsvp_service()

        result = rsvp_service.get_rsvp_status(event_id, user_id)

        return RSVPStatusResponse(**result)

    except RSVPServiceError as e:
        logger.error(f"RSVP service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RSVP status: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting RSVP status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{event_id}/waitlist",
    response_model=AddToWaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add to Waitlist",
    description="Adds user to event waitlist when event is full"
)
async def add_to_waitlist(
    event_id: str = Path(..., description="Event UUID"),
    request: AddToWaitlistRequest = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Add user to event waitlist

    Flow:
    1. Verify waitlist is enabled for event
    2. Check for duplicate entry
    3. Create waitlist RSVP entry
    4. Send waitlist confirmation email
    5. Return waitlist entry details

    Args:
        event_id: Event UUID
        request: Waitlist request
        current_user: Authenticated user from JWT

    Returns:
        AddToWaitlistResponse with waitlist entry details

    Raises:
        HTTPException 400: Waitlist not enabled or duplicate entry
        HTTPException 404: Event not found
        HTTPException 500: Service error
    """
    try:
        user_id = current_user.get("user_id")
        rsvp_service = get_rsvp_service()

        result = rsvp_service.add_to_waitlist(
            event_id=event_id,
            user_id=user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            user_phone=request.user_phone
        )

        logger.info(f"Added user {user_id} to waitlist for event {event_id}")

        return AddToWaitlistResponse(**result)

    except DuplicateRSVPError as e:
        logger.warning(f"Duplicate waitlist attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RSVPServiceError as e:
        logger.error(f"Waitlist service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to waitlist: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error adding to waitlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/rsvps/health",
    summary="RSVP Service Health Check",
    description="Check if RSVP service is operational"
)
async def health_check():
    """
    Health check endpoint for RSVP service

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "event_rsvps",
        "version": "1.0.0"
    }
