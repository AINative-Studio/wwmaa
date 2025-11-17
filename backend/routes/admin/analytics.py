"""
Admin Analytics Routes for WWMAA Backend

Provides real-time analytics data for the admin dashboard.
All endpoints require admin authentication and implement caching for performance.

Endpoints:
- GET /api/admin/analytics - Get comprehensive platform analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBError,
    ZeroDBNotFoundError
)
from backend.services.instrumented_cache_service import get_cache_service
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import User, UserRole, SubscriptionStatus, PaymentStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/admin/analytics",
    tags=["admin-analytics"]
)

# Cache configuration
ANALYTICS_CACHE_KEY = "admin:analytics:dashboard"
ANALYTICS_CACHE_TTL = 300  # 5 minutes in seconds


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class AnalyticsResponse(BaseModel):
    """Response model for admin analytics dashboard"""
    total_members: int = Field(..., description="Total number of members (role = member)")
    active_subscriptions: int = Field(..., description="Active subscriptions count")
    total_revenue: float = Field(..., description="Total revenue from successful payments")
    recent_signups: int = Field(..., description="Users created in last 30 days")
    upcoming_events: int = Field(..., description="Events with date > today")
    active_sessions: int = Field(..., description="Live training sessions currently active")

    # Additional insights
    pending_applications: int = Field(default=0, description="Applications pending review")
    total_events_this_month: int = Field(default=0, description="Events scheduled this month")
    revenue_this_month: float = Field(default=0.0, description="Revenue this month")

    # Metadata
    cached: bool = Field(default=False, description="Whether data came from cache")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when analytics were generated")
    cache_expires_at: Optional[datetime] = Field(None, description="When cached data expires")


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role for analytics access

    Args:
        current_user: Currently authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# ANALYTICS SERVICE FUNCTIONS
# ============================================================================

def safe_parse_date(date_str: str, default: Optional[datetime] = None) -> datetime:
    """
    Safely parse ISO format date string with fallback.

    Args:
        date_str: ISO format date string
        default: Default datetime if parsing fails

    Returns:
        Parsed datetime or default
    """
    if default is None:
        default = datetime(1970, 1, 1)

    try:
        # Handle 'Z' timezone indicator
        clean_date = date_str.replace("Z", "+00:00") if date_str else ""
        return datetime.fromisoformat(clean_date)
    except (ValueError, AttributeError):
        return default


async def calculate_analytics() -> Dict[str, Any]:
    """
    Calculate comprehensive analytics from database.

    Optimized queries with parallel execution where possible.

    Returns:
        Dictionary with analytics metrics

    Raises:
        ZeroDBError: If database query fails
    """
    db = get_zerodb_client()

    try:
        # Calculate date boundaries for time-based queries
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 1. Total members (role = member)
        # Optimized: Use filter with role field
        members_result = db.find_documents(
            collection="users",
            filters={"role": "member", "is_active": True},
            limit=10000  # Safety limit
        )
        total_members = len(members_result.get("documents", []))

        # 2. Active subscriptions (status = active)
        # Optimized: Single filter query
        active_subs_result = db.find_documents(
            collection="subscriptions",
            filters={"status": "active"},
            limit=10000
        )
        active_subscriptions = len(active_subs_result.get("documents", []))

        # 3. Total revenue from successful payments
        # Optimized: Filter for succeeded status and sum amounts
        payments_result = db.find_documents(
            collection="payments",
            filters={"status": "succeeded"},
            limit=50000  # Higher limit for payments
        )
        payments = payments_result.get("documents", [])
        total_revenue = sum(float(p.get("amount") or 0) for p in payments)

        # 4. Revenue this month (for additional insight)
        # Filter payments by month in application layer (ZeroDB doesn't support date range filters directly)
        revenue_this_month = sum(
            float(p.get("amount") or 0)
            for p in payments
            if safe_parse_date(p.get("created_at", "1970-01-01T00:00:00")) >= start_of_month
        )

        # 5. Recent signups (last 30 days)
        # Get all users and filter by created_at in application layer
        # Note: In production with large datasets, consider ZeroDB date range support
        all_users_result = db.find_documents(
            collection="users",
            filters={},
            limit=50000
        )
        all_users = all_users_result.get("documents", [])
        recent_signups = sum(
            1 for u in all_users
            if safe_parse_date(u.get("created_at", "1970-01-01T00:00:00")) >= thirty_days_ago
        )

        # 6. Upcoming events (date > today)
        # Get all published events and filter by start_date
        events_result = db.find_documents(
            collection="events",
            filters={"is_published": True, "is_deleted": False},
            limit=10000
        )
        events = events_result.get("documents", [])
        upcoming_events = sum(
            1 for e in events
            if safe_parse_date(e.get("start_date", "1970-01-01T00:00:00")) > now
        )

        # 7. Events this month
        total_events_this_month = sum(
            1 for e in events
            if safe_parse_date(e.get("start_date", "1970-01-01T00:00:00")) >= start_of_month
        )

        # 8. Active live sessions (currently live)
        # Optimized: Filter for is_live = true
        live_sessions_result = db.find_documents(
            collection="training_sessions",
            filters={"is_live": True},
            limit=1000
        )
        active_sessions = len(live_sessions_result.get("documents", []))

        # 9. Pending applications (additional insight)
        pending_apps_result = db.find_documents(
            collection="applications",
            filters={"status": "submitted"},
            limit=5000
        )
        pending_applications = len(pending_apps_result.get("documents", []))

        analytics_data = {
            "total_members": total_members,
            "active_subscriptions": active_subscriptions,
            "total_revenue": round(total_revenue, 2),
            "recent_signups": recent_signups,
            "upcoming_events": upcoming_events,
            "active_sessions": active_sessions,
            "pending_applications": pending_applications,
            "total_events_this_month": total_events_this_month,
            "revenue_this_month": round(revenue_this_month, 2),
            "cached": False,
            "generated_at": now.isoformat(),
            "cache_expires_at": (now + timedelta(seconds=ANALYTICS_CACHE_TTL)).isoformat()
        }

        logger.info(
            f"Analytics calculated: {total_members} members, "
            f"{active_subscriptions} active subs, "
            f"${total_revenue:.2f} total revenue"
        )

        return analytics_data

    except ZeroDBError as e:
        logger.error(f"Database error calculating analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics data"
        )
    except Exception as e:
        logger.error(f"Unexpected error calculating analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=AnalyticsResponse,
    summary="Get Admin Analytics",
    description="Retrieve comprehensive platform analytics for the admin dashboard. "
                "Results are cached for 5 minutes for optimal performance.",
    responses={
        200: {
            "description": "Analytics data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_members": 145,
                        "active_subscriptions": 89,
                        "total_revenue": 12450.50,
                        "recent_signups": 23,
                        "upcoming_events": 12,
                        "active_sessions": 2,
                        "pending_applications": 5,
                        "total_events_this_month": 8,
                        "revenue_this_month": 2340.00,
                        "cached": False,
                        "generated_at": "2025-01-14T10:30:00",
                        "cache_expires_at": "2025-01-14T10:35:00"
                    }
                }
            }
        },
        403: {
            "description": "Not authorized - admin role required"
        },
        500: {
            "description": "Server error retrieving analytics"
        }
    }
)
async def get_analytics(
    force_refresh: bool = False,
    current_user: User = Depends(require_admin)
) -> AnalyticsResponse:
    """
    Get comprehensive admin analytics dashboard data.

    This endpoint provides real-time metrics about:
    - Total members (users with role = member)
    - Active subscriptions (subscriptions with status = active)
    - Total revenue (sum of successful payments)
    - Recent signups (users created in last 30 days)
    - Upcoming events (events with start_date > today)
    - Active sessions (live training sessions)
    - Pending applications (applications awaiting review)
    - Monthly metrics (events and revenue this month)

    Results are cached for 5 minutes to ensure fast response times.
    Use force_refresh=true to bypass cache and get fresh data.

    Args:
        force_refresh: If True, bypass cache and recalculate analytics
        current_user: Authenticated admin user (injected by dependency)

    Returns:
        AnalyticsResponse with all metrics

    Raises:
        HTTPException: 403 if not admin, 500 if database error
    """
    cache = get_cache_service()

    try:
        # Try to get from cache unless force refresh
        if not force_refresh:
            cached_data = cache.get(ANALYTICS_CACHE_KEY)
            if cached_data:
                logger.info("Returning cached analytics data")
                cached_data["cached"] = True
                return AnalyticsResponse(**cached_data)

        # Calculate fresh analytics
        logger.info(f"Calculating fresh analytics (force_refresh={force_refresh})")
        analytics_data = await calculate_analytics()

        # Cache the results
        cache.set(
            key=ANALYTICS_CACHE_KEY,
            value=analytics_data,
            expiration=ANALYTICS_CACHE_TTL
        )

        return AnalyticsResponse(**analytics_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics data"
        )


@router.delete(
    "/cache",
    summary="Clear Analytics Cache",
    description="Force clear the analytics cache. Next request will recalculate fresh data.",
    responses={
        200: {
            "description": "Cache cleared successfully"
        },
        403: {
            "description": "Not authorized - admin role required"
        }
    }
)
async def clear_analytics_cache(
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Clear the analytics cache to force fresh data on next request.

    Useful when immediate data updates are needed after significant changes.

    Args:
        current_user: Authenticated admin user (injected by dependency)

    Returns:
        Success message

    Raises:
        HTTPException: 403 if not admin
    """
    cache = get_cache_service()

    try:
        cache.delete(ANALYTICS_CACHE_KEY)
        logger.info(f"Analytics cache cleared by admin: {current_user.email}")

        return {
            "message": "Analytics cache cleared successfully",
            "cleared_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing analytics cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )
