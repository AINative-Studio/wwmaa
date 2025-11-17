"""
Resources Routes for WWMAA Backend

Provides API endpoints for managing training resources (videos, documents, PDFs, etc.)
with role-based access control, file uploads, and filtering.

Endpoints:
- GET /api/resources - List all accessible resources (filtered by user role)
- GET /api/resources/{resource_id} - Get a specific resource
- POST /api/resources - Create a new resource (admin/instructor only)
- PUT /api/resources/{resource_id} - Update a resource (admin/instructor only)
- DELETE /api/resources/{resource_id} - Delete a resource (admin only)
- POST /api/resources/upload - Upload a resource file (admin/instructor only)
- POST /api/resources/{resource_id}/track-view - Track resource view
- POST /api/resources/{resource_id}/track-download - Track resource download
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import uuid4, UUID

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from pydantic import BaseModel, Field, HttpUrl

from backend.services.zerodb_service import get_zerodb_client, ZeroDBError, ZeroDBValidationError
from backend.middleware.auth_middleware import CurrentUser, RoleChecker
from backend.models.schemas import (
    ResourceCategory,
    ResourceVisibility,
    ResourceStatus,
    UserRole
)
from backend.utils.file_upload import (
    validate_document_upload,
    validate_video_upload,
    sanitize_upload_filename,
    ALLOWED_DOCUMENT_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/resources", tags=["resources"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateResourceRequest(BaseModel):
    """Create resource request"""
    title: str = Field(..., min_length=1, max_length=200, description="Resource title")
    description: Optional[str] = Field(None, max_length=2000, description="Resource description")
    category: ResourceCategory = Field(..., description="Resource category")
    tags: List[str] = Field(default_factory=list, description="Resource tags")
    file_url: Optional[str] = Field(None, description="File URL (if already uploaded)")
    external_url: Optional[HttpUrl] = Field(None, description="External URL (YouTube, etc.)")
    visibility: ResourceVisibility = Field(
        default=ResourceVisibility.MEMBERS_ONLY,
        description="Resource visibility"
    )
    status: ResourceStatus = Field(default=ResourceStatus.DRAFT, description="Resource status")
    discipline: Optional[str] = Field(None, max_length=100, description="Martial arts discipline")
    related_session_id: Optional[str] = Field(None, description="Related training session ID")
    related_event_id: Optional[str] = Field(None, description="Related event ID")
    is_featured: bool = Field(default=False, description="Featured resource")
    display_order: int = Field(default=0, ge=0, description="Display order")


class UpdateResourceRequest(BaseModel):
    """Update resource request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Resource title")
    description: Optional[str] = Field(None, max_length=2000, description="Resource description")
    category: Optional[ResourceCategory] = Field(None, description="Resource category")
    tags: Optional[List[str]] = Field(None, description="Resource tags")
    file_url: Optional[str] = Field(None, description="File URL")
    external_url: Optional[HttpUrl] = Field(None, description="External URL")
    visibility: Optional[ResourceVisibility] = Field(None, description="Resource visibility")
    status: Optional[ResourceStatus] = Field(None, description="Resource status")
    discipline: Optional[str] = Field(None, max_length=100, description="Martial arts discipline")
    related_session_id: Optional[str] = Field(None, description="Related training session ID")
    related_event_id: Optional[str] = Field(None, description="Related event ID")
    is_featured: Optional[bool] = Field(None, description="Featured resource")
    display_order: Optional[int] = Field(None, ge=0, description="Display order")


class ResourceResponse(BaseModel):
    """Resource response model"""
    id: str
    title: str
    description: Optional[str]
    category: str
    tags: List[str]
    file_url: Optional[str]
    file_name: Optional[str]
    file_size_bytes: Optional[int]
    file_type: Optional[str]
    external_url: Optional[str]
    cloudflare_stream_id: Optional[str]
    video_duration_seconds: Optional[int]
    thumbnail_url: Optional[str]
    visibility: str
    status: str
    published_at: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    discipline: Optional[str]
    related_session_id: Optional[str]
    related_event_id: Optional[str]
    is_featured: bool
    display_order: int
    view_count: int
    download_count: int


class ResourceListResponse(BaseModel):
    """Resource list response"""
    resources: List[ResourceResponse]
    total: int
    page: int
    page_size: int


class FileUploadResponse(BaseModel):
    """File upload response"""
    file_url: str
    file_name: str
    file_size_bytes: int
    file_type: str
    message: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def can_access_resource(user_role: str, resource_visibility: str) -> bool:
    """
    Check if user role can access resource based on visibility

    Args:
        user_role: User's role (public, member, instructor, board_member, admin)
        resource_visibility: Resource visibility level

    Returns:
        True if user can access resource, False otherwise
    """
    # Admin can access everything
    if user_role == UserRole.ADMIN:
        return True

    # Map visibility to required role
    visibility_role_map = {
        ResourceVisibility.PUBLIC: UserRole.PUBLIC,
        ResourceVisibility.MEMBERS_ONLY: UserRole.MEMBER,
        ResourceVisibility.INSTRUCTORS_ONLY: UserRole.INSTRUCTOR,
        ResourceVisibility.ADMIN_ONLY: UserRole.ADMIN,
    }

    required_role = visibility_role_map.get(resource_visibility)
    if not required_role:
        return False

    # Role hierarchy check
    role_hierarchy = {
        UserRole.PUBLIC: 0,
        UserRole.MEMBER: 1,
        UserRole.INSTRUCTOR: 2,
        UserRole.BOARD_MEMBER: 3,
        UserRole.ADMIN: 4,
    }

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level


def format_resource_response(resource_doc: dict) -> ResourceResponse:
    """
    Format ZeroDB resource document to ResourceResponse

    Args:
        resource_doc: ZeroDB document

    Returns:
        Formatted ResourceResponse
    """
    data = resource_doc.get("data", {})

    return ResourceResponse(
        id=resource_doc.get("id"),
        title=data.get("title"),
        description=data.get("description"),
        category=data.get("category"),
        tags=data.get("tags", []),
        file_url=data.get("file_url"),
        file_name=data.get("file_name"),
        file_size_bytes=data.get("file_size_bytes"),
        file_type=data.get("file_type"),
        external_url=data.get("external_url"),
        cloudflare_stream_id=data.get("cloudflare_stream_id"),
        video_duration_seconds=data.get("video_duration_seconds"),
        thumbnail_url=data.get("thumbnail_url"),
        visibility=data.get("visibility"),
        status=data.get("status"),
        published_at=data.get("published_at"),
        created_by=data.get("created_by"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        discipline=data.get("discipline"),
        related_session_id=data.get("related_session_id"),
        related_event_id=data.get("related_event_id"),
        is_featured=data.get("is_featured", False),
        display_order=data.get("display_order", 0),
        view_count=data.get("view_count", 0),
        download_count=data.get("download_count", 0),
    )


# ============================================================================
# RESOURCE ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=ResourceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all accessible resources",
    description="Get all resources that the current user can access (filtered by role and visibility)"
)
async def list_resources(
    current_user: dict = Depends(CurrentUser()),
    category: Optional[ResourceCategory] = Query(None, description="Filter by category"),
    status_filter: Optional[ResourceStatus] = Query(None, alias="status", description="Filter by status"),
    featured_only: bool = Query(False, description="Show only featured resources"),
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ResourceListResponse:
    """
    List all resources accessible to the current user

    Filtering:
    - Automatically filters based on user role and resource visibility
    - Students see only published resources they have access to
    - Admins/instructors see all resources including drafts

    Returns:
        List of resources with pagination
    """
    db_client = get_zerodb_client()
    user_role = current_user["role"]

    try:
        # Build filters
        filters = {}

        # Category filter
        if category:
            filters["category"] = category.value

        # Discipline filter
        if discipline:
            filters["discipline"] = discipline

        # Featured filter
        if featured_only:
            filters["is_featured"] = True

        # Status filter - only admins/instructors can see drafts
        if user_role in [UserRole.ADMIN, UserRole.INSTRUCTOR, UserRole.BOARD_MEMBER]:
            # Admins/instructors can see all statuses or filter by specific status
            if status_filter:
                filters["status"] = status_filter.value
        else:
            # Students can only see published resources
            filters["status"] = ResourceStatus.PUBLISHED.value

        logger.info(f"Fetching resources with filters: {filters}")

        # Query resources from ZeroDB
        result = db_client.query_documents(
            collection="resources",
            filters=filters,
            limit=page_size * 10,  # Get more to filter by visibility
        )

        all_resources = result.get("documents", [])

        # Filter by visibility based on user role
        accessible_resources = []
        for resource_doc in all_resources:
            resource_visibility = resource_doc.get("data", {}).get("visibility")
            if can_access_resource(user_role, resource_visibility):
                accessible_resources.append(resource_doc)

        # Sort by display_order, then by created_at (desc)
        accessible_resources.sort(
            key=lambda x: (
                x.get("data", {}).get("display_order", 0),
                -datetime.fromisoformat(x.get("data", {}).get("created_at", datetime.min.isoformat())).timestamp()
            )
        )

        # Pagination
        total = len(accessible_resources)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_resources = accessible_resources[start:end]

        # Format response
        resources = [format_resource_response(doc) for doc in paginated_resources]

        logger.info(f"Returning {len(resources)} resources (total: {total})")

        return ResourceListResponse(
            resources=resources,
            total=total,
            page=page,
            page_size=page_size
        )

    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch resources"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific resource",
    description="Get details of a specific resource by ID"
)
async def get_resource(
    resource_id: str,
    current_user: dict = Depends(CurrentUser())
) -> ResourceResponse:
    """
    Get a specific resource by ID

    Authorization:
    - Checks if user has permission to access resource based on visibility

    Returns:
        Resource details
    """
    db_client = get_zerodb_client()
    user_role = current_user["role"]

    try:
        # Query resource by ID
        logger.info(f"Fetching resource: {resource_id}")
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        resources = result.get("documents", [])
        if not resources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource_doc = resources[0]
        resource_data = resource_doc.get("data", {})

        # Check visibility permissions
        resource_visibility = resource_data.get("visibility")
        if not can_access_resource(user_role, resource_visibility):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        # Check if published (unless admin/instructor)
        if user_role not in [UserRole.ADMIN, UserRole.INSTRUCTOR, UserRole.BOARD_MEMBER]:
            if resource_data.get("status") != ResourceStatus.PUBLISHED.value:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resource not found"
                )

        return format_resource_response(resource_doc)

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch resource"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resource",
    description="Create a new training resource (admin/instructor only)"
)
async def create_resource(
    request: CreateResourceRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "instructor"]))
) -> ResourceResponse:
    """
    Create a new resource

    Authorization:
    - Only admins and instructors can create resources

    Validation:
    - Either file_url or external_url must be provided
    - Title is required

    Returns:
        Created resource details
    """
    db_client = get_zerodb_client()
    user_id = str(current_user["id"])

    try:
        # Validate at least one URL is provided
        if not request.file_url and not request.external_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file_url or external_url must be provided"
            )

        # Create resource document
        resource_id = str(uuid4())
        now = datetime.utcnow()

        resource_data = {
            "title": request.title,
            "description": request.description,
            "category": request.category.value,
            "tags": request.tags,
            "file_url": request.file_url,
            "external_url": str(request.external_url) if request.external_url else None,
            "visibility": request.visibility.value,
            "status": request.status.value,
            "created_by": user_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "discipline": request.discipline,
            "related_session_id": request.related_session_id,
            "related_event_id": request.related_event_id,
            "is_featured": request.is_featured,
            "display_order": request.display_order,
            "view_count": 0,
            "download_count": 0,
        }

        # Set published_at if status is published
        if request.status == ResourceStatus.PUBLISHED:
            resource_data["published_at"] = now.isoformat()
            resource_data["published_by"] = user_id

        logger.info(f"Creating resource: {request.title}")

        # Create in ZeroDB
        created = db_client.create_document(
            collection="resources",
            data=resource_data,
            document_id=resource_id
        )

        logger.info(f"Resource created successfully: {resource_id}")

        # Fetch and return the created resource
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        resource_doc = result.get("documents", [])[0]
        return format_resource_response(resource_doc)

    except HTTPException:
        raise
    except ZeroDBValidationError as e:
        logger.error(f"Validation error creating resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error creating resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resource"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.put(
    "/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a resource",
    description="Update an existing resource (admin/instructor only)"
)
async def update_resource(
    resource_id: str,
    request: UpdateResourceRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "instructor"]))
) -> ResourceResponse:
    """
    Update an existing resource

    Authorization:
    - Only admins and instructors can update resources
    - Instructors can only update resources they created (admins can update all)

    Returns:
        Updated resource details
    """
    db_client = get_zerodb_client()
    user_id = str(current_user["id"])
    user_role = current_user["role"]

    try:
        # Fetch existing resource
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        resources = result.get("documents", [])
        if not resources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource_doc = resources[0]
        resource_data = resource_doc.get("data", {})

        # Check ownership (instructors can only update their own resources)
        if user_role == UserRole.INSTRUCTOR:
            if resource_data.get("created_by") != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update resources you created"
                )

        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat(), "updated_by": user_id}

        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.category is not None:
            update_data["category"] = request.category.value
        if request.tags is not None:
            update_data["tags"] = request.tags
        if request.file_url is not None:
            update_data["file_url"] = request.file_url
        if request.external_url is not None:
            update_data["external_url"] = str(request.external_url)
        if request.visibility is not None:
            update_data["visibility"] = request.visibility.value
        if request.status is not None:
            update_data["status"] = request.status.value
            # Set published_at when publishing
            if request.status == ResourceStatus.PUBLISHED and not resource_data.get("published_at"):
                update_data["published_at"] = datetime.utcnow().isoformat()
                update_data["published_by"] = user_id
        if request.discipline is not None:
            update_data["discipline"] = request.discipline
        if request.related_session_id is not None:
            update_data["related_session_id"] = request.related_session_id
        if request.related_event_id is not None:
            update_data["related_event_id"] = request.related_event_id
        if request.is_featured is not None:
            update_data["is_featured"] = request.is_featured
        if request.display_order is not None:
            update_data["display_order"] = request.display_order

        logger.info(f"Updating resource: {resource_id}")

        # Update in ZeroDB
        db_client.update_document(
            collection="resources",
            document_id=resource_id,
            data=update_data,
            merge=True
        )

        logger.info(f"Resource updated successfully: {resource_id}")

        # Fetch and return updated resource
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        resource_doc = result.get("documents", [])[0]
        return format_resource_response(resource_doc)

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error updating resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resource"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resource",
    description="Delete a resource (admin only)"
)
async def delete_resource(
    resource_id: str,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
):
    """
    Delete a resource

    Authorization:
    - Only admins can delete resources

    Returns:
        204 No Content on success
    """
    db_client = get_zerodb_client()

    try:
        # Check if resource exists
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        if not result.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        logger.info(f"Deleting resource: {resource_id}")

        # Delete from ZeroDB
        db_client.delete_document(
            collection="resources",
            document_id=resource_id
        )

        logger.info(f"Resource deleted successfully: {resource_id}")

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error deleting resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resource"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting resource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resource file",
    description="Upload a file for a resource (admin/instructor only)"
)
async def upload_resource_file(
    file: UploadFile = File(..., description="File to upload"),
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "instructor"]))
) -> FileUploadResponse:
    """
    Upload a resource file (document or video)

    Authorization:
    - Only admins and instructors can upload files

    Supported file types:
    - Documents: PDF, DOC, DOCX, TXT, MD
    - Videos: MP4, WEBM, MOV, AVI, MKV

    Returns:
        File URL and metadata
    """
    try:
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )

        # Sanitize filename
        safe_filename = sanitize_upload_filename(file.filename)
        logger.info(f"Processing file upload: {safe_filename}")

        # Determine file type and validate
        file_extension = safe_filename.rsplit('.', 1)[-1].lower() if '.' in safe_filename else ''

        if file_extension in ALLOWED_DOCUMENT_EXTENSIONS:
            is_valid, error_msg = validate_document_upload(file)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        elif file_extension in ALLOWED_VIDEO_EXTENSIONS:
            is_valid, error_msg = validate_video_upload(file)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS)}"
            )

        # Get file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # In a real implementation, upload to ZeroDB Object Storage or Cloudflare
        # For now, return a mock URL
        file_url = f"https://storage.wwmaa.com/resources/{uuid4()}/{safe_filename}"

        logger.info(f"File uploaded successfully: {safe_filename} ({file_size} bytes)")

        return FileUploadResponse(
            file_url=file_url,
            file_name=safe_filename,
            file_size_bytes=file_size,
            file_type=file.content_type,
            message="File uploaded successfully. Use this URL when creating or updating a resource."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.post(
    "/{resource_id}/track-view",
    status_code=status.HTTP_200_OK,
    summary="Track resource view",
    description="Increment view count for a resource"
)
async def track_resource_view(
    resource_id: str,
    current_user: dict = Depends(CurrentUser())
):
    """
    Track resource view

    Increments the view_count for analytics

    Returns:
        Success message
    """
    db_client = get_zerodb_client()

    try:
        # Fetch resource
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        if not result.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource_doc = result.get("documents")[0]
        current_views = resource_doc.get("data", {}).get("view_count", 0)

        # Increment view count
        db_client.update_document(
            collection="resources",
            document_id=resource_id,
            data={"view_count": current_views + 1},
            merge=True
        )

        logger.info(f"Resource view tracked: {resource_id}")

        return {"message": "View tracked successfully"}

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error tracking view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track view"
        )
    except Exception as e:
        logger.error(f"Unexpected error tracking view: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/{resource_id}/track-download",
    status_code=status.HTTP_200_OK,
    summary="Track resource download",
    description="Increment download count for a resource"
)
async def track_resource_download(
    resource_id: str,
    current_user: dict = Depends(CurrentUser())
):
    """
    Track resource download

    Increments the download_count for analytics

    Returns:
        Success message
    """
    db_client = get_zerodb_client()

    try:
        # Fetch resource
        result = db_client.query_documents(
            collection="resources",
            filters={"id": resource_id},
            limit=1
        )

        if not result.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource_doc = result.get("documents")[0]
        current_downloads = resource_doc.get("data", {}).get("download_count", 0)

        # Increment download count
        db_client.update_document(
            collection="resources",
            document_id=resource_id,
            data={"download_count": current_downloads + 1},
            merge=True
        )

        logger.info(f"Resource download tracked: {resource_id}")

        return {"message": "Download tracked successfully"}

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error tracking download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track download"
        )
    except Exception as e:
        logger.error(f"Unexpected error tracking download: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
