"""
Admin Search Analytics Routes - US-040: Search Feedback System

Provides administrative endpoints for viewing and managing search feedback.
All endpoints require admin authentication.

Endpoints:
- GET /api/admin/search/feedback - List all feedback with filters
- GET /api/admin/search/feedback/flagged - Get negative feedback flagged for review
- GET /api/admin/search/statistics - Get search feedback statistics
- POST /api/admin/search/feedback/{query_id}/unflag - Remove review flag
- GET /api/admin/search/feedback/export - Export feedback to CSV
"""

import logging
import csv
import io
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.services.search_service import SearchService
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.middleware.auth_middleware import RoleChecker
from backend.models.schemas import UserRole

# Configure logging
logger = logging.getLogger(__name__)

# Create router with admin prefix
router = APIRouter(
    prefix="/api/admin/search",
    tags=["admin", "search", "analytics"]
)


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class FeedbackItem(BaseModel):
    """Individual feedback item response"""
    id: UUID
    query_text: str
    feedback_rating: str
    feedback_text: Optional[str] = None
    feedback_timestamp: datetime
    flagged_for_review: bool
    results_count: int
    response_time_ms: Optional[int] = None
    ip_hash: Optional[str] = None
    user_id: Optional[UUID] = None
    created_at: datetime


class FeedbackListResponse(BaseModel):
    """Response model for feedback list"""
    items: List[FeedbackItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class FeedbackStatisticsResponse(BaseModel):
    """Response model for feedback statistics"""
    total_queries: int
    queries_with_feedback: int
    positive_count: int
    negative_count: int
    feedback_rate: float
    satisfaction_rate: float
    flagged_count: int
    with_text_count: int
    period: dict


class UnflagResponse(BaseModel):
    """Response for unflag action"""
    success: bool
    query_id: UUID
    message: str


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_search_service(db = Depends(get_zerodb_client)) -> SearchService:
    """Dependency injection for SearchService"""
    return SearchService(db)


# Admin role checker dependency
require_admin = RoleChecker(allowed_roles=[UserRole.ADMIN])


# ============================================================================
# ADMIN ENDPOINTS - Require Admin Authentication
# ============================================================================

@router.get(
    "/feedback",
    response_model=FeedbackListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all search feedback",
    description="""
    Get all search feedback with optional filtering.

    Filters:
    - rating: Filter by 'positive' or 'negative'
    - has_text: Filter for feedback with text comments
    - start_date: Filter by start date (ISO 8601)
    - end_date: Filter by end date (ISO 8601)

    Pagination:
    - limit: Maximum results (default 50, max 200)
    - offset: Number of results to skip (default 0)

    Requires: Admin role
    """
)
async def get_all_feedback(
    rating: Optional[str] = Query(None, description="Filter by rating (positive/negative)"),
    has_text: Optional[bool] = Query(None, description="Filter for feedback with text"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO 8601)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    search_service: SearchService = Depends(get_search_service),
    current_user = Depends(require_admin)
):
    """
    Get all search feedback with filtering and pagination

    Admin-only endpoint for viewing all search feedback submitted by users.

    Args:
        rating: Optional filter by rating
        has_text: Optional filter for feedback with text
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Max results to return
        offset: Number of results to skip
        search_service: Injected search service
        current_user: Authenticated admin user

    Returns:
        FeedbackListResponse with paginated results

    Raises:
        HTTPException 400: Invalid filters
        HTTPException 500: Server error
    """
    try:
        # Validate rating if provided
        if rating and rating not in ["positive", "negative"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be 'positive' or 'negative'"
            )

        # Get feedback with filters
        result = await search_service.get_all_feedback(
            rating=rating,
            has_text=has_text,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Convert to response model
        items = [
            FeedbackItem(
                id=UUID(item["id"]),
                query_text=item.get("query_text", ""),
                feedback_rating=item.get("feedback_rating", ""),
                feedback_text=item.get("feedback_text"),
                feedback_timestamp=item.get("feedback_timestamp", datetime.utcnow()),
                flagged_for_review=item.get("flagged_for_review", False),
                results_count=item.get("results_count", 0),
                response_time_ms=item.get("response_time_ms"),
                ip_hash=item.get("ip_hash"),
                user_id=UUID(item["user_id"]) if item.get("user_id") else None,
                created_at=item.get("created_at", datetime.utcnow())
            )
            for item in result["items"]
        ]

        return FeedbackListResponse(
            items=items,
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
            has_more=result["has_more"]
        )

    except ValueError as e:
        logger.warning(f"Invalid feedback query parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ZeroDBError as e:
        logger.error(f"Database error fetching feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback data"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/feedback/flagged",
    response_model=List[FeedbackItem],
    status_code=status.HTTP_200_OK,
    summary="Get flagged feedback",
    description="""
    Get negative feedback flagged for admin review.

    Returns queries with negative ratings that need attention.
    Sorted by most recent first.

    Requires: Admin role
    """
)
async def get_flagged_feedback(
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    search_service: SearchService = Depends(get_search_service),
    current_user = Depends(require_admin)
):
    """
    Get feedback flagged for review (negative feedback)

    Admin-only endpoint for reviewing negative search feedback.

    Args:
        limit: Max results to return
        offset: Number of results to skip
        search_service: Injected search service
        current_user: Authenticated admin user

    Returns:
        List of FeedbackItem objects

    Raises:
        HTTPException 500: Server error
    """
    try:
        flagged_queries = await search_service.get_flagged_feedback(
            limit=limit,
            offset=offset
        )

        # Convert to response model
        items = [
            FeedbackItem(
                id=UUID(item["id"]),
                query_text=item.get("query_text", ""),
                feedback_rating=item.get("feedback_rating", ""),
                feedback_text=item.get("feedback_text"),
                feedback_timestamp=item.get("feedback_timestamp", datetime.utcnow()),
                flagged_for_review=item.get("flagged_for_review", False),
                results_count=item.get("results_count", 0),
                response_time_ms=item.get("response_time_ms"),
                ip_hash=item.get("ip_hash"),
                user_id=UUID(item["user_id"]) if item.get("user_id") else None,
                created_at=item.get("created_at", datetime.utcnow())
            )
            for item in flagged_queries
        ]

        return items

    except ZeroDBError as e:
        logger.error(f"Database error fetching flagged feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch flagged feedback"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching flagged feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/statistics",
    response_model=FeedbackStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get search feedback statistics",
    description="""
    Get comprehensive statistics about search feedback.

    Statistics include:
    - Total queries
    - Feedback rate (% of queries with feedback)
    - Satisfaction rate (% of positive feedback)
    - Flagged count (negative feedback needing review)
    - Text feedback count

    Optional date range filtering.

    Requires: Admin role
    """
)
async def get_feedback_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    search_service: SearchService = Depends(get_search_service),
    current_user = Depends(require_admin)
):
    """
    Get search feedback statistics

    Admin-only endpoint for analytics dashboard.

    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        search_service: Injected search service
        current_user: Authenticated admin user

    Returns:
        FeedbackStatisticsResponse with comprehensive stats

    Raises:
        HTTPException 500: Server error
    """
    try:
        stats = await search_service.get_feedback_statistics(
            start_date=start_date,
            end_date=end_date
        )

        return FeedbackStatisticsResponse(**stats)

    except ZeroDBError as e:
        logger.error(f"Database error fetching statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/feedback/{query_id}/unflag",
    response_model=UnflagResponse,
    status_code=status.HTTP_200_OK,
    summary="Unflag feedback",
    description="""
    Remove review flag from a query (mark as reviewed).

    Use this after reviewing negative feedback to clear the flag.

    Requires: Admin role
    """
)
async def unflag_feedback(
    query_id: UUID,
    search_service: SearchService = Depends(get_search_service),
    current_user = Depends(require_admin)
):
    """
    Remove review flag from feedback

    Admin action to mark negative feedback as reviewed.

    Args:
        query_id: UUID of the search query
        search_service: Injected search service
        current_user: Authenticated admin user

    Returns:
        UnflagResponse with success confirmation

    Raises:
        HTTPException 404: Query not found
        HTTPException 500: Server error
    """
    try:
        updated = await search_service.unflag_feedback(query_id)

        logger.info(f"Admin {current_user.get('email', 'unknown')} unflagged query {query_id}")

        return UnflagResponse(
            success=True,
            query_id=query_id,
            message="Feedback flag removed successfully"
        )

    except ValueError as e:
        logger.warning(f"Query not found for unflag: {query_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search query {query_id} not found"
        )

    except ZeroDBError as e:
        logger.error(f"Database error unflagging feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unflag feedback"
        )

    except Exception as e:
        logger.error(f"Unexpected error unflagging feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/feedback/export",
    status_code=status.HTTP_200_OK,
    summary="Export feedback to CSV",
    description="""
    Export search feedback to CSV file for analysis.

    Includes all feedback fields:
    - Query ID
    - Query text
    - Rating
    - Feedback text
    - Timestamp
    - Flagged status
    - Results count
    - Response time

    Optional date range filtering.

    Requires: Admin role
    """
)
async def export_feedback_csv(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    search_service: SearchService = Depends(get_search_service),
    current_user = Depends(require_admin)
):
    """
    Export feedback to CSV file

    Admin-only endpoint for exporting feedback data.

    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        rating: Optional rating filter
        search_service: Injected search service
        current_user: Authenticated admin user

    Returns:
        StreamingResponse with CSV file

    Raises:
        HTTPException 500: Server error
    """
    try:
        # Get all feedback (no pagination for export)
        result = await search_service.get_all_feedback(
            rating=rating,
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # High limit for export
            offset=0
        )

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Query ID",
            "Query Text",
            "Rating",
            "Feedback Text",
            "Timestamp",
            "Flagged",
            "Results Count",
            "Response Time (ms)",
            "Created At"
        ])

        # Write data rows
        for item in result["items"]:
            writer.writerow([
                item.get("id", ""),
                item.get("query_text", ""),
                item.get("feedback_rating", ""),
                item.get("feedback_text", ""),
                item.get("feedback_timestamp", ""),
                item.get("flagged_for_review", False),
                item.get("results_count", 0),
                item.get("response_time_ms", ""),
                item.get("created_at", "")
            ])

        # Prepare response
        output.seek(0)
        filename = f"search_feedback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        logger.info(
            f"Admin {current_user.get('email', 'unknown')} exported "
            f"{len(result['items'])} feedback records"
        )

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ZeroDBError as e:
        logger.error(f"Database error exporting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export feedback"
        )

    except Exception as e:
        logger.error(f"Unexpected error exporting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
