"""
Tests for Checkout Routes

Tests the checkout API endpoints for session creation and payment processing.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from backend.app import app
from backend.services.stripe_service import CheckoutSessionError


client = TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "user_id": "user_123",
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_auth_token():
    """Mock JWT token"""
    return "Bearer test_token_123"


class TestCreateCheckoutSessionEndpoint:
    """Test POST /api/checkout/create-session endpoint"""

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.get_stripe_service')
    @patch('backend.routes.checkout.ZeroDBClient')
    def test_create_checkout_session_success(
        self,
        mock_zerodb_class,
        mock_get_stripe,
        mock_get_user,
        mock_current_user
    ):
        """Test successful checkout session creation"""
        # Mock user
        mock_get_user.return_value = mock_current_user

        # Mock application
        mock_db = Mock()
        mock_db.get_document.return_value = {
            "data": {
                "id": "app_123",
                "user_id": "user_123",
                "status": "approved",
                "payment_completed": False,
                "email": "test@example.com",
                "subscription_tier": "basic"
            }
        }
        mock_zerodb_class.return_value = mock_db

        # Mock Stripe service
        mock_stripe = Mock()
        mock_stripe.create_checkout_session.return_value = {
            "session_id": "cs_test_123",
            "url": "https://checkout.stripe.com/test",
            "amount": 2900,
            "currency": "usd",
            "tier": "basic",
            "mode": "subscription",
            "expires_at": 1234567890
        }
        mock_get_stripe.return_value = mock_stripe

        # Make request
        response = client.post(
            "/api/checkout/create-session",
            json={
                "application_id": "app_123",
                "tier_id": "basic"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "cs_test_123"
        assert data["url"] == "https://checkout.stripe.com/test"
        assert data["tier"] == "basic"
        assert data["amount"] == 2900

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.ZeroDBClient')
    def test_create_checkout_session_application_not_found(
        self,
        mock_zerodb_class,
        mock_get_user,
        mock_current_user
    ):
        """Test error when application not found"""
        mock_get_user.return_value = mock_current_user

        mock_db = Mock()
        mock_db.get_document.return_value = {"data": None}
        mock_zerodb_class.return_value = mock_db

        response = client.post(
            "/api/checkout/create-session",
            json={
                "application_id": "invalid_app",
                "tier_id": "basic"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.ZeroDBClient')
    def test_create_checkout_session_wrong_user(
        self,
        mock_zerodb_class,
        mock_get_user,
        mock_current_user
    ):
        """Test error when user doesn't own application"""
        mock_get_user.return_value = mock_current_user

        mock_db = Mock()
        mock_db.get_document.return_value = {
            "data": {
                "user_id": "different_user",
                "status": "approved"
            }
        }
        mock_zerodb_class.return_value = mock_db

        response = client.post(
            "/api/checkout/create-session",
            json={
                "application_id": "app_123",
                "tier_id": "basic"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.ZeroDBClient')
    def test_create_checkout_session_not_approved(
        self,
        mock_zerodb_class,
        mock_get_user,
        mock_current_user
    ):
        """Test error when application not approved"""
        mock_get_user.return_value = mock_current_user

        mock_db = Mock()
        mock_db.get_document.return_value = {
            "data": {
                "user_id": "user_123",
                "status": "submitted"
            }
        }
        mock_zerodb_class.return_value = mock_db

        response = client.post(
            "/api/checkout/create-session",
            json={
                "application_id": "app_123",
                "tier_id": "basic"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 400
        assert "approved" in response.json()["detail"].lower()

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.ZeroDBClient')
    def test_create_checkout_session_already_paid(
        self,
        mock_zerodb_class,
        mock_get_user,
        mock_current_user
    ):
        """Test error when payment already completed"""
        mock_get_user.return_value = mock_current_user

        mock_db = Mock()
        mock_db.get_document.return_value = {
            "data": {
                "user_id": "user_123",
                "status": "approved",
                "payment_completed": True
            }
        }
        mock_zerodb_class.return_value = mock_db

        response = client.post(
            "/api/checkout/create-session",
            json={
                "application_id": "app_123",
                "tier_id": "basic"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 400
        assert "already completed" in response.json()["detail"].lower()


class TestRetrieveCheckoutSession:
    """Test POST /api/checkout/retrieve-session endpoint"""

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.get_stripe_service')
    def test_retrieve_session_success(
        self,
        mock_get_stripe,
        mock_get_user,
        mock_current_user
    ):
        """Test successful session retrieval"""
        mock_get_user.return_value = mock_current_user

        mock_stripe = Mock()
        mock_stripe.retrieve_checkout_session.return_value = {
            "id": "cs_test_123",
            "payment_status": "paid",
            "customer_email": "test@example.com",
            "amount_total": 2900,
            "currency": "usd",
            "status": "complete"
        }
        mock_get_stripe.return_value = mock_stripe

        response = client.post(
            "/api/checkout/retrieve-session",
            json={"session_id": "cs_test_123"},
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "cs_test_123"
        assert data["payment_status"] == "paid"


class TestProcessPayment:
    """Test POST /api/checkout/process-payment endpoint"""

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.get_stripe_service')
    def test_process_payment_success(
        self,
        mock_get_stripe,
        mock_get_user,
        mock_current_user
    ):
        """Test successful payment processing"""
        mock_get_user.return_value = mock_current_user

        mock_stripe = Mock()
        mock_stripe.process_successful_payment.return_value = {
            "success": True,
            "user_id": "user_123",
            "application_id": "app_123",
            "subscription_id": "sub_123",
            "tier": "basic",
            "amount": 29.0
        }
        mock_get_stripe.return_value = mock_stripe

        response = client.post(
            "/api/checkout/process-payment",
            json={"session_id": "cs_test_123"},
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "user_123"

    @patch('backend.routes.checkout.get_current_user')
    @patch('backend.routes.checkout.get_stripe_service')
    def test_process_payment_wrong_user(
        self,
        mock_get_stripe,
        mock_get_user,
        mock_current_user
    ):
        """Test error when processing payment for different user"""
        mock_get_user.return_value = mock_current_user

        mock_stripe = Mock()
        mock_stripe.process_successful_payment.return_value = {
            "user_id": "different_user"
        }
        mock_get_stripe.return_value = mock_stripe

        response = client.post(
            "/api/checkout/process-payment",
            json={"session_id": "cs_test_123"},
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 403


class TestGetTierPricing:
    """Test GET /api/checkout/tier-pricing/{tier_id} endpoint"""

    @patch('backend.routes.checkout.get_stripe_service')
    def test_get_tier_pricing_success(self, mock_get_stripe):
        """Test successful tier pricing retrieval"""
        mock_stripe = Mock()
        mock_stripe.get_tier_pricing.return_value = {
            "tier": "basic",
            "amount_cents": 2900,
            "amount_dollars": 29.0,
            "currency": "USD",
            "interval": "month",
            "features": {}
        }
        mock_get_stripe.return_value = mock_stripe

        response = client.get("/api/checkout/tier-pricing/basic")

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "basic"
        assert data["amount_dollars"] == 29.0

    @patch('backend.routes.checkout.get_stripe_service')
    def test_get_tier_pricing_invalid_tier(self, mock_get_stripe):
        """Test error for invalid tier"""
        mock_stripe = Mock()
        mock_stripe.get_tier_pricing.side_effect = ValueError("Invalid tier")
        mock_get_stripe.return_value = mock_stripe

        response = client.get("/api/checkout/tier-pricing/invalid")

        assert response.status_code == 400


class TestHealthCheck:
    """Test GET /api/checkout/health endpoint"""

    @patch('backend.routes.checkout.get_stripe_service')
    def test_health_check(self, mock_get_stripe):
        """Test checkout service health check"""
        mock_stripe = Mock()
        mock_stripe.api_key = "test_key"
        mock_get_stripe.return_value = mock_stripe

        response = client.get("/api/checkout/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "checkout"
        assert data["stripe_configured"] is True


pytestmark = pytest.mark.unit
