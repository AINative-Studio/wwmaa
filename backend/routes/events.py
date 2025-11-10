"""
Event Routes for WWMAA Backend

Provides RESTful API endpoints for event management (Admin only):
- GET /api/events - List all events with filters
- POST /api/events - Create new event
- GET /api/events/:id - Get single event
- PUT /api/events/:id - Update event
- DELETE /api/events/:id - Soft delete event
- POST /api/events/:id/duplicate - Duplicate event
- PATCH /api/events/:id/publish - Toggle publish/unpublish
- GET /api/events/deleted/list - List deleted events (archive)
- POST /api/events/:id/restore - Restore deleted event
- POST /api/events/upload-image - Upload event image to ZeroDB Object Storage
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import tempfile
import os

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Query,
    UploadFile,
    File,
    Form
)
from pydantic import BaseModel, Field, field_validator, HttpUrl

from backend.services.event_service import get_event_service, EventService
from backend.services.zerodb_service import (
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import User, UserRole, EventType, EventVisibility, EventStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/events", tags=["events"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class EventCreateRequest(BaseModel):
    """Request model for creating an event"""
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=10000, description="Event description (rich text)")
    event_type: EventType = Field(..., description="Event type")
    visibility: EventVisibility = Field(default=EventVisibility.PUBLIC, description="Visibility level")
    start_date: datetime = Field(..., description="Event start date and time")
    end_date: datetime = Field(..., description="Event end date and time")
    timezone: str = Field(default="America/Los_Angeles", description="Timezone")
    location: Optional[str] = Field(None, max_length=500, description="Location (address or 'Online')")
    is_online: bool = Field(default=False, description="Is this an online event?")
    capacity: Optional[int] = Field(None, ge=1, description="Maximum capacity (optional)")
    price: Optional[float] = Field(None, ge=0, description="Event price (0 or null for free)")
    instructor_info: Optional[str] = Field(None, max_length=1000, description="Instructor/speaker info")
    featured_image_url: Optional[str] = Field(None, description="Featured image URL")

    @field_validator('end_date')
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Validate that end_date is after start_date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v


class EventUpdateRequest(BaseModel):
    """Request model for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=10000, description="Event description (rich text)")
    event_type: Optional[EventType] = Field(None, description="Event type")
    visibility: Optional[EventVisibility] = Field(None, description="Visibility level")
    start_date: Optional[datetime] = Field(None, description="Event start date and time")
    end_date: Optional[datetime] = Field(None, description="Event end date and time")
    timezone: Optional[str] = Field(None, description="Timezone")
    location: Optional[str] = Field(None, max_length=500, description="Location (address or 'Online')")
    is_online: Optional[bool] = Field(None, description="Is this an online event?")
    capacity: Optional[int] = Field(None, ge=1, description="Maximum capacity (optional)")
    price: Optional[float] = Field(None, ge=0, description="Event price (0 or null for free)")
    instructor_info: Optional[str] = Field(None, max_length=1000, description="Instructor/speaker info")
    featured_image_url: Optional[str] = Field(None, description="Featured image URL")


class EventDuplicateRequest(BaseModel):
    """Request model for duplicating an event"""
    title_suffix: str = Field(default=" (Copy)", max_length=50, description="Suffix to add to title")


class EventListResponse(BaseModel):
    """Response model for event listing"""
    events: List[Dict[str, Any]] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Number of items skipped")


class EventResponse(BaseModel):
    """Response model for single event"""
    id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    event_type: str = Field(..., description="Event type")
    visibility: str = Field(..., description="Visibility level")
    status: str = Field(..., description="Event status")
    start_date: str = Field(..., description="Event start date")
    end_date: str = Field(..., description="Event end date")
    timezone: str = Field(..., description="Timezone")
    location: Optional[str] = Field(None, description="Location")
    is_online: bool = Field(..., description="Is online event")
    capacity: Optional[int] = Field(None, description="Maximum capacity")
    price: Optional[float] = Field(None, description="Event price")
    instructor_info: Optional[str] = Field(None, description="Instructor info")
    featured_image_url: Optional[str] = Field(None, description="Featured image URL")
    is_published: bool = Field(..., description="Is published")
    is_deleted: bool = Field(..., description="Is deleted")
    created_at: str = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Creator user ID")
    updated_at: str = Field(..., description="Last update timestamp")


class PublishToggleResponse(BaseModel):
    """Response model for publish toggle"""
    id: str = Field(..., description="Event ID")
    is_published: bool = Field(..., description="New publish status")
    status: str = Field(..., description="Event status")


class ImageUploadResponse(BaseModel):
    """Response model for image upload"""
    url: str = Field(..., description="Uploaded image URL")
    object_name: str = Field(..., description="Object storage name")


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role for event management

    Args:
        current_user: Currently authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# EVENT ROUTES
# ============================================================================

@router.get("/public", response_model=EventListResponse)
async def list_public_events(
    event_type: Optional[EventType] = Query(None, alias="type", description="Filter by event type"),
    location: Optional[str] = Query(None, description="Filter by location type (in_person, online)"),
    price: Optional[str] = Query(None, description="Filter by price (free, paid)"),
    date_from: Optional[str] = Query(None, description="Filter events from this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter events until this date (YYYY-MM-DD)"),
    sort: str = Query("date", description="Sort by (date, price)"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(12, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    event_service: EventService = Depends(get_event_service)
):
    """
    List public events (No auth required)

    This endpoint returns only published, public events for visitors and members.
    Supports filtering by type, location, price, and date range.
    """
    try:
        # Build filters - only show published, public events
        filters = {
            "status": EventStatus.PUBLISHED.value,
            "visibility": EventVisibility.PUBLIC.value,
            "is_published": True
        }

        if event_type:
            filters["event_type"] = event_type.value

        if location:
            filters["is_online"] = (location == "online")

        # Apply price filter
        if price == "free":
            filters["price"] = 0
        elif price == "paid":
            filters["price"] = {"$gt": 0}

        # Apply date range filters
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from)
                if "start_date" not in filters:
                    filters["start_date"] = {}
                filters["start_date"]["$gte"] = from_date.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use YYYY-MM-DD"
                )

        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to)
                if "start_date" not in filters:
                    filters["start_date"] = {}
                filters["start_date"]["$lte"] = to_date.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use YYYY-MM-DD"
                )

        # Map sort field
        sort_field = "start_date" if sort == "date" else "price"

        # Query events
        result = event_service.list_events(
            filters=filters,
            limit=limit,
            offset=offset,
            include_deleted=False,
            sort_by=sort_field,
            sort_order=order
        )

        # Check if there are more events
        has_more = result.get("total", 0) > (offset + limit)

        return {
            "events": result.get("documents", []),
            "total": result.get("total", 0),
            "limit": limit,
            "offset": offset,
            "has_more": has_more
        }

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Failed to list public events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}"
        )


@router.get("", response_model=EventListResponse)
async def list_events(
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    visibility: Optional[EventVisibility] = Query(None, description="Filter by visibility"),
    status_filter: Optional[EventStatus] = Query(None, alias="status", description="Filter by status"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(20, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    sort_by: str = Query("start_date", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    List all events with optional filtering and pagination (Admin only)

    Supports filtering by:
    - Event type (live_training, seminar, tournament, certification)
    - Visibility (public, members_only)
    - Status (draft, published, deleted, canceled)
    - Published status
    - Search text (in title/description)

    Returns paginated list of events with metadata.
    """
    try:
        # Build filters
        filters = {}

        if event_type:
            filters["event_type"] = event_type.value

        if visibility:
            filters["visibility"] = visibility.value

        if status_filter:
            filters["status"] = status_filter.value

        if is_published is not None:
            filters["is_published"] = is_published

        if search:
            # Note: ZeroDB may support text search differently
            # This is a simplified implementation
            filters["title"] = {"$regex": search, "$options": "i"}

        # Query events
        result = event_service.list_events(
            filters=filters,
            limit=limit,
            offset=offset,
            include_deleted=False,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return EventListResponse(
            events=result.get("documents", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset
        )

    except ZeroDBError as e:
        logger.error(f"Failed to list events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list events: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreateRequest,
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Create a new event (Admin only)

    Creates an event with all required fields. The event is created in DRAFT status
    and must be explicitly published using the publish endpoint.
    """
    try:
        # Convert to dict and create event
        event_dict = event_data.model_dump()

        # Convert datetime objects to ISO format strings
        event_dict["start_date"] = event_data.start_date.isoformat()
        event_dict["end_date"] = event_data.end_date.isoformat()

        result = event_service.create_event(
            event_data=event_dict,
            created_by=current_user.id
        )

        return result

    except ZeroDBValidationError as e:
        logger.error(f"Validation error creating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.get("/public/{event_id}")
async def get_public_event(
    event_id: str,
    event_service: EventService = Depends(get_event_service)
):
    """
    Get a single public event by ID (No auth required)

    Returns event details for published, public events only.
    """
    try:
        event = event_service.get_event(event_id)

        # Verify it's a published, public event
        if event.get("status") != EventStatus.PUBLISHED.value or event.get("visibility") != EventVisibility.PUBLIC.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        return event

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Failed to fetch event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event: {str(e)}"
        )


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Get a single event by ID (Admin only)

    Returns full event details including all fields.
    """
    try:
        event = event_service.get_event(event_id)
        return event

    except ZeroDBNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to fetch event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event: {str(e)}"
        )


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    event_data: EventUpdateRequest,
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Update an existing event (Admin only)

    All fields are optional. Only provided fields will be updated.
    """
    try:
        # Convert to dict, excluding None values
        event_dict = event_data.model_dump(exclude_none=True)

        # Convert datetime objects to ISO format strings
        if event_data.start_date:
            event_dict["start_date"] = event_data.start_date.isoformat()
        if event_data.end_date:
            event_dict["end_date"] = event_data.end_date.isoformat()

        result = event_service.update_event(
            event_id=event_id,
            event_data=event_dict,
            updated_by=current_user.id
        )

        return result

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )
    except ZeroDBValidationError as e:
        logger.error(f"Validation error updating event: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"Failed to update event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}"
        )


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Delete an event (Admin only)

    By default, performs a soft delete (status='deleted', is_deleted=true).
    Set hard_delete=true for permanent deletion.

    Soft-deleted events can be viewed in the archive and restored.
    """
    try:
        result = event_service.delete_event(
            event_id=event_id,
            deleted_by=current_user.id,
            hard_delete=hard_delete
        )

        return {
            "message": "Event deleted successfully",
            "event_id": event_id,
            "hard_delete": hard_delete
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )


@router.post("/{event_id}/duplicate", status_code=status.HTTP_201_CREATED)
async def duplicate_event(
    event_id: str,
    duplicate_data: EventDuplicateRequest = EventDuplicateRequest(),
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Duplicate an existing event (Admin only)

    Creates a copy of the event with a new ID and " (Copy)" suffix on the title.
    The duplicated event is created in DRAFT status.
    """
    try:
        result = event_service.duplicate_event(
            event_id=event_id,
            created_by=current_user.id,
            title_suffix=duplicate_data.title_suffix
        )

        return result

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to duplicate event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate event: {str(e)}"
        )


@router.patch("/{event_id}/publish")
async def toggle_publish(
    event_id: str,
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Toggle publish/unpublish status (Admin only)

    Toggles the is_published flag and updates the status accordingly:
    - Published: status='published', is_published=true
    - Unpublished: status='draft', is_published=false
    """
    try:
        result = event_service.toggle_publish(
            event_id=event_id,
            updated_by=current_user.id
        )

        return PublishToggleResponse(
            id=str(result.get("id")),
            is_published=result.get("is_published", False),
            status=result.get("status", "draft")
        )

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )
    except ZeroDBError as e:
        logger.error(f"Failed to toggle publish status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle publish status: {str(e)}"
        )


@router.get("/deleted/list", response_model=EventListResponse)
async def list_deleted_events(
    limit: int = Query(20, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    sort_by: str = Query("deleted_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    List deleted events archive (Admin only)

    Returns all soft-deleted events. These events can be restored.
    """
    try:
        result = event_service.get_deleted_events(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return EventListResponse(
            events=result.get("documents", []),
            total=result.get("total", 0),
            limit=limit,
            offset=offset
        )

    except ZeroDBError as e:
        logger.error(f"Failed to list deleted events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deleted events: {str(e)}"
        )


@router.post("/{event_id}/restore")
async def restore_event(
    event_id: str,
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Restore a soft-deleted event (Admin only)

    Restores an event from the deleted archive back to DRAFT status.
    """
    try:
        result = event_service.restore_event(
            event_id=event_id,
            restored_by=current_user.id
        )

        return {
            "message": "Event restored successfully",
            "event": result
        }

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found: {event_id}"
        )
    except ZeroDBValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"Failed to restore event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore event: {str(e)}"
        )


@router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_event_image(
    file: UploadFile = File(..., description="Image file to upload"),
    event_id: Optional[str] = Form(None, description="Event ID for organizing images"),
    current_user: User = Depends(require_admin),
    event_service: EventService = Depends(get_event_service)
):
    """
    Upload an event image to ZeroDB Object Storage (Admin only)

    Accepts image files and stores them in ZeroDB Object Storage.
    Returns the URL to use in the featured_image_url field.

    Supported formats: JPEG, PNG, GIF, WebP
    """
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Upload to ZeroDB Object Storage
            image_url = event_service.upload_event_image(
                file_path=temp_file_path,
                event_id=event_id,
                object_name=None  # Auto-generate
            )

            # Generate object name for response
            object_name = f"events/{event_id or 'temp'}/{file.filename}"

            return ImageUploadResponse(
                url=image_url,
                object_name=object_name
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )
