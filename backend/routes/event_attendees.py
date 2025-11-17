"""
Event Attendee Management Routes for WWMAA Backend

Admin-only endpoints for managing event attendees:
- List attendees with filtering
- Export to CSV
- Bulk email
- Check-in management
- Waitlist promotion
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, Field, EmailStr

from backend.middleware.auth_middleware import require_role
from backend.services.attendee_service import get_attendee_service, AttendeeServiceError
from backend.models.schemas import UserRole

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/events",
    tags=["event-attendees"]
)

# Get service instance
# NOTE: Commented out to prevent module-level DB connection during imports (breaks tests)
# Use get_attendee_service() instead
# attendee_service = get_attendee_service()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class BulkEmailRequest(BaseModel):
    """Request model for bulk email"""
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    message: str = Field(..., min_length=1, description="Email message body (HTML supported)")
    status_filter: Optional[str] = Field(None, description="Filter by attendee status")


class PromoteWaitlistRequest(BaseModel):
    """Request model for promoting waitlist"""
    count: int = Field(default=1, ge=1, le=100, description="Number of attendees to promote")


class AttendeeListResponse(BaseModel):
    """Response model for attendee list"""
    attendees: list
    total: int
    limit: int
    offset: int


class BulkEmailResponse(BaseModel):
    """Response model for bulk email"""
    sent: int
    failed: int
    total: int
    errors: list


class CheckInResponse(BaseModel):
    """Response model for check-in"""
    success: bool
    message: str
    rsvp: dict


class WaitlistPromotionResponse(BaseModel):
    """Response model for waitlist promotion"""
    promoted: int
    attendees: list
    message: str


class AttendeeStatsResponse(BaseModel):
    """Response model for attendee statistics"""
    total: int
    confirmed: int
    waitlist: int
    canceled: int
    checked_in: int
    no_show: int
    pending: int


# ============================================================================
# ROUTES
# ============================================================================

@router.get(
    "/{event_id}/attendees",
    response_model=AttendeeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Event Attendees (Admin)",
    description="Get list of attendees for an event with optional filtering and search"
)
async def list_attendees(
    event_id: UUID,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER]))
):
    """
    List attendees for an event (Admin/Board Member only)

    Query Parameters:
    - status: Filter by RSVP status (all, confirmed, waitlist, canceled, checked-in, no-show)
    - search: Search by name or email
    - limit: Maximum results (default: 100)
    - offset: Pagination offset (default: 0)

    Returns:
    - List of attendees with RSVP details
    - Total count and pagination info
    """
    try:
        logger.info(f"Listing attendees for event {event_id} by user {current_user['email']}")

        result = get_attendee_service().get_attendees(
            event_id=event_id,
            status=status,
            search=search,
            limit=limit,
            offset=offset
        )

        return result

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch attendees: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error listing attendees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{event_id}/attendees/export",
    status_code=status.HTTP_200_OK,
    summary="Export Attendees to CSV (Admin)",
    description="Export event attendees to CSV file"
)
async def export_attendees(
    event_id: UUID,
    status: Optional[str] = None,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER]))
):
    """
    Export attendees to CSV (Admin/Board Member only)

    Query Parameters:
    - status: Optional status filter

    Returns:
    - CSV file download
    """
    try:
        logger.info(f"Exporting attendees for event {event_id} by user {current_user['email']}")

        csv_content = get_attendee_service().export_attendees_csv(
            event_id=event_id,
            status=status
        )

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"attendees_{event_id}_{timestamp}.csv"

        # Return CSV file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV export failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting attendees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{event_id}/attendees/bulk-email",
    response_model=BulkEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Bulk Email to Attendees (Admin)",
    description="Send email to all or filtered attendees"
)
async def send_bulk_email(
    event_id: UUID,
    request: BulkEmailRequest,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER]))
):
    """
    Send bulk email to attendees (Admin/Board Member only)

    Request Body:
    - subject: Email subject
    - message: Email body (HTML supported)
    - status_filter: Optional filter (confirmed, waitlist, etc.)

    Returns:
    - Send statistics (sent, failed, total)
    - List of errors (if any)
    """
    try:
        logger.info(f"Sending bulk email for event {event_id} by user {current_user['email']}")

        result = get_attendee_service().send_bulk_email(
            event_id=event_id,
            subject=request.subject,
            message=request.message,
            status_filter=request.status_filter,
            user_email=current_user["email"]
        )

        return result

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk email failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error sending bulk email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{event_id}/attendees/{rsvp_id}/check-in",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="Check In Attendee (Admin)",
    description="Mark an attendee as checked in"
)
async def check_in_attendee(
    event_id: UUID,
    rsvp_id: UUID,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER, UserRole.INSTRUCTOR]))
):
    """
    Check in an attendee (Admin/Board Member/Instructor)

    Path Parameters:
    - event_id: Event UUID
    - rsvp_id: RSVP UUID

    Returns:
    - Updated RSVP data
    - Success message
    """
    try:
        logger.info(f"Checking in attendee {rsvp_id} for event {event_id} by user {current_user['email']}")

        result = get_attendee_service().check_in_attendee(
            rsvp_id=rsvp_id,
            checked_in_by=UUID(current_user["id"])
        )

        return {
            "success": True,
            "message": "Attendee checked in successfully",
            "rsvp": result
        }

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check-in failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error checking in attendee: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{event_id}/attendees/{rsvp_id}/no-show",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark Attendee as No-Show (Admin)",
    description="Mark an attendee as a no-show"
)
async def mark_no_show(
    event_id: UUID,
    rsvp_id: UUID,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER]))
):
    """
    Mark attendee as no-show (Admin/Board Member only)

    Path Parameters:
    - event_id: Event UUID
    - rsvp_id: RSVP UUID

    Returns:
    - Updated RSVP data
    - Success message
    """
    try:
        logger.info(f"Marking attendee {rsvp_id} as no-show for event {event_id} by user {current_user['email']}")

        result = get_attendee_service().mark_no_show(
            rsvp_id=rsvp_id,
            marked_by=UUID(current_user["id"])
        )

        return {
            "success": True,
            "message": "Attendee marked as no-show",
            "rsvp": result
        }

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No-show marking failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error marking no-show: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{event_id}/waitlist/promote",
    response_model=WaitlistPromotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Promote from Waitlist (Admin)",
    description="Promote attendees from waitlist to confirmed"
)
async def promote_from_waitlist(
    event_id: UUID,
    request: PromoteWaitlistRequest,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER]))
):
    """
    Promote attendees from waitlist (Admin/Board Member only)

    Request Body:
    - count: Number of attendees to promote (1-100)

    Returns:
    - Number of promoted attendees
    - List of promoted attendees
    - Success message
    """
    try:
        logger.info(f"Promoting {request.count} from waitlist for event {event_id} by user {current_user['email']}")

        result = get_attendee_service().promote_from_waitlist(
            event_id=event_id,
            count=request.count
        )

        return result

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Waitlist promotion failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error promoting waitlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{event_id}/attendees/stats",
    response_model=AttendeeStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Attendee Statistics (Admin)",
    description="Get attendance statistics for an event"
)
async def get_attendee_stats(
    event_id: UUID,
    current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.BOARD_MEMBER, UserRole.INSTRUCTOR]))
):
    """
    Get attendee statistics (Admin/Board Member/Instructor)

    Returns:
    - Total attendees
    - Confirmed count
    - Waitlist count
    - Canceled count
    - Checked-in count
    - No-show count
    - Pending count
    """
    try:
        logger.info(f"Getting attendee stats for event {event_id} by user {current_user['email']}")

        stats = get_attendee_service().get_attendee_stats(event_id=event_id)

        return stats

    except AttendeeServiceError as e:
        logger.error(f"Attendee service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats query failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
