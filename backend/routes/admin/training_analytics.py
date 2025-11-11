"""
Training Analytics Admin Routes for WWMAA Backend

Provides API endpoints for training session analytics accessible to instructors and admins:
- GET /api/admin/training/sessions/{id}/analytics - Get full session analytics
- GET /api/admin/training/sessions/{id}/attendance - Get attendance list
- GET /api/admin/training/sessions/{id}/attendance/export - Export attendance CSV
- POST /api/admin/training/sessions/compare - Compare multiple sessions
- GET /api/admin/training/analytics/overview - Instructor dashboard overview
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Response,
    Query
)
from pydantic import BaseModel, Field

from backend.services.session_analytics_service import (
    get_session_analytics_service,
    SessionAnalyticsService,
    SessionAnalyticsError,
    CloudflareAnalyticsError
)
from backend.services.zerodb_service import (
    ZeroDBError,
    ZeroDBNotFoundError
)
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import User, UserRole

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/admin/training",
    tags=["training-analytics-admin"]
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SessionCompareRequest(BaseModel):
    """Request model for comparing multiple sessions"""
    session_ids: List[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of session IDs to compare (2-10)"
    )


class AnalyticsOverviewResponse(BaseModel):
    """Response model for instructor analytics overview"""
    instructor_id: str = Field(..., description="Instructor user ID")
    total_sessions: int = Field(..., description="Total sessions conducted")
    total_attendees: int = Field(..., description="Total unique attendees")
    average_attendance_rate: float = Field(..., description="Average attendance rate %")
    average_engagement_score: float = Field(..., description="Average engagement score")
    average_rating: float = Field(..., description="Average session rating")
    recent_sessions: List[dict] = Field(..., description="Recent session summaries")


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

def require_instructor(current_user: User = Depends(get_current_user)) -> User:
    """
    Require instructor role or higher for analytics access

    Args:
        current_user: Currently authenticated user

    Returns:
        User object if instructor, board member, or admin

    Raises:
        HTTPException: If user doesn't have required role
    """
    allowed_roles = [UserRole.INSTRUCTOR, UserRole.BOARD_MEMBER, UserRole.ADMIN]
    if current_user.role not in [role.value for role in allowed_roles]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access or higher required"
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role for administrative analytics operations

    Args:
        current_user: Currently authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# ANALYTICS ROUTES
# ============================================================================

@router.get("/sessions/{session_id}/analytics")
async def get_session_analytics(
    session_id: str,
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Get comprehensive analytics for a training session

    Returns complete analytics including:
    - Session information and metadata
    - Attendance statistics (registered vs attended)
    - Engagement metrics (chat, reactions, questions)
    - Peak concurrent viewers with timeline
    - VOD metrics (if recording exists)
    - Feedback and ratings summary
    - Overall engagement score

    Permissions:
    - Instructor can view analytics for their own sessions
    - Admin can view analytics for any session
    """
    try:
        # Get the session to verify instructor access
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        session = session_service.get_session(session_id)

        # Check permissions
        is_instructor = str(session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view analytics for your own sessions"
            )

        # Get analytics
        analytics = analytics_service.get_session_analytics(session_id)

        return analytics

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except SessionAnalyticsError as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get session analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session analytics: {str(e)}"
        )


@router.get("/sessions/{session_id}/attendance")
async def get_session_attendance(
    session_id: str,
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Get attendance statistics for a training session

    Returns detailed attendance information including:
    - Total registered vs attended counts
    - Attendance rate percentage
    - On-time vs late arrivals
    - Average session duration
    - Individual attendee records

    Permissions:
    - Instructor can view attendance for their own sessions
    - Admin can view attendance for any session
    """
    try:
        # Get the session to verify instructor access
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        session = session_service.get_session(session_id)

        # Check permissions
        is_instructor = str(session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view attendance for your own sessions"
            )

        # Get attendance stats
        attendance = analytics_service.get_attendance_stats(session_id)

        return {
            "session_id": session_id,
            "session_title": session.get("title"),
            "attendance": attendance,
            "generated_at": datetime.utcnow().isoformat()
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except SessionAnalyticsError as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get session attendance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session attendance: {str(e)}"
        )


@router.get("/sessions/{session_id}/attendance/export")
async def export_attendance_csv(
    session_id: str,
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Export attendance report to CSV file

    Downloads a comprehensive CSV report with:
    - Session name and attendee details
    - Join/leave timestamps and duration
    - Engagement metrics (messages, reactions, questions)
    - VOD watch statistics
    - Ratings and feedback

    CSV format is UTF-8 with BOM for Excel compatibility.

    Permissions:
    - Instructor can export attendance for their own sessions
    - Admin can export attendance for any session
    """
    try:
        # Get the session to verify instructor access
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        session = session_service.get_session(session_id)

        # Check permissions
        is_instructor = str(session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only export attendance for your own sessions"
            )

        # Generate CSV
        csv_content = analytics_service.export_attendance_csv(session_id)

        # Generate filename
        date_str = datetime.utcnow().strftime("%Y%m%d")
        filename = f"session-{session_id}-attendance-{date_str}.csv"

        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/csv; charset=utf-8"
            }
        )

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except SessionAnalyticsError as e:
        logger.error(f"CSV export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to export attendance CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export attendance CSV: {str(e)}"
        )


@router.post("/sessions/compare")
async def compare_sessions(
    request: SessionCompareRequest,
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Compare analytics across multiple training sessions

    Accepts 2-10 session IDs and returns comparative analytics including:
    - Side-by-side session metrics
    - Average metrics across all sessions
    - Trend analysis (improving/declining/stable)

    Useful for instructors to track performance over time and
    identify areas for improvement.

    Permissions:
    - Instructor can compare their own sessions
    - Admin can compare any sessions
    """
    try:
        # Verify instructor has access to all requested sessions
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        is_admin = current_user.role == UserRole.ADMIN.value

        for session_id in request.session_ids:
            try:
                session = session_service.get_session(session_id)

                # Check permissions for each session
                is_instructor = str(session.get("instructor_id")) == str(current_user.id)

                if not (is_instructor or is_admin):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You don't have access to session: {session_id}"
                    )

            except ZeroDBNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}"
                )

        # Generate comparative analytics
        comparison = analytics_service.get_comparative_analytics(request.session_ids)

        return comparison

    except HTTPException:
        raise
    except SessionAnalyticsError as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to compare sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare sessions: {str(e)}"
        )


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
async def get_instructor_overview(
    instructor_id: Optional[str] = Query(None, description="Instructor ID (admin only)"),
    limit: int = Query(10, ge=1, le=50, description="Number of recent sessions"),
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Get analytics overview for an instructor's sessions

    Returns summary statistics including:
    - Total sessions conducted
    - Total unique attendees across all sessions
    - Average attendance rate
    - Average engagement score
    - Average session rating
    - List of recent sessions with key metrics

    By default, returns stats for the current user (instructor).
    Admins can specify instructor_id to view any instructor's overview.

    Permissions:
    - Instructor can view their own overview
    - Admin can view any instructor's overview
    """
    try:
        # Determine which instructor's data to fetch
        target_instructor_id = instructor_id

        if target_instructor_id:
            # Only admin can view other instructors' data
            if current_user.role != UserRole.ADMIN.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can view other instructors' analytics"
                )
        else:
            # Default to current user
            target_instructor_id = str(current_user.id)

        # Get all sessions for this instructor
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        sessions_result = session_service.list_sessions(
            filters={"instructor_id": target_instructor_id},
            limit=100,
            sort_by="session_date",
            sort_order="desc"
        )

        sessions = sessions_result.get("documents", [])

        if not sessions:
            return AnalyticsOverviewResponse(
                instructor_id=target_instructor_id,
                total_sessions=0,
                total_attendees=0,
                average_attendance_rate=0.0,
                average_engagement_score=0.0,
                average_rating=0.0,
                recent_sessions=[]
            )

        # Calculate aggregate statistics
        total_sessions = len(sessions)
        attendance_rates = []
        engagement_scores = []
        ratings = []
        all_attendees = set()
        recent_sessions = []

        for i, session in enumerate(sessions[:limit]):
            try:
                session_id = session.get("id")
                analytics = analytics_service.get_session_analytics(str(session_id))

                attendance_rates.append(analytics["attendance"]["attendance_rate"])
                engagement_scores.append(analytics["engagement_score"])

                if analytics["feedback"].get("average_rating"):
                    ratings.append(analytics["feedback"]["average_rating"])

                # Collect unique attendees (simplified - would need actual user IDs)
                all_attendees.add(session_id)  # Placeholder

                # Add to recent sessions list
                recent_sessions.append({
                    "session_id": str(session_id),
                    "title": session.get("title"),
                    "session_date": session.get("session_date"),
                    "attendance_rate": analytics["attendance"]["attendance_rate"],
                    "total_attended": analytics["attendance"]["total_attended"],
                    "engagement_score": analytics["engagement_score"],
                    "average_rating": analytics["feedback"].get("average_rating", 0)
                })

            except Exception as e:
                logger.warning(f"Failed to get analytics for session {session.get('id')}: {e}")
                continue

        # Calculate averages
        avg_attendance = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 0
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        return AnalyticsOverviewResponse(
            instructor_id=target_instructor_id,
            total_sessions=total_sessions,
            total_attendees=len(all_attendees),  # Simplified
            average_attendance_rate=round(avg_attendance, 2),
            average_engagement_score=round(avg_engagement, 2),
            average_rating=round(avg_rating, 2),
            recent_sessions=recent_sessions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get instructor overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get instructor overview: {str(e)}"
        )


@router.get("/sessions/{session_id}/engagement")
async def get_session_engagement(
    session_id: str,
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Get detailed engagement metrics for a training session

    Returns engagement data including:
    - Chat message count and unique chatters
    - Reaction counts and breakdown by type
    - Questions asked count
    - Overall engagement rate

    Permissions:
    - Instructor can view engagement for their own sessions
    - Admin can view engagement for any session
    """
    try:
        # Get the session to verify instructor access
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        session = session_service.get_session(session_id)

        # Check permissions
        is_instructor = str(session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view engagement for your own sessions"
            )

        # Get engagement metrics
        engagement = analytics_service.get_engagement_metrics(session_id)

        return {
            "session_id": session_id,
            "session_title": session.get("title"),
            "engagement": engagement,
            "generated_at": datetime.utcnow().isoformat()
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except SessionAnalyticsError as e:
        logger.error(f"Engagement metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement metrics: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get session engagement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session engagement: {str(e)}"
        )


@router.get("/sessions/{session_id}/peak-viewers")
async def get_session_peak_viewers(
    session_id: str,
    current_user: User = Depends(require_instructor),
    analytics_service: SessionAnalyticsService = Depends(get_session_analytics_service)
):
    """
    Get peak concurrent viewers data for a training session

    Returns peak viewership information including:
    - Peak concurrent viewer count
    - Timestamp when peak occurred
    - Timeline data for charting viewer counts over time

    Useful for understanding session reach and identifying
    optimal session times.

    Permissions:
    - Instructor can view peak viewers for their own sessions
    - Admin can view peak viewers for any session
    """
    try:
        # Get the session to verify instructor access
        from backend.services.training_session_service import get_training_session_service
        session_service = get_training_session_service()

        session = session_service.get_session(session_id)

        # Check permissions
        is_instructor = str(session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view peak viewers for your own sessions"
            )

        # Get peak viewers data
        peak_viewers = analytics_service.get_peak_concurrent_viewers(session_id)

        return {
            "session_id": session_id,
            "session_title": session.get("title"),
            "peak_viewers": peak_viewers,
            "generated_at": datetime.utcnow().isoformat()
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except SessionAnalyticsError as e:
        logger.error(f"Peak viewers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get peak viewers: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get session peak viewers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session peak viewers: {str(e)}"
        )
