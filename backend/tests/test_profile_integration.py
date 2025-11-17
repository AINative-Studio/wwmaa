"""
Integration Test for Profile Update Functionality

This test verifies that profile updates and photo uploads work end-to-end
by calling the route functions directly with mocked database and authentication.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from io import BytesIO

from backend.routes.profile import (
    update_user_profile,
    upload_profile_photo
)
from backend.models.request_schemas import ProfileUpdateRequest, EmergencyContact
from backend.services.zerodb_service import ZeroDBNotFoundError


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_db_client():
    """Mock ZeroDB client"""
    return Mock()


# ============================================================================
# Profile Update Tests
# ============================================================================

@pytest.mark.asyncio
async def test_profile_update_integration(mock_user, mock_db_client, monkeypatch):
    """Test that profile update works end-to-end"""
    # Mock the get_zerodb_client function
    monkeypatch.setattr("backend.routes.profile.get_zerodb_client", lambda: mock_db_client)

    # Setup mock responses
    mock_db_client.update_document.return_value = {"success": True}
    mock_db_client.get_document.return_value = {
        "data": {
            "id": mock_user["id"],
            "email": mock_user["email"],
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+12025551234",
            "city": "Seattle",
            "role": "member"
        }
    }

    # Create update request
    update_request = ProfileUpdateRequest(
        first_name="Jane",
        last_name="Smith",
        phone="+12025551234",
        city="Seattle"
    )

    # Execute update
    response = await update_user_profile(update_request, mock_user)

    # Verify response
    assert response.message == "Profile updated successfully"
    assert response.user["first_name"] == "Jane"
    assert response.user["last_name"] == "Smith"
    assert response.user["phone"] == "+12025551234"
    assert response.user["city"] == "Seattle"

    # Verify database was called
    assert mock_db_client.update_document.called
    assert mock_db_client.get_document.called


@pytest.mark.asyncio
async def test_profile_update_with_emergency_contact(mock_user, mock_db_client, monkeypatch):
    """Test profile update with emergency contact"""
    monkeypatch.setattr("backend.routes.profile.get_zerodb_client", lambda: mock_db_client)

    mock_db_client.update_document.return_value = {"success": True}

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
                            "phone": "+12025555678"
                        }
                    }
                }
            }

    mock_db_client.get_document.side_effect = mock_get_document

    # Create update with emergency contact
    update_request = ProfileUpdateRequest(
        first_name="John",
        emergency_contact=EmergencyContact(
            name="Jane Doe",
            relationship="Spouse",
            phone="+12025555678"
        )
    )

    response = await update_user_profile(update_request, mock_user)

    assert response.message == "Profile updated successfully"
    assert response.user["emergency_contact"]["name"] == "Jane Doe"
    assert response.user["emergency_contact"]["relationship"] == "Spouse"


@pytest.mark.asyncio
async def test_profile_creates_if_not_exists(mock_user, mock_db_client, monkeypatch):
    """Test that profile is created if it doesn't exist"""
    monkeypatch.setattr("backend.routes.profile.get_zerodb_client", lambda: mock_db_client)

    # Mock update to raise NotFoundError (profile doesn't exist)
    def mock_update(collection, document_id, data, merge=True):
        if collection == "profiles":
            raise ZeroDBNotFoundError("Profile not found")
        return {"success": True}

    mock_db_client.update_document.side_effect = mock_update
    mock_db_client.create_document.return_value = {"success": True}
    mock_db_client.get_document.return_value = {
        "data": {
            "id": mock_user["id"],
            "email": mock_user["email"],
            "first_name": "John",
            "last_name": "Doe",
            "role": "member"
        }
    }

    update_request = ProfileUpdateRequest(
        first_name="John",
        last_name="Doe"
    )

    response = await update_user_profile(update_request, mock_user)

    assert response.message == "Profile updated successfully"
    # Verify create_document was called
    assert mock_db_client.create_document.called


# ============================================================================
# Photo Upload Tests
# ============================================================================

@pytest.mark.asyncio
async def test_photo_upload_integration(mock_user, mock_db_client, monkeypatch):
    """Test photo upload works end-to-end"""
    monkeypatch.setattr("backend.routes.profile.get_zerodb_client", lambda: mock_db_client)

    # Mock upload
    mock_db_client.upload_object_from_bytes.return_value = {
        "url": "https://api.ainative.studio/storage/project-id/profiles/user-id/avatar.jpg"
    }
    mock_db_client.update_document.return_value = {"success": True}

    # Create mock file
    from fastapi import UploadFile
    file_content = b"fake-image-data"
    file = UploadFile(
        filename="test.jpg",
        file=BytesIO(file_content),
        headers={"content-type": "image/jpeg"}
    )

    response = await upload_profile_photo(file, mock_user)

    assert response.message == "Profile photo uploaded successfully"
    assert "photo_url" in response.model_dump()
    assert response.photo_url.startswith("https://")

    # Verify upload was called
    assert mock_db_client.upload_object_from_bytes.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
