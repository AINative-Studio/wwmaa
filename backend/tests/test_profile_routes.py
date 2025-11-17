"""
Unit Tests for Profile Routes

Tests profile retrieval, updates, and photo upload endpoints.
Ensures data persistence and proper validation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from uuid import uuid4, UUID
from datetime import datetime

from backend.app import app
from backend.services.zerodb_service import ZeroDBNotFoundError


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user_id = str(uuid4())
    return {
        "id": user_id,
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_auth_token():
    """Mock JWT token"""
    return "Bearer test-jwt-token"


@pytest.fixture
def mock_db_client():
    """Mock ZeroDB client"""
    with patch("backend.routes.profile.get_zerodb_client") as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def auth_client(mock_user):
    """Create test client with mocked authentication"""
    from backend.middleware.auth_middleware import get_current_user

    async def override_current_user(credentials=None):
        return mock_user

    app.dependency_overrides[get_current_user] = override_current_user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# GET /api/me - Current User Profile Tests
# ============================================================================

def test_get_current_user_profile_success(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test successful profile retrieval"""
    # Mock user document
    mock_db_client.get_document.return_value = {
        "data": {
            "id": mock_user["id"],
            "email": mock_user["email"],
            "first_name": "John",
            "last_name": "Doe",
            "role": "member"
        }
    }

    response = auth_client.get(
        "/api/me",
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_user["id"]
    assert data["email"] == mock_user["email"]
    assert data["name"] == "John Doe"
    assert data["role"] == "member"


def test_get_current_user_profile_with_profile_data(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test profile retrieval with extended profile data"""
    # Mock user document
    def mock_get_document(collection, document_id):
        if collection == "users":
            return {
                "data": {
                    "id": mock_user["id"],
                    "email": mock_user["email"],
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "member"
                }
            }
        elif collection == "profiles":
            return {
                "data": {
                    "ranks": {"Karate": "Black Belt"},
                    "schools_affiliated": ["Test Dojo"],
                    "country": "USA",
                    "locale": "en-US"
                }
            }

    mock_db_client.get_document.side_effect = mock_get_document

    response = auth_client.get(
        "/api/me",
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["belt_rank"] == "Black Belt"
    assert data["dojo"] == "Test Dojo"


# ============================================================================
# PATCH /api/me/profile - Profile Update Tests
# ============================================================================

def test_update_profile_success(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test successful profile update"""
    update_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "+12025551234",
        "city": "Seattle",
        "state": "WA",
        "country": "USA"
    }

    # Mock update document
    mock_db_client.update_document.return_value = {"success": True}

    # Mock get_document to return updated data
    mock_db_client.get_document.return_value = {
        "data": {
            "id": mock_user["id"],
            "email": mock_user["email"],
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+12025551234",
            "city": "Seattle",
            "state": "WA",
            "country": "USA",
            "role": "member"
        }
    }

    response = auth_client.patch(
        "/api/me/profile",
        json=update_data,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Profile updated successfully"
    assert data["user"]["first_name"] == "Jane"
    assert data["user"]["last_name"] == "Smith"
    assert data["user"]["phone"] == "+12025551234"
    assert data["user"]["city"] == "Seattle"

    # Verify update_document was called
    assert mock_db_client.update_document.called


def test_update_profile_with_emergency_contact(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test profile update with emergency contact"""
    update_data = {
        "first_name": "John",
        "emergency_contact": {
            "name": "Jane Doe",
            "relationship": "Spouse",
            "phone": "+12025555678",
            "email": "jane@example.com"
        }
    }

    mock_db_client.update_document.return_value = {"success": True}

    # Mock get_document to return updated data with emergency contact
    def mock_get_document(collection, document_id):
        if collection == "users":
            return {
                "data": {
                    "id": mock_user["id"],
                    "email": mock_user["email"],
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "member"
                }
            }
        elif collection == "profiles":
            return {
                "data": {
                    "metadata": {
                        "emergency_contact": {
                            "name": "Jane Doe",
                            "relationship": "Spouse",
                            "phone": "+12025555678",
                            "email": "jane@example.com"
                        }
                    }
                }
            }

    mock_db_client.get_document.side_effect = mock_get_document

    response = auth_client.patch(
        "/api/me/profile",
        json=update_data,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["emergency_contact"]["name"] == "Jane Doe"
    assert data["user"]["emergency_contact"]["relationship"] == "Spouse"


def test_update_profile_creates_if_not_exists(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test profile creation when it doesn't exist"""
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+12025551234"
    }

    # Mock update to raise NotFoundError first time (profiles collection)
    def mock_update(collection, document_id, data, merge=True):
        if collection == "profiles":
            raise ZeroDBNotFoundError("Profile not found")
        return {"success": True}

    mock_db_client.update_document.side_effect = mock_update
    mock_db_client.create_document.return_value = {"success": True}

    # Mock get_document
    mock_db_client.get_document.return_value = {
        "data": {
            "id": mock_user["id"],
            "email": mock_user["email"],
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+12025551234",
            "role": "member"
        }
    }

    response = auth_client.patch(
        "/api/me/profile",
        json=update_data,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    # Verify create_document was called
    assert mock_db_client.create_document.called


def test_update_profile_validation_error(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test profile update with invalid data"""
    # Invalid phone number
    update_data = {
        "phone": "invalid-phone"
    }

    response = auth_client.patch(
        "/api/me/profile",
        json=update_data,
        headers={"Authorization": mock_auth_token}
    )

    # Should return 422 for validation error
    assert response.status_code == 422


# ============================================================================
# POST /api/me/profile/photo - Photo Upload Tests
# ============================================================================

def test_upload_profile_photo_success(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test successful profile photo upload"""
    # Create a mock image file
    image_data = b"fake-image-data"
    files = {
        "file": ("profile.jpg", BytesIO(image_data), "image/jpeg")
    }

    # Mock upload_object_from_bytes
    mock_db_client.upload_object_from_bytes.return_value = {
        "url": "https://api.ainative.studio/storage/project-id/profiles/user-id/avatar.jpg"
    }

    # Mock update_document
    mock_db_client.update_document.return_value = {"success": True}

    response = auth_client.post(
        "/api/me/profile/photo",
        files=files,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Profile photo uploaded successfully"
    assert "photo_url" in data
    assert data["photo_url"].startswith("https://")

    # Verify upload_object_from_bytes was called
    assert mock_db_client.upload_object_from_bytes.called


def test_upload_profile_photo_invalid_type(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test photo upload with invalid file type"""
    # Create a mock PDF file (invalid)
    file_data = b"fake-pdf-data"
    files = {
        "file": ("document.pdf", BytesIO(file_data), "application/pdf")
    }

    response = auth_client.post(
        "/api/me/profile/photo",
        files=files,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_upload_profile_photo_too_large(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test photo upload with file too large"""
    # Create a mock file larger than 10MB
    large_data = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {
        "file": ("large.jpg", BytesIO(large_data), "image/jpeg")
    }

    response = auth_client.post(
        "/api/me/profile/photo",
        files=files,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_upload_profile_photo_empty_file(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test photo upload with empty file"""
    # Create an empty file
    files = {
        "file": ("empty.jpg", BytesIO(b""), "image/jpeg")
    }

    response = auth_client.post(
        "/api/me/profile/photo",
        files=files,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_profile_photo_creates_profile_if_not_exists(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test photo upload creates profile if it doesn't exist"""
    image_data = b"fake-image-data"
    files = {
        "file": ("profile.jpg", BytesIO(image_data), "image/jpeg")
    }

    # Mock upload success
    mock_db_client.upload_object_from_bytes.return_value = {
        "url": "https://api.ainative.studio/storage/project-id/profiles/user-id/avatar.jpg"
    }

    # Mock update to raise NotFoundError (profile doesn't exist)
    mock_db_client.update_document.side_effect = ZeroDBNotFoundError("Profile not found")

    # Mock get_document for user data
    mock_db_client.get_document.return_value = {
        "data": {
            "first_name": "John",
            "last_name": "Doe"
        }
    }

    # Mock create_document
    mock_db_client.create_document.return_value = {"success": True}

    response = auth_client.post(
        "/api/me/profile/photo",
        files=files,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200
    # Verify create_document was called
    assert mock_db_client.create_document.called


# ============================================================================
# Data Persistence Tests
# ============================================================================

def test_profile_update_persists_to_database(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test that profile updates are saved to database"""
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "city": "New City"
    }

    # Track calls to update_document
    update_calls = []

    def track_update(collection, document_id, data, merge=True):
        update_calls.append({
            "collection": collection,
            "document_id": document_id,
            "data": data
        })
        return {"success": True}

    mock_db_client.update_document.side_effect = track_update

    # Mock get_document to return updated data
    mock_db_client.get_document.return_value = {
        "data": {
            "id": mock_user["id"],
            "email": mock_user["email"],
            "first_name": "Updated",
            "last_name": "Name",
            "city": "New City",
            "role": "member"
        }
    }

    response = auth_client.patch(
        "/api/me/profile",
        json=update_data,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200

    # Verify database was updated
    assert len(update_calls) >= 1

    # Verify users collection was updated with name
    users_update = next((c for c in update_calls if c["collection"] == "users"), None)
    assert users_update is not None
    assert users_update["data"]["first_name"] == "Updated"
    assert users_update["data"]["last_name"] == "Name"

    # Verify profiles collection was updated
    profiles_update = next((c for c in update_calls if c["collection"] == "profiles"), None)
    assert profiles_update is not None
    assert profiles_update["data"]["city"] == "New City"


def test_photo_upload_persists_to_storage_and_database(auth_client, mock_db_client, mock_user, mock_auth_token):
    """Test that photo upload saves to storage and updates database"""
    image_data = b"fake-image-data"
    files = {
        "file": ("profile.jpg", BytesIO(image_data), "image/jpeg")
    }

    # Track storage and database calls
    storage_calls = []
    db_update_calls = []

    def track_upload(key, content, content_type):
        storage_calls.append({
            "key": key,
            "content_length": len(content),
            "content_type": content_type
        })
        return {
            "url": f"https://api.ainative.studio/storage/project-id/{key}"
        }

    def track_update(collection, document_id, data, merge=True):
        db_update_calls.append({
            "collection": collection,
            "document_id": document_id,
            "avatar_url": data.get("avatar_url")
        })
        return {"success": True}

    mock_db_client.upload_object_from_bytes.side_effect = track_upload
    mock_db_client.update_document.side_effect = track_update

    response = auth_client.post(
        "/api/me/profile/photo",
        files=files,
        headers={"Authorization": mock_auth_token}
    )

    assert response.status_code == 200

    # Verify file was uploaded to storage
    assert len(storage_calls) == 1
    assert storage_calls[0]["content_length"] == len(image_data)
    assert storage_calls[0]["content_type"] == "image/jpeg"
    assert storage_calls[0]["key"].startswith("profiles/")

    # Verify database was updated with avatar URL
    assert len(db_update_calls) == 1
    assert db_update_calls[0]["collection"] == "profiles"
    assert db_update_calls[0]["avatar_url"] is not None
    assert db_update_calls[0]["avatar_url"].startswith("https://")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
