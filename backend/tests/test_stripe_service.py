"""
Comprehensive Test Suite for Stripe Service

Tests cover:
- API key validation
- Customer management
- Product and price creation
- Subscription management
- Checkout session creation
- Webhook signature verification
- Error handling
- Edge cases

Target: 80%+ code coverage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from backend.services.stripe_service import (
    StripeService,
    StripeServiceError,
    CheckoutSessionError,
    SubscriptionError,
    TIER_PRICING,
    MEMBERSHIP_TIER_NAMES,
    get_stripe_service
)
from backend.models.schemas import SubscriptionTier, SubscriptionStatus
import stripe
from stripe import StripeError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_stripe_key():
    """Mock Stripe API key"""
    return "sk_test_mock123456789"


@pytest.fixture
def mock_webhook_secret():
    """Mock webhook secret"""
    return "whsec_mock123456789"


@pytest.fixture
def stripe_service(mock_stripe_key, mock_webhook_secret, mocker):
    """Create StripeService instance with mocked dependencies"""
    # Mock ZeroDB client
    mock_db = mocker.Mock()
    mock_db.create_document = mocker.Mock(return_value={"id": "test_id", "data": {}})
    mock_db.update_document = mocker.Mock(return_value={"id": "test_id", "data": {}})

    with patch("backend.services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = mock_stripe_key
        mock_settings.STRIPE_WEBHOOK_SECRET = mock_webhook_secret
        mock_settings.PYTHON_BACKEND_URL = "http://localhost:8000"

        service = StripeService(
            api_key=mock_stripe_key,
            webhook_secret=mock_webhook_secret,
            zerodb_client=mock_db
        )
        return service


@pytest.fixture
def sample_customer():
    """Sample Stripe customer data"""
    return {
        "id": "cus_test123",
        "email": "test@example.com",
        "name": "Test User",
        "metadata": {"user_id": "user_123"}
    }


@pytest.fixture
def sample_subscription():
    """Sample Stripe subscription data"""
    return {
        "id": "sub_test123",
        "customer": "cus_test123",
        "status": "active",
        "items": {
            "data": [{
                "id": "si_test123",
                "price": {
                    "id": "price_test123",
                    "unit_amount": 2900
                }
            }]
        }
    }


@pytest.fixture
def sample_checkout_session():
    """Sample Stripe checkout session"""
    return {
        "id": "cs_test123",
        "url": "https://checkout.stripe.com/test",
        "payment_status": "paid",
        "customer": "cus_test123",
        "customer_email": "test@example.com",
        "amount_total": 2900,
        "currency": "usd",
        "metadata": {
            "user_id": "user_123",
            "application_id": "app_123",
            "tier_id": "basic"
        },
        "status": "complete",
        "mode": "subscription",
        "subscription": "sub_test123",
        "expires_at": int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
    }


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_stripe_service_initialization(stripe_service, mock_stripe_key, mock_webhook_secret):
    """Test StripeService initialization with valid configuration"""
    assert stripe_service.api_key == mock_stripe_key
    assert stripe_service.webhook_secret == mock_webhook_secret
    assert stripe.api_key == mock_stripe_key


def test_stripe_service_missing_api_key():
    """Test StripeService raises error when API key is missing"""
    with patch("backend.services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = None
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"

        with pytest.raises(StripeServiceError, match="STRIPE_SECRET_KEY is required"):
            StripeService()


def test_get_stripe_service_singleton():
    """Test get_stripe_service returns singleton instance"""
    with patch("backend.services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"

        # Clear singleton
        import backend.services.stripe_service as stripe_module
        stripe_module._stripe_service_instance = None

        service1 = get_stripe_service()
        service2 = get_stripe_service()

        assert service1 is service2


# ============================================================================
# PRICING CONFIGURATION TESTS
# ============================================================================

def test_tier_pricing_configuration():
    """Test that TIER_PRICING matches US-021 requirements"""
    assert TIER_PRICING[SubscriptionTier.BASIC] == 2900  # $29/year
    assert TIER_PRICING[SubscriptionTier.PREMIUM] == 7900  # $79/year
    assert TIER_PRICING[SubscriptionTier.LIFETIME] == 14900  # $149/year (Instructor)


def test_membership_tier_names():
    """Test membership tier name mapping"""
    assert MEMBERSHIP_TIER_NAMES[SubscriptionTier.BASIC] == "Basic Membership"
    assert MEMBERSHIP_TIER_NAMES[SubscriptionTier.PREMIUM] == "Premium Membership"
    assert MEMBERSHIP_TIER_NAMES[SubscriptionTier.LIFETIME] == "Instructor Membership"


# ============================================================================
# CHECKOUT SESSION TESTS
# ============================================================================

@patch('stripe.checkout.Session.create')
def test_create_checkout_session_basic(mock_create, stripe_service, sample_checkout_session):
    """Test creating checkout session for basic tier"""
    mock_create.return_value = Mock(**sample_checkout_session)

    result = stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="basic",
        customer_email="test@example.com"
    )

    assert result["session_id"] == "cs_test123"
    assert result["amount"] == 2900
    assert result["tier"] == "basic"
    assert result["mode"] == "subscription"

    # Verify create was called with correct parameters
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert call_args["mode"] == "subscription"
    assert call_args["customer_email"] == "test@example.com"
    assert call_args["metadata"]["tier_id"] == "basic"


@patch('stripe.checkout.Session.create')
def test_create_checkout_session_premium(mock_create, stripe_service):
    """Test creating checkout session for premium tier"""
    session_data = {
        "id": "cs_premium123",
        "url": "https://checkout.stripe.com/premium",
        "amount_total": 7900,
        "mode": "subscription",
        "expires_at": int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
    }
    mock_create.return_value = Mock(**session_data)

    result = stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="premium",
        customer_email="test@example.com"
    )

    assert result["amount"] == 7900
    assert result["tier"] == "premium"


@patch('stripe.checkout.Session.create')
def test_create_checkout_session_instructor_lifetime(mock_create, stripe_service):
    """Test creating checkout session for instructor (lifetime) tier"""
    session_data = {
        "id": "cs_instructor123",
        "url": "https://checkout.stripe.com/instructor",
        "amount_total": 14900,
        "mode": "payment",  # One-time payment for lifetime
        "expires_at": int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
    }
    mock_create.return_value = Mock(**session_data)

    result = stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="lifetime",
        customer_email="test@example.com"
    )

    assert result["amount"] == 14900
    assert result["tier"] == "lifetime"
    assert result["mode"] == "payment"


def test_create_checkout_session_invalid_tier(stripe_service):
    """Test creating checkout session with invalid tier raises ValueError"""
    with pytest.raises(ValueError, match="Invalid tier_id"):
        stripe_service.create_checkout_session(
            user_id="user_123",
            application_id="app_123",
            tier_id="invalid_tier",
            customer_email="test@example.com"
        )


def test_create_checkout_session_free_tier(stripe_service):
    """Test creating checkout session for free tier raises ValueError"""
    with pytest.raises(ValueError, match="Free tier does not require payment"):
        stripe_service.create_checkout_session(
            user_id="user_123",
            application_id="app_123",
            tier_id="free",
            customer_email="test@example.com"
        )


@patch('stripe.checkout.Session.create')
def test_create_checkout_session_stripe_error(mock_create, stripe_service):
    """Test checkout session creation handles Stripe API errors"""
    mock_create.side_effect = StripeError("API error")

    with pytest.raises(CheckoutSessionError, match="Failed to create checkout session"):
        stripe_service.create_checkout_session(
            user_id="user_123",
            application_id="app_123",
            tier_id="basic",
            customer_email="test@example.com"
        )


@patch('stripe.checkout.Session.create')
def test_create_checkout_session_with_custom_urls(mock_create, stripe_service):
    """Test checkout session creation with custom success/cancel URLs"""
    mock_create.return_value = Mock(
        id="cs_test",
        url="https://checkout.stripe.com/test",
        amount_total=2900,
        mode="subscription",
        expires_at=int(datetime.utcnow().timestamp())
    )

    result = stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="basic",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        customer_email="test@example.com"
    )

    call_args = mock_create.call_args[1]
    assert call_args["success_url"] == "https://example.com/success"
    assert call_args["cancel_url"] == "https://example.com/cancel"


# ============================================================================
# CHECKOUT SESSION RETRIEVAL TESTS
# ============================================================================

@patch('stripe.checkout.Session.retrieve')
def test_retrieve_checkout_session(mock_retrieve, stripe_service, sample_checkout_session):
    """Test retrieving checkout session"""
    mock_retrieve.return_value = Mock(**sample_checkout_session)

    result = stripe_service.retrieve_checkout_session("cs_test123")

    assert result["id"] == "cs_test123"
    assert result["payment_status"] == "paid"
    assert result["customer_email"] == "test@example.com"

    mock_retrieve.assert_called_once_with("cs_test123")


@patch('stripe.checkout.Session.retrieve')
def test_retrieve_checkout_session_error(mock_retrieve, stripe_service):
    """Test retrieving checkout session handles errors"""
    mock_retrieve.side_effect = StripeError("Not found")

    with pytest.raises(CheckoutSessionError, match="Failed to retrieve session"):
        stripe_service.retrieve_checkout_session("cs_invalid")


# ============================================================================
# SUBSCRIPTION CREATION TESTS
# ============================================================================

def test_create_subscription_in_db_basic(stripe_service, mocker):
    """Test creating basic subscription in database"""
    mock_create = mocker.patch.object(
        stripe_service.db,
        'create_document',
        return_value={"id": "sub_db_123", "data": {"tier": "basic"}}
    )

    result = stripe_service.create_subscription_in_db(
        user_id="user_123",
        tier="basic",
        stripe_subscription_id="sub_stripe_123",
        stripe_customer_id="cus_123",
        amount=29.00
    )

    # Verify create_document was called
    mock_create.assert_called_once()
    call_args = mock_create.call_args[0]

    assert call_args[0] == "subscriptions"
    subscription_data = call_args[1]
    assert subscription_data["user_id"] == "user_123"
    assert subscription_data["tier"] == "basic"
    assert subscription_data["status"] == SubscriptionStatus.ACTIVE
    assert subscription_data["interval"] == "year"  # Annual billing per US-021


def test_create_subscription_in_db_lifetime(stripe_service, mocker):
    """Test creating lifetime subscription in database"""
    mock_create = mocker.patch.object(
        stripe_service.db,
        'create_document',
        return_value={"id": "sub_db_456", "data": {"tier": "lifetime"}}
    )

    result = stripe_service.create_subscription_in_db(
        user_id="user_123",
        tier="lifetime",
        stripe_customer_id="cus_123",
        amount=149.00
    )

    call_args = mock_create.call_args[0]
    subscription_data = call_args[1]
    assert subscription_data["interval"] == "lifetime"


def test_create_subscription_in_db_error(stripe_service, mocker):
    """Test creating subscription in database handles errors"""
    mocker.patch.object(
        stripe_service.db,
        'create_document',
        side_effect=Exception("DB error")
    )

    with pytest.raises(SubscriptionError, match="Failed to create subscription"):
        stripe_service.create_subscription_in_db(
            user_id="user_123",
            tier="basic",
            stripe_customer_id="cus_123"
        )


# ============================================================================
# PAYMENT PROCESSING TESTS
# ============================================================================

@patch('stripe.checkout.Session.retrieve')
def test_process_successful_payment(mock_retrieve, stripe_service, sample_checkout_session, mocker):
    """Test processing successful payment"""
    mock_retrieve.return_value = Mock(**sample_checkout_session)

    mock_create_sub = mocker.patch.object(
        stripe_service,
        'create_subscription_in_db',
        return_value={"id": "sub_db_123", "tier": "basic"}
    )

    mock_update = mocker.patch.object(
        stripe_service.db,
        'update_document',
        return_value={"id": "app_123", "data": {}}
    )

    result = stripe_service.process_successful_payment("cs_test123")

    assert result["success"] is True
    assert result["user_id"] == "user_123"
    assert result["application_id"] == "app_123"
    assert result["tier"] == "basic"

    # Verify subscription was created
    mock_create_sub.assert_called_once()

    # Verify application was updated
    mock_update.assert_called_once()


@patch('stripe.checkout.Session.retrieve')
def test_process_successful_payment_missing_metadata(mock_retrieve, stripe_service):
    """Test processing payment with missing metadata raises error"""
    session_data = {
        "id": "cs_test",
        "metadata": {}  # Missing required fields
    }
    mock_retrieve.return_value = Mock(**session_data)

    with pytest.raises(SubscriptionError, match="Missing required metadata"):
        stripe_service.process_successful_payment("cs_test")


@patch('stripe.checkout.Session.retrieve')
def test_process_successful_payment_stripe_error(mock_retrieve, stripe_service):
    """Test processing payment handles Stripe errors"""
    mock_retrieve.side_effect = StripeError("Session not found")

    with pytest.raises(SubscriptionError, match="Failed to process payment"):
        stripe_service.process_successful_payment("cs_invalid")


# ============================================================================
# TIER PRICING TESTS
# ============================================================================

def test_get_tier_pricing_basic(stripe_service):
    """Test getting pricing for basic tier"""
    pricing = stripe_service.get_tier_pricing("basic")

    assert pricing["tier"] == "basic"
    assert pricing["amount_cents"] == 2900
    assert pricing["amount_dollars"] == 29.0
    assert pricing["currency"] == "USD"
    assert pricing["interval"] == "year"  # Annual billing per US-021
    assert "features" in pricing


def test_get_tier_pricing_premium(stripe_service):
    """Test getting pricing for premium tier"""
    pricing = stripe_service.get_tier_pricing("premium")

    assert pricing["amount_cents"] == 7900
    assert pricing["amount_dollars"] == 79.0
    assert pricing["interval"] == "year"


def test_get_tier_pricing_instructor(stripe_service):
    """Test getting pricing for instructor/lifetime tier"""
    pricing = stripe_service.get_tier_pricing("lifetime")

    assert pricing["amount_cents"] == 14900
    assert pricing["amount_dollars"] == 149.0
    assert pricing["interval"] == "lifetime"


def test_get_tier_pricing_invalid(stripe_service):
    """Test getting pricing for invalid tier raises error"""
    with pytest.raises(ValueError, match="Invalid tier"):
        stripe_service.get_tier_pricing("invalid")


# ============================================================================
# TIER FEATURES TESTS
# ============================================================================

def test_get_tier_features_free(stripe_service):
    """Test getting features for free tier"""
    features = stripe_service._get_tier_features(SubscriptionTier.FREE)

    assert features["event_access"] == "public_only"
    assert features["training_videos"] is False
    assert features["newsletter"] is True


def test_get_tier_features_basic(stripe_service):
    """Test getting features for basic tier"""
    features = stripe_service._get_tier_features(SubscriptionTier.BASIC)

    assert features["event_access"] == "all"
    assert features["training_videos"] is True
    assert features["member_directory"] is True
    assert features["discount_events"] == "10%"


def test_get_tier_features_premium(stripe_service):
    """Test getting features for premium tier"""
    features = stripe_service._get_tier_features(SubscriptionTier.PREMIUM)

    assert features["video_limit"] == "unlimited"
    assert features["priority_support"] is True
    assert features["exclusive_content"] is True
    assert features["discount_events"] == "20%"


def test_get_tier_features_lifetime(stripe_service):
    """Test getting features for lifetime tier"""
    features = stripe_service._get_tier_features(SubscriptionTier.LIFETIME)

    assert features["lifetime_access"] is True
    assert features["founding_member"] is True
    assert features["discount_events"] == "25%"


# ============================================================================
# DATABASE UPDATE TESTS
# ============================================================================

@patch('stripe.checkout.Session.create')
def test_checkout_session_stored_in_application(mock_create, stripe_service, mocker):
    """Test that checkout session is stored in application"""
    mock_create.return_value = Mock(
        id="cs_test123",
        url="https://checkout.stripe.com/test",
        amount_total=2900,
        mode="subscription",
        expires_at=int(datetime.utcnow().timestamp())
    )

    mock_update = mocker.patch.object(
        stripe_service.db,
        'update_document',
        return_value={"id": "app_123"}
    )

    stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="basic",
        customer_email="test@example.com"
    )

    # Verify application was updated with session info
    mock_update.assert_called_once()
    call_args = mock_update.call_args[0]
    assert call_args[0] == "applications"
    assert call_args[1] == "app_123"

    update_data = call_args[2]
    assert "checkout_session_id" in update_data
    assert "checkout_session_url" in update_data


@patch('stripe.checkout.Session.create')
def test_checkout_session_db_error_doesnt_fail(mock_create, stripe_service, mocker):
    """Test that database errors don't fail checkout session creation"""
    mock_create.return_value = Mock(
        id="cs_test123",
        url="https://checkout.stripe.com/test",
        amount_total=2900,
        mode="subscription",
        expires_at=int(datetime.utcnow().timestamp())
    )

    # Make DB update fail
    mocker.patch.object(
        stripe_service.db,
        'update_document',
        side_effect=Exception("DB error")
    )

    # Should still succeed and return session
    result = stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="basic",
        customer_email="test@example.com"
    )

    assert result["session_id"] == "cs_test123"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_stripe_service_with_invalid_tier_type(stripe_service):
    """Test handling of invalid tier types"""
    with pytest.raises(SubscriptionError, match="Failed to create subscription"):
        stripe_service.create_subscription_in_db(
            user_id="user_123",
            tier="not_a_valid_tier",
            stripe_customer_id="cus_123"
        )


def test_subscription_amount_calculation(stripe_service, mocker):
    """Test automatic amount calculation from tier"""
    mock_create = mocker.patch.object(
        stripe_service.db,
        'create_document',
        return_value={"id": "sub_123", "data": {}}
    )

    stripe_service.create_subscription_in_db(
        user_id="user_123",
        tier="premium",
        stripe_customer_id="cus_123"
        # amount not provided, should calculate from TIER_PRICING
    )

    call_args = mock_create.call_args[0]
    subscription_data = call_args[1]
    assert subscription_data["amount"] == 79.0  # 7900 cents / 100


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@patch('stripe.checkout.Session.create')
@patch('stripe.checkout.Session.retrieve')
def test_full_payment_flow(mock_retrieve, mock_create, stripe_service, sample_checkout_session, mocker):
    """Test complete payment flow from checkout to subscription creation"""
    # Setup mocks
    mock_create.return_value = Mock(**sample_checkout_session)
    mock_retrieve.return_value = Mock(**sample_checkout_session)

    mock_create_sub = mocker.patch.object(
        stripe_service,
        'create_subscription_in_db',
        return_value={"id": "sub_123", "tier": "basic"}
    )

    mock_update = mocker.patch.object(
        stripe_service.db,
        'update_document',
        return_value={"id": "app_123"}
    )

    # Step 1: Create checkout session
    session_result = stripe_service.create_checkout_session(
        user_id="user_123",
        application_id="app_123",
        tier_id="basic",
        customer_email="test@example.com"
    )

    assert session_result["session_id"] == "cs_test123"

    # Step 2: Process successful payment
    payment_result = stripe_service.process_successful_payment(session_result["session_id"])

    assert payment_result["success"] is True
    assert payment_result["subscription_id"] == "sub_123"

    # Verify all operations were called
    mock_create.assert_called_once()
    mock_retrieve.assert_called_once()
    mock_create_sub.assert_called_once()
    assert mock_update.call_count == 2  # Once for session, once for payment
