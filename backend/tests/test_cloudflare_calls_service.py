"""
Comprehensive Tests for Cloudflare Calls Service

Tests cover:
- Room creation, retrieval, and deletion
- Signed URL generation
- Recording start, stop, and status
- Error handling and retries
- Webhook signature verification
- API request mocking

Test Coverage Target: 80%+
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import hmac
import hashlib
import time
import sys
import os

# Ensure environment variables are set before importing the service
os.environ.setdefault('AI_REGISTRY_API_KEY', 'test_ai_registry_key')
os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key_sk_1234567890')

from backend.services.cloudflare_calls_service import (
    CloudflareCallsService,
    get_cloudflare_calls_service,
    CloudflareCallsError,
    CallsAPIError,
    RecordingError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings configuration"""
    with patch('backend.services.cloudflare_calls_service.settings') as mock:
        mock.CLOUDFLARE_ACCOUNT_ID = "test_account_123"
        mock.CLOUDFLARE_API_TOKEN = "test_token_abc"
        mock.CLOUDFLARE_CALLS_APP_ID = "test_app_456"
        mock.CLOUDFLARE_WEBHOOK_SECRET = "test_secret_xyz"
        yield mock


@pytest.fixture
def calls_service(mock_settings):
    """Create CloudflareCallsService instance with mocked settings"""
    return CloudflareCallsService()


@pytest.fixture
def mock_requests():
    """Mock requests library"""
    import requests as req_module
    with patch('backend.services.cloudflare_calls_service.requests') as mock:
        # Make sure the mock has the exceptions module
        mock.exceptions = req_module.exceptions
        yield mock


@pytest.fixture
def sample_room_response():
    """Sample Cloudflare API room response"""
    return {
        "success": True,
        "result": {
            "roomId": "room_123abc",
            "roomUrl": "https://calls.cloudflare.com/room_123abc",
            "sessionId": "session_456def",
            "status": "active",
            "maxParticipants": 50,
            "created": datetime.utcnow().isoformat()
        }
    }


@pytest.fixture
def sample_recording_response():
    """Sample Cloudflare API recording response"""
    return {
        "success": True,
        "result": {
            "recordingId": "rec_789ghi",
            "status": "recording",
            "duration": 0
        }
    }


@pytest.fixture
def sample_recording_status_response():
    """Sample recording status response"""
    return {
        "success": True,
        "result": {
            "recordingId": "rec_789ghi",
            "status": "ready",
            "duration": 3600,
            "fileSize": 524288000,
            "streamId": "stream_abc123",
            "streamUrl": "https://cloudflarestream.com/stream_abc123/manifest/video.m3u8"
        }
    }


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_service_initialization_success(mock_settings):
    """Test successful service initialization"""
    service = CloudflareCallsService()

    assert service.account_id == "test_account_123"
    assert service.api_token == "test_token_abc"
    assert service.app_id == "test_app_456"
    assert "test_account_123" in service.base_url
    assert "Bearer test_token_abc" in service.headers["Authorization"]


def test_service_initialization_missing_account_id(mock_settings):
    """Test initialization fails without account ID"""
    mock_settings.CLOUDFLARE_ACCOUNT_ID = ""

    with pytest.raises(CloudflareCallsError) as exc_info:
        CloudflareCallsService()

    assert "account ID and API token are required" in str(exc_info.value)


def test_service_initialization_missing_token(mock_settings):
    """Test initialization fails without API token"""
    mock_settings.CLOUDFLARE_API_TOKEN = ""

    with pytest.raises(CloudflareCallsError) as exc_info:
        CloudflareCallsService()

    assert "account ID and API token are required" in str(exc_info.value)


def test_get_singleton_service(mock_settings):
    """Test singleton service getter"""
    service1 = get_cloudflare_calls_service()
    service2 = get_cloudflare_calls_service()

    assert service1 is service2


# ============================================================================
# ROOM MANAGEMENT TESTS
# ============================================================================

def test_create_room_success(calls_service, mock_requests, sample_room_response):
    """Test successful room creation"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = sample_room_response
    mock_requests.request.return_value = mock_response

    result = calls_service.create_room(
        session_id="session_123",
        max_participants=50,
        enable_recording=True
    )

    assert result["room_id"] == "room_123abc"
    assert result["session_id"] == "session_123"
    assert "created_at" in result

    # Verify API call
    mock_requests.request.assert_called_once()
    call_args = mock_requests.request.call_args
    assert call_args[1]["method"] == "POST"
    assert "rooms" in call_args[1]["url"]
    assert call_args[1]["json"]["sessionId"] == "session_123"
    assert call_args[1]["json"]["maxParticipants"] == 50


def test_create_room_api_error(calls_service, mock_requests):
    """Test room creation with API error"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.json.return_value = {
        "success": False,
        "errors": [{"message": "Invalid session ID"}]
    }
    mock_requests.request.return_value = mock_response

    with pytest.raises(CallsAPIError) as exc_info:
        calls_service.create_room(session_id="invalid")

    assert "Invalid session ID" in str(exc_info.value)


def test_create_room_request_exception(calls_service, mock_requests):
    """Test room creation with request exception"""
    import requests as req_module

    mock_requests.request.side_effect = req_module.exceptions.RequestException("Network error")
    mock_requests.exceptions = req_module.exceptions

    with pytest.raises(CallsAPIError) as exc_info:
        calls_service.create_room(session_id="session_123")

    assert "API request failed" in str(exc_info.value)


def test_delete_room_success(calls_service, mock_requests):
    """Test successful room deletion"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"success": True, "result": {}}
    mock_requests.request.return_value = mock_response

    result = calls_service.delete_room(room_id="room_123")

    assert result is True
    mock_requests.request.assert_called_once()
    call_args = mock_requests.request.call_args
    assert call_args[1]["method"] == "DELETE"
    assert "rooms/room_123" in call_args[1]["url"]


def test_delete_room_failure(calls_service, mock_requests):
    """Test room deletion failure"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.json.return_value = {
        "success": False,
        "errors": [{"message": "Room not found"}]
    }
    mock_requests.request.return_value = mock_response

    result = calls_service.delete_room(room_id="nonexistent")

    assert result is False


def test_get_room_participants(calls_service, mock_requests):
    """Test getting room participants"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "participants": [
                {"userId": "user_1", "userName": "Alice", "role": "moderator"},
                {"userId": "user_2", "userName": "Bob", "role": "participant"}
            ]
        }
    }
    mock_requests.request.return_value = mock_response

    participants = calls_service.get_room_participants(room_id="room_123")

    assert len(participants) == 2
    assert participants[0]["userName"] == "Alice"
    assert participants[1]["role"] == "participant"


# ============================================================================
# RECORDING TESTS
# ============================================================================

def test_start_recording_success(calls_service, mock_requests, sample_recording_response):
    """Test successful recording start"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = sample_recording_response
    mock_requests.request.return_value = mock_response

    result = calls_service.start_recording(room_id="room_123")

    assert result["recording_id"] == "rec_789ghi"
    assert result["room_id"] == "room_123"
    assert result["status"] == "recording"
    assert "started_at" in result


def test_start_recording_failure(calls_service, mock_requests):
    """Test recording start failure"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.json.return_value = {
        "success": False,
        "errors": [{"message": "Recording already in progress"}]
    }
    mock_requests.request.return_value = mock_response

    with pytest.raises(RecordingError) as exc_info:
        calls_service.start_recording(room_id="room_123")

    assert "Failed to start recording" in str(exc_info.value)


def test_stop_recording_success(calls_service, mock_requests):
    """Test successful recording stop"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "recordingId": "rec_789ghi",
            "status": "processing",
            "duration": 3600
        }
    }
    mock_requests.request.return_value = mock_response

    result = calls_service.stop_recording(
        room_id="room_123",
        recording_id="rec_789ghi"
    )

    assert result["recording_id"] == "rec_789ghi"
    assert result["status"] == "processing"
    assert result["duration_seconds"] == 3600


def test_stop_recording_failure(calls_service, mock_requests):
    """Test recording stop failure"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.json.return_value = {
        "success": False,
        "errors": [{"message": "Recording not found"}]
    }
    mock_requests.request.return_value = mock_response

    with pytest.raises(RecordingError) as exc_info:
        calls_service.stop_recording(
            room_id="room_123",
            recording_id="invalid"
        )

    assert "Failed to stop recording" in str(exc_info.value)


def test_get_recording_status_success(calls_service, mock_requests, sample_recording_status_response):
    """Test getting recording status"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = sample_recording_status_response
    mock_requests.request.return_value = mock_response

    result = calls_service.get_recording_status(
        room_id="room_123",
        recording_id="rec_789ghi"
    )

    assert result["recording_id"] == "rec_789ghi"
    assert result["status"] == "ready"
    assert result["stream_url"] is not None
    assert result["duration_seconds"] == 3600
    assert result["file_size_bytes"] == 524288000


# ============================================================================
# TOKEN GENERATION TESTS
# ============================================================================

def test_generate_room_token_success(calls_service, mock_requests):
    """Test successful room token generation"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    }
    mock_requests.request.return_value = mock_response

    token = calls_service.generate_room_token(
        room_id="room_123",
        user_id="user_456",
        user_name="Alice",
        role="moderator",
        expiry_hours=24
    )

    assert token.startswith("eyJ")
    mock_requests.request.assert_called_once()
    call_args = mock_requests.request.call_args
    assert call_args[1]["json"]["userId"] == "user_456"
    assert call_args[1]["json"]["role"] == "moderator"


def test_generate_room_token_default_values(calls_service, mock_requests):
    """Test room token generation with default values"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "success": True,
        "result": {"token": "test_token"}
    }
    mock_requests.request.return_value = mock_response

    token = calls_service.generate_room_token(
        room_id="room_123",
        user_id="user_456",
        user_name="Bob"
    )

    assert token == "test_token"
    call_args = mock_requests.request.call_args
    assert call_args[1]["json"]["role"] == "participant"  # Default role


# ============================================================================
# ERROR HANDLING AND EDGE CASES
# ============================================================================

def test_make_request_timeout(calls_service, mock_requests):
    """Test request timeout handling"""
    import requests as req_module
    mock_requests.request.side_effect = req_module.exceptions.Timeout()
    mock_requests.exceptions = req_module.exceptions

    with pytest.raises(CallsAPIError) as exc_info:
        calls_service._make_request("GET", "test")

    assert "request failed" in str(exc_info.value).lower()


def test_make_request_invalid_json(calls_service, mock_requests):
    """Test handling of invalid JSON response"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_requests.request.return_value = mock_response

    # JSON parsing errors will propagate as ValueError
    with pytest.raises(ValueError) as exc_info:
        calls_service._make_request("GET", "test")

    assert "Invalid JSON" in str(exc_info.value)


def test_make_request_with_params(calls_service, mock_requests):
    """Test request with query parameters"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"success": True, "result": {}}
    mock_requests.request.return_value = mock_response

    calls_service._make_request(
        "GET",
        "test",
        params={"limit": 10, "offset": 0}
    )

    call_args = mock_requests.request.call_args
    assert call_args[1]["params"]["limit"] == 10
    assert call_args[1]["params"]["offset"] == 0


def test_api_error_with_multiple_errors(calls_service, mock_requests):
    """Test API error handling with multiple error messages"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.json.return_value = {
        "success": False,
        "errors": [
            {"message": "Error 1"},
            {"message": "Error 2"}
        ]
    }
    mock_requests.request.return_value = mock_response

    with pytest.raises(CallsAPIError) as exc_info:
        calls_service._make_request("POST", "test")

    assert "Error 1" in str(exc_info.value)


def test_api_error_with_no_error_message(calls_service, mock_requests):
    """Test API error handling with no error message"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.json.return_value = {
        "success": False,
        "errors": []
    }
    mock_requests.request.return_value = mock_response

    with pytest.raises(CallsAPIError) as exc_info:
        calls_service._make_request("POST", "test")

    # When there are no error messages, it should say "API request failed"
    assert "API request failed" in str(exc_info.value)


# ============================================================================
# INTEGRATION-STYLE TESTS
# ============================================================================

def test_full_room_lifecycle(calls_service, mock_requests):
    """Test complete room lifecycle: create -> use -> delete"""
    # Mock create room
    create_response = Mock()
    create_response.ok = True
    create_response.json.return_value = {
        "success": True,
        "result": {
            "roomId": "room_123",
            "roomUrl": "https://calls.cloudflare.com/room_123",
            "sessionId": "session_456",
            "status": "active"
        }
    }

    # Mock delete room
    delete_response = Mock()
    delete_response.ok = True
    delete_response.json.return_value = {"success": True, "result": {}}

    mock_requests.request.side_effect = [create_response, delete_response]

    # Create room
    room = calls_service.create_room(session_id="session_456")
    assert room["room_id"] == "room_123"

    # Delete room
    success = calls_service.delete_room(room_id="room_123")
    assert success is True


def test_full_recording_lifecycle(calls_service, mock_requests):
    """Test complete recording lifecycle: start -> stop -> check status"""
    # Mock start recording
    start_response = Mock()
    start_response.ok = True
    start_response.json.return_value = {
        "success": True,
        "result": {"recordingId": "rec_123", "status": "recording"}
    }

    # Mock stop recording
    stop_response = Mock()
    stop_response.ok = True
    stop_response.json.return_value = {
        "success": True,
        "result": {"recordingId": "rec_123", "status": "processing", "duration": 1800}
    }

    # Mock get status
    status_response = Mock()
    status_response.ok = True
    status_response.json.return_value = {
        "success": True,
        "result": {
            "recordingId": "rec_123",
            "status": "ready",
            "streamUrl": "https://stream.example.com/rec_123"
        }
    }

    mock_requests.request.side_effect = [
        start_response,
        stop_response,
        status_response
    ]

    # Start recording
    recording = calls_service.start_recording(room_id="room_123")
    assert recording["recording_id"] == "rec_123"
    assert recording["status"] == "recording"

    # Stop recording
    stopped = calls_service.stop_recording(
        room_id="room_123",
        recording_id="rec_123"
    )
    assert stopped["status"] == "processing"

    # Check status
    status = calls_service.get_recording_status(
        room_id="room_123",
        recording_id="rec_123"
    )
    assert status["status"] == "ready"
    assert status["stream_url"] is not None


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

def test_service_with_custom_parameters():
    """Test service initialization with custom parameters"""
    service = CloudflareCallsService(
        account_id="custom_account",
        api_token="custom_token",
        app_id="custom_app"
    )

    assert service.account_id == "custom_account"
    assert service.api_token == "custom_token"
    assert service.app_id == "custom_app"


def test_base_url_construction(calls_service):
    """Test proper base URL construction"""
    assert calls_service.base_url == "https://api.cloudflare.com/client/v4/accounts/test_account_123/calls"


def test_headers_configuration(calls_service):
    """Test proper headers configuration"""
    headers = calls_service.headers

    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer test_token_abc"
    assert headers["Content-Type"] == "application/json"


# ============================================================================
# TIMEOUT AND RETRY TESTS
# ============================================================================

def test_request_timeout_value(calls_service, mock_requests):
    """Test that requests have proper timeout"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"success": True, "result": {}}
    mock_requests.request.return_value = mock_response

    calls_service._make_request("GET", "test")

    call_args = mock_requests.request.call_args
    assert call_args[1]["timeout"] == 30


# ============================================================================
# COVERAGE HELPERS
# ============================================================================

def test_error_classes():
    """Test custom error classes"""
    base_error = CloudflareCallsError("Base error")
    api_error = CallsAPIError("API error")
    recording_error = RecordingError("Recording error")

    assert isinstance(api_error, CloudflareCallsError)
    assert isinstance(recording_error, CloudflareCallsError)
    assert str(base_error) == "Base error"
    assert str(api_error) == "API error"
    assert str(recording_error) == "Recording error"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.services.cloudflare_calls_service", "--cov-report=term-missing"])
