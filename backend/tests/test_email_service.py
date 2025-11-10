"""
Unit Tests for Email Service

Tests for Postmark email service integration including
verification emails, welcome emails, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from backend.services.email_service import (
    EmailService,
    EmailServiceError,
    EmailSendError,
    get_email_service
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def email_service():
    """Create email service instance with test credentials"""
    return EmailService(
        api_key="test-api-key",
        from_email="test@wwmaa.com"
    )


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for email API calls"""
    with patch('backend.services.email_service.requests.post') as mock:
        yield mock


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestEmailServiceInitialization:
    """Test EmailService initialization"""

    def test_initialization_with_credentials(self):
        """Test initialization with provided credentials"""
        service = EmailService(
            api_key="test-key",
            from_email="sender@test.com"
        )

        assert service.api_key == "test-key"
        assert service.from_email == "sender@test.com"
        assert service.base_url == "https://api.postmarkapp.com"
        assert "X-Postmark-Server-Token" in service.headers

    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key"""
        with patch('backend.services.email_service.settings') as mock_settings:
            mock_settings.POSTMARK_API_KEY = None
            mock_settings.FROM_EMAIL = "test@test.com"

            with pytest.raises(EmailServiceError, match="POSTMARK_API_KEY is required"):
                EmailService()

    @patch('backend.services.email_service.settings')
    def test_initialization_from_settings(self, mock_settings):
        """Test initialization uses settings as defaults"""
        mock_settings.POSTMARK_API_KEY = "settings-key"
        mock_settings.FROM_EMAIL = "settings@test.com"

        service = EmailService()

        assert service.api_key == "settings-key"
        assert service.from_email == "settings@test.com"


# ============================================================================
# VERIFICATION EMAIL TESTS
# ============================================================================

class TestVerificationEmail:
    """Test verification email sending"""

    def test_send_verification_email_success(
        self,
        email_service,
        mock_requests_post
    ):
        """Test successful verification email sending"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "MessageID": "test-message-id",
            "To": "user@example.com"
        }
        mock_requests_post.return_value = mock_response

        # Send verification email
        result = email_service.send_verification_email(
            email="user@example.com",
            token="test-token-123",
            user_name="Jane Doe"
        )

        # Assertions
        assert result["MessageID"] == "test-message-id"
        mock_requests_post.assert_called_once()

        # Verify request payload
        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["To"] == "user@example.com"
        assert payload["Subject"] == "Verify Your WWMAA Account"
        assert "test-token-123" in payload["HtmlBody"]
        assert "Jane Doe" in payload["HtmlBody"]
        assert payload["Tag"] == "email-verification"

    def test_send_verification_email_contains_token(
        self,
        email_service,
        mock_requests_post
    ):
        """Test verification email contains token in URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"MessageID": "test-id"}
        mock_requests_post.return_value = mock_response

        email_service.send_verification_email(
            email="user@example.com",
            token="unique-token-xyz",
            user_name="Test User"
        )

        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]

        # Token should be in both HTML and text body
        assert "unique-token-xyz" in payload["HtmlBody"]
        assert "unique-token-xyz" in payload["TextBody"]
        assert "verify-email?token=unique-token-xyz" in payload["HtmlBody"]

    def test_send_verification_email_api_error(
        self,
        email_service,
        mock_requests_post
    ):
        """Test verification email fails on API error"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.text = "Invalid email"
        mock_response.json.return_value = {"Message": "Invalid recipient"}
        mock_requests_post.return_value = mock_response

        # Should raise EmailSendError
        with pytest.raises(EmailSendError, match="Failed to send email"):
            email_service.send_verification_email(
                email="invalid@example.com",
                token="test-token",
                user_name="Test User"
            )

    def test_send_verification_email_connection_error(
        self,
        email_service,
        mock_requests_post
    ):
        """Test verification email fails on connection error"""
        # Mock connection error
        mock_requests_post.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        # Should raise EmailSendError
        with pytest.raises(EmailSendError, match="Email sending request failed"):
            email_service.send_verification_email(
                email="user@example.com",
                token="test-token",
                user_name="Test User"
            )


# ============================================================================
# WELCOME EMAIL TESTS
# ============================================================================

class TestWelcomeEmail:
    """Test welcome email sending"""

    def test_send_welcome_email_success(
        self,
        email_service,
        mock_requests_post
    ):
        """Test successful welcome email sending"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "MessageID": "welcome-message-id",
            "To": "user@example.com"
        }
        mock_requests_post.return_value = mock_response

        # Send welcome email
        result = email_service.send_welcome_email(
            email="user@example.com",
            user_name="Jane Doe"
        )

        # Assertions
        assert result["MessageID"] == "welcome-message-id"
        mock_requests_post.assert_called_once()

        # Verify request payload
        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["To"] == "user@example.com"
        assert "Welcome to WWMAA" in payload["Subject"]
        assert "Jane Doe" in payload["HtmlBody"]
        assert payload["Tag"] == "welcome"

    def test_send_welcome_email_includes_user_name(
        self,
        email_service,
        mock_requests_post
    ):
        """Test welcome email includes user name"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"MessageID": "test-id"}
        mock_requests_post.return_value = mock_response

        email_service.send_welcome_email(
            email="user@example.com",
            user_name="John Smith"
        )

        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]

        # User name should be in both HTML and text body
        assert "John Smith" in payload["HtmlBody"]
        assert "John Smith" in payload["TextBody"]


# ============================================================================
# PASSWORD RESET EMAIL TESTS
# ============================================================================

class TestPasswordResetEmail:
    """Test password reset email sending"""

    def test_send_password_reset_email_success(
        self,
        email_service,
        mock_requests_post
    ):
        """Test successful password reset email sending"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "MessageID": "reset-message-id"
        }
        mock_requests_post.return_value = mock_response

        # Send password reset email
        result = email_service.send_password_reset_email(
            email="user@example.com",
            token="reset-token-456",
            user_name="Jane Doe"
        )

        # Assertions
        assert result["MessageID"] == "reset-message-id"
        mock_requests_post.assert_called_once()

        # Verify request payload
        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["To"] == "user@example.com"
        assert "Reset Your WWMAA Password" in payload["Subject"]
        assert "reset-token-456" in payload["HtmlBody"]
        assert "Jane Doe" in payload["HtmlBody"]
        assert payload["Tag"] == "password-reset"

    def test_send_password_reset_email_contains_token(
        self,
        email_service,
        mock_requests_post
    ):
        """Test password reset email contains token in URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"MessageID": "test-id"}
        mock_requests_post.return_value = mock_response

        email_service.send_password_reset_email(
            email="user@example.com",
            token="unique-reset-token",
            user_name="Test User"
        )

        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]

        # Token should be in both HTML and text body
        assert "unique-reset-token" in payload["HtmlBody"]
        assert "unique-reset-token" in payload["TextBody"]
        assert "reset-password?token=unique-reset-token" in payload["HtmlBody"]


# ============================================================================
# SINGLETON TESTS
# ============================================================================

class TestEmailServiceSingleton:
    """Test email service singleton pattern"""

    @patch('backend.services.email_service.settings')
    def test_get_email_service_singleton(self, mock_settings):
        """Test get_email_service returns same instance"""
        mock_settings.POSTMARK_API_KEY = "test-key"
        mock_settings.FROM_EMAIL = "test@test.com"

        # Clear any existing instance
        import backend.services.email_service as email_module
        email_module._email_service_instance = None

        # Get service twice
        service1 = get_email_service()
        service2 = get_email_service()

        # Should be the same instance
        assert service1 is service2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestEmailServiceErrorHandling:
    """Test email service error handling"""

    def test_send_email_timeout(self, email_service, mock_requests_post):
        """Test email sending handles timeout"""
        mock_requests_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(EmailSendError, match="Email sending request failed"):
            email_service.send_verification_email(
                email="user@example.com",
                token="test-token",
                user_name="Test User"
            )

    def test_send_email_network_error(self, email_service, mock_requests_post):
        """Test email sending handles network error"""
        mock_requests_post.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        with pytest.raises(EmailSendError, match="Email sending request failed"):
            email_service.send_verification_email(
                email="user@example.com",
                token="test-token",
                user_name="Test User"
            )

    def test_send_email_non_200_status(self, email_service, mock_requests_post):
        """Test email sending handles non-200 status codes"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.json.return_value = {"Message": "Server error"}
        mock_requests_post.return_value = mock_response

        with pytest.raises(EmailSendError, match="Failed to send email"):
            email_service.send_verification_email(
                email="user@example.com",
                token="test-token",
                user_name="Test User"
            )

    def test_send_email_invalid_json_response(self, email_service, mock_requests_post):
        """Test email sending handles invalid JSON response"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request - not JSON"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests_post.return_value = mock_response

        with pytest.raises(EmailSendError):
            email_service.send_verification_email(
                email="user@example.com",
                token="test-token",
                user_name="Test User"
            )
