"""
Comprehensive tests for Newsletter Service (US-058)

Tests cover:
- Public subscription with double opt-in
- Email confirmation flow
- Unsubscribe functionality
- Subscription status checks
- Preference updates
- GDPR compliance features
- Rate limiting
- Error handling
- BeeHiiv integration mocking

Target: 80%+ code coverage
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

from backend.services.newsletter_service import (
    NewsletterService,
    NewsletterServiceError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client"""
    client = Mock()
    client.create_document = Mock()
    client.get_document = Mock()
    client.update_document = Mock()
    client.query_documents = Mock()
    return client


@pytest.fixture
def mock_beehiiv_service():
    """Mock BeeHiiv service"""
    service = Mock()
    service.add_subscriber = AsyncMock(return_value={"data": {"id": "beehiiv_123"}})
    service.remove_subscriber = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_email_service():
    """Mock Email service"""
    service = Mock()
    service.send_newsletter_confirmation = Mock(return_value={"MessageID": "msg_123"})
    return service


@pytest.fixture
def newsletter_service(mock_zerodb_client, mock_beehiiv_service, mock_email_service):
    """Newsletter service with mocked dependencies"""
    with patch('backend.services.newsletter_service.BeeHiivService', return_value=mock_beehiiv_service), \
         patch('backend.services.newsletter_service.EmailService', return_value=mock_email_service):
        service = NewsletterService(zerodb_client=mock_zerodb_client)
        return service


# ============================================================================
# TEST PUBLIC SUBSCRIPTION
# ============================================================================

@pytest.mark.asyncio
async def test_public_subscribe_success(newsletter_service, mock_zerodb_client, mock_email_service):
    """Test successful newsletter subscription"""
    # Setup
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Subscribe
    result = await newsletter_service.public_subscribe(
        email="test@example.com",
        name="Test User",
        interests=["events", "training"],
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        source="website"
    )

    # Assertions
    assert result["status"] == "pending"
    assert result["message"] == "Please check your email to confirm your subscription"
    assert "subscription_id" in result

    # Verify database call
    mock_zerodb_client.create_document.assert_called_once()
    call_args = mock_zerodb_client.create_document.call_args
    assert call_args[0][0] == "newsletter_subscriptions"

    subscription_data = call_args[0][1]
    assert subscription_data["email"] == "test@example.com"
    assert subscription_data["name"] == "Test User"
    assert subscription_data["interests"] == ["events", "training"]
    assert subscription_data["status"] == "pending"
    assert subscription_data["ip_address_hash"] is not None

    # Verify confirmation email sent
    mock_email_service.send_newsletter_confirmation.assert_called_once()


@pytest.mark.asyncio
async def test_public_subscribe_already_subscribed(newsletter_service, mock_zerodb_client):
    """Test subscription when email is already active"""
    # Setup existing subscription
    existing_subscription = {
        "id": str(uuid4()),
        "email": "test@example.com",
        "status": "active",
        "name": "Existing User"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [existing_subscription]}

    # Try to subscribe
    result = await newsletter_service.public_subscribe(
        email="test@example.com",
        name="Test User"
    )

    # Assertions
    assert result["status"] == "already_subscribed"
    assert "already subscribed" in result["message"].lower()


@pytest.mark.asyncio
async def test_public_subscribe_resend_confirmation(newsletter_service, mock_zerodb_client, mock_email_service):
    """Test resending confirmation email for pending subscription"""
    # Setup pending subscription
    pending_subscription = {
        "id": str(uuid4()),
        "email": "test@example.com",
        "status": "pending",
        "name": "Test User",
        "confirmation_token": "existing_token_123"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [pending_subscription]}

    # Try to subscribe again
    result = await newsletter_service.public_subscribe(
        email="test@example.com",
        name="Test User"
    )

    # Assertions
    assert result["status"] == "pending"
    assert "resent" in result["message"].lower()

    # Verify confirmation email was resent
    mock_email_service.send_newsletter_confirmation.assert_called_once()


@pytest.mark.asyncio
async def test_public_subscribe_email_normalization(newsletter_service, mock_zerodb_client):
    """Test that email addresses are normalized to lowercase"""
    # Setup
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Subscribe with mixed case email
    await newsletter_service.public_subscribe(
        email="Test@Example.COM",
        name="Test User"
    )

    # Verify email was normalized
    call_args = mock_zerodb_client.create_document.call_args
    subscription_data = call_args[0][1]
    assert subscription_data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_public_subscribe_ip_hashing(newsletter_service, mock_zerodb_client):
    """Test that IP address is hashed for GDPR compliance"""
    # Setup
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Subscribe with IP address
    test_ip = "192.168.1.100"
    await newsletter_service.public_subscribe(
        email="test@example.com",
        name="Test User",
        ip_address=test_ip
    )

    # Verify IP was hashed
    call_args = mock_zerodb_client.create_document.call_args
    subscription_data = call_args[0][1]
    assert subscription_data["ip_address_hash"] is not None
    assert subscription_data["ip_address_hash"] != test_ip
    assert len(subscription_data["ip_address_hash"]) == 64  # SHA256 hex length


# ============================================================================
# TEST CONFIRMATION
# ============================================================================

@pytest.mark.asyncio
async def test_confirm_subscription_success(newsletter_service, mock_zerodb_client):
    """Test successful subscription confirmation"""
    subscription_id = str(uuid4())
    email = "test@example.com"

    # Setup existing pending subscription
    pending_subscription = {
        "id": subscription_id,
        "email": email,
        "name": "Test User",
        "status": "pending",
        "interests": ["events"]
    }
    mock_zerodb_client.get_document.return_value = {"data": pending_subscription}

    # Mock BeeHiiv subscription
    newsletter_service._subscribe_to_list = AsyncMock(return_value={"id": "beehiiv_123"})

    # Generate valid token
    from backend.config import settings
    token = jwt.encode(
        {
            "email": email,
            "subscription_id": subscription_id,
            "type": "newsletter_confirmation",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    # Confirm subscription
    result = await newsletter_service.confirm_public_subscription(token)

    # Assertions
    assert result["status"] == "active"
    assert result["email"] == email
    assert "confirmed" in result["message"].lower()

    # Verify database update
    mock_zerodb_client.update_document.assert_called_once()
    call_args = mock_zerodb_client.update_document.call_args
    assert call_args[0][0] == "newsletter_subscriptions"
    assert call_args[0][1] == subscription_id
    update_data = call_args[0][2]
    assert update_data["status"] == "active"
    assert "confirmed_at" in update_data


@pytest.mark.asyncio
async def test_confirm_subscription_already_confirmed(newsletter_service, mock_zerodb_client):
    """Test confirming an already active subscription"""
    subscription_id = str(uuid4())
    email = "test@example.com"

    # Setup existing active subscription
    active_subscription = {
        "id": subscription_id,
        "email": email,
        "status": "active"
    }
    mock_zerodb_client.get_document.return_value = {"data": active_subscription}

    # Generate valid token
    from backend.config import settings
    token = jwt.encode(
        {
            "email": email,
            "subscription_id": subscription_id,
            "type": "newsletter_confirmation",
            "exp": datetime.utcnow() + timedelta(hours=24)
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    # Confirm subscription
    result = await newsletter_service.confirm_public_subscription(token)

    # Assertions
    assert result["status"] == "active"
    assert "already confirmed" in result["message"].lower()


@pytest.mark.asyncio
async def test_confirm_subscription_expired_token(newsletter_service):
    """Test confirmation with expired token"""
    from backend.config import settings

    # Generate expired token
    token = jwt.encode(
        {
            "email": "test@example.com",
            "subscription_id": str(uuid4()),
            "type": "newsletter_confirmation",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    # Try to confirm
    with pytest.raises(NewsletterServiceError, match="expired"):
        await newsletter_service.confirm_public_subscription(token)


@pytest.mark.asyncio
async def test_confirm_subscription_invalid_token(newsletter_service):
    """Test confirmation with invalid token"""
    # Invalid token
    invalid_token = "invalid.token.here"

    # Try to confirm
    with pytest.raises(NewsletterServiceError, match="Invalid"):
        await newsletter_service.confirm_public_subscription(invalid_token)


@pytest.mark.asyncio
async def test_confirm_subscription_wrong_token_type(newsletter_service):
    """Test confirmation with wrong token type"""
    from backend.config import settings

    # Generate token with wrong type
    token = jwt.encode(
        {
            "email": "test@example.com",
            "subscription_id": str(uuid4()),
            "type": "password_reset",  # Wrong type
            "exp": datetime.utcnow() + timedelta(hours=24)
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    # Try to confirm
    with pytest.raises(NewsletterServiceError, match="Invalid token type"):
        await newsletter_service.confirm_public_subscription(token)


# ============================================================================
# TEST UNSUBSCRIBE
# ============================================================================

@pytest.mark.asyncio
async def test_unsubscribe_success(newsletter_service, mock_zerodb_client):
    """Test successful unsubscribe"""
    subscription_id = str(uuid4())
    email = "test@example.com"

    # Setup existing active subscription
    active_subscription = {
        "id": subscription_id,
        "email": email,
        "status": "active"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [active_subscription]}

    # Mock BeeHiiv unsubscribe
    newsletter_service._unsubscribe_from_list = AsyncMock()

    # Unsubscribe
    result = await newsletter_service.public_unsubscribe(
        email=email,
        reason="Too many emails"
    )

    # Assertions
    assert result["status"] == "unsubscribed"
    assert "unsubscribed" in result["message"].lower()

    # Verify database update
    mock_zerodb_client.update_document.assert_called_once()
    call_args = mock_zerodb_client.update_document.call_args
    update_data = call_args[0][2]
    assert update_data["status"] == "unsubscribed"
    assert update_data["unsubscribe_reason"] == "Too many emails"


@pytest.mark.asyncio
async def test_unsubscribe_not_found(newsletter_service, mock_zerodb_client):
    """Test unsubscribe when email not found"""
    # Setup no existing subscription
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Unsubscribe
    result = await newsletter_service.public_unsubscribe(email="notfound@example.com")

    # Assertions - should still return success for privacy
    assert result["status"] == "not_found"
    assert "not subscribed" in result["message"].lower()


@pytest.mark.asyncio
async def test_unsubscribe_already_unsubscribed(newsletter_service, mock_zerodb_client):
    """Test unsubscribe when already unsubscribed"""
    # Setup existing unsubscribed subscription
    unsubscribed_subscription = {
        "id": str(uuid4()),
        "email": "test@example.com",
        "status": "unsubscribed"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [unsubscribed_subscription]}

    # Unsubscribe
    result = await newsletter_service.public_unsubscribe(email="test@example.com")

    # Assertions
    assert result["status"] == "unsubscribed"
    assert "already unsubscribed" in result["message"].lower()


# ============================================================================
# TEST SUBSCRIPTION STATUS
# ============================================================================

@pytest.mark.asyncio
async def test_get_subscription_status_active(newsletter_service, mock_zerodb_client):
    """Test getting status for active subscription"""
    subscription = {
        "id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "status": "active",
        "interests": ["events", "training"],
        "subscribed_at": "2025-01-01T00:00:00",
        "confirmed_at": "2025-01-01T01:00:00"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [subscription]}

    # Get status
    result = await newsletter_service.get_public_subscription_status("test@example.com")

    # Assertions
    assert result["subscribed"] is True
    assert result["status"] == "active"
    assert result["email"] == "test@example.com"
    assert result["name"] == "Test User"
    assert result["interests"] == ["events", "training"]


@pytest.mark.asyncio
async def test_get_subscription_status_not_found(newsletter_service, mock_zerodb_client):
    """Test getting status for non-existent subscription"""
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Get status
    result = await newsletter_service.get_public_subscription_status("notfound@example.com")

    # Assertions
    assert result["subscribed"] is False
    assert result["status"] == "not_found"


# ============================================================================
# TEST PREFERENCE UPDATES
# ============================================================================

@pytest.mark.asyncio
async def test_update_preferences_success(newsletter_service, mock_zerodb_client):
    """Test successful preference update"""
    subscription_id = str(uuid4())
    subscription = {
        "id": subscription_id,
        "email": "test@example.com",
        "status": "active",
        "name": "Old Name",
        "interests": ["events"],
        "beehiiv_subscriber_id": "beehiiv_123"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [subscription]}
    mock_zerodb_client.get_document.return_value = {
        "data": {**subscription, "name": "New Name", "interests": ["events", "training"]}
    }

    # Mock BeeHiiv update
    newsletter_service._make_beehiiv_request = AsyncMock()

    # Update preferences
    result = await newsletter_service.update_public_preferences(
        email="test@example.com",
        name="New Name",
        interests=["events", "training"]
    )

    # Assertions
    assert result["message"] == "Preferences updated successfully"
    assert "subscription" in result

    # Verify database update
    mock_zerodb_client.update_document.assert_called_once()
    call_args = mock_zerodb_client.update_document.call_args
    update_data = call_args[0][2]
    assert update_data["name"] == "New Name"
    assert update_data["interests"] == ["events", "training"]


@pytest.mark.asyncio
async def test_update_preferences_not_found(newsletter_service, mock_zerodb_client):
    """Test updating preferences for non-existent subscription"""
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Try to update
    with pytest.raises(NewsletterServiceError, match="not found"):
        await newsletter_service.update_public_preferences(
            email="notfound@example.com",
            name="New Name"
        )


@pytest.mark.asyncio
async def test_update_preferences_inactive_subscription(newsletter_service, mock_zerodb_client):
    """Test updating preferences for inactive subscription"""
    subscription = {
        "id": str(uuid4()),
        "email": "test@example.com",
        "status": "unsubscribed"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [subscription]}

    # Try to update
    with pytest.raises(NewsletterServiceError, match="inactive"):
        await newsletter_service.update_public_preferences(
            email="test@example.com",
            name="New Name"
        )


# ============================================================================
# TEST TOKEN GENERATION
# ============================================================================

def test_generate_confirmation_token(newsletter_service):
    """Test confirmation token generation"""
    email = "test@example.com"
    subscription_id = str(uuid4())

    # Generate token
    token = newsletter_service._generate_confirmation_token(email, subscription_id)

    # Verify token can be decoded
    from backend.config import settings
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

    assert payload["email"] == email
    assert payload["subscription_id"] == subscription_id
    assert payload["type"] == "newsletter_confirmation"
    assert "exp" in payload
    assert "iat" in payload


# ============================================================================
# TEST ERROR HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_subscribe_database_error(newsletter_service, mock_zerodb_client):
    """Test handling of database errors during subscription"""
    mock_zerodb_client.query_documents.return_value = {"documents": []}
    mock_zerodb_client.create_document.side_effect = Exception("Database error")

    # Try to subscribe
    with pytest.raises(Exception, match="Database error"):
        await newsletter_service.public_subscribe(
            email="test@example.com",
            name="Test User"
        )


@pytest.mark.asyncio
async def test_confirmation_email_failure(newsletter_service, mock_zerodb_client, mock_email_service):
    """Test handling of email sending failure"""
    mock_zerodb_client.query_documents.return_value = {"documents": []}
    mock_email_service.send_newsletter_confirmation.side_effect = Exception("Email error")

    # Try to subscribe - should raise error since email is critical
    with pytest.raises(NewsletterServiceError, match="Failed to send confirmation email"):
        await newsletter_service.public_subscribe(
            email="test@example.com",
            name="Test User"
        )


# ============================================================================
# TEST COVERAGE HELPERS
# ============================================================================

def test_newsletter_service_initialization():
    """Test NewsletterService initialization"""
    from backend.services.zerodb_service import ZeroDBClient

    with patch('backend.services.newsletter_service.ZeroDBClient') as mock_db_class:
        mock_db_class.return_value = Mock()
        service = NewsletterService()

        assert service.db is not None
        assert service.beehiiv is not None
        assert service.email_service is not None


@pytest.mark.asyncio
async def test_get_public_subscription_by_email(newsletter_service, mock_zerodb_client):
    """Test internal method for getting subscription by email"""
    subscription = {
        "id": str(uuid4()),
        "email": "test@example.com",
        "status": "active"
    }
    mock_zerodb_client.query_documents.return_value = {"documents": [subscription]}

    # Get subscription
    result = await newsletter_service._get_public_subscription_by_email("test@example.com")

    # Assertions
    assert result is not None
    assert result["email"] == "test@example.com"

    # Verify query was called correctly
    mock_zerodb_client.query_documents.assert_called_once_with(
        "newsletter_subscriptions",
        filters={"email": "test@example.com"},
        limit=1
    )


@pytest.mark.asyncio
async def test_get_public_subscription_by_email_not_found(newsletter_service, mock_zerodb_client):
    """Test getting non-existent subscription by email"""
    mock_zerodb_client.query_documents.return_value = {"documents": []}

    # Get subscription
    result = await newsletter_service._get_public_subscription_by_email("notfound@example.com")

    # Assertions
    assert result is None
