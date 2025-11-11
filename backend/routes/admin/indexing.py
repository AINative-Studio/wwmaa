"""
Admin Indexing Routes

API endpoints for managing content indexing operations.
Restricted to admin users only.

Endpoints:
    POST /api/admin/indexing/trigger - Trigger manual reindex
    GET /api/admin/indexing/status - Get indexing status
    POST /api/admin/indexing/index-content - Index specific content
    GET /api/admin/indexing/stats - Get indexing statistics
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from backend.services.indexing_service import (
    get_indexing_service,
    ContentType,
    IndexingStatus
)
from backend.services.auth_service import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/admin/indexing", tags=["admin", "indexing"])


# Request/Response Models


class TriggerReindexRequest(BaseModel):
    """Request model for triggering a reindex"""
    content_types: Optional[List[str]] = Field(
        default=None,
        description="List of content types to reindex (all if not specified)"
    )
    incremental: bool = Field(
        default=True,
        description="Use incremental indexing (only new/updated content)"
    )


class IndexContentRequest(BaseModel):
    """Request model for indexing specific content"""
    content_type: str = Field(
        ...,
        description="Type of content to index (events, articles, training_videos, member_profiles)"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Specific document ID to index (optional)"
    )
    force: bool = Field(
        default=False,
        description="Force reindex even if already indexed"
    )


class IndexingStatusResponse(BaseModel):
    """Response model for indexing status"""
    status: str = Field(..., description="Current indexing status")
    current_operation: Optional[str] = Field(None, description="Current operation description")
    stats: dict = Field(..., description="Indexing statistics")


class IndexingStatsResponse(BaseModel):
    """Response model for detailed indexing statistics"""
    total_documents_indexed: int = Field(..., description="Total documents indexed")
    total_chunks: int = Field(..., description="Total chunks created")
    by_content_type: dict = Field(..., description="Statistics by content type")
    current_status: str = Field(..., description="Current indexing status")


class TriggerReindexResponse(BaseModel):
    """Response model for reindex trigger"""
    message: str = Field(..., description="Response message")
    job_id: Optional[str] = Field(None, description="Background job ID")
    content_types: List[str] = Field(..., description="Content types being indexed")


class IndexContentResponse(BaseModel):
    """Response model for index content operation"""
    success: bool = Field(..., description="Whether indexing succeeded")
    message: str = Field(..., description="Response message")
    details: Optional[dict] = Field(None, description="Indexing details")


# Dependency for admin-only access


async def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency to require admin role for accessing endpoints.

    Args:
        current_user: Current authenticated user

    Raises:
        HTTPException: If user is not an admin
    """
    user_data = current_user.get("data", {})
    role = user_data.get("role", "member")

    if role != "admin":
        logger.warning(
            f"Unauthorized admin access attempt by user {user_data.get('email')}"
        )
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# Route Handlers


@router.post("/trigger", response_model=TriggerReindexResponse)
async def trigger_reindex(
    request: TriggerReindexRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)
):
    """
    Trigger a manual reindex operation.

    Initiates a full or incremental reindex for specified content types.
    The operation runs in the background to avoid blocking the API.

    Args:
        request: Reindex parameters
        background_tasks: FastAPI background tasks
        current_user: Current authenticated admin user

    Returns:
        Response with job details

    Raises:
        HTTPException: If reindex fails to start
    """
    try:
        indexing_service = get_indexing_service()

        # Check if already running
        status = indexing_service.get_status()
        if status["status"] == IndexingStatus.RUNNING.value:
            raise HTTPException(
                status_code=409,
                detail="Indexing operation already in progress"
            )

        # Parse content types
        content_types = None
        if request.content_types:
            try:
                content_types = [ContentType(ct) for ct in request.content_types]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content type: {e}"
                )

        # Run reindex in background
        if request.incremental:
            # Incremental indexing
            if content_types is None:
                content_types = list(ContentType)

            async def run_incremental_indexing():
                """Background task for incremental indexing"""
                for ct in content_types:
                    try:
                        indexing_service.index_collection(ct, incremental=True)
                    except Exception as e:
                        logger.error(f"Error in incremental indexing for {ct}: {e}")

            background_tasks.add_task(run_incremental_indexing)
            message = "Incremental indexing started in background"
        else:
            # Full reindex
            async def run_full_reindex():
                """Background task for full reindex"""
                indexing_service.reindex_all(content_types)

            background_tasks.add_task(run_full_reindex)
            message = "Full reindex started in background"

        content_type_names = [ct.value for ct in (content_types or list(ContentType))]

        logger.info(
            f"Reindex triggered by {current_user.get('data', {}).get('email')} "
            f"(incremental={request.incremental}, types={content_type_names})"
        )

        return TriggerReindexResponse(
            message=message,
            job_id=None,  # Could implement job tracking here
            content_types=content_type_names
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering reindex: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger reindex: {str(e)}"
        )


@router.get("/status", response_model=IndexingStatusResponse)
async def get_indexing_status(
    current_user: dict = Depends(require_admin)
):
    """
    Get current indexing status and statistics.

    Returns:
        Current indexing status and stats

    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        indexing_service = get_indexing_service()
        status = indexing_service.get_status()

        return IndexingStatusResponse(**status)

    except Exception as e:
        logger.error(f"Error getting indexing status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get indexing status: {str(e)}"
        )


@router.get("/stats", response_model=IndexingStatsResponse)
async def get_indexing_stats(
    current_user: dict = Depends(require_admin)
):
    """
    Get detailed indexing statistics.

    Returns comprehensive statistics including:
    - Total documents indexed
    - Total chunks created
    - Statistics per content type
    - Last indexing timestamps

    Returns:
        Detailed indexing statistics

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        indexing_service = get_indexing_service()
        stats = indexing_service.get_stats()

        return IndexingStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting indexing stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get indexing stats: {str(e)}"
        )


@router.post("/index-content", response_model=IndexContentResponse)
async def index_specific_content(
    request: IndexContentRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)
):
    """
    Index specific content by type or document ID.

    Allows granular control over what gets indexed. Can index:
    - All documents of a specific content type
    - A single specific document

    Args:
        request: Content indexing parameters
        background_tasks: FastAPI background tasks
        current_user: Current authenticated admin user

    Returns:
        Indexing operation result

    Raises:
        HTTPException: If indexing fails
    """
    try:
        indexing_service = get_indexing_service()

        # Validate content type
        try:
            content_type = ContentType(request.content_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type: {request.content_type}. "
                       f"Must be one of: {[ct.value for ct in ContentType]}"
            )

        if request.document_id:
            # Index specific document
            # First, fetch the document from ZeroDB
            from backend.services.zerodb_service import get_zerodb_client

            zerodb = get_zerodb_client()

            try:
                document = zerodb.get_document(
                    collection=content_type.value,
                    document_id=request.document_id
                )
            except Exception as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document not found: {request.document_id}"
                )

            # Index the document
            result = indexing_service.index_document(
                content_type=content_type,
                document=document,
                force=request.force
            )

            if result.get("success"):
                return IndexContentResponse(
                    success=True,
                    message=f"Successfully indexed document {request.document_id}",
                    details=result
                )
            else:
                return IndexContentResponse(
                    success=False,
                    message=f"Failed to index document: {result.get('error')}",
                    details=result
                )

        else:
            # Index entire content type in background
            async def run_content_type_indexing():
                """Background task for content type indexing"""
                indexing_service.index_collection(
                    content_type=content_type,
                    incremental=not request.force
                )

            background_tasks.add_task(run_content_type_indexing)

            logger.info(
                f"Content type indexing started by {current_user.get('data', {}).get('email')} "
                f"(type={content_type.value}, force={request.force})"
            )

            return IndexContentResponse(
                success=True,
                message=f"Indexing started for {content_type.value} in background",
                details={
                    "content_type": content_type.value,
                    "incremental": not request.force
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index content: {str(e)}"
        )
