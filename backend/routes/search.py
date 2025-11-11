"""
Search Routes - US-038 & US-040

Provides search query endpoints and feedback submission.
Combines US-038 (Search Query Endpoint) and US-040 (Search Feedback System).

Endpoints:
- POST /api/search/query - Execute search query with RAG pipeline (US-038)
- POST /api/search/feedback - Submit feedback on search results (US-040)
"""

import logging
import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field, field_validator

from backend.services.search_service import SearchService
from backend.services.query_search_service import get_query_search_service, QuerySearchError
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.middleware.rate_limit import rate_limit

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/search", tags=["search"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

# --- US-038: Search Query Models ---

class SearchQueryRequest(BaseModel):
    """
    Search query request model (US-038).

    Validates query parameters before processing.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text (1-500 characters)"
    )
    bypass_cache: bool = Field(
        default=False,
        description="Bypass cache for testing (default: False)"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitize query"""
        # Strip whitespace
        v = v.strip()

        # Check minimum length after stripping
        if not v:
            raise ValueError("Query cannot be empty or whitespace only")

        # Check for suspicious patterns (basic SQL injection prevention)
        suspicious_patterns = ["--", "/*", "*/", "xp_", "sp_", "exec", "execute"]
        v_lower = v.lower()
        for pattern in suspicious_patterns:
            if pattern in v_lower:
                raise ValueError(f"Query contains invalid pattern: {pattern}")

        return v


class SearchQueryResponse(BaseModel):
    """
    Search query response model (US-038).

    Contains AI-generated answer, sources, media, and metadata.
    """
    answer: str = Field(..., description="AI-generated markdown answer")
    sources: list[dict] = Field(..., description="List of source documents")
    media: dict = Field(..., description="Attached media (videos and images)")
    related_queries: list[str] = Field(..., description="Related search queries")
    latency_ms: int = Field(..., description="Query processing latency in milliseconds")
    cached: bool = Field(..., description="Whether result was from cache")


# --- US-040: Feedback Models ---

class FeedbackRequest(BaseModel):
    """Search feedback submission request"""
    query_id: UUID = Field(..., description="UUID of the search query")
    rating: str = Field(..., description="Feedback rating: 'positive' or 'negative'")
    feedback_text: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional text feedback from user"
    )

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is positive or negative"""
        if v not in ["positive", "negative"]:
            raise ValueError("Rating must be 'positive' or 'negative'")
        return v

    @field_validator('feedback_text')
    @classmethod
    def validate_feedback_text(cls, v):
        """Trim and validate feedback text"""
        if v:
            v = v.strip()
            if len(v) > 2000:
                raise ValueError("Feedback text must not exceed 2000 characters")
            if len(v) == 0:
                return None
        return v


class FeedbackResponse(BaseModel):
    """Search feedback submission response"""
    success: bool = Field(..., description="Whether feedback was submitted successfully")
    query_id: UUID = Field(..., description="UUID of the search query")
    rating: str = Field(..., description="Submitted rating")
    flagged_for_review: bool = Field(..., description="Whether feedback was flagged for admin review")
    message: str = Field(..., description="Success message")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_search_service(db = Depends(get_zerodb_client)) -> SearchService:
    """Dependency injection for SearchService"""
    return SearchService(db)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request

    Checks X-Forwarded-For header first (for proxies/load balancers),
    then falls back to direct client IP.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    # Check X-Forwarded-For header (behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


# ============================================================================
# PUBLIC ENDPOINTS - No Authentication Required
# ============================================================================

# --- US-038: Search Query Endpoint ---

@router.post(
    "/query",
    response_model=SearchQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute search query (US-038)",
    description="""
    Execute a search query using RAG (Retrieval Augmented Generation) pipeline.

    This endpoint:
    1. Normalizes and validates the query
    2. Checks rate limits (10 queries per minute per IP)
    3. Checks cache (5-minute TTL)
    4. Generates query embedding using OpenAI
    5. Performs vector search in ZeroDB
    6. Sends context to AI Registry for answer generation
    7. Attaches relevant media (videos and images)
    8. Caches result for 5 minutes
    9. Logs query for analytics
    10. Returns formatted response

    Rate Limits:
    - 10 queries per minute per IP address
    - Returns 429 Too Many Requests when exceeded

    Performance:
    - p95 latency < 1.2 seconds (excluding LLM time)
    - p50 latency < 800ms
    - Timeout after 10 seconds

    The response includes:
    - AI-generated markdown answer based on context
    - Source documents with titles and URLs
    - Attached media (videos from Cloudflare Stream, images from ZeroDB)
    - Related search queries for exploration
    - Performance metadata (latency, cache status)
    """
)
@rate_limit(requests=10, window_seconds=60)  # 10 queries per minute
async def search_query(
    request: Request,
    search_request: SearchQueryRequest
):
    """
    Execute search query endpoint (US-038).

    Args:
        request: FastAPI request object (for IP extraction)
        search_request: Search query request with validation

    Returns:
        JSON response with search results

    Raises:
        HTTPException 400: Invalid query
        HTTPException 429: Rate limit exceeded (handled by middleware)
        HTTPException 408: Request timeout
        HTTPException 500: Internal server error
    """
    start_time = asyncio.get_event_loop().time()

    try:
        # Extract client IP for logging
        client_ip = get_client_ip(request)

        # Extract user ID if authenticated
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        logger.info(
            f"Search query request: '{search_request.query[:50]}...' "
            f"(user_id={user_id}, ip={client_ip})"
        )

        # Get search service
        search_service = get_query_search_service()

        # Execute search with timeout
        try:
            # Run search in executor to avoid blocking
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    search_service.search_query,
                    query=search_request.query,
                    user_id=user_id,
                    ip_address=client_ip,
                    bypass_cache=search_request.bypass_cache
                ),
                timeout=10.0  # 10 second timeout
            )

            elapsed_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            logger.info(
                f"Search completed successfully in {elapsed_ms}ms "
                f"(cached={result.get('cached', False)})"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Search query timeout after 10 seconds: '{search_request.query[:50]}...'")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail={
                    "error": "search_timeout",
                    "message": "Search query timed out after 10 seconds. Please try a simpler query."
                }
            )

    except QuerySearchError as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "search_error",
                "message": str(e)
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions (timeout, rate limit, etc.)
        raise

    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred while processing your search. Please try again."
            }
        )


# --- US-040: Feedback Endpoint ---

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit search feedback",
    description="""
    Submit anonymous feedback for a search query.

    Features:
    - Anonymous submission (no login required)
    - Thumbs up/down rating
    - Optional text feedback
    - IP address hashed for privacy (SHA256)
    - Negative feedback automatically flagged for admin review

    Privacy:
    - IP addresses are hashed with SHA256 + salt
    - No personally identifiable information stored
    - Feedback is completely anonymous

    Rate Limiting:
    - One feedback per query
    - IP-based duplicate prevention
    """
)
async def submit_search_feedback(
    feedback: FeedbackRequest,
    request: Request,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Submit feedback for a search query (anonymous, no auth required)

    This endpoint allows users to provide feedback on search results without
    requiring authentication. IP addresses are hashed for privacy while still
    allowing detection of duplicate feedback.

    Args:
        feedback: Feedback submission data (query_id, rating, optional text)
        request: FastAPI request object (for IP extraction)
        search_service: Injected search service

    Returns:
        FeedbackResponse with submission confirmation

    Raises:
        HTTPException 404: Query not found
        HTTPException 400: Invalid rating or feedback already submitted
        HTTPException 500: Server error
    """
    try:
        # Get client IP for privacy-preserving hashing
        client_ip = get_client_ip(request)

        # Submit feedback
        updated_query = await search_service.submit_feedback(
            query_id=feedback.query_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            ip_address=client_ip
        )

        # Log feedback submission (without PII)
        logger.info(
            f"Search feedback submitted - Query: {feedback.query_id}, "
            f"Rating: {feedback.rating}, "
            f"Has Text: {bool(feedback.feedback_text)}, "
            f"Flagged: {updated_query.get('flagged_for_review', False)}"
        )

        return FeedbackResponse(
            success=True,
            query_id=feedback.query_id,
            rating=feedback.rating,
            flagged_for_review=updated_query.get("flagged_for_review", False),
            message="Thank you for your feedback! It helps us improve search results."
        )

    except ValueError as e:
        # Query not found or validation error
        error_msg = str(e)
        logger.warning(f"Search feedback validation error: {error_msg}")

        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Search query not found: {feedback.query_id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

    except ZeroDBError as e:
        # Database error
        logger.error(f"Database error submitting search feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback. Please try again later."
        )

    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error submitting search feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Search service health check",
    description="Check if the search service is operational"
)
async def search_health_check():
    """
    Health check endpoint for search service

    Returns:
        Simple status response
    """
    return {
        "status": "healthy",
        "service": "search",
        "features": {
            "feedback": True,
            "anonymous": True,
            "privacy_protected": True
        }
    }
