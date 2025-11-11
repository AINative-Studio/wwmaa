"""
Test Suite for Billing Routes

Tests for subscription management and Stripe Customer Portal integration.
Covers subscription details retrieval and portal session creation.

Test Coverage:
- Portal session creation (success and error cases)
- Subscription details retrieval (success and error cases)
- Access control (members only)
- Stripe API integration (mocked)
- ZeroDB query integration (mocked)
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import stripe

from backend.routes.billing import router, create_portal_session, get_subscription_details
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


@pytest.fixture
def mock_stripe_subscription():
    """Mock Stripe subscription object"""
    mock_card = Mock()
    mock_card.brand = "visa"
    mock_card.last4 = "4242"
    mock_card.exp_month = 12
    mock_card.exp_year = 2025

    mock_pm = Mock()
    mock_pm.id = "pm_123"
    mock_pm.type = "card"
    mock_pm.card = mock_card

    mock_sub = Mock()
    mock_sub.id = "sub_stripe_123"
    mock_sub.default_payment_method = mock_pm
    mock_sub.latest_invoice = None

    return mock_sub


@pytest.fixture
def mock_stripe_invoice():
    """Mock Stripe invoice object"""
    mock_invoice = Mock()
    mock_invoice.id = "in_123"
    mock_invoice.number = "INV-001"
    mock_invoice.amount_paid = 2999  # cents
    mock_invoice.currency = "usd"
    mock_invoice.status = "paid"
    mock_invoice.created = int(datetime.utcnow().timestamp())
    mock_invoice.invoice_pdf = "https://example.com/invoice.pdf"
    mock_invoice.hosted_invoice_url = "https://example.com/invoice"

    return mock_invoice


@pytest.fixture
def mock_upcoming_invoice():
    """Mock Stripe upcoming invoice"""
    mock_invoice = Mock()
    mock_invoice.amount_due = 2999  # cents
    mock_invoice.currency = "usd"
    mock_invoice.next_payment_attempt = int((datetime.utcnow() + timedelta(days=15)).timestamp())

    return mock_invoice


# ============================================================================
# PORTAL SESSION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_portal_session_success(mock_current_user, mock_subscription_data):
    """Test successful portal session creation"""
    # Mock ZeroDB response
    mock_zerodb_response = {
        "documents": [mock_subscription_data]
    }

    # Mock Stripe portal session
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

            # Verify ZeroDB was queried correctly
            mock_zerodb.query_documents.assert_called_once_with(
                collection="subscriptions",
                filters={"user_id": {"$eq": "user_123"}},
                limit=1
            )


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
        "stripe_customer_id": None  # Missing customer ID
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


@pytest.mark.asyncio
async def test_create_portal_session_stripe_error(mock_current_user, mock_subscription_data):
    """Test portal session creation when Stripe API fails"""
    mock_zerodb_response = {"documents": [mock_subscription_data]}

    request = PortalSessionRequest(return_url="https://example.com/dashboard")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.billing_portal.Session.create', side_effect=stripe.error.StripeError("API Error")):
            with pytest.raises(HTTPException) as exc_info:
                await create_portal_session(request, mock_current_user)

            assert exc_info.value.status_code == 500
            assert "Failed to create billing portal session" in exc_info.value.detail


# ============================================================================
# SUBSCRIPTION DETAILS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_subscription_details_success(
    mock_current_user,
    mock_subscription_data,
    mock_stripe_subscription,
    mock_stripe_invoice,
    mock_upcoming_invoice
):
    """Test successful subscription details retrieval"""
    mock_zerodb_response = {"documents": [mock_subscription_data]}

    # Mock Stripe invoices list
    mock_invoices_list = Mock()
    mock_invoices_list.data = [mock_stripe_invoice]

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.Subscription.retrieve', return_value=mock_stripe_subscription):
            with patch('stripe.Invoice.upcoming', return_value=mock_upcoming_invoice):
                with patch('stripe.Invoice.list', return_value=mock_invoices_list):
                    response = await get_subscription_details(mock_current_user)

                    # Verify response structure
                    assert "subscription" in response
                    assert "payment_method" in response
                    assert "upcoming_invoice" in response
                    assert "recent_invoices" in response

                    # Verify subscription data
                    sub = response["subscription"]
                    assert sub["id"] == "sub_123"
                    assert sub["tier"] == "premium"
                    assert sub["status"] == "active"
                    assert sub["price"] == 29.99

                    # Verify payment method
                    pm = response["payment_method"]
                    assert pm["brand"] == "visa"
                    assert pm["last4"] == "4242"

                    # Verify upcoming invoice
                    upcoming = response["upcoming_invoice"]
                    assert upcoming["amount_due"] == 29.99  # Converted from cents

                    # Verify recent invoices
                    assert len(response["recent_invoices"]) == 1
                    invoice = response["recent_invoices"][0]
                    assert invoice["number"] == "INV-001"
                    assert invoice["amount_paid"] == 29.99  # Converted from cents


@pytest.mark.asyncio
async def test_get_subscription_details_no_subscription(mock_current_user):
    """Test subscription details retrieval when user has no subscription"""
    mock_zerodb_response = {"data": []}

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with pytest.raises(HTTPException) as exc_info:
            await get_subscription_details(mock_current_user)

        assert exc_info.value.status_code == 404
        assert "No subscription found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_subscription_details_without_stripe(mock_current_user, mock_subscription_data):
    """Test subscription details retrieval when subscription has no Stripe ID"""
    # Remove Stripe IDs
    subscription_without_stripe = mock_subscription_data.copy()
    subscription_without_stripe["stripe_subscription_id"] = None

    mock_zerodb_response = {"data": [subscription_without_stripe]}

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        response = await get_subscription_details(mock_current_user)

        # Should return subscription data without Stripe details
        assert "subscription" in response
        assert response["payment_method"] is None
        assert response["upcoming_invoice"] is None
        assert response["recent_invoices"] == []


@pytest.mark.asyncio
async def test_get_subscription_details_stripe_failure_graceful(
    mock_current_user,
    mock_subscription_data
):
    """Test that Stripe failures don't break subscription details retrieval"""
    mock_zerodb_response = {"documents": [mock_subscription_data]}

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.Subscription.retrieve', side_effect=stripe.error.StripeError("API Error")):
            response = await get_subscription_details(mock_current_user)

            # Should still return subscription data from ZeroDB
            assert "subscription" in response
            assert response["subscription"]["id"] == "sub_123"
            # But no Stripe-specific details
            assert response["payment_method"] is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_portal_session_end_to_end(mock_current_user, mock_subscription_data):
    """Test complete portal session creation flow"""
    mock_zerodb_response = {"documents": [mock_subscription_data]}
    mock_portal_session = Mock()
    mock_portal_session.url = "https://billing.stripe.com/session/test_123"

    request = PortalSessionRequest(return_url="https://wwmaa.com/dashboard/subscription")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.billing_portal.Session.create', return_value=mock_portal_session) as mock_create:
            response = await create_portal_session(request, mock_current_user)

            # Verify Stripe was called with correct parameters
            mock_create.assert_called_once_with(
                customer="cus_stripe_123",
                return_url="https://wwmaa.com/dashboard/subscription"
            )

            # Verify response
            assert response.url == "https://billing.stripe.com/session/test_123"


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_subscriptions_returns_first(mock_current_user):
    """Test that when user has multiple subscriptions, first is returned"""
    subscription1 = {"id": "sub_1", "user_id": "user_123", "stripe_customer_id": "cus_1"}
    subscription2 = {"id": "sub_2", "user_id": "user_123", "stripe_customer_id": "cus_2"}

    mock_zerodb_response = {"documents": [subscription1, subscription2]}
    mock_portal_session = Mock()
    mock_portal_session.url = "https://billing.stripe.com/session/test_123"

    request = PortalSessionRequest(return_url="https://example.com")

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        with patch('stripe.billing_portal.Session.create', return_value=mock_portal_session) as mock_create:
            response = await create_portal_session(request, mock_current_user)

            # Should use first subscription's customer ID
            mock_create.assert_called_once_with(
                customer="cus_1",
                return_url="https://example.com"
            )


@pytest.mark.asyncio
async def test_subscription_with_special_characters_in_tier(mock_current_user):
    """Test subscription details with special characters in tier name"""
    subscription_data = {
        "id": "sub_123",
        "user_id": "user_123",
        "tier": "premium-plus-2024",
        "status": "active",
        "price": 49.99,
        "currency": "usd",
        "stripe_subscription_id": None,
        "current_period_start": datetime.utcnow().isoformat(),
        "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    mock_zerodb_response = {"documents": [subscription_data]}

    with patch('backend.routes.billing.ZeroDBClient') as mock_zerodb_class:
        mock_zerodb = Mock()
        mock_zerodb.query_documents.return_value = mock_zerodb_response
        mock_zerodb_class.return_value = mock_zerodb

        response = await get_subscription_details(mock_current_user)

        assert response["subscription"]["tier"] == "premium-plus-2024"
        assert response["subscription"]["tier_name"] == "Premium-Plus-2024"
