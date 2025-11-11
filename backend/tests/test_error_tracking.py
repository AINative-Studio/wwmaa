"""
Tests for Error Tracking and Monitoring (US-066)

This module tests the Sentry error tracking integration, including:
- Sentry initialization
- Error capture and context
- User context tracking
- Breadcrumb management
- PII filtering
- Domain-specific error tracking
- Middleware functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from sentry_sdk import Hub
from jose import jwt

from backend.observability.errors import (
    init_sentry,
    add_request_context,
    add_user_context,
    clear_user_context,
    before_send,
    traces_sampler,
    _sanitize_value,
)
from backend.observability.error_utils import (
    capture_exception,
    capture_message,
    add_breadcrumb,
    set_tag,
    set_context,
    track_payment_error,
    track_auth_error,
    track_subscription_error,
    track_api_error,
    track_database_error,
)
from backend.middleware.error_tracking_middleware import (
    ErrorTrackingMiddleware,
    track_business_operation,
    track_external_api_call,
    track_database_operation as track_db_op_middleware,
    track_cache_operation,
)
from backend.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings with Sentry configuration."""
    settings = Mock(spec=Settings)
    settings.SENTRY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0"
    settings.PYTHON_ENV = "test"
    settings.SENTRY_ENVIRONMENT = "test"
    settings.SENTRY_RELEASE = "test-release"
    settings.SENTRY_TRACES_SAMPLE_RATE = 0.1
    settings.SENTRY_PROFILES_SAMPLE_RATE = 0.1
    settings.is_development = True
    settings.JWT_SECRET = "test_secret_key_minimum_32_characters_long"
    settings.JWT_ALGORITHM = "HS256"
    return settings


@pytest.fixture
def fastapi_app():
    """Create a test FastAPI app."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")

    return app


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.method = "POST"
    request.url = Mock()
    request.url.path = "/api/payments"
    request.url.__str__ = Mock(return_value="http://localhost/api/payments?test=1")
    request.headers = {"user-agent": "test-client", "content-type": "application/json"}
    request.query_params = {"test": "1"}
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


class TestSentryInitialization:
    """Test Sentry SDK initialization."""

    @patch('backend.observability.errors.sentry_sdk.init')
    @patch('backend.observability.errors.get_settings')
    def test_init_sentry_with_dsn(self, mock_get_settings, mock_sentry_init, mock_settings, fastapi_app):
        """Test Sentry initialization when DSN is configured."""
        mock_get_settings.return_value = mock_settings

        init_sentry(fastapi_app)

        # Verify Sentry was initialized
        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args[1]

        assert call_kwargs['dsn'] == mock_settings.SENTRY_DSN
        assert call_kwargs['environment'] == mock_settings.SENTRY_ENVIRONMENT
        assert call_kwargs['traces_sample_rate'] == 0.1
        assert call_kwargs['enable_tracing'] is True
        assert call_kwargs['send_default_pii'] is False

    @patch('backend.observability.errors.sentry_sdk.init')
    @patch('backend.observability.errors.get_settings')
    @patch('backend.observability.errors.logger')
    def test_init_sentry_without_dsn(self, mock_logger, mock_get_settings, mock_sentry_init, mock_settings, fastapi_app):
        """Test Sentry initialization when DSN is not configured."""
        mock_settings.SENTRY_DSN = ""
        mock_get_settings.return_value = mock_settings

        init_sentry(fastapi_app)

        # Verify Sentry was NOT initialized
        mock_sentry_init.assert_not_called()
        mock_logger.warning.assert_called_once()

    @patch('backend.observability.errors.sentry_sdk.init')
    @patch('backend.observability.errors.get_settings')
    @patch('subprocess.check_output')
    def test_init_sentry_with_git_release(self, mock_subprocess, mock_get_settings, mock_sentry_init, mock_settings, fastapi_app):
        """Test Sentry initialization extracts git commit for release."""
        mock_get_settings.return_value = mock_settings
        mock_subprocess.return_value = b'abc123def456\n'

        init_sentry(fastapi_app)

        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs['release'].startswith('wwmaa-backend@abc123de')


class TestPIIFiltering:
    """Test PII sanitization in before_send hook."""

    def test_sanitize_value_password(self):
        """Test password sanitization."""
        data = {"password": "secret123", "username": "testuser"}
        sanitized = _sanitize_value(data)

        assert "REDACTED_PASSWORD" in str(sanitized)
        assert "secret123" not in str(sanitized)
        assert sanitized["username"] == "testuser"

    def test_sanitize_value_api_key(self):
        """Test API key sanitization."""
        data = {"api_key": "sk_test_123456", "name": "test"}
        sanitized = _sanitize_value(data)

        assert "REDACTED_API_KEY" in str(sanitized)
        assert "sk_test_123456" not in str(sanitized)

    def test_sanitize_value_nested(self):
        """Test nested data sanitization."""
        data = {
            "user": {
                "email": "test@example.com",
                "password": "secret",
                "profile": {
                    "token": "xyz789"
                }
            }
        }
        sanitized = _sanitize_value(data)

        assert "REDACTED_PASSWORD" in str(sanitized)
        assert "REDACTED_TOKEN" in str(sanitized)
        assert "secret" not in str(sanitized)

    def test_sanitize_value_credit_card(self):
        """Test credit card number sanitization."""
        value = "My card is 4242-4242-4242-4242"
        sanitized = _sanitize_value(value)

        assert "4242-4242-4242-4242" not in sanitized
        assert "REDACTED_CREDIT_CARD" in sanitized

    def test_before_send_sanitizes_request_data(self):
        """Test before_send hook sanitizes request data."""
        event = {
            "request": {
                "headers": {
                    "Authorization": "Bearer token123",
                    "Content-Type": "application/json"
                },
                "data": {
                    "password": "secret",
                    "username": "testuser"
                },
                "query_string": "api_key=sk_test_123"
            },
            "user": {
                "ip_address": "192.168.1.1"
            }
        }

        sanitized_event = before_send(event, {})

        # Headers should be redacted
        assert sanitized_event["request"]["headers"]["Authorization"] == "[REDACTED]"

        # Query string should be sanitized
        assert "REDACTED_API_KEY" in str(sanitized_event["request"]["query_string"])

        # IP should be hashed
        assert sanitized_event["user"]["ip_address"] != "192.168.1.1"
        assert len(sanitized_event["user"]["ip_address"]) == 16  # SHA256 hash truncated

    def test_before_send_sanitizes_breadcrumbs(self):
        """Test before_send hook sanitizes breadcrumbs."""
        event = {
            "breadcrumbs": [
                {
                    "message": "API call",
                    "data": {
                        "api_key": "sk_test_123",
                        "endpoint": "/api/test"
                    }
                }
            ]
        }

        sanitized_event = before_send(event, {})

        assert "REDACTED_API_KEY" in str(sanitized_event["breadcrumbs"][0]["data"])


class TestUserContext:
    """Test user context management."""

    @patch('backend.observability.errors.sentry_sdk.configure_scope')
    def test_add_user_context(self, mock_scope):
        """Test adding user context."""
        mock_scope_obj = MagicMock()
        mock_scope.return_value.__enter__ = Mock(return_value=mock_scope_obj)
        mock_scope.return_value.__exit__ = Mock(return_value=False)

        add_user_context(
            user_id="user123",
            email="test@example.com",
            username="testuser",
            role="member",
            tier="premium"
        )

        # Verify set_user was called
        mock_scope_obj.set_user.assert_called_once()
        user_data = mock_scope_obj.set_user.call_args[0][0]

        assert user_data["id"] == "user123"
        assert user_data["username"] == "testuser"
        assert user_data["role"] == "premium"
        # Email should be hashed
        assert user_data["email"] != "test@example.com"

    @patch('backend.observability.errors.sentry_sdk.configure_scope')
    def test_clear_user_context(self, mock_scope):
        """Test clearing user context."""
        mock_scope_obj = MagicMock()
        mock_scope.return_value.__enter__ = Mock(return_value=mock_scope_obj)
        mock_scope.return_value.__exit__ = Mock(return_value=False)

        clear_user_context()

        mock_scope_obj.set_user.assert_called_once_with(None)

    @patch('backend.observability.errors.sentry_sdk.configure_scope')
    def test_add_request_context(self, mock_scope, mock_request):
        """Test adding request context."""
        mock_scope_obj = MagicMock()
        mock_scope.return_value.__enter__ = Mock(return_value=mock_scope_obj)
        mock_scope.return_value.__exit__ = Mock(return_value=False)

        add_request_context(mock_request)

        # Verify context was set
        mock_scope_obj.set_context.assert_called()
        mock_scope_obj.set_tag.assert_called()


class TestErrorCapture:
    """Test error capture utilities."""

    @patch('backend.observability.error_utils.sentry_capture_exception')
    @patch('backend.observability.error_utils.sentry_sdk.push_scope')
    def test_capture_exception_basic(self, mock_push_scope, mock_capture):
        """Test basic exception capture."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = Mock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = Mock(return_value=False)
        mock_capture.return_value = "event-123"

        error = ValueError("Test error")
        event_id = capture_exception(error)

        assert event_id == "event-123"
        mock_capture.assert_called_once_with(error)

    @patch('backend.observability.error_utils.sentry_capture_exception')
    @patch('backend.observability.error_utils.sentry_sdk.push_scope')
    def test_capture_exception_with_context(self, mock_push_scope, mock_capture):
        """Test exception capture with context."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = Mock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = Mock(return_value=False)

        error = ValueError("Test error")
        capture_exception(
            error,
            context={"payment": {"amount": 100}},
            tags={"payment_type": "subscription"},
            level="error"
        )

        # Verify context was set
        mock_scope.set_context.assert_called_with("payment", {"amount": 100})
        mock_scope.set_tag.assert_called_with("payment_type", "subscription")
        mock_scope.set_level.assert_called_with("error")

    @patch('backend.observability.error_utils.sentry_capture_message')
    @patch('backend.observability.error_utils.sentry_sdk.push_scope')
    def test_capture_message(self, mock_push_scope, mock_capture):
        """Test message capture."""
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = Mock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = Mock(return_value=False)
        mock_capture.return_value = "event-456"

        event_id = capture_message(
            "Payment successful",
            level="info",
            context={"payment": {"amount": 100}},
            tags={"event_type": "payment"}
        )

        assert event_id == "event-456"
        mock_capture.assert_called_once_with("Payment successful", level="info")


class TestBreadcrumbs:
    """Test breadcrumb management."""

    @patch('backend.observability.error_utils.sentry_sdk.add_breadcrumb')
    def test_add_breadcrumb(self, mock_add):
        """Test adding breadcrumb."""
        add_breadcrumb(
            "payment",
            "Payment initiated",
            {"amount": 100, "currency": "usd"},
            "info"
        )

        mock_add.assert_called_once_with(
            category="payment",
            message="Payment initiated",
            data={"amount": 100, "currency": "usd"},
            level="info"
        )

    @patch('backend.observability.error_utils.sentry_sdk.configure_scope')
    def test_set_tag(self, mock_scope):
        """Test setting tag."""
        mock_scope_obj = MagicMock()
        mock_scope.return_value.__enter__ = Mock(return_value=mock_scope_obj)
        mock_scope.return_value.__exit__ = Mock(return_value=False)

        set_tag("payment_method", "stripe")

        mock_scope_obj.set_tag.assert_called_once_with("payment_method", "stripe")

    @patch('backend.observability.error_utils.sentry_sdk.configure_scope')
    def test_set_context(self, mock_scope):
        """Test setting context."""
        mock_scope_obj = MagicMock()
        mock_scope.return_value.__enter__ = Mock(return_value=mock_scope_obj)
        mock_scope.return_value.__exit__ = Mock(return_value=False)

        set_context("payment", {"amount": 100, "currency": "usd"})

        mock_scope_obj.set_context.assert_called_once_with(
            "payment",
            {"amount": 100, "currency": "usd"}
        )


class TestDomainSpecificTracking:
    """Test domain-specific error tracking helpers."""

    @patch('backend.observability.error_utils.capture_exception')
    def test_track_payment_error(self, mock_capture):
        """Test payment error tracking."""
        error = ValueError("Payment failed")
        track_payment_error(
            error,
            customer_id="cus_123",
            amount=100.0,
            currency="usd",
            payment_method="card"
        )

        # Verify capture_exception was called with correct context
        call_args = mock_capture.call_args
        assert call_args[0][0] == error
        assert call_args[1]["context"]["payment"]["customer_id"] == "cus_123"
        assert call_args[1]["context"]["payment"]["amount"] == 100.0
        assert call_args[1]["tags"]["error_type"] == "payment"
        assert call_args[1]["fingerprint"] == ["payment-error", "ValueError"]

    @patch('backend.observability.error_utils.capture_exception')
    def test_track_auth_error(self, mock_capture):
        """Test authentication error tracking."""
        error = ValueError("Auth failed")
        track_auth_error(
            error,
            username="testuser",
            auth_method="password",
            reason="invalid_credentials"
        )

        call_args = mock_capture.call_args
        assert call_args[1]["context"]["authentication"]["username"] == "testuser"
        assert call_args[1]["tags"]["error_type"] == "authentication"
        assert call_args[1]["fingerprint"] == ["auth-error", "ValueError", "password"]

    @patch('backend.observability.error_utils.capture_exception')
    def test_track_subscription_error(self, mock_capture):
        """Test subscription error tracking."""
        error = ValueError("Subscription failed")
        track_subscription_error(
            error,
            customer_id="cus_123",
            subscription_id="sub_456",
            tier="premium",
            action="create"
        )

        call_args = mock_capture.call_args
        assert call_args[1]["context"]["subscription"]["tier"] == "premium"
        assert call_args[1]["tags"]["subscription_action"] == "create"

    @patch('backend.observability.error_utils.capture_exception')
    def test_track_api_error(self, mock_capture):
        """Test API error tracking."""
        error = ValueError("API failed")
        track_api_error(
            error,
            endpoint="/v1/test",
            method="POST",
            status_code=500
        )

        call_args = mock_capture.call_args
        assert call_args[1]["context"]["api"]["endpoint"] == "/v1/test"
        assert call_args[1]["tags"]["status_code"] == "500"

    @patch('backend.observability.error_utils.capture_exception')
    def test_track_database_error(self, mock_capture):
        """Test database error tracking."""
        error = ValueError("DB error")
        track_database_error(
            error,
            operation="INSERT",
            table="subscriptions"
        )

        call_args = mock_capture.call_args
        assert call_args[1]["context"]["database"]["operation"] == "INSERT"
        assert call_args[1]["tags"]["db_table"] == "subscriptions"


class TestTracesSampler:
    """Test dynamic traces sampling."""

    def test_traces_sampler_critical_endpoint(self):
        """Test 100% sampling for critical endpoints."""
        context = {
            "transaction_context": {
                "name": "POST /api/payments"
            }
        }

        sample_rate = traces_sampler(context)
        assert sample_rate == 1.0

    def test_traces_sampler_health_check(self):
        """Test low sampling for health checks."""
        context = {
            "transaction_context": {
                "name": "GET /health"
            }
        }

        sample_rate = traces_sampler(context)
        assert sample_rate == 0.01

    def test_traces_sampler_default(self):
        """Test default sampling for other endpoints."""
        context = {
            "transaction_context": {
                "name": "GET /api/members"
            }
        }

        sample_rate = traces_sampler(context)
        assert sample_rate == 0.1


class TestErrorTrackingMiddleware:
    """Test error tracking middleware."""

    @pytest.mark.asyncio
    @patch('backend.middleware.error_tracking_middleware.add_request_context')
    @patch('backend.middleware.error_tracking_middleware.add_user_context')
    @patch('backend.middleware.error_tracking_middleware.add_breadcrumb')
    async def test_middleware_adds_context(self, mock_breadcrumb, mock_user_context, mock_request_context, mock_settings):
        """Test middleware adds request and user context."""
        with patch('backend.middleware.error_tracking_middleware.get_settings', return_value=mock_settings):
            # Create mock request with JWT token
            token = jwt.encode(
                {
                    "sub": "user123",
                    "email": "test@example.com",
                    "role": "member"
                },
                mock_settings.JWT_SECRET,
                algorithm=mock_settings.JWT_ALGORITHM
            )

            request = Mock(spec=Request)
            request.method = "GET"
            request.url = Mock()
            request.url.path = "/api/test"
            request.url.__str__ = Mock(return_value="http://localhost/api/test")
            request.headers = {"Authorization": f"Bearer {token}"}

            async def mock_call_next(req):
                response = Mock()
                response.status_code = 200
                return response

            middleware = ErrorTrackingMiddleware(Mock())
            await middleware.dispatch(request, mock_call_next)

            # Verify contexts were added
            mock_request_context.assert_called_once()
            mock_user_context.assert_called_once()
            assert mock_breadcrumb.call_count >= 2  # Start and end breadcrumbs

    @pytest.mark.asyncio
    @patch('backend.middleware.error_tracking_middleware.add_breadcrumb')
    async def test_middleware_tracks_operations(self, mock_breadcrumb):
        """Test middleware breadcrumb tracking helpers."""
        # Test business operation tracking
        track_business_operation("payment_processed", {"amount": 100})
        mock_breadcrumb.assert_called()

        # Test external API tracking
        track_external_api_call("stripe", "/v1/subscriptions", "POST", 200, 150.5)
        assert mock_breadcrumb.call_count >= 2

        # Test database tracking
        track_db_op_middleware("INSERT", "subscriptions", 25.3, 1)
        assert mock_breadcrumb.call_count >= 3

        # Test cache tracking
        track_cache_operation("GET", "user:123", hit=True, duration_ms=2.5)
        assert mock_breadcrumb.call_count >= 4


class TestIntegration:
    """Integration tests for error tracking."""

    @pytest.mark.asyncio
    @patch('backend.observability.errors.sentry_sdk.init')
    @patch('backend.observability.errors.get_settings')
    async def test_end_to_end_error_tracking(self, mock_get_settings, mock_sentry_init, mock_settings, fastapi_app):
        """Test end-to-end error tracking flow."""
        mock_get_settings.return_value = mock_settings

        # Initialize Sentry
        init_sentry(fastapi_app)

        # Simulate error
        try:
            raise ValueError("Test error")
        except ValueError as e:
            # Track error with context
            event_id = capture_exception(
                e,
                context={"test": {"value": 123}},
                tags={"test": "true"}
            )

        # Verify Sentry was initialized
        mock_sentry_init.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
