"""
Unit tests for Admin Analytics Endpoint

Tests the /api/admin/analytics endpoint for:
- Real-time metric calculation from database
- Caching behavior (5-minute TTL)
- Admin-only access control
- Edge cases and error handling
- Performance optimization
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status
from freezegun import freeze_time

from backend.routes.admin.analytics import (
    router,
    calculate_analytics,
    get_analytics,
    clear_analytics_cache,
    require_admin,
    AnalyticsResponse,
    ANALYTICS_CACHE_KEY,
    ANALYTICS_CACHE_TTL,
)
from backend.models.schemas import User, UserRole


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_admin_user():
    """Create a mock admin user"""
    return User(
        id=uuid4(),
        email="admin@wwmaa.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_member_user():
    """Create a mock member user (not admin)"""
    return User(
        id=uuid4(),
        email="member@wwmaa.com",
        password_hash="hashed_password",
        role=UserRole.MEMBER,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_zerodb_client():
    """Create a mock ZeroDB client with test data"""
    mock_db = MagicMock()

    # Mock users (total members)
    mock_db.find_documents.return_value = {
        "documents": [
            {"id": str(uuid4()), "email": f"member{i}@test.com", "role": "member", "is_active": True}
            for i in range(145)
        ]
    }

    return mock_db


@pytest.fixture
def sample_analytics_data():
    """Sample analytics data for testing"""
    now = datetime.utcnow()
    return {
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
        "generated_at": now.isoformat(),
        "cache_expires_at": (now + timedelta(seconds=ANALYTICS_CACHE_TTL)).isoformat()
    }


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

def test_require_admin_success(mock_admin_user):
    """Test that admin users pass authorization"""
    result = require_admin(current_user=mock_admin_user)
    assert result == mock_admin_user
    assert result.role == UserRole.ADMIN.value


def test_require_admin_rejects_member(mock_member_user):
    """Test that member users are rejected"""
    with pytest.raises(HTTPException) as exc_info:
        require_admin(current_user=mock_member_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Admin access required" in str(exc_info.value.detail)


def test_require_admin_rejects_instructor():
    """Test that instructor users are rejected"""
    instructor_user = User(
        id=uuid4(),
        email="instructor@wwmaa.com",
        password_hash="hashed_password",
        role=UserRole.INSTRUCTOR,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    with pytest.raises(HTTPException) as exc_info:
        require_admin(current_user=instructor_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# ANALYTICS CALCULATION TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_success(mock_get_db):
    """Test successful analytics calculation with real data"""
    # Setup mock database responses
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Mock users (members)
    mock_db.find_documents.side_effect = [
        # Call 1: total members
        {"documents": [{"id": str(uuid4()), "role": "member", "is_active": True} for _ in range(145)]},
        # Call 2: active subscriptions
        {"documents": [{"id": str(uuid4()), "status": "active"} for _ in range(89)]},
        # Call 3: successful payments
        {"documents": [
            {"id": str(uuid4()), "status": "succeeded", "amount": 100.00, "created_at": now.isoformat()}
            for _ in range(124)
        ] + [
            {"id": str(uuid4()), "status": "succeeded", "amount": 50.50, "created_at": start_of_month.isoformat()}
        ]},
        # Call 4: all users (for recent signups)
        {"documents": [
            {"id": str(uuid4()), "created_at": (now - timedelta(days=5)).isoformat()}
            for _ in range(23)
        ] + [
            {"id": str(uuid4()), "created_at": (now - timedelta(days=60)).isoformat()}
            for _ in range(50)
        ]},
        # Call 5: published events
        {"documents": [
            {"id": str(uuid4()), "is_published": True, "is_deleted": False,
             "start_date": (now + timedelta(days=7)).isoformat()}
            for _ in range(12)
        ] + [
            {"id": str(uuid4()), "is_published": True, "is_deleted": False,
             "start_date": (now + timedelta(days=5)).isoformat()}
            for _ in range(8)
        ]},
        # Call 6: live sessions
        {"documents": [{"id": str(uuid4()), "is_live": True} for _ in range(2)]},
        # Call 7: pending applications
        {"documents": [{"id": str(uuid4()), "status": "submitted"} for _ in range(5)]},
    ]

    result = await calculate_analytics()

    assert result["total_members"] == 145
    assert result["active_subscriptions"] == 89
    assert result["total_revenue"] == 12450.50  # (124 * 100) + 50.50
    assert result["recent_signups"] == 23
    assert result["upcoming_events"] == 20  # 12 + 8 future events
    assert result["active_sessions"] == 2
    assert result["pending_applications"] == 5
    assert result["cached"] is False
    assert "generated_at" in result
    assert "cache_expires_at" in result


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_empty_database(mock_get_db):
    """Test analytics calculation with empty database"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # All queries return empty results
    mock_db.find_documents.return_value = {"documents": []}

    result = await calculate_analytics()

    assert result["total_members"] == 0
    assert result["active_subscriptions"] == 0
    assert result["total_revenue"] == 0.0
    assert result["recent_signups"] == 0
    assert result["upcoming_events"] == 0
    assert result["active_sessions"] == 0
    assert result["pending_applications"] == 0
    assert result["total_events_this_month"] == 0
    assert result["revenue_this_month"] == 0.0


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_handles_database_error(mock_get_db):
    """Test that database errors are handled gracefully"""
    from backend.services.zerodb_service import ZeroDBError

    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.find_documents.side_effect = ZeroDBError("Database connection failed")

    with pytest.raises(HTTPException) as exc_info:
        await calculate_analytics()

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to retrieve analytics data" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_revenue_calculation(mock_get_db):
    """Test revenue calculations are accurate"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Mock payments with different amounts
    payments = [
        {"id": str(uuid4()), "status": "succeeded", "amount": 50.00,
         "created_at": (now - timedelta(days=5)).isoformat()},
        {"id": str(uuid4()), "status": "succeeded", "amount": 75.50,
         "created_at": (now - timedelta(days=10)).isoformat()},
        {"id": str(uuid4()), "status": "succeeded", "amount": 100.00,
         "created_at": start_of_month.isoformat()},
        {"id": str(uuid4()), "status": "succeeded", "amount": 25.25,
         "created_at": (now - timedelta(days=60)).isoformat()},  # Outside this month
    ]

    mock_db.find_documents.side_effect = [
        {"documents": []},  # members
        {"documents": []},  # subscriptions
        {"documents": payments},  # payments
        {"documents": []},  # users
        {"documents": []},  # events
        {"documents": []},  # live sessions
        {"documents": []},  # applications
    ]

    result = await calculate_analytics()

    # Total revenue = 50 + 75.50 + 100 + 25.25 = 250.75
    assert result["total_revenue"] == 250.75
    # Revenue this month = 50 + 75.50 + 100 = 225.50
    assert result["revenue_this_month"] == 225.50


# ============================================================================
# CACHING TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_cache_service')
@patch('backend.routes.admin.analytics.calculate_analytics')
async def test_get_analytics_returns_cached_data(mock_calculate, mock_get_cache, mock_admin_user, sample_analytics_data):
    """Test that cached data is returned when available"""
    # Setup mocks
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache
    mock_cache.get.return_value = sample_analytics_data

    result = await get_analytics(force_refresh=False, current_user=mock_admin_user)

    # Verify cache was checked
    mock_cache.get.assert_called_once_with(ANALYTICS_CACHE_KEY)

    # Verify calculate_analytics was NOT called
    mock_calculate.assert_not_called()

    # Verify response has cached=True
    assert result.cached is True
    assert result.total_members == 145


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_cache_service')
@patch('backend.routes.admin.analytics.calculate_analytics')
async def test_get_analytics_calculates_when_cache_miss(mock_calculate, mock_get_cache, mock_admin_user, sample_analytics_data):
    """Test that analytics are calculated when cache is empty"""
    # Setup mocks
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache
    mock_cache.get.return_value = None  # Cache miss
    mock_calculate.return_value = sample_analytics_data

    result = await get_analytics(force_refresh=False, current_user=mock_admin_user)

    # Verify cache was checked
    mock_cache.get.assert_called_once_with(ANALYTICS_CACHE_KEY)

    # Verify calculate_analytics WAS called
    mock_calculate.assert_called_once()

    # Verify result was cached
    mock_cache.set.assert_called_once_with(
        key=ANALYTICS_CACHE_KEY,
        value=sample_analytics_data,
        expiration=ANALYTICS_CACHE_TTL
    )

    assert result.total_members == 145


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_cache_service')
@patch('backend.routes.admin.analytics.calculate_analytics')
async def test_get_analytics_force_refresh_bypasses_cache(mock_calculate, mock_get_cache, mock_admin_user, sample_analytics_data):
    """Test that force_refresh=True bypasses cache"""
    # Setup mocks
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache
    mock_cache.get.return_value = sample_analytics_data  # Cache has data
    mock_calculate.return_value = sample_analytics_data

    result = await get_analytics(force_refresh=True, current_user=mock_admin_user)

    # Verify cache was NOT checked
    mock_cache.get.assert_not_called()

    # Verify calculate_analytics WAS called
    mock_calculate.assert_called_once()

    # Verify fresh data was cached
    mock_cache.set.assert_called_once()


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_cache_service')
async def test_clear_analytics_cache_success(mock_get_cache, mock_admin_user):
    """Test successful cache clearing"""
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache

    result = await clear_analytics_cache(current_user=mock_admin_user)

    # Verify cache.delete was called
    mock_cache.delete.assert_called_once_with(ANALYTICS_CACHE_KEY)

    assert result["message"] == "Analytics cache cleared successfully"
    assert "cleared_at" in result


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_handles_malformed_dates(mock_get_db):
    """Test analytics calculation handles malformed date strings gracefully"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    now = datetime.utcnow()

    # Mock data with malformed dates - should use fallback (1970-01-01)
    mock_db.find_documents.side_effect = [
        {"documents": []},  # members
        {"documents": []},  # subscriptions
        {"documents": [
            {"id": str(uuid4()), "status": "succeeded", "amount": 100, "created_at": "invalid-date"}
        ]},  # payments with bad date
        {"documents": [
            {"id": str(uuid4()), "created_at": "1970-01-01T00:00:00"}  # Default fallback
        ]},  # users
        {"documents": []},  # events
        {"documents": []},  # live sessions
        {"documents": []},  # applications
    ]

    # Should not raise an exception, should use default fallback dates
    result = await calculate_analytics()

    # Payment with invalid date should still be counted (amount=100)
    # but won't count toward this month's revenue (defaults to 1970)
    assert result["total_revenue"] == 100.0
    assert result["revenue_this_month"] == 0.0  # 1970 date is not this month
    assert result["recent_signups"] == 0  # User with 1970 date is not recent


@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_handles_null_amounts(mock_get_db):
    """Test analytics calculation handles null/missing amounts gracefully"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    now = datetime.utcnow()

    # Mock payments with null/missing amounts
    mock_db.find_documents.side_effect = [
        {"documents": []},  # members
        {"documents": []},  # subscriptions
        {"documents": [
            {"id": str(uuid4()), "status": "succeeded", "amount": 50.00, "created_at": now.isoformat()},
            {"id": str(uuid4()), "status": "succeeded", "amount": None, "created_at": now.isoformat()},
            {"id": str(uuid4()), "status": "succeeded", "created_at": now.isoformat()},  # No amount field
        ]},
        {"documents": []},  # users
        {"documents": []},  # events
        {"documents": []},  # live sessions
        {"documents": []},  # applications
    ]

    result = await calculate_analytics()

    # Payment with amount=50 should be counted
    # Payments with null/missing amounts default to 0
    assert result["total_revenue"] == 50.00
    assert result["revenue_this_month"] == 50.00


# ============================================================================
# RESPONSE MODEL TESTS
# ============================================================================

def test_analytics_response_model_validation():
    """Test AnalyticsResponse model validates correctly"""
    now = datetime.utcnow()

    data = {
        "total_members": 100,
        "active_subscriptions": 50,
        "total_revenue": 5000.00,
        "recent_signups": 10,
        "upcoming_events": 5,
        "active_sessions": 1,
        "pending_applications": 3,
        "total_events_this_month": 4,
        "revenue_this_month": 1000.00,
        "cached": False,
        "generated_at": now,
        "cache_expires_at": now + timedelta(seconds=300)
    }

    response = AnalyticsResponse(**data)

    assert response.total_members == 100
    assert response.active_subscriptions == 50
    assert response.total_revenue == 5000.00
    assert response.cached is False


def test_analytics_response_model_defaults():
    """Test AnalyticsResponse model uses correct defaults"""
    now = datetime.utcnow()

    minimal_data = {
        "total_members": 0,
        "active_subscriptions": 0,
        "total_revenue": 0.0,
        "recent_signups": 0,
        "upcoming_events": 0,
        "active_sessions": 0,
        "generated_at": now
    }

    response = AnalyticsResponse(**minimal_data)

    assert response.pending_applications == 0
    assert response.total_events_this_month == 0
    assert response.revenue_this_month == 0.0
    assert response.cached is False
    assert response.cache_expires_at is None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_query_optimization(mock_get_db):
    """Test that analytics uses optimized queries (filters, limits)"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_db.find_documents.return_value = {"documents": []}

    await calculate_analytics()

    # Verify queries use filters for optimization
    calls = mock_db.find_documents.call_args_list

    # First call should filter for members
    assert calls[0][1]["filters"] == {"role": "member", "is_active": True}
    assert calls[0][1]["limit"] == 10000

    # Second call should filter for active subscriptions
    assert calls[1][1]["filters"] == {"status": "active"}

    # Third call should filter for succeeded payments
    assert calls[2][1]["filters"] == {"status": "succeeded"}


# ============================================================================
# DATE RANGE TESTS
# ============================================================================

@pytest.mark.asyncio
@freeze_time("2025-01-15 12:00:00")
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_recent_signups_30_days(mock_get_db):
    """Test recent signups calculation (last 30 days)"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Users created at different times
    users = [
        {"id": str(uuid4()), "created_at": "2025-01-10T12:00:00"},  # 5 days ago (included)
        {"id": str(uuid4()), "created_at": "2025-01-01T12:00:00"},  # 14 days ago (included)
        {"id": str(uuid4()), "created_at": "2024-12-20T12:00:00"},  # 26 days ago (included)
        {"id": str(uuid4()), "created_at": "2024-12-10T12:00:00"},  # 36 days ago (excluded)
        {"id": str(uuid4()), "created_at": "2024-11-01T12:00:00"},  # 75 days ago (excluded)
    ]

    mock_db.find_documents.side_effect = [
        {"documents": []},  # members
        {"documents": []},  # subscriptions
        {"documents": []},  # payments
        {"documents": users},  # all users
        {"documents": []},  # events
        {"documents": []},  # live sessions
        {"documents": []},  # applications
    ]

    result = await calculate_analytics()

    assert result["recent_signups"] == 3  # Only last 30 days


@pytest.mark.asyncio
@freeze_time("2025-01-15 12:00:00")
@patch('backend.routes.admin.analytics.get_zerodb_client')
async def test_calculate_analytics_events_this_month(mock_get_db):
    """Test events this month calculation"""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Events at different times
    events = [
        {"id": str(uuid4()), "is_published": True, "is_deleted": False,
         "start_date": "2025-01-20T12:00:00"},  # This month (included)
        {"id": str(uuid4()), "is_published": True, "is_deleted": False,
         "start_date": "2025-01-05T12:00:00"},  # This month (included)
        {"id": str(uuid4()), "is_published": True, "is_deleted": False,
         "start_date": "2024-12-28T12:00:00"},  # Last month (excluded)
    ]

    mock_db.find_documents.side_effect = [
        {"documents": []},  # members
        {"documents": []},  # subscriptions
        {"documents": []},  # payments
        {"documents": []},  # users
        {"documents": events},  # events
        {"documents": []},  # live sessions
        {"documents": []},  # applications
    ]

    result = await calculate_analytics()

    assert result["total_events_this_month"] == 2
