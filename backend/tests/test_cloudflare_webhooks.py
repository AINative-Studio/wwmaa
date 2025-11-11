"""
Comprehensive Tests for Cloudflare Webhooks

Tests cover:
- Webhook signature verification
- Recording ready event handling
- Recording failed event handling
- Database updates
- Error handling
- Security validations

Test Coverage Target: 80%+
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json
import hmac
import hashlib
import time
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.routes.webhooks.cloudflare import (
    router,
    verify_cloudflare_signature,
    handle_recording_ready,
    handle_recording_failed
)
from backend.config import settings


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create test client"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def webhook_secret():
    """Webhook secret for signature generation"""
    return "test_webhook_secret_xyz"


@pytest.fixture
def valid_payload():
    """Valid webhook payload"""
    return {
        "event_type": "recording.ready",
        "data": {
            "recording_id": "rec_123abc",
            "room_id": "room_456def",
            "stream_url": "https://cloudflarestream.com/abc123/manifest/video.m3u8",
            "stream_id": "stream_abc123",
            "duration": 3600,
            "size_bytes": 524288000
        }
    }


@pytest.fixture
def failed_payload():
    """Failed recording webhook payload"""
    return {
        "event_type": "recording.failed",
        "data": {
            "recording_id": "rec_789xyz",
            "room_id": "room_456def",
            "error_message": "Processing timeout"
        }
    }


def generate_signature(payload: dict, secret: str, timestamp: int = None) -> tuple:
    """Generate valid webhook signature"""
    if timestamp is None:
        timestamp = int(time.time())

    payload_str = json.dumps(payload)
    signed_payload = f"{timestamp}.{payload_str}"

    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature, str(timestamp), payload_str


@pytest.fixture
def mock_zerodb():
    """Mock ZeroDB service"""
    with patch('backend.routes.webhooks.cloudflare.get_zerodb_service') as mock:
        zerodb = Mock()
        zerodb.query_collection = Mock(return_value=[])
        zerodb.update_document = Mock()
        mock.return_value = zerodb
        yield zerodb


# ============================================================================
# SIGNATURE VERIFICATION TESTS
# ============================================================================

def test_verify_signature_valid(webhook_secret, valid_payload):
    """Test successful signature verification"""
    signature, timestamp, payload_str = generate_signature(valid_payload, webhook_secret)

    result = verify_cloudflare_signature(
        payload=payload_str.encode('utf-8'),
        signature=signature,
        timestamp=timestamp,
        secret=webhook_secret
    )

    assert result is True


def test_verify_signature_invalid(webhook_secret, valid_payload):
    """Test signature verification with invalid signature"""
    _, timestamp, payload_str = generate_signature(valid_payload, webhook_secret)

    with pytest.raises(HTTPException) as exc_info:
        verify_cloudflare_signature(
            payload=payload_str.encode('utf-8'),
            signature="invalid_signature",
            timestamp=timestamp,
            secret=webhook_secret
        )

    assert exc_info.value.status_code == 401
    assert "Invalid webhook signature" in exc_info.value.detail


def test_verify_signature_wrong_secret(webhook_secret, valid_payload):
    """Test signature verification with wrong secret"""
    signature, timestamp, payload_str = generate_signature(valid_payload, webhook_secret)

    with pytest.raises(HTTPException) as exc_info:
        verify_cloudflare_signature(
            payload=payload_str.encode('utf-8'),
            signature=signature,
            timestamp=timestamp,
            secret="wrong_secret"
        )

    assert exc_info.value.status_code == 401


def test_verify_signature_old_timestamp(webhook_secret, valid_payload):
    """Test signature verification with old timestamp"""
    old_timestamp = int(time.time()) - 400  # 6 minutes ago
    signature, _, payload_str = generate_signature(valid_payload, webhook_secret, old_timestamp)

    with pytest.raises(HTTPException) as exc_info:
        verify_cloudflare_signature(
            payload=payload_str.encode('utf-8'),
            signature=signature,
            timestamp=str(old_timestamp),
            secret=webhook_secret
        )

    assert exc_info.value.status_code == 401
    assert "timestamp too old" in exc_info.value.detail.lower()


def test_verify_signature_future_timestamp(webhook_secret, valid_payload):
    """Test signature verification with future timestamp"""
    future_timestamp = int(time.time()) + 400  # 6 minutes in future
    signature, _, payload_str = generate_signature(valid_payload, webhook_secret, future_timestamp)

    with pytest.raises(HTTPException) as exc_info:
        verify_cloudflare_signature(
            payload=payload_str.encode('utf-8'),
            signature=signature,
            timestamp=str(future_timestamp),
            secret=webhook_secret
        )

    assert exc_info.value.status_code == 401


# ============================================================================
# WEBHOOK ENDPOINT TESTS
# ============================================================================

@patch('backend.routes.webhooks.cloudflare.settings')
def test_webhook_missing_signature_header(mock_settings, client, valid_payload):
    """Test webhook request without signature header"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = "test_secret"

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=valid_payload
    )

    assert response.status_code == 400
    assert "Missing required webhook headers" in response.json()["detail"]


@patch('backend.routes.webhooks.cloudflare.settings')
def test_webhook_missing_timestamp_header(mock_settings, client, valid_payload, webhook_secret):
    """Test webhook request without timestamp header"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = webhook_secret

    signature, _, _ = generate_signature(valid_payload, webhook_secret)

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=valid_payload,
        headers={"X-Cloudflare-Signature": signature}
    )

    assert response.status_code == 400


@patch('backend.routes.webhooks.cloudflare.settings')
def test_webhook_invalid_json(mock_settings, client):
    """Test webhook with invalid JSON payload"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = ""

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422  # FastAPI validation error


@patch('backend.routes.webhooks.cloudflare.settings')
def test_webhook_missing_recording_id(mock_settings, client, webhook_secret):
    """Test webhook with missing recording_id"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = webhook_secret

    payload = {
        "event_type": "recording.ready",
        "data": {
            "room_id": "room_456def"
            # Missing recording_id
        }
    }

    signature, timestamp, _ = generate_signature(payload, webhook_secret)

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=payload,
        headers={
            "X-Cloudflare-Signature": signature,
            "X-Cloudflare-Timestamp": timestamp
        }
    )

    assert response.status_code == 400
    assert "missing recording_id" in response.json()["detail"].lower()


@patch('backend.routes.webhooks.cloudflare.settings')
def test_webhook_no_secret_configured(mock_settings, client, valid_payload, mock_zerodb):
    """Test webhook when secret is not configured (development mode)"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = ""

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=valid_payload
    )

    # Should succeed even without signature when secret not configured
    assert response.status_code == 200


# ============================================================================
# RECORDING READY EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_handle_recording_ready_success(mock_zerodb):
    """Test successful recording ready event handling"""
    # Mock database responses
    mock_zerodb.query_collection.side_effect = [
        # First call: find recording
        [{
            "id": "doc_123",
            "recording_id": "rec_123abc",
            "session_id": "session_456"
        }],
        # Second call: find training session
        [{
            "id": "session_456",
            "title": "Test Training"
        }]
    ]

    recording_data = {
        "stream_url": "https://stream.example.com/video.m3u8",
        "stream_id": "stream_abc123",
        "duration": 3600,
        "size_bytes": 524288000
    }

    await handle_recording_ready(
        zerodb=mock_zerodb,
        recording_id="rec_123abc",
        room_id="room_456def",
        recording_data=recording_data
    )

    # Verify database updates
    assert mock_zerodb.update_document.call_count == 2

    # Check recording update
    recording_update = mock_zerodb.update_document.call_args_list[0]
    assert recording_update[1]["collection_name"] == "cloudflare_recordings"
    assert recording_update[1]["document_id"] == "doc_123"
    assert recording_update[1]["data"]["stream_url"] == recording_data["stream_url"]
    assert recording_update[1]["data"]["status"] == "ready"

    # Check training session update
    session_update = mock_zerodb.update_document.call_args_list[1]
    assert session_update[1]["collection_name"] == "training_sessions"
    assert session_update[1]["data"]["video_url"] == recording_data["stream_url"]
    assert session_update[1]["data"]["recording_status"] == "ready"


@pytest.mark.asyncio
async def test_handle_recording_ready_not_found(mock_zerodb):
    """Test recording ready event when recording not in database"""
    mock_zerodb.query_collection.return_value = []

    recording_data = {
        "stream_url": "https://stream.example.com/video.m3u8",
        "stream_id": "stream_abc123"
    }

    await handle_recording_ready(
        zerodb=mock_zerodb,
        recording_id="rec_unknown",
        room_id="room_456def",
        recording_data=recording_data
    )

    # Should not crash, just log warning
    mock_zerodb.update_document.assert_not_called()


@pytest.mark.asyncio
async def test_handle_recording_ready_no_session(mock_zerodb):
    """Test recording ready event when recording has no session_id"""
    mock_zerodb.query_collection.return_value = [{
        "id": "doc_123",
        "recording_id": "rec_123abc",
        "session_id": None
    }]

    recording_data = {
        "stream_url": "https://stream.example.com/video.m3u8",
        "stream_id": "stream_abc123"
    }

    await handle_recording_ready(
        zerodb=mock_zerodb,
        recording_id="rec_123abc",
        room_id="room_456def",
        recording_data=recording_data
    )

    # Should update recording but not training session
    assert mock_zerodb.update_document.call_count == 1


# ============================================================================
# RECORDING FAILED EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_handle_recording_failed_success(mock_zerodb):
    """Test successful recording failed event handling"""
    mock_zerodb.query_collection.side_effect = [
        # First call: find recording
        [{
            "id": "doc_123",
            "recording_id": "rec_789xyz",
            "session_id": "session_456"
        }],
        # Second call: find training session
        [{
            "id": "session_456",
            "title": "Test Training"
        }]
    ]

    recording_data = {
        "error_message": "Processing timeout"
    }

    await handle_recording_failed(
        zerodb=mock_zerodb,
        recording_id="rec_789xyz",
        room_id="room_456def",
        recording_data=recording_data
    )

    # Verify database updates
    assert mock_zerodb.update_document.call_count == 2

    # Check recording update
    recording_update = mock_zerodb.update_document.call_args_list[0]
    assert recording_update[1]["data"]["status"] == "failed"
    assert recording_update[1]["data"]["error_message"] == "Processing timeout"

    # Check training session update
    session_update = mock_zerodb.update_document.call_args_list[1]
    assert session_update[1]["data"]["recording_status"] == "failed"


@pytest.mark.asyncio
async def test_handle_recording_failed_no_error_message(mock_zerodb):
    """Test recording failed event with no error message"""
    mock_zerodb.query_collection.return_value = [{
        "id": "doc_123",
        "recording_id": "rec_789xyz",
        "session_id": "session_456"
    }]

    recording_data = {}  # No error_message

    await handle_recording_failed(
        zerodb=mock_zerodb,
        recording_id="rec_789xyz",
        room_id="room_456def",
        recording_data=recording_data
    )

    # Should use default error message
    recording_update = mock_zerodb.update_document.call_args_list[0]
    assert recording_update[1]["data"]["error_message"] == "Unknown error"


@pytest.mark.asyncio
async def test_handle_recording_failed_not_found(mock_zerodb):
    """Test recording failed event when recording not in database"""
    mock_zerodb.query_collection.return_value = []

    recording_data = {
        "error_message": "Processing failed"
    }

    await handle_recording_failed(
        zerodb=mock_zerodb,
        recording_id="rec_unknown",
        room_id="room_456def",
        recording_data=recording_data
    )

    # Should not crash, just log warning
    mock_zerodb.update_document.assert_not_called()


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

@patch('backend.routes.webhooks.cloudflare.settings')
def test_health_check_with_secret(mock_settings, client):
    """Test health check when webhook secret is configured"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = "test_secret"

    response = client.get("/api/webhooks/cloudflare/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cloudflare_webhooks"
    assert data["webhook_secret_configured"] is True


@patch('backend.routes.webhooks.cloudflare.settings')
def test_health_check_without_secret(mock_settings, client):
    """Test health check when webhook secret is not configured"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = ""

    response = client.get("/api/webhooks/cloudflare/health")

    assert response.status_code == 200
    data = response.json()
    assert data["webhook_secret_configured"] is False


# ============================================================================
# END-TO-END WEBHOOK TESTS
# ============================================================================

@patch('backend.routes.webhooks.cloudflare.settings')
@patch('backend.routes.webhooks.cloudflare.handle_recording_ready')
async def test_webhook_recording_ready_e2e(mock_handle, mock_settings, client, valid_payload, webhook_secret, mock_zerodb):
    """Test end-to-end recording.ready webhook"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = webhook_secret
    mock_handle.return_value = None

    signature, timestamp, _ = generate_signature(valid_payload, webhook_secret)

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=valid_payload,
        headers={
            "X-Cloudflare-Signature": signature,
            "X-Cloudflare-Timestamp": timestamp
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event_type"] == "recording.ready"
    assert data["recording_id"] == "rec_123abc"


@patch('backend.routes.webhooks.cloudflare.settings')
@patch('backend.routes.webhooks.cloudflare.handle_recording_failed')
async def test_webhook_recording_failed_e2e(mock_handle, mock_settings, client, failed_payload, webhook_secret, mock_zerodb):
    """Test end-to-end recording.failed webhook"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = webhook_secret
    mock_handle.return_value = None

    signature, timestamp, _ = generate_signature(failed_payload, webhook_secret)

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=failed_payload,
        headers={
            "X-Cloudflare-Signature": signature,
            "X-Cloudflare-Timestamp": timestamp
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event_type"] == "recording.failed"


@patch('backend.routes.webhooks.cloudflare.settings')
def test_webhook_unknown_event_type(mock_settings, client, webhook_secret, mock_zerodb):
    """Test webhook with unknown event type"""
    mock_settings.CLOUDFLARE_WEBHOOK_SECRET = webhook_secret

    payload = {
        "event_type": "recording.unknown",
        "data": {
            "recording_id": "rec_123",
            "room_id": "room_456"
        }
    }

    signature, timestamp, _ = generate_signature(payload, webhook_secret)

    response = client.post(
        "/api/webhooks/cloudflare/recording",
        json=payload,
        headers={
            "X-Cloudflare-Signature": signature,
            "X-Cloudflare-Timestamp": timestamp
        }
    )

    # Should still return success (unknown events are logged and ignored)
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.routes.webhooks.cloudflare", "--cov-report=term-missing"])
