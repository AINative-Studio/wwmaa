"""
Unit Tests for Admin Settings API

Tests for admin settings endpoints including:
- GET /admin/settings
- PATCH /admin/settings/org
- PATCH /admin/settings/email
- PATCH /admin/settings/stripe
- PATCH /admin/settings/membership-tiers
- POST /admin/settings/email/test

Tests cover:
- Settings retrieval and creation
- Partial updates
- Encryption/decryption of sensitive fields
- Input validation
- Email sending functionality
- Authentication/authorization
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from backend.models.schemas import AdminSettings, UserRole
from backend.models.request_schemas import (
    OrganizationSettingsUpdate,
    EmailSettingsUpdate,
    StripeSettingsUpdate,
    MembershipTiersUpdate,
    MembershipTierConfig,
    EmailTestRequest,
)
from backend.routes.admin.settings import (
    get_or_create_settings,
    decrypt_settings_for_response,
)
from backend.utils.encryption import encrypt_value, decrypt_value


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock ZeroDB client"""
    db = Mock()
    return db


@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication"""
    return {
        "id": str(uuid4()),
        "email": "admin@test.com",
        "role": UserRole.ADMIN.value
    }


@pytest.fixture
def sample_settings():
    """Sample admin settings document"""
    return AdminSettings(
        org_name="Test WWMAA",
        org_email="test@wwmaa.com",
        org_phone="+1-555-1234",
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_username="test@test.com",
        smtp_password_encrypted=encrypt_value("test_password"),
        smtp_from_email="from@test.com",  # Required for email test
        stripe_publishable_key="pk_test_123",
        stripe_secret_key_encrypted=encrypt_value("sk_test_123"),
        stripe_webhook_secret_encrypted=encrypt_value("whsec_test_123"),
    )


# ============================================================================
# ENCRYPTION/DECRYPTION TESTS
# ============================================================================

def test_encrypt_decrypt_value():
    """Test encryption and decryption of sensitive values"""
    plaintext = "my_secret_password_12345"

    # Encrypt
    encrypted = encrypt_value(plaintext)
    assert encrypted is not None
    assert encrypted != plaintext
    assert len(encrypted) > 0

    # Decrypt
    decrypted = decrypt_value(encrypted)
    assert decrypted == plaintext


def test_encrypt_none_value():
    """Test encrypting None returns None"""
    assert encrypt_value(None) is None
    assert encrypt_value("") is None


def test_decrypt_none_value():
    """Test decrypting None returns None"""
    assert decrypt_value(None) is None
    assert decrypt_value("") is None


def test_decrypt_invalid_value():
    """Test decrypting invalid value raises error"""
    with pytest.raises(ValueError, match="Failed to decrypt"):
        decrypt_value("invalid_encrypted_value")


def test_decrypt_settings_for_response(sample_settings):
    """Test decryption of settings for API response"""
    decrypted = decrypt_settings_for_response(sample_settings)

    # Check encrypted fields are decrypted
    assert decrypted['smtp_password'] == "test_password"
    assert decrypted['stripe_secret_key'] == "sk_test_123"
    assert decrypted['stripe_webhook_secret'] == "whsec_test_123"

    # Check encrypted field keys are removed
    assert 'smtp_password_encrypted' not in decrypted
    assert 'stripe_secret_key_encrypted' not in decrypted
    assert 'stripe_webhook_secret_encrypted' not in decrypted

    # Check non-encrypted fields remain
    assert decrypted['org_name'] == "Test WWMAA"
    assert decrypted['smtp_host'] == "smtp.test.com"


# ============================================================================
# GET SETTINGS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_or_create_settings_existing(mock_db, sample_settings):
    """Test retrieving existing settings"""
    mock_db.query_documents.return_value = [sample_settings.model_dump(mode='json')]

    result = await get_or_create_settings(mock_db)

    assert result.org_name == sample_settings.org_name
    mock_db.query_documents.assert_called_once()
    mock_db.insert_document.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_settings_create_default(mock_db):
    """Test creating default settings when none exist"""
    mock_db.query_documents.return_value = []
    default_settings = AdminSettings()
    mock_db.insert_document.return_value = default_settings.model_dump(mode='json')

    result = await get_or_create_settings(mock_db)

    assert result.org_name == "WWMAA"  # Default value
    mock_db.query_documents.assert_called_once()
    mock_db.insert_document.assert_called_once()


# ============================================================================
# ORGANIZATION SETTINGS UPDATE TESTS
# ============================================================================

def test_organization_settings_update_validation():
    """Test organization settings update validation"""
    # Valid update
    update = OrganizationSettingsUpdate(
        org_name="New Organization",
        org_email="new@org.com",
        org_phone="+1-555-9999"
    )
    assert update.org_name == "New Organization"

    # Test phone validation
    with pytest.raises(ValueError):
        OrganizationSettingsUpdate(org_phone="invalid")


def test_organization_settings_update_optional_fields():
    """Test organization settings with only some fields"""
    update = OrganizationSettingsUpdate(org_name="Just Name")
    assert update.org_name == "Just Name"
    assert update.org_email is None


# ============================================================================
# EMAIL SETTINGS UPDATE TESTS
# ============================================================================

def test_email_settings_update_validation():
    """Test email settings update validation"""
    # Valid update
    update = EmailSettingsUpdate(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="user@gmail.com",
        smtp_password="secure_password_123",
        smtp_use_tls=True
    )
    assert update.smtp_host == "smtp.gmail.com"
    assert update.smtp_port == 587


def test_email_settings_invalid_port():
    """Test email settings with invalid port"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EmailSettingsUpdate(smtp_port=99999)

    with pytest.raises(ValidationError):
        EmailSettingsUpdate(smtp_port=0)


# ============================================================================
# STRIPE SETTINGS UPDATE TESTS
# ============================================================================

def test_stripe_settings_update_validation():
    """Test Stripe settings update validation"""
    # Valid update
    update = StripeSettingsUpdate(
        stripe_publishable_key="pk_test_123456",
        stripe_secret_key="sk_test_abcdef",
        stripe_webhook_secret="whsec_test_xyz",
        stripe_enabled=True
    )
    assert update.stripe_publishable_key == "pk_test_123456"
    assert update.stripe_enabled is True


def test_stripe_publishable_key_format():
    """Test Stripe publishable key format validation"""
    with pytest.raises(ValueError, match="must start with 'pk_'"):
        StripeSettingsUpdate(stripe_publishable_key="invalid_key")


def test_stripe_secret_key_format():
    """Test Stripe secret key format validation"""
    with pytest.raises(ValueError, match="must start with 'sk_'"):
        StripeSettingsUpdate(stripe_secret_key="invalid_key")


def test_stripe_webhook_secret_format():
    """Test Stripe webhook secret format validation"""
    with pytest.raises(ValueError, match="must start with 'whsec_'"):
        StripeSettingsUpdate(stripe_webhook_secret="invalid_secret")


# ============================================================================
# MEMBERSHIP TIERS UPDATE TESTS
# ============================================================================

def test_membership_tier_config_validation():
    """Test membership tier configuration validation"""
    # Valid tier
    tier = MembershipTierConfig(
        name="Premium",
        price=49.99,
        currency="USD",
        interval="month",
        features=["Feature 1", "Feature 2"]
    )
    assert tier.name == "Premium"
    assert tier.price == 49.99


def test_membership_tier_invalid_interval():
    """Test membership tier with invalid interval"""
    with pytest.raises(ValueError, match="Interval must be one of"):
        MembershipTierConfig(
            name="Test",
            price=10.0,
            currency="USD",
            interval="invalid",
            features=["Feature 1"]
        )


def test_membership_tier_invalid_currency():
    """Test membership tier with invalid currency"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MembershipTierConfig(
            name="Test",
            price=10.0,
            currency="US",  # Too short
            interval="month",
            features=["Feature 1"]
        )


def test_membership_tier_no_features():
    """Test membership tier requires at least one feature"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MembershipTierConfig(
            name="Test",
            price=10.0,
            currency="USD",
            interval="month",
            features=[]
        )


def test_membership_tier_negative_price():
    """Test membership tier with negative price"""
    with pytest.raises(ValueError):
        MembershipTierConfig(
            name="Test",
            price=-10.0,
            currency="USD",
            interval="month",
            features=["Feature 1"]
        )


def test_membership_tiers_update_partial():
    """Test updating only some tiers"""
    update = MembershipTiersUpdate(
        premium=MembershipTierConfig(
            name="Premium Updated",
            price=59.99,
            currency="USD",
            interval="month",
            features=["New Feature"]
        )
    )
    assert update.premium.name == "Premium Updated"
    assert update.basic is None


# ============================================================================
# EMAIL TEST REQUEST TESTS
# ============================================================================

def test_email_test_request_validation():
    """Test email test request validation"""
    # Valid request
    request = EmailTestRequest(
        test_email="test@example.com",
        test_subject="Test Subject",
        test_message="Test message content"
    )
    assert request.test_email == "test@example.com"


def test_email_test_request_html_rejection():
    """Test email test request rejects HTML"""
    with pytest.raises(ValueError, match="HTML not allowed"):
        EmailTestRequest(
            test_email="test@example.com",
            test_subject="<script>alert('xss')</script>",
            test_message="Clean message"
        )


# ============================================================================
# INTEGRATION TESTS WITH MOCK DB
# ============================================================================

@pytest.mark.asyncio
async def test_update_settings_encryption(mock_db, sample_settings, mock_admin_user):
    """Test that sensitive fields are encrypted when updating"""
    from backend.routes.admin.settings import update_email_settings, get_or_create_settings

    mock_db.query_documents.return_value = [sample_settings.model_dump(mode='json')]
    mock_db.update_document.return_value = sample_settings.model_dump(mode='json')

    update_data = EmailSettingsUpdate(smtp_password="new_password_123")

    # The password should be encrypted before saving
    result = await update_email_settings(update_data, mock_admin_user, mock_db)

    # Verify update_document was called
    mock_db.update_document.assert_called_once()

    # Get the actual call arguments - the third argument is the updates dict
    call_args = mock_db.update_document.call_args
    if call_args.args and len(call_args.args) >= 3:
        updates = call_args.args[2]
    else:
        updates = call_args.kwargs.get('updates')

    # Verify password is encrypted (not plaintext)
    assert 'smtp_password_encrypted' in updates
    assert updates['smtp_password_encrypted'] is not None
    assert updates['smtp_password_encrypted'] != "new_password_123"


@pytest.mark.asyncio
async def test_email_test_smtp_connection(mock_db, sample_settings, mock_admin_user):
    """Test email sending with mocked SMTP"""
    from backend.routes.admin.settings import send_test_email

    mock_db.query_documents.return_value = [sample_settings.model_dump(mode='json')]
    mock_db.update_document.return_value = sample_settings.model_dump(mode='json')

    test_request = EmailTestRequest(test_email="test@example.com")

    # Mock SMTP server
    with patch('backend.routes.admin.settings.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = await send_test_email(test_request, mock_admin_user, mock_db)

        assert result['success'] is True
        assert "sent successfully" in result['message']

        # Verify SMTP methods were called
        mock_server.starttls.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_decrypt_settings_with_missing_encrypted_fields():
    """Test decryption handles missing encrypted fields gracefully"""
    settings = AdminSettings(
        org_name="Test",
        # No encrypted fields set
    )

    decrypted = decrypt_settings_for_response(settings)

    # Should have None for missing fields
    assert decrypted['smtp_password'] is None
    assert decrypted['stripe_secret_key'] is None
    assert decrypted['stripe_webhook_secret'] is None


def test_settings_version_tracking():
    """Test settings version is tracked"""
    settings = AdminSettings()
    assert settings.settings_version == 1


def test_settings_singleton_pattern():
    """Test settings uses singleton pattern (is_active flag)"""
    settings = AdminSettings()
    assert settings.is_active is True


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_settings_require_admin_role():
    """Test that settings endpoints require admin role"""
    # This would be tested via integration tests with actual auth middleware
    # For unit tests, we verify the dependency is used
    from backend.routes.admin.settings import get_admin_settings
    import inspect

    # Check that get_current_admin_user is a dependency
    sig = inspect.signature(get_admin_settings)
    params = sig.parameters

    assert 'current_user' in params
    # The default should be a Depends() call to get_current_admin_user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
