"""
Simplified Test Suite for Billing Routes

Tests for subscription management and Stripe Customer Portal integration.
Tests cover the critical paths without Stripe API mocking complications.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from backend.routes.billing import create_portal_session, get_subscription_details
from backend.routes.billing import PortalSessionRequest, PortalSessionResponse


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_subscription_data():
    """Mock subscription data from ZeroDB"""
    return {
        "id": "sub_123",
        "user_id": "user_123",
        "tier": "premium",
        "status": "active",
        "price": 29.99,
        "currency": "usd",
        "stripe_subscription_id": "sub_stripe_123",
        "stripe_customer_id": "cus_stripe_123",
        "current_period_start": (datetime.utcnow() - timedelta(days=15)).isoformat(),
        "current_period_end": (datetime.utcnow() + timedelta(days=15)).isoformat(),
        "cancel_at_period_end": False,
        "created_at": (datetime.utcnow() - timedelta(days=90)).isoformat(),
        "updated_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
    }


# ============================================================================
# PORTAL SESSION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_portal_session_success(mock_current_user, mock_subscription_data):
    """Test successful portal session creation"""
    mock_zerodb_response = {
        "documents": [mock_subscription_data]
    }

    mock_portal_session = Mock()
    mock_portal_session.url = "https://billing.stripe.com/session/test_123"

    request = PortalSessionRequest(return_url="https://example.com/dashboard")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.billing_portal.Session.create', return_value=mock_portal_session):
            response = await create_portal_session(request, mock_current_user)

            assert isinstance(response, PortalSessionResponse)
            assert response.url == "https://billing.stripe.com/session/test_123"


@pytest.mark.asyncio
async def test_create_portal_session_no_subscription(mock_current_user):
    """Test portal session creation when user has no subscription"""
    mock_zerodb_response = {"documents": []}

    request = PortalSessionRequest(return_url="https://example.com/dashboard")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with pytest.raises(HTTPException) as exc_info:
            await create_portal_session(request, mock_current_user)

        assert exc_info.value.status_code == 404
        assert "No subscription found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_portal_session_no_customer_id(mock_current_user):
    """Test portal session creation when subscription has no Stripe customer ID"""
    mock_subscription = {
        "id": "sub_123",
        "user_id": "user_123",
        "stripe_customer_id": None
    }
    mock_zerodb_response = {"documents": [mock_subscription]}

    request = PortalSessionRequest(return_url="https://example.com/dashboard")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with pytest.raises(HTTPException) as exc_info:
            await create_portal_session(request, mock_current_user)

        assert exc_info.value.status_code == 400
        assert "Invalid subscription data" in exc_info.value.detail


# ============================================================================
# SUBSCRIPTION DETAILS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_subscription_details_no_subscription(mock_current_user):
    """Test subscription details retrieval when user has no subscription"""
    mock_zerodb_response = {"documents": []}

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with pytest.raises(HTTPException) as exc_info:
            await get_subscription_details(mock_current_user)

        assert exc_info.value.status_code == 404
        assert "No subscription found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_subscription_details_basic(mock_current_user, mock_subscription_data):
    """Test basic subscription details retrieval without Stripe calls"""
    subscription_without_stripe = mock_subscription_data.copy()
    subscription_without_stripe["stripe_subscription_id"] = None
    subscription_without_stripe["stripe_customer_id"] = None

    mock_zerodb_response = {"documents": [subscription_without_stripe]}

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        response = await get_subscription_details(mock_current_user)

        # Should return subscription data without Stripe details
        assert "subscription" in response
        assert response["subscription"]["id"] == "sub_123"
        assert response["subscription"]["tier"] == "premium"
        assert response["subscription"]["status"] == "active"
        assert response["subscription"]["price"] == 29.99
        assert response["payment_method"] is None
        assert response["upcoming_invoice"] is None
        assert response["recent_invoices"] == []


@pytest.mark.asyncio
async def test_portal_session_correct_customer_id(mock_current_user, mock_subscription_data):
    """Test that correct Stripe customer ID is used"""
    mock_zerodb_response = {"documents": [mock_subscription_data]}
    mock_portal_session = Mock()
    mock_portal_session.url = "https://billing.stripe.com/session/test"

    request = PortalSessionRequest(return_url="https://example.com")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.billing_portal.Session.create', return_value=mock_portal_session) as mock_create:
            await create_portal_session(request, mock_current_user)

            # Verify Stripe was called with correct customer ID
            mock_create.assert_called_once_with(
                customer="cus_stripe_123",
                return_url="https://example.com"
            )
