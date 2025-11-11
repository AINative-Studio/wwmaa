"""
Training Session Routes for WWMAA Backend

Provides RESTful API endpoints for live training session management:
- POST /api/training/sessions - Create session (admin/instructor only)
- GET /api/training/sessions - List all sessions (with filters)
- GET /api/training/sessions/:id - Get session details
- PUT /api/training/sessions/:id - Update session (admin/instructor)
- DELETE /api/training/sessions/:id - Cancel session (admin/instructor)
- POST /api/training/sessions/:id/start - Start session (instructor only)
- POST /api/training/sessions/:id/end - End session (instructor only)
- GET /api/training/sessions/:id/can-join - Check if user can join
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Query
)
from pydantic import BaseModel, Field, field_validator

from backend.services.training_session_service import (
    get_training_session_service,
    TrainingSessionService
)
from backend.services.zerodb_service import (
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import User, UserRole, SessionStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/training/sessions", tags=["training-sessions"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Request model for creating a training session"""
    event_id: Optional[str] = Field(None, description="Associated event ID (optional)")
    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    description: Optional[str] = Field(None, max_length=2000, description="Session description")
    start_time: datetime = Field(..., description="Session start date and time")
    duration_minutes: int = Field(..., ge=1, le=480, description="Duration in minutes")
    capacity: Optional[int] = Field(None, ge=1, description="Maximum participants (optional)")
    recording_enabled: bool = Field(default=False, description="Enable recording")
    chat_enabled: bool = Field(default=True, description="Enable chat")
    is_public: bool = Field(default=False, description="Public access")
    members_only: bool = Field(default=True, description="Members-only access")
    tags: List[str] = Field(default_factory=list, description="Session tags")

    @field_validator('start_time')
    @classmethod
    def validate_start_time_future(cls, v):
        """Validate that start_time is in the future"""
        if v <= datetime.utcnow():
            raise ValueError("start_time must be in the future")
        return v


class SessionUpdateRequest(BaseModel):
    """Request model for updating a training session"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Session title")
    description: Optional[str] = Field(None, max_length=2000, description="Session description")
    start_time: Optional[datetime] = Field(None, description="Session start date and time")
    duration_minutes: Optional[int] = Field(None, ge=1, le=480, description="Duration in minutes")
    capacity: Optional[int] = Field(None, ge=1, description="Maximum participants")
    recording_enabled: Optional[bool] = Field(None, description="Enable recording")
    chat_enabled: Optional[bool] = Field(None, description="Enable chat")
    is_public: Optional[bool] = Field(None, description="Public access")
    members_only: Optional[bool] = Field(None, description="Members-only access")
    tags: Optional[List[str]] = Field(None, description="Session tags")


class SessionListResponse(BaseModel):
    """Response model for session listing"""
    sessions: List[Dict[str, Any]] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Number of items skipped")


class CanJoinResponse(BaseModel):
    """Response model for can-join check"""
    can_join: bool = Field(..., description="Whether user can join")
    reason: str = Field(..., description="Reason for can/cannot join")
    join_time_remaining: Optional[int] = Field(None, description="Seconds until join opens")


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

def require_instructor(current_user: User = Depends(get_current_user)) -> User:
    """
    Require instructor role or higher for session management

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
    Require admin role for administrative operations

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
# SESSION ROUTES
# ============================================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreateRequest,
    current_user: User = Depends(require_instructor),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    Create a new training session (Instructor/Admin only)

    Creates a session and automatically creates a Cloudflare Calls room.
    The room ID is stored in the session for participant access.

    Permissions:
    - Instructor, Board Member, or Admin can create sessions
    """
    try:
        # Convert to dict
        session_dict = session_data.model_dump()

        # Convert datetime to ISO format
        session_dict["start_time"] = session_data.start_time.isoformat()

        # Create session
        result = session_service.create_session(
            session_data=session_dict,
            instructor_id=current_user.id
        )

        return result

    except ZeroDBValidationError as e:
        logger.error(f"Validation error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    status_filter: Optional[SessionStatus] = Query(None, alias="status", description="Filter by status"),
    instructor_id: Optional[str] = Query(None, description="Filter by instructor ID"),
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    upcoming: bool = Query(False, description="Show only upcoming sessions"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    sort_by: str = Query("start_time", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: Optional[User] = Depends(get_current_user),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    List training sessions with optional filtering and pagination

    Supports filtering by:
    - Status (scheduled, live, ended, canceled)
    - Instructor ID
    - Event ID
    - Upcoming sessions only

    Returns paginated list of sessions with metadata.
    """
    try:
        # Build filters
        filters = {}

        if status_filter:
            filters["status"] = status_filter.value

        if instructor_id:
            filters["instructor_id"] = instructor_id

        if event_id:
            filters["event_id"] = event_id

        if upcoming:
            filters["status"] = SessionStatus.SCHEDULED.value
            filters["start_time"] = {"$gte": datetime.utcnow().isoformat()}

        # Query sessions
        result = session_service.list_sessions(
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return SessionListResponse(
            sessions=result.get("documents", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset
        )

    except ZeroDBError as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    Get a single training session by ID

    Returns full session details including room information.
    """
    try:
        session = session_service.get_session(session_id)
        return session

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to fetch session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch session: {str(e)}"
        )


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    session_data: SessionUpdateRequest,
    current_user: User = Depends(require_instructor),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    Update an existing training session (Instructor/Admin only)

    All fields are optional. Only provided fields will be updated.

    Permissions:
    - Only the session instructor or admin can update the session
    - Cannot update ended or canceled sessions
    """
    try:
        # Get existing session to check permissions
        existing_session = session_service.get_session(session_id)

        # Check if user is instructor or admin
        is_instructor = str(existing_session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the session instructor or admin can update this session"
            )

        # Convert to dict, excluding None values
        session_dict = session_data.model_dump(exclude_none=True)

        # Convert datetime to ISO format if present
        if session_data.start_time:
            session_dict["start_time"] = session_data.start_time.isoformat()

        # Update session
        result = session_service.update_session(
            session_id=session_id,
            updates=session_dict,
            updated_by=current_user.id
        )

        return result

    except HTTPException:
        raise
    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except ZeroDBValidationError as e:
        logger.error(f"Validation error updating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"Failed to update session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(require_instructor),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    Cancel a training session (Instructor/Admin only)

    Cancels the session and deletes the associated Cloudflare room.

    Permissions:
    - Only the session instructor or admin can cancel the session
    """
    try:
        # Get existing session to check permissions
        existing_session = session_service.get_session(session_id)

        # Check if user is instructor or admin
        is_instructor = str(existing_session.get("instructor_id")) == str(current_user.id)
        is_admin = current_user.role == UserRole.ADMIN.value

        if not (is_instructor or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the session instructor or admin can cancel this session"
            )

        # Delete session
        result = session_service.delete_session(
            session_id=session_id,
            deleted_by=current_user.id
        )

        return {
            "message": "Session canceled successfully",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to cancel session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel session: {str(e)}"
        )


@router.post("/{session_id}/start")
async def start_session(
    session_id: str,
    current_user: User = Depends(require_instructor),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    Start a training session (Instructor only)

    Marks the session as live and allows participants to join.

    Permissions:
    - Only the session instructor can start the session
    """
    try:
        result = session_service.start_session(
            session_id=session_id,
            instructor_id=current_user.id
        )

        return {
            "message": "Session started successfully",
            "session": result
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except ZeroDBValidationError as e:
        logger.error(f"Validation error starting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(require_instructor),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    End a training session (Instructor only)

    Marks the session as ended and stops new participants from joining.

    Permissions:
    - Only the session instructor can end the session
    """
    try:
        result = session_service.end_session(
            session_id=session_id,
            instructor_id=current_user.id
        )

        return {
            "message": "Session ended successfully",
            "session": result
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except ZeroDBValidationError as e:
        logger.error(f"Validation error ending session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}"
        )


@router.get("/{session_id}/can-join", response_model=CanJoinResponse)
async def can_user_join(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session_service: TrainingSessionService = Depends(get_training_session_service)
):
    """
    Check if current user can join a training session

    Checks:
    - Session status (not canceled or ended)
    - Time window (10 minutes before start or session is live)
    - Capacity limits
    - Access permissions (members-only, etc.)

    Returns whether user can join and the reason.
    """
    try:
        result = session_service.can_user_join(
            session_id=session_id,
            user_id=current_user.id,
            user_role=current_user.role
        )

        return CanJoinResponse(**result)

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to check join permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check join permission: {str(e)}"
        )
