"""
Unit Tests for Membership Renewal Functionality

Tests the renewal checkout session creation, webhook processing,
and subscription expiry date extension.
"""

import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from backend.services.stripe_service import StripeService, CheckoutSessionError
from backend.services.webhook_service import WebhookService, WebhookProcessingError
from backend.models.schemas import SubscriptionStatus, SubscriptionTier, PaymentStatus


class TestRenewalCheckoutSession:
    """Tests for renewal checkout session creation"""

    @pytest.fixture
    def stripe_service(self):
        """Create StripeService instance with mocked dependencies"""
        with patch('backend.services.stripe_service.ZeroDBClient'):
            with patch('backend.services.stripe_service.stripe'):
                service = StripeService()
                return service

    @pytest.fixture
    def mock_stripe_session(self):
        """Mock Stripe checkout session response"""
        return Mock(
            id="cs_test_renewal_123",
            url="https://checkout.stripe.com/test/renewal",
            expires_at=int((datetime.utcnow() + timedelta(minutes=30)).timestamp()),
            amount_total=2900,
            currency="usd"
        )

    def test_create_renewal_session_basic_tier(self, stripe_service, mock_stripe_session):
        """Test creating renewal session for basic tier"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())

        with patch('backend.services.stripe_service.stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = mock_stripe_session

            result = stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="basic",
                subscription_id=subscription_id,
                customer_email="test@example.com"
            )

            # Verify session created
            assert result["session_id"] == "cs_test_renewal_123"
            assert result["url"] == "https://checkout.stripe.com/test/renewal"
            assert result["amount"] == 2900  # $29.00
            assert result["tier"] == "basic"
            assert result["mode"] == "subscription"

            # Verify Stripe was called with correct parameters
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["mode"] == "subscription"
            assert call_kwargs["metadata"]["user_id"] == user_id
            assert call_kwargs["metadata"]["subscription_id"] == subscription_id
            assert call_kwargs["metadata"]["tier_id"] == "basic"
            assert call_kwargs["metadata"]["type"] == "renewal"

    def test_create_renewal_session_premium_tier(self, stripe_service, mock_stripe_session):
        """Test creating renewal session for premium tier"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())

        mock_stripe_session.amount_total = 7900

        with patch('backend.services.stripe_service.stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = mock_stripe_session

            result = stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="premium",
                subscription_id=subscription_id,
                customer_email="test@example.com"
            )

            assert result["amount"] == 7900  # $79.00
            assert result["tier"] == "premium"

    def test_create_renewal_session_with_stripe_customer(self, stripe_service, mock_stripe_session):
        """Test renewal uses existing Stripe customer ID"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())
        stripe_customer_id = "cus_test_123"

        with patch('backend.services.stripe_service.stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = mock_stripe_session

            stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="basic",
                subscription_id=subscription_id,
                customer_email="test@example.com",
                stripe_customer_id=stripe_customer_id
            )

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["customer"] == stripe_customer_id
            assert "customer_email" not in call_kwargs

    def test_create_renewal_session_free_tier_error(self, stripe_service):
        """Test renewal fails for free tier"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())

        with pytest.raises(ValueError, match="Free tier cannot be renewed"):
            stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="free",
                subscription_id=subscription_id,
                customer_email="test@example.com"
            )

    def test_create_renewal_session_lifetime_tier_error(self, stripe_service):
        """Test renewal fails for lifetime tier"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())

        with pytest.raises(ValueError, match="Lifetime tier does not require renewal"):
            stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="lifetime",
                subscription_id=subscription_id,
                customer_email="test@example.com"
            )

    def test_create_renewal_session_invalid_tier_error(self, stripe_service):
        """Test renewal fails for invalid tier"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())

        with pytest.raises(ValueError, match="Invalid tier_id"):
            stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="invalid_tier",
                subscription_id=subscription_id,
                customer_email="test@example.com"
            )

    def test_create_renewal_session_custom_urls(self, stripe_service, mock_stripe_session):
        """Test renewal with custom success/cancel URLs"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())
        success_url = "https://example.com/success"
        cancel_url = "https://example.com/cancel"

        with patch('backend.services.stripe_service.stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = mock_stripe_session

            stripe_service.create_renewal_checkout_session(
                user_id=user_id,
                tier_id="basic",
                subscription_id=subscription_id,
                customer_email="test@example.com",
                success_url=success_url,
                cancel_url=cancel_url
            )

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["success_url"] == success_url
            assert call_kwargs["cancel_url"] == cancel_url


class TestRenewalWebhookProcessing:
    """Tests for renewal payment webhook processing"""

    @pytest.fixture
    def webhook_service(self):
        """Create WebhookService instance with mocked dependencies"""
        with patch('backend.services.webhook_service.get_zerodb_client'):
            with patch('backend.services.webhook_service.get_email_service'):
                with patch('backend.services.webhook_service.get_dunning_service'):
                    service = WebhookService()
                    return service

    @pytest.fixture
    def renewal_session_data(self):
        """Mock renewal checkout session data"""
        user_id = str(uuid4())
        subscription_id = str(uuid4())

        return {
            "id": "cs_test_renewal_123",
            "customer": "cus_test_123",
            "subscription": "sub_stripe_123",
            "amount_total": 2900,
            "currency": "usd",
            "payment_intent": "pi_test_123",
            "metadata": {
                "type": "renewal",
                "user_id": user_id,
                "subscription_id": subscription_id,
                "tier_id": "basic"
            }
        }

    @pytest.fixture
    def existing_subscription(self):
        """Mock existing subscription data"""
        now = datetime.utcnow()
        end_date = now + timedelta(days=30)  # Expires in 30 days

        return {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "tier": "basic",
            "status": "active",
            "end_date": end_date.isoformat(),
            "metadata": {}
        }

    @pytest.fixture
    def user_data(self):
        """Mock user data"""
        return {
            "id": str(uuid4()),
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }

    def test_handle_renewal_payment_extends_subscription(
        self, webhook_service, renewal_session_data, existing_subscription, user_data
    ):
        """Test renewal payment extends subscription by 1 year"""
        # Mock database responses
        webhook_service.db.get_document = Mock(side_effect=[
            {"data": existing_subscription},  # First call: get subscription
            {"data": user_data}  # Second call: get user
        ])
        webhook_service.db.update_document = Mock()
        webhook_service.db.create_document = Mock(return_value={"id": str(uuid4())})

        # Mock email service
        webhook_service.email_service.send_renewal_confirmation_email = Mock()

        # Process renewal
        result = webhook_service._handle_renewal_payment(renewal_session_data)

        # Verify result
        assert result["status"] == "success"
        assert result["action"] == "renewal_payment"
        assert result["tier"] == "basic"
        assert result["amount"] == 29.0

        # Verify subscription was updated
        webhook_service.db.update_document.assert_called_once()
        update_call = webhook_service.db.update_document.call_args
        update_data = update_call[0][2]

        assert update_data["status"] == "active"
        assert update_data["stripe_subscription_id"] == "sub_stripe_123"
        assert update_data["canceled_at"] is None

        # Verify new end date is ~1 year from current end date
        new_end_date = datetime.fromisoformat(update_data["end_date"].replace("Z", "+00:00"))
        current_end_date = datetime.fromisoformat(existing_subscription["end_date"])
        expected_end_date = current_end_date + relativedelta(years=1)

        # Allow 1 second tolerance for test execution time
        assert abs((new_end_date - expected_end_date).total_seconds()) < 1

        # Verify payment record was created
        # Look through all calls to find the payments collection call
        payment_call_found = False
        for call in webhook_service.db.create_document.call_args_list:
            if call.kwargs and call.kwargs.get("collection") == "payments":
                payment_data = call.kwargs.get("data")
                payment_call_found = True
                break
            elif call.args and len(call.args) >= 2 and call.args[0] == "payments":
                payment_data = call.args[1]
                payment_call_found = True
                break

        assert payment_call_found, "Payment record creation not found in create_document calls"
        assert payment_data["amount"] == 29.0
        assert payment_data["description"] == "Membership renewal: basic tier"
        assert payment_data["metadata"]["type"] == "renewal"

        # Verify email was sent
        webhook_service.email_service.send_renewal_confirmation_email.assert_called_once()

    def test_handle_renewal_payment_expired_subscription(
        self, webhook_service, renewal_session_data, existing_subscription, user_data
    ):
        """Test renewal of expired subscription starts from now"""
        # Set subscription as expired 30 days ago
        now = datetime.utcnow()
        expired_date = now - timedelta(days=30)
        existing_subscription["end_date"] = expired_date.isoformat()
        existing_subscription["status"] = "expired"

        webhook_service.db.get_document = Mock(side_effect=[
            {"data": existing_subscription},
            {"data": user_data}
        ])
        webhook_service.db.update_document = Mock()
        webhook_service.db.create_document = Mock(return_value={"id": str(uuid4())})
        webhook_service.email_service.send_renewal_confirmation_email = Mock()

        result = webhook_service._handle_renewal_payment(renewal_session_data)

        # Verify new end date is ~1 year from now (not from expired date)
        update_call = webhook_service.db.update_document.call_args
        update_data = update_call[0][2]
        new_end_date = datetime.fromisoformat(update_data["end_date"].replace("Z", "+00:00"))
        expected_end_date = now + relativedelta(years=1)

        # Allow 2 seconds tolerance
        assert abs((new_end_date - expected_end_date).total_seconds()) < 2

    def test_handle_renewal_payment_missing_subscription(
        self, webhook_service, renewal_session_data
    ):
        """Test renewal fails if subscription not found"""
        webhook_service.db.get_document = Mock(return_value={"data": None})

        with pytest.raises(WebhookProcessingError, match="Subscription .* not found"):
            webhook_service._handle_renewal_payment(renewal_session_data)

    def test_handle_renewal_payment_missing_metadata(self, webhook_service):
        """Test renewal fails if required metadata missing"""
        invalid_session = {
            "id": "cs_test_123",
            "metadata": {}  # Missing user_id and subscription_id
        }

        with pytest.raises(WebhookProcessingError, match="Missing user_id or subscription_id"):
            webhook_service._handle_renewal_payment(invalid_session)


class TestRenewalEndpoint:
    """Integration tests for the renewal API endpoint"""

    def test_create_renewal_session_endpoint_requires_auth(self):
        """Test endpoint requires authentication"""
        # This would be an integration test with the FastAPI test client
        # Placeholder for actual implementation
        pass

    def test_create_renewal_session_endpoint_validates_active_subscription(self):
        """Test endpoint validates user has active subscription"""
        # This would be an integration test with the FastAPI test client
        # Placeholder for actual implementation
        pass

    def test_create_renewal_session_endpoint_success(self):
        """Test successful renewal session creation"""
        # This would be an integration test with the FastAPI test client
        # Placeholder for actual implementation
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
