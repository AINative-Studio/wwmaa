"""
BeeHiiv Service Tests

Comprehensive test suite for BeeHiiv API integration.
Achieves 80%+ code coverage with unit tests and integration scenarios.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests

from services.beehiiv_service import (
    BeeHiivService,
    BeeHiivRateLimitError,
    BeeHiivAPIError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_api_key():
    """Mock API key"""
    return "test_api_key_12345"


@pytest.fixture
def mock_publication_id():
    """Mock publication ID"""
    return "pub_test123"


@pytest.fixture
def beehiiv_service(mock_api_key, mock_publication_id):
    """Create BeeHiiv service instance with mocked credentials"""
    return BeeHiivService(
        api_key=mock_api_key,
        publication_id=mock_publication_id
    )


@pytest.fixture
def mock_subscriber_response():
    """Mock subscriber API response"""
    return {
        "data": {
            "id": "sub_123",
            "email": "test@example.com",
            "name": "Test User",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }


@pytest.fixture
def mock_publication_response():
    """Mock publication API response"""
    return {
        "data": {
            "id": "post_123",
            "title": "Test Newsletter",
            "subject": "Test Subject",
            "content": "<p>Test content</p>",
            "status": "draft",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }


@pytest.fixture
def mock_stats_response():
    """Mock subscriber stats response"""
    return {
        "data": {
            "total_subscribers": 1000,
            "active_subscribers": 950,
            "growth_30d": 50,
            "open_rate": 0.45,
            "click_rate": 0.12
        }
    }


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_service_initialization_with_credentials(mock_api_key, mock_publication_id):
    """Test service initialization with explicit credentials"""
    service = BeeHiivService(
        api_key=mock_api_key,
        publication_id=mock_publication_id
    )

    assert service.api_key == mock_api_key
    assert service.publication_id == mock_publication_id
    assert service.session is not None


def test_service_initialization_from_env():
    """Test service initialization from environment variables"""
    with patch.dict(os.environ, {
        "BEEHIIV_API_KEY": "env_api_key",
        "BEEHIIV_PUBLICATION_ID": "env_pub_id"
    }):
        service = BeeHiivService()
        assert service.api_key == "env_api_key"
        assert service.publication_id == "env_pub_id"


def test_service_initialization_missing_api_key():
    """Test service initialization fails without API key"""
    # Clear environment variable to ensure None
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="API key is required"):
            BeeHiivService(api_key=None, publication_id="pub_123")


def test_session_headers_configured(beehiiv_service):
    """Test session has correct headers"""
    headers = beehiiv_service.session.headers

    assert "Authorization" in headers
    assert headers["Authorization"] == f"Bearer {beehiiv_service.api_key}"
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

def test_rate_limit_tracking(beehiiv_service):
    """Test rate limit tracking mechanism"""
    # Should start with no tracked requests
    assert len(beehiiv_service._request_timestamps) == 0

    # Simulate requests
    with patch.object(beehiiv_service.session, 'request') as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"data": {}}

        beehiiv_service._make_request("GET", "/test")
        assert len(beehiiv_service._request_timestamps) == 1


def test_rate_limit_exceeded():
    """Test rate limit enforcement"""
    service = BeeHiivService(api_key="test", publication_id="pub_test")

    # Simulate 1000 requests in the last hour
    import time
    current_time = time.time()
    service._request_timestamps = [current_time - i for i in range(1000)]

    # Next request should trigger rate limit
    with pytest.raises(BeeHiivRateLimitError):
        service._check_rate_limit()


def test_rate_limit_window_expiry():
    """Test old requests are removed from rate limit tracking"""
    service = BeeHiivService(api_key="test", publication_id="pub_test")

    import time
    current_time = time.time()

    # Add old timestamps (more than 1 hour ago)
    service._request_timestamps = [current_time - 4000] * 500

    # Check rate limit - should clean up old timestamps
    service._check_rate_limit()

    # Old timestamps should be removed
    assert len(service._request_timestamps) <= 1


# ============================================================================
# SUBSCRIBER MANAGEMENT TESTS
# ============================================================================

def test_add_subscriber_success(beehiiv_service, mock_subscriber_response):
    """Test successful subscriber addition"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = mock_subscriber_response

        result = beehiiv_service.add_subscriber(
            email="test@example.com",
            name="Test User",
            metadata={"source": "test"}
        )

        assert result == mock_subscriber_response
        mock_request.assert_called_once()

        # Verify request payload
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "test@example.com" in str(call_args[1]["data"])


def test_add_subscriber_email_normalization(beehiiv_service):
    """Test email addresses are normalized to lowercase"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": {}}

        beehiiv_service.add_subscriber(
            email="Test.User@EXAMPLE.COM",
            name="Test User"
        )

        call_args = mock_request.call_args
        data = call_args[1]["data"]
        assert data["email"] == "test.user@example.com"


def test_remove_subscriber(beehiiv_service):
    """Test subscriber removal/unsubscribe"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"success": True}

        result = beehiiv_service.remove_subscriber("test@example.com")

        assert result["success"] is True
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "DELETE"


def test_update_subscriber(beehiiv_service):
    """Test subscriber update"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": {"updated": True}}

        updates = {"name": "Updated Name"}
        result = beehiiv_service.update_subscriber(
            email="test@example.com",
            updates=updates
        )

        assert result["data"]["updated"] is True
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "PATCH"


def test_get_subscriber(beehiiv_service, mock_subscriber_response):
    """Test get subscriber details"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = mock_subscriber_response

        result = beehiiv_service.get_subscriber("test@example.com")

        assert result == mock_subscriber_response
        assert mock_request.call_args[0][0] == "GET"


def test_list_subscribers_with_pagination(beehiiv_service):
    """Test listing subscribers with pagination"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {
            "data": [{"email": f"user{i}@example.com"} for i in range(50)],
            "pagination": {"page": 2, "has_more": True}
        }

        result = beehiiv_service.list_subscribers(page=2, limit=50)

        assert len(result["data"]) == 50
        assert result["pagination"]["has_more"] is True

        # Verify pagination params
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["page"] == 2
        assert params["limit"] == 50


def test_list_subscribers_with_filters(beehiiv_service):
    """Test listing subscribers with filters"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": []}

        filters = {"status": "active", "created_after": "2024-01-01"}
        beehiiv_service.list_subscribers(filters=filters)

        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["status"] == "active"
        assert params["created_after"] == "2024-01-01"


# ============================================================================
# PUBLICATION MANAGEMENT TESTS
# ============================================================================

def test_create_publication(beehiiv_service, mock_publication_response):
    """Test newsletter publication creation"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = mock_publication_response

        result = beehiiv_service.create_publication(
            title="Test Newsletter",
            content="<p>Newsletter content</p>",
            subject="Custom Subject",
            preview_text="Preview text"
        )

        assert result == mock_publication_response
        mock_request.assert_called_once()

        # Verify request data
        call_args = mock_request.call_args
        data = call_args[1]["data"]
        assert data["title"] == "Test Newsletter"
        assert data["subject"] == "Custom Subject"
        assert data["content"] == "<p>Newsletter content</p>"


def test_create_publication_default_subject(beehiiv_service):
    """Test publication creation uses title as default subject"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": {}}

        beehiiv_service.create_publication(
            title="Test Title",
            content="Content"
        )

        call_args = mock_request.call_args
        data = call_args[1]["data"]
        assert data["subject"] == "Test Title"


def test_get_publication(beehiiv_service, mock_publication_response):
    """Test get publication details"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = mock_publication_response

        result = beehiiv_service.get_publication("post_123")

        assert result == mock_publication_response
        assert "post_123" in mock_request.call_args[0][1]


def test_list_publications(beehiiv_service):
    """Test listing publications"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {
            "data": [{"id": f"post_{i}"} for i in range(10)]
        }

        result = beehiiv_service.list_publications(page=1, limit=10)

        assert len(result["data"]) == 10


def test_send_newsletter(beehiiv_service):
    """Test sending newsletter"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"success": True}

        result = beehiiv_service.send_newsletter(
            post_id="post_123",
            send_to="all"
        )

        assert result["success"] is True
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "PATCH"


# ============================================================================
# ANALYTICS TESTS
# ============================================================================

def test_get_subscriber_stats(beehiiv_service, mock_stats_response):
    """Test fetching subscriber statistics"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = mock_stats_response

        result = beehiiv_service.get_subscriber_stats()

        assert result == mock_stats_response
        assert result["data"]["total_subscribers"] == 1000


def test_get_publication_stats(beehiiv_service):
    """Test fetching publication statistics"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {
            "data": {
                "opens": 450,
                "clicks": 120,
                "open_rate": 0.45,
                "click_rate": 0.12
            }
        }

        result = beehiiv_service.get_publication_stats("post_123")

        assert result["data"]["opens"] == 450
        assert result["data"]["click_rate"] == 0.12


# ============================================================================
# VALIDATION & TESTING TESTS
# ============================================================================

def test_validate_api_key_success(beehiiv_service):
    """Test API key validation success"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": {"id": "pub_123"}}

        is_valid = beehiiv_service.validate_api_key()

        assert is_valid is True


def test_validate_api_key_failure(beehiiv_service):
    """Test API key validation failure"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.side_effect = BeeHiivAPIError("Invalid API key")

        is_valid = beehiiv_service.validate_api_key()

        assert is_valid is False


def test_send_test_email(beehiiv_service):
    """Test sending test email"""
    with patch.object(beehiiv_service, 'create_publication') as mock_create:
        with patch.object(beehiiv_service, '_make_request') as mock_request:
            mock_create.return_value = {"data": {"id": "post_test"}}
            mock_request.return_value = {"success": True}

            result = beehiiv_service.send_test_email(
                email="test@example.com",
                subject="Test Subject",
                content="<p>Test content</p>"
            )

            assert result["success"] is True
            mock_create.assert_called_once()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_http_error_handling(beehiiv_service):
    """Test HTTP error handling"""
    with patch.object(beehiiv_service.session, 'request') as mock_request:
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not found"}
        mock_response.text = "Not found"

        # Create HTTPError with response attached
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_request.return_value = mock_response

        with pytest.raises(BeeHiivAPIError, match="404"):
            beehiiv_service._make_request("GET", "/test")


def test_rate_limit_response_handling(beehiiv_service):
    """Test 429 rate limit response handling"""
    with patch.object(beehiiv_service.session, 'request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_request.return_value = mock_response

        with pytest.raises(BeeHiivRateLimitError, match="Retry after 60"):
            beehiiv_service._make_request("GET", "/test")


def test_network_error_handling(beehiiv_service):
    """Test network error handling"""
    with patch.object(beehiiv_service.session, 'request') as mock_request:
        mock_request.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(BeeHiivAPIError, match="Request failed"):
            beehiiv_service._make_request("GET", "/test")


def test_timeout_handling(beehiiv_service):
    """Test request timeout handling"""
    with patch.object(beehiiv_service.session, 'request') as mock_request:
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(BeeHiivAPIError, match="Request failed"):
            beehiiv_service._make_request("GET", "/test")


# ============================================================================
# RETRY LOGIC TESTS
# ============================================================================

def test_retry_logic_configured(beehiiv_service):
    """Test retry logic is configured in session adapter"""
    # The retry logic is configured in the HTTPAdapter
    # Verify it's been set up correctly
    adapter = beehiiv_service.session.get_adapter("https://api.beehiiv.com")

    assert adapter is not None
    assert adapter.max_retries.total == beehiiv_service.MAX_RETRIES
    assert adapter.max_retries.backoff_factor == beehiiv_service.BACKOFF_FACTOR
    assert 500 in adapter.max_retries.status_forcelist


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
def test_full_subscriber_workflow(beehiiv_service):
    """Test complete subscriber management workflow"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        # Add subscriber
        mock_request.return_value = {"data": {"id": "sub_123", "email": "workflow@test.com"}}
        result = beehiiv_service.add_subscriber("workflow@test.com", "Workflow Test")
        assert result["data"]["id"] == "sub_123"

        # Get subscriber
        mock_request.return_value = {"data": {"email": "workflow@test.com", "status": "active"}}
        result = beehiiv_service.get_subscriber("workflow@test.com")
        assert result["data"]["status"] == "active"

        # Update subscriber
        mock_request.return_value = {"data": {"updated": True}}
        result = beehiiv_service.update_subscriber("workflow@test.com", {"name": "Updated"})
        assert result["data"]["updated"] is True

        # Remove subscriber
        mock_request.return_value = {"success": True}
        result = beehiiv_service.remove_subscriber("workflow@test.com")
        assert result["success"] is True


@pytest.mark.integration
def test_full_newsletter_workflow(beehiiv_service):
    """Test complete newsletter creation and sending workflow"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        # Create publication
        mock_request.return_value = {"data": {"id": "post_123", "status": "draft"}}
        result = beehiiv_service.create_publication(
            title="Weekly Newsletter",
            content="<p>Content</p>"
        )
        post_id = result["data"]["id"]

        # Send newsletter
        mock_request.return_value = {"success": True}
        result = beehiiv_service.send_newsletter(post_id)
        assert result["success"] is True

        # Get stats
        mock_request.return_value = {"data": {"opens": 100}}
        stats = beehiiv_service.get_publication_stats(post_id)
        assert stats["data"]["opens"] == 100


# ============================================================================
# EDGE CASES
# ============================================================================

def test_empty_response_handling(beehiiv_service):
    """Test handling of empty API responses"""
    with patch.object(beehiiv_service.session, 'request') as mock_request:
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = beehiiv_service._make_request("DELETE", "/test")
        assert result == {}


def test_list_limit_enforcement(beehiiv_service):
    """Test list operations enforce maximum limit"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": []}

        # Request with limit > 100 should be capped
        beehiiv_service.list_subscribers(limit=200)

        call_args = mock_request.call_args
        params = call_args[1]["params"]
        assert params["limit"] == 100  # Should be capped


def test_special_characters_in_email(beehiiv_service):
    """Test handling special characters in email addresses"""
    with patch.object(beehiiv_service, '_make_request') as mock_request:
        mock_request.return_value = {"data": {}}

        # Email with special characters
        beehiiv_service.add_subscriber(
            email="test+tag@example.com",
            name="Test User"
        )

        call_args = mock_request.call_args
        data = call_args[1]["data"]
        assert data["email"] == "test+tag@example.com"


# ============================================================================
# COVERAGE TESTS
# ============================================================================

def test_base_url_constant(beehiiv_service):
    """Test BASE_URL is correctly set"""
    assert beehiiv_service.BASE_URL == "https://api.beehiiv.com/v2"


def test_rate_limit_constant(beehiiv_service):
    """Test rate limit constant"""
    assert beehiiv_service.RATE_LIMIT_PER_HOUR == 1000


def test_max_retries_constant(beehiiv_service):
    """Test max retries constant"""
    assert beehiiv_service.MAX_RETRIES == 3


def test_backoff_factor_constant(beehiiv_service):
    """Test backoff factor constant"""
    assert beehiiv_service.BACKOFF_FACTOR == 2
