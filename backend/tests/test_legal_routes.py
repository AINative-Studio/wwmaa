"""
Tests for Legal Routes

Tests the API endpoints for Terms of Service and Privacy Policy acceptance tracking.
Validates version tracking, authentication requirements, and audit trail functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from backend.main import app
from backend.routes.legal import router


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client"""
    with patch('backend.routes.legal.get_zerodb_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_current_user():
    """Mock authenticated user"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_auth():
    """Mock authentication dependency"""
    with patch('backend.routes.legal.get_current_user') as mock:
        yield mock


class TestAcceptTermsEndpoint:
    """Tests for POST /api/legal/accept-terms endpoint"""

    def test_accept_terms_success(self, client, mock_zerodb_client, mock_auth, mock_current_user):
        """Test successful terms acceptance"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.update_document.return_value = {"success": True}

        # Request payload
        payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Terms of Service and Privacy Policy acceptance recorded successfully"
        assert data["terms_accepted_version"] == "1.0"
        assert data["privacy_accepted_version"] == "1.0"
        assert "accepted_at" in data

        # Verify database call
        mock_zerodb_client.update_document.assert_called_once()
        call_args = mock_zerodb_client.update_document.call_args
        assert call_args[1]["collection"] == "users"
        assert call_args[1]["document_id"] == "test-user-123"
        assert call_args[1]["merge"] is True

        # Check update data
        update_data = call_args[1]["data"]
        assert update_data["terms_accepted_version"] == "1.0"
        assert update_data["privacy_accepted_version"] == "1.0"
        assert "terms_accepted_at" in update_data
        assert "privacy_accepted_at" in update_data
        assert "updated_at" in update_data
        assert "legal_acceptance_audit" in update_data
        assert update_data["legal_acceptance_audit"]["ip_address"] == "192.168.1.1"

    def test_accept_terms_without_audit_data(self, client, mock_zerodb_client, mock_auth, mock_current_user):
        """Test terms acceptance without IP/user agent"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.update_document.return_value = {"success": True}

        # Request without audit data
        payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify no audit data in update
        call_args = mock_zerodb_client.update_document.call_args
        update_data = call_args[1]["data"]
        assert "legal_acceptance_audit" not in update_data

    def test_accept_terms_unauthenticated(self, client, mock_auth):
        """Test terms acceptance without authentication"""
        # Setup - mock authentication failure
        from fastapi import HTTPException
        mock_auth.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

        payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_accept_terms_missing_fields(self, client, mock_auth, mock_current_user):
        """Test terms acceptance with missing required fields"""
        # Setup
        mock_auth.return_value = mock_current_user

        # Missing privacy_version
        payload = {
            "terms_version": "1.0"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_accept_terms_database_error(self, client, mock_zerodb_client, mock_auth, mock_current_user):
        """Test terms acceptance with database error"""
        # Setup
        mock_auth.return_value = mock_current_user
        from backend.services.zerodb_service import ZeroDBError
        mock_zerodb_client.update_document.side_effect = ZeroDBError("Database error")

        payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to record acceptance" in response.json()["detail"]


class TestGetAcceptanceStatusEndpoint:
    """Tests for GET /api/legal/acceptance-status endpoint"""

    def test_get_acceptance_status_current_versions(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test getting acceptance status with current versions"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.get_document.return_value = {
            "data": {
                "terms_accepted_version": "1.0",
                "privacy_accepted_version": "1.0",
                "terms_accepted_at": "2025-01-01T00:00:00",
                "privacy_accepted_at": "2025-01-01T00:00:00"
            }
        }

        # Execute
        response = client.get("/api/legal/acceptance-status")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["terms_accepted"] is True
        assert data["privacy_accepted"] is True
        assert data["terms_accepted_version"] == "1.0"
        assert data["privacy_accepted_version"] == "1.0"
        assert data["requires_update"] is False
        assert data["current_terms_version"] == "1.0"
        assert data["current_privacy_version"] == "1.0"

    def test_get_acceptance_status_outdated_versions(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test getting acceptance status with outdated versions"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.get_document.return_value = {
            "data": {
                "terms_accepted_version": "0.9",
                "privacy_accepted_version": "0.9",
                "terms_accepted_at": "2024-01-01T00:00:00",
                "privacy_accepted_at": "2024-01-01T00:00:00"
            }
        }

        # Execute
        response = client.get("/api/legal/acceptance-status")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["terms_accepted"] is False
        assert data["privacy_accepted"] is False
        assert data["terms_accepted_version"] == "0.9"
        assert data["privacy_accepted_version"] == "0.9"
        assert data["requires_update"] is True

    def test_get_acceptance_status_no_acceptance(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test getting acceptance status when user hasn't accepted"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.get_document.return_value = {
            "data": {}
        }

        # Execute
        response = client.get("/api/legal/acceptance-status")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["terms_accepted"] is False
        assert data["privacy_accepted"] is False
        assert data["terms_accepted_version"] is None
        assert data["privacy_accepted_version"] is None
        assert data["requires_update"] is True

    def test_get_acceptance_status_user_not_found(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test getting acceptance status for non-existent user"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.get_document.return_value = None

        # Execute
        response = client.get("/api/legal/acceptance-status")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_acceptance_status_unauthenticated(self, client, mock_auth):
        """Test getting acceptance status without authentication"""
        # Setup - mock authentication failure
        from fastapi import HTTPException
        mock_auth.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

        # Execute
        response = client.get("/api/legal/acceptance-status")

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_acceptance_status_database_error(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test getting acceptance status with database error"""
        # Setup
        mock_auth.return_value = mock_current_user
        from backend.services.zerodb_service import ZeroDBError
        mock_zerodb_client.get_document.side_effect = ZeroDBError("Database error")

        # Execute
        response = client.get("/api/legal/acceptance-status")

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to fetch acceptance status" in response.json()["detail"]


class TestGetVersionInfoEndpoint:
    """Tests for GET /api/legal/version-info endpoint"""

    def test_get_version_info_public_endpoint(self, client):
        """Test getting version info (public endpoint)"""
        # Execute
        response = client.get("/api/legal/version-info")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify Terms of Service info
        assert "terms_of_service" in data
        tos = data["terms_of_service"]
        assert tos["version"] == "1.0"
        assert "last_updated" in tos
        assert "effective_date" in tos

        # Verify Privacy Policy info
        assert "privacy_policy" in data
        privacy = data["privacy_policy"]
        assert privacy["version"] == "1.0"
        assert "last_updated" in privacy
        assert "effective_date" in privacy

    def test_get_version_info_no_authentication_required(self, client):
        """Test that version info doesn't require authentication"""
        # Execute (without any authentication headers)
        response = client.get("/api/legal/version-info")

        # Assert
        assert response.status_code == status.HTTP_200_OK


class TestLegalAcceptanceIntegration:
    """Integration tests for legal acceptance workflow"""

    def test_full_acceptance_workflow(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test complete workflow: check status -> accept -> verify"""
        # Setup
        mock_auth.return_value = mock_current_user

        # Step 1: Check status (not accepted)
        mock_zerodb_client.get_document.return_value = {"data": {}}
        response = client.get("/api/legal/acceptance-status")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["requires_update"] is True

        # Step 2: Accept terms
        mock_zerodb_client.update_document.return_value = {"success": True}
        accept_payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0"
        }
        response = client.post("/api/legal/accept-terms", json=accept_payload)
        assert response.status_code == status.HTTP_200_OK

        # Step 3: Check status again (now accepted)
        mock_zerodb_client.get_document.return_value = {
            "data": {
                "terms_accepted_version": "1.0",
                "privacy_accepted_version": "1.0",
                "terms_accepted_at": "2025-01-01T00:00:00",
                "privacy_accepted_at": "2025-01-01T00:00:00"
            }
        }
        response = client.get("/api/legal/acceptance-status")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["requires_update"] is False

    def test_version_upgrade_workflow(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test workflow when terms version is updated"""
        # Setup
        mock_auth.return_value = mock_current_user

        # User accepted old version
        mock_zerodb_client.get_document.return_value = {
            "data": {
                "terms_accepted_version": "0.9",
                "privacy_accepted_version": "0.9"
            }
        }

        # Check status - should require update
        response = client.get("/api/legal/acceptance-status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["requires_update"] is True
        assert data["current_terms_version"] == "1.0"
        assert data["terms_accepted_version"] == "0.9"

        # Accept new version
        mock_zerodb_client.update_document.return_value = {"success": True}
        accept_payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0"
        }
        response = client.post("/api/legal/accept-terms", json=accept_payload)
        assert response.status_code == status.HTTP_200_OK


class TestLegalAcceptanceAuditTrail:
    """Tests for audit trail functionality"""

    def test_audit_trail_includes_all_data(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test that audit trail captures all relevant information"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.update_document.return_value = {"success": True}

        payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0",
            "ip_address": "203.0.113.45",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify audit data
        call_args = mock_zerodb_client.update_document.call_args
        update_data = call_args[1]["data"]
        audit = update_data["legal_acceptance_audit"]

        assert audit["ip_address"] == "203.0.113.45"
        assert "Mozilla/5.0" in audit["user_agent"]
        assert "timestamp" in audit

    def test_audit_trail_timestamp_format(
        self, client, mock_zerodb_client, mock_auth, mock_current_user
    ):
        """Test that timestamps are in ISO format"""
        # Setup
        mock_auth.return_value = mock_current_user
        mock_zerodb_client.update_document.return_value = {"success": True}

        payload = {
            "terms_version": "1.0",
            "privacy_version": "1.0",
            "ip_address": "192.168.1.1"
        }

        # Execute
        response = client.post("/api/legal/accept-terms", json=payload)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify timestamp format
        call_args = mock_zerodb_client.update_document.call_args
        update_data = call_args[1]["data"]

        # Check all timestamps are ISO format
        accepted_at = update_data["terms_accepted_at"]
        assert "T" in accepted_at
        # Verify it can be parsed
        datetime.fromisoformat(accepted_at)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
