"""
Integration Tests for Profile Persistence (Issue #2)

Tests the complete profile update flow including:
- Profile field updates
- Emergency contact storage
- Photo upload
- Data persistence verification

These tests verify that student dashboard profile edits persist to the database.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
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
        "email": "student@example.com",
        "role": "member"
    }


@pytest.fixture
def client(mock_user):
    """Create test client with authenticated user"""
    from backend.middleware.auth_middleware import get_current_user

    async def override_current_user(credentials=None):
        return mock_user

    app.dependency_overrides[get_current_user] = override_current_user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_client():
    """Mock ZeroDB client with realistic behavior"""
    with patch("backend.routes.profile.get_zerodb_client") as mock:
        client = Mock()

        # In-memory storage to simulate database persistence
        storage = {
            "users": {},
            "profiles": {}
        }

        def get_document(collection, document_id):
            if collection not in storage or document_id not in storage[collection]:
                raise ZeroDBNotFoundError(f"Document not found in {collection}")
            return {"data": storage[collection][document_id]}

        def update_document(collection, document_id, data, merge=True):
            if collection not in storage:
                storage[collection] = {}
            if document_id not in storage[collection]:
                if not merge:
                    storage[collection][document_id] = data
                else:
                    raise ZeroDBNotFoundError(f"Document not found in {collection}")
            else:
                if merge:
                    storage[collection][document_id].update(data)
                else:
                    storage[collection][document_id] = data
            return {"success": True}

        def create_document(collection, data, document_id=None):
            if collection not in storage:
                storage[collection] = {}
            doc_id = document_id or str(uuid4())
            storage[collection][doc_id] = data
            return {"success": True, "id": doc_id}

        def upload_object_from_bytes(key, content, content_type):
            return {
                "url": f"https://api.ainative.studio/storage/test-project/{key}",
                "key": key
            }

        client.get_document.side_effect = get_document
        client.update_document.side_effect = update_document
        client.create_document.side_effect = create_document
        client.upload_object_from_bytes.side_effect = upload_object_from_bytes
        client.base_url = "https://api.ainative.studio"
        client.project_id = "test-project"

        # Initialize user in storage
        storage["users"] = {}
        storage["profiles"] = {}

        mock.return_value = client
        yield client


# ============================================================================
# Profile Update Persistence Tests
# ============================================================================

def test_profile_update_persists_basic_info(client, mock_db_client, mock_user):
    """Test that basic profile updates persist to database"""
    # Initialize user data
    mock_db_client.create_document(
        collection="users",
        data={
            "id": UUID(mock_user["id"]),
            "email": mock_user["email"],
            "first_name": "Original",
            "last_name": "Name",
            "role": "member"
        },
        document_id=mock_user["id"]
    )

    # Update profile
    update_data = {
        "first_name": "Updated",
        "last_name": "Student",
        "phone": "+12025551234",
        "city": "Seattle",
        "state": "WA"
    }

    response = client.patch(
        "/api/me/profile",
        json=update_data
    )

    assert response.status_code == 200
    result = response.json()

    # Verify response
    assert result["message"] == "Profile updated successfully"
    assert result["user"]["first_name"] == "Updated"
    assert result["user"]["last_name"] == "Student"

    # Verify data persisted by making another request
    verify_response = client.get("/api/me")

    assert verify_response.status_code == 200
    profile = verify_response.json()
    assert "Updated Student" in profile["name"]


def test_profile_update_persists_contact_info(client, mock_db_client, mock_user):
    """Test that contact information updates persist"""
    # Initialize user
    mock_db_client.create_document(
        collection="users",
        data={
            "id": UUID(mock_user["id"]),
            "email": mock_user["email"],
            "first_name": "Test",
            "last_name": "Student",
            "role": "member"
        },
        document_id=mock_user["id"]
    )

    # Update contact info
    update_data = {
        "phone": "+12025551234",
        "address": "123 Main St",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "country": "USA"
    }

    response = client.patch(
        "/api/me/profile",
        json=update_data
    )

    assert response.status_code == 200

    # Verify persistence
    user_doc = mock_db_client.get_document("profiles", mock_user["id"])
    profile_data = user_doc["data"]

    assert profile_data["phone"] == "+12025551234"
    assert profile_data["city"] == "Seattle"
    assert profile_data["state"] == "WA"
    assert profile_data["zip_code"] == "98101"


def test_emergency_contact_persists(client, mock_db_client, mock_user):
    """Test that emergency contact information persists to database"""
    # Initialize user
    mock_db_client.create_document(
        collection="users",
        data={
            "id": UUID(mock_user["id"]),
            "email": mock_user["email"],
            "first_name": "Test",
            "last_name": "Student",
            "role": "member"
        },
        document_id=mock_user["id"]
    )

    # Update with emergency contact
    update_data = {
        "first_name": "Test",
        "emergency_contact": {
            "name": "Emergency Person",
            "relationship": "Parent",
            "phone": "+12025555678",
            "email": "emergency@example.com"
        }
    }

    response = client.patch(
        "/api/me/profile",
        json=update_data
    )

    assert response.status_code == 200

    # Verify emergency contact persisted
    profile_doc = mock_db_client.get_document("profiles", mock_user["id"])
    profile_data = profile_doc["data"]

    assert "metadata" in profile_data
    assert "emergency_contact" in profile_data["metadata"]
    emergency = profile_data["metadata"]["emergency_contact"]
    assert emergency["name"] == "Emergency Person"
    assert emergency["phone"] == "+12025555678"


def test_profile_photo_persists(client, mock_db_client, mock_user):
    """Test that profile photo upload persists URL to database"""
    # Initialize user
    mock_db_client.create_document(
        collection="users",
        data={
            "id": UUID(mock_user["id"]),
            "email": mock_user["email"],
            "first_name": "Test",
            "last_name": "Student",
            "role": "member"
        },
        document_id=mock_user["id"]
    )

    # Create profile
    mock_db_client.create_document(
        collection="profiles",
        data={
            "id": UUID(mock_user["id"]),
            "user_id": UUID(mock_user["id"]),
            "first_name": "Test",
            "last_name": "Student",
            "created_at": datetime.utcnow()
        },
        document_id=mock_user["id"]
    )

    # Upload photo
    image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    files = {
        "file": ("profile.png", BytesIO(image_data), "image/png")
    }

    response = client.post(
        "/api/me/profile/photo",
        files=files
    )

    assert response.status_code == 200
    result = response.json()
    assert "photo_url" in result
    assert result["photo_url"].startswith("https://")

    # Verify photo URL persisted
    profile_doc = mock_db_client.get_document("profiles", mock_user["id"])
    profile_data = profile_doc["data"]
    assert "avatar_url" in profile_data
    assert profile_data["avatar_url"] == result["photo_url"]


def test_multiple_updates_persist_incrementally(client, mock_db_client, mock_user):
    """Test that multiple sequential updates all persist correctly"""
    # Initialize user
    mock_db_client.create_document(
        collection="users",
        data={
            "id": UUID(mock_user["id"]),
            "email": mock_user["email"],
            "first_name": "Test",
            "last_name": "Student",
            "role": "member"
        },
        document_id=mock_user["id"]
    )

    # First update: name
    response1 = client.patch(
        "/api/me/profile",
        json={"first_name": "First", "last_name": "Update"}
    )
    assert response1.status_code == 200

    # Second update: contact info
    response2 = client.patch(
        "/api/me/profile",
        json={"phone": "+12025551234", "city": "Seattle"}
    )
    assert response2.status_code == 200

    # Third update: emergency contact
    response3 = client.patch(
        "/api/me/profile",
        json={
            "emergency_contact": {
                "name": "Emergency",
                "relationship": "Friend",
                "phone": "+12025555678"
            }
        }
    )
    assert response3.status_code == 200

    # Verify all updates persisted
    profile_doc = mock_db_client.get_document("profiles", mock_user["id"])
    profile_data = profile_doc["data"]

    assert profile_data["first_name"] == "First"
    assert profile_data["last_name"] == "Update"
    assert profile_data["phone"] == "+12025551234"
    assert profile_data["city"] == "Seattle"
    assert "metadata" in profile_data
    assert profile_data["metadata"]["emergency_contact"]["name"] == "Emergency"


def test_profile_creates_if_not_exists(client, mock_db_client, mock_user):
    """Test that profile is created if it doesn't exist"""
    # Initialize user WITHOUT profile
    mock_db_client.create_document(
        collection="users",
        data={
            "id": UUID(mock_user["id"]),
            "email": mock_user["email"],
            "first_name": "Test",
            "last_name": "Student",
            "role": "member"
        },
        document_id=mock_user["id"]
    )

    # Update profile (should create it)
    update_data = {
        "phone": "+12025551234",
        "city": "Seattle"
    }

    response = client.patch(
        "/api/me/profile",
        json=update_data
    )

    assert response.status_code == 200

    # Verify profile was created
    profile_doc = mock_db_client.get_document("profiles", mock_user["id"])
    assert profile_doc is not None
    assert profile_doc["data"]["phone"] == "+12025551234"
    assert profile_doc["data"]["city"] == "Seattle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
