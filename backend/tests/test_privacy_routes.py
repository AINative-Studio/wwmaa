"""
Integration Tests for Privacy API Routes

Tests GDPR compliance endpoints including:
- Data export request
- Export status checking
- Export deletion
- Authentication and authorization
- Error handling

Target: 80%+ code coverage
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from typing import Dict, Any

try:
    from backend.main import app
except ImportError:
    from backend.app import app

from backend.services.gdpr_service import (
    GDPRService,
    DataExportError,
    GDPRServiceError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "id": "user_123",
        "user_id": "user_123",
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_export_result():
    """Mock successful export result"""
    return {
        "export_id": "export_123",
        "status": "completed",
        "download_url": "https://example.com/download/export_123",
        "expiry_date": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "file_size_bytes": 1024000,
        "record_counts": {
            "profiles": 1,
            "applications": 2,
            "subscriptions": 1,
            "payments": 5,
            "rsvps": 10,
            "search_queries": 50,
            "attendees": 20,
            "audit_logs": 100
        }
    }


@pytest.fixture
def mock_export_status():
    """Mock export status response"""
    return {
        "export_id": "export_123",
        "status": "completed",
        "created_at": datetime.utcnow().isoformat(),
        "expiry_date": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "file_size_bytes": 1024000
    }


@pytest.fixture
def auth_headers():
    """Authentication headers with valid JWT token"""
    # In real tests, this would be a valid JWT token
    # For now, we'll mock the authentication
    return {"Authorization": "Bearer mock_token"}


# ============================================================================
# DATA EXPORT ENDPOINT TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_request_data_export_success(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    mock_export_result,
    auth_headers
):
    """Test successful data export request"""
    # Mock authentication
    mock_get_current_user.return_value = mock_current_user

    # Mock GDPR service
    mock_service = Mock()
    mock_service.export_user_data = AsyncMock(return_value=mock_export_result)
    mock_gdpr_service_class.return_value = mock_service

    # Make request
    response = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )

    # Verify response
    assert response.status_code == 202
    data = response.json()

    assert data["export_id"] == "export_123"
    assert data["status"] == "completed"
    assert data["download_url"] is not None
    assert data["expiry_date"] is not None
    assert data["file_size_bytes"] == 1024000
    assert "record_counts" in data

    # Verify service was called correctly
    mock_service.export_user_data.assert_called_once()
    call_args = mock_service.export_user_data.call_args
    assert call_args[1]["user_id"] == "user_123"
    assert call_args[1]["user_email"] == "test@example.com"


@patch('backend.routes.privacy.get_current_user')
def test_request_data_export_unauthenticated(client):
    """Test data export request without authentication"""
    # Mock authentication failure
    with patch('backend.routes.privacy.get_current_user') as mock_auth:
        mock_auth.side_effect = Exception("Not authenticated")

        response = client.post("/api/privacy/export-data", json={})

        # Should return 401 or 500 depending on error handling
        assert response.status_code in [401, 500]


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_request_data_export_service_error(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test data export request when service fails"""
    mock_get_current_user.return_value = mock_current_user

    # Mock service error
    mock_service = Mock()
    mock_service.export_user_data = AsyncMock(
        side_effect=DataExportError("Export failed")
    )
    mock_gdpr_service_class.return_value = mock_service

    response = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Export failed" in data["detail"] or "export" in data["detail"].lower()


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_request_data_export_invalid_user_data(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    auth_headers
):
    """Test data export request with invalid user data in token"""
    # Mock user without required fields
    mock_get_current_user.return_value = {"invalid": "data"}

    response = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_request_data_export_unexpected_error(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test data export request with unexpected error"""
    mock_get_current_user.return_value = mock_current_user

    # Mock unexpected error
    mock_service = Mock()
    mock_service.export_user_data = AsyncMock(
        side_effect=Exception("Unexpected error")
    )
    mock_gdpr_service_class.return_value = mock_service

    response = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


# ============================================================================
# EXPORT STATUS ENDPOINT TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_get_export_status_success(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    mock_export_status,
    auth_headers
):
    """Test successful export status retrieval"""
    mock_get_current_user.return_value = mock_current_user

    # Mock GDPR service
    mock_service = Mock()
    mock_service.get_export_status = AsyncMock(return_value=mock_export_status)
    mock_gdpr_service_class.return_value = mock_service

    response = client.get(
        "/api/privacy/export-status/export_123",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["export_id"] == "export_123"
    assert data["status"] == "completed"
    assert "created_at" in data
    assert "expiry_date" in data
    assert "file_size_bytes" in data

    # Verify service was called correctly
    mock_service.get_export_status.assert_called_once_with(
        user_id="user_123",
        export_id="export_123"
    )


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_get_export_status_not_found(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test export status when export not found"""
    mock_get_current_user.return_value = mock_current_user

    # Mock service returning not found
    mock_service = Mock()
    mock_service.get_export_status = AsyncMock(return_value={"status": "not_found"})
    mock_gdpr_service_class.return_value = mock_service

    response = client.get(
        "/api/privacy/export-status/nonexistent",
        headers=auth_headers
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@patch('backend.routes.privacy.get_current_user')
def test_get_export_status_unauthenticated(client):
    """Test export status without authentication"""
    with patch('backend.routes.privacy.get_current_user') as mock_auth:
        mock_auth.side_effect = Exception("Not authenticated")

        response = client.get("/api/privacy/export-status/export_123")

        assert response.status_code in [401, 500]


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_get_export_status_service_error(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test export status when service fails"""
    mock_get_current_user.return_value = mock_current_user

    # Mock service error
    mock_service = Mock()
    mock_service.get_export_status = AsyncMock(
        side_effect=GDPRServiceError("Service error")
    )
    mock_gdpr_service_class.return_value = mock_service

    response = client.get(
        "/api/privacy/export-status/export_123",
        headers=auth_headers
    )

    assert response.status_code == 500


# ============================================================================
# DELETE EXPORT ENDPOINT TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_delete_export_success(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test successful export deletion"""
    mock_get_current_user.return_value = mock_current_user

    # Mock GDPR service
    mock_service = Mock()
    mock_service.delete_export = AsyncMock(return_value=True)
    mock_gdpr_service_class.return_value = mock_service

    response = client.delete(
        "/api/privacy/export/export_123",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["deleted"] is True
    assert "message" in data

    # Verify service was called correctly
    mock_service.delete_export.assert_called_once_with(
        user_id="user_123",
        export_id="export_123"
    )


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_delete_export_not_found(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test deleting non-existent export"""
    mock_get_current_user.return_value = mock_current_user

    # Mock service returning false (not found)
    mock_service = Mock()
    mock_service.delete_export = AsyncMock(return_value=False)
    mock_gdpr_service_class.return_value = mock_service

    response = client.delete(
        "/api/privacy/export/nonexistent",
        headers=auth_headers
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@patch('backend.routes.privacy.get_current_user')
def test_delete_export_unauthenticated(client):
    """Test export deletion without authentication"""
    with patch('backend.routes.privacy.get_current_user') as mock_auth:
        mock_auth.side_effect = Exception("Not authenticated")

        response = client.delete("/api/privacy/export/export_123")

        assert response.status_code in [401, 500]


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_delete_export_service_error(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test export deletion when service fails"""
    mock_get_current_user.return_value = mock_current_user

    # Mock service error
    mock_service = Mock()
    mock_service.delete_export = AsyncMock(
        side_effect=Exception("Deletion failed")
    )
    mock_gdpr_service_class.return_value = mock_service

    response = client.delete(
        "/api/privacy/export/export_123",
        headers=auth_headers
    )

    assert response.status_code == 500


# ============================================================================
# HEALTH CHECK ENDPOINT TESTS
# ============================================================================

def test_privacy_health_check(client):
    """Test privacy service health check endpoint"""
    response = client.get("/api/privacy/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "privacy"
    assert "timestamp" in data


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_user_can_only_access_own_exports(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    auth_headers
):
    """Test that users can only access their own export data"""
    # Mock user 1
    user1 = {
        "id": "user_1",
        "user_id": "user_1",
        "email": "user1@example.com"
    }
    mock_get_current_user.return_value = user1

    # Mock service to track user_id parameter
    mock_service = Mock()
    mock_service.get_export_status = AsyncMock(
        return_value={"status": "completed"}
    )
    mock_gdpr_service_class.return_value = mock_service

    # Try to access export
    response = client.get(
        "/api/privacy/export-status/export_123",
        headers=auth_headers
    )

    # Verify service was called with correct user_id
    call_args = mock_service.get_export_status.call_args
    assert call_args[1]["user_id"] == "user_1"

    # The service would handle authorization by checking if the export
    # belongs to the user_id in the filter


# ============================================================================
# RESPONSE MODEL VALIDATION TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_export_response_includes_all_required_fields(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    mock_export_result,
    auth_headers
):
    """Test that export response includes all required fields"""
    mock_get_current_user.return_value = mock_current_user

    mock_service = Mock()
    mock_service.export_user_data = AsyncMock(return_value=mock_export_result)
    mock_gdpr_service_class.return_value = mock_service

    response = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 202
    data = response.json()

    # Verify all required fields are present
    required_fields = [
        "export_id",
        "status",
        "message",
        "download_url",
        "expiry_date",
        "file_size_bytes",
        "record_counts"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_status_response_includes_all_required_fields(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    mock_export_status,
    auth_headers
):
    """Test that status response includes all required fields"""
    mock_get_current_user.return_value = mock_current_user

    mock_service = Mock()
    mock_service.get_export_status = AsyncMock(return_value=mock_export_status)
    mock_gdpr_service_class.return_value = mock_service

    response = client.get(
        "/api/privacy/export-status/export_123",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify required fields
    required_fields = ["export_id", "status"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_handles_various_error_types(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    auth_headers
):
    """Test that different error types are handled appropriately"""
    mock_get_current_user.return_value = mock_current_user

    test_cases = [
        (DataExportError("Export failed"), 500),
        (GDPRServiceError("GDPR error"), 500),
        (Exception("Generic error"), 500),
    ]

    for error, expected_status in test_cases:
        mock_service = Mock()
        mock_service.export_user_data = AsyncMock(side_effect=error)
        mock_gdpr_service_class.return_value = mock_service

        response = client.post(
            "/api/privacy/export-data",
            json={},
            headers=auth_headers
        )

        assert response.status_code == expected_status
        assert "detail" in response.json()


# ============================================================================
# INTEGRATION WORKFLOW TESTS
# ============================================================================

@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_complete_export_workflow(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    mock_export_result,
    mock_export_status,
    auth_headers
):
    """Test complete export workflow: request -> check status -> delete"""
    mock_get_current_user.return_value = mock_current_user

    # Mock service
    mock_service = Mock()
    mock_service.export_user_data = AsyncMock(return_value=mock_export_result)
    mock_service.get_export_status = AsyncMock(return_value=mock_export_status)
    mock_service.delete_export = AsyncMock(return_value=True)
    mock_gdpr_service_class.return_value = mock_service

    # Step 1: Request export
    export_response = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )
    assert export_response.status_code == 202
    export_id = export_response.json()["export_id"]

    # Step 2: Check status
    status_response = client.get(
        f"/api/privacy/export-status/{export_id}",
        headers=auth_headers
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "completed"

    # Step 3: Delete export
    delete_response = client.delete(
        f"/api/privacy/export/{export_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


# ============================================================================
# RATE LIMITING TESTS (if implemented)
# ============================================================================

@pytest.mark.skip(reason="Rate limiting not yet implemented")
@patch('backend.routes.privacy.get_current_user')
@patch('backend.routes.privacy.GDPRService')
def test_export_rate_limiting(
    mock_gdpr_service_class,
    mock_get_current_user,
    client,
    mock_current_user,
    mock_export_result,
    auth_headers
):
    """Test that export requests are rate limited (one per 24 hours)"""
    mock_get_current_user.return_value = mock_current_user

    mock_service = Mock()
    mock_service.export_user_data = AsyncMock(return_value=mock_export_result)
    mock_gdpr_service_class.return_value = mock_service

    # First request should succeed
    response1 = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )
    assert response1.status_code == 202

    # Second immediate request should be rate limited
    response2 = client.post(
        "/api/privacy/export-data",
        json={},
        headers=auth_headers
    )
    assert response2.status_code == 429  # Too Many Requests
