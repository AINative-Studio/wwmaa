"""
Tests for Event Routes

Tests all API endpoints for event management including:
- GET /api/events - List events
- POST /api/events - Create event
- GET /api/events/:id - Get single event
- PUT /api/events/:id - Update event
- DELETE /api/events/:id - Delete event
- POST /api/events/:id/duplicate - Duplicate event
- PATCH /api/events/:id/publish - Toggle publish
- GET /api/events/deleted/list - List deleted events
- POST /api/events/:id/restore - Restore event
- POST /api/events/upload-image - Upload image
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import UploadFile
from io import BytesIO

from backend.routes.events import router
from backend.models.schemas import EventType, EventVisibility, EventStatus, UserRole
from backend.services.zerodb_service import ZeroDBNotFoundError, ZeroDBValidationError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_event_service():
    """Mock event service"""
    with patch('backend.routes.events.get_event_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    return MagicMock(
        id=uuid4(),
        email="admin@test.com",
        role=UserRole.ADMIN
    )


@pytest.fixture
def sample_event():
    """Sample event data"""
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "title": "Test Event",
        "description": "Test description",
        "event_type": EventType.SEMINAR.value,
        "visibility": EventVisibility.PUBLIC.value,
        "status": EventStatus.DRAFT.value,
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat(),
        "timezone": "America/Los_Angeles",
        "location": "Test Location",
        "is_online": False,
        "capacity": 50,
        "price": 25.00,
        "instructor_info": "Test Instructor",
        "is_published": False,
        "is_deleted": False,
        "created_at": now.isoformat(),
        "created_by": str(uuid4())
    }


# ============================================================================
# LIST EVENTS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_events_success(mock_event_service, mock_admin_user, sample_event):
    """Test successful event listing"""
    # Arrange
    from fastapi.testclient import TestClient
    from backend.routes.events import router

    mock_event_service.list_events.return_value = {
        "documents": [sample_event],
        "total": 1
    }

    # Create test client
    client = TestClient(router)

    # Mock authentication
    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.get("/api/events")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert len(data['events']) == 1
        assert data['events'][0]['title'] == "Test Event"


@pytest.mark.asyncio
async def test_list_events_with_filters(mock_event_service, mock_admin_user):
    """Test event listing with filters"""
    # Arrange
    from fastapi.testclient import TestClient

    mock_event_service.list_events.return_value = {
        "documents": [],
        "total": 0
    }

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.get(
            "/api/events",
            params={
                "event_type": EventType.SEMINAR.value,
                "visibility": EventVisibility.PUBLIC.value,
                "status": EventStatus.PUBLISHED.value
            }
        )

        # Assert
        assert response.status_code == 200
        mock_event_service.list_events.assert_called_once()


# ============================================================================
# CREATE EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_event_success(mock_event_service, mock_admin_user, sample_event):
    """Test successful event creation"""
    # Arrange
    from fastapi.testclient import TestClient

    now = datetime.utcnow()
    create_data = {
        "title": "New Event",
        "event_type": EventType.SEMINAR.value,
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat()
    }

    mock_event_service.create_event.return_value = sample_event

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post("/api/events", json=create_data)

        # Assert
        assert response.status_code == 201
        mock_event_service.create_event.assert_called_once()


@pytest.mark.asyncio
async def test_create_event_validation_error(mock_event_service, mock_admin_user):
    """Test event creation with validation error"""
    # Arrange
    from fastapi.testclient import TestClient

    now = datetime.utcnow()
    invalid_data = {
        "title": "Invalid Event",
        "event_type": EventType.SEMINAR.value,
        "start_date": now.isoformat(),
        "end_date": (now - timedelta(hours=1)).isoformat()  # End before start!
    }

    mock_event_service.create_event.side_effect = ZeroDBValidationError("end_date must be after start_date")

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post("/api/events", json=invalid_data)

        # Assert
        assert response.status_code == 400
        assert "end_date must be after start_date" in response.json()['detail']


# ============================================================================
# GET EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_event_success(mock_event_service, mock_admin_user, sample_event):
    """Test successful event retrieval"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = sample_event['id']
    mock_event_service.get_event.return_value = sample_event

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.get(f"/api/events/{event_id}")

        # Assert
        assert response.status_code == 200
        assert response.json()['id'] == event_id


@pytest.mark.asyncio
async def test_get_event_not_found(mock_event_service, mock_admin_user):
    """Test getting non-existent event"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = str(uuid4())
    mock_event_service.get_event.side_effect = ZeroDBNotFoundError(f"Event not found: {event_id}")

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.get(f"/api/events/{event_id}")

        # Assert
        assert response.status_code == 404


# ============================================================================
# UPDATE EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_event_success(mock_event_service, mock_admin_user, sample_event):
    """Test successful event update"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = sample_event['id']
    update_data = {"title": "Updated Title", "price": 30.00}

    updated_event = {**sample_event, **update_data}
    mock_event_service.update_event.return_value = updated_event

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.put(f"/api/events/{event_id}", json=update_data)

        # Assert
        assert response.status_code == 200
        assert response.json()['title'] == "Updated Title"


# ============================================================================
# DELETE EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_event_soft_delete(mock_event_service, mock_admin_user, sample_event):
    """Test soft delete event"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = sample_event['id']
    mock_event_service.delete_event.return_value = {"success": True}

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.delete(f"/api/events/{event_id}")

        # Assert
        assert response.status_code == 200
        assert "deleted successfully" in response.json()['message']
        mock_event_service.delete_event.assert_called_once()
        call_args = mock_event_service.delete_event.call_args
        assert call_args[1]['hard_delete'] is False


@pytest.mark.asyncio
async def test_delete_event_hard_delete(mock_event_service, mock_admin_user, sample_event):
    """Test hard delete event"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = sample_event['id']
    mock_event_service.delete_event.return_value = {"success": True}

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.delete(f"/api/events/{event_id}", params={"hard_delete": True})

        # Assert
        assert response.status_code == 200
        call_args = mock_event_service.delete_event.call_args
        assert call_args[1]['hard_delete'] is True


# ============================================================================
# DUPLICATE EVENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_duplicate_event_success(mock_event_service, mock_admin_user, sample_event):
    """Test successful event duplication"""
    # Arrange
    from fastapi.testclient import TestClient

    original_id = sample_event['id']
    duplicated_event = {
        **sample_event,
        'id': str(uuid4()),
        'title': sample_event['title'] + " (Copy)"
    }

    mock_event_service.duplicate_event.return_value = duplicated_event

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post(f"/api/events/{original_id}/duplicate")

        # Assert
        assert response.status_code == 201
        assert response.json()['id'] != original_id
        assert "(Copy)" in response.json()['title']


# ============================================================================
# PUBLISH TOGGLE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_toggle_publish_to_published(mock_event_service, mock_admin_user, sample_event):
    """Test toggling event to published"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = sample_event['id']
    published_event = {
        **sample_event,
        'is_published': True,
        'status': EventStatus.PUBLISHED.value
    }

    mock_event_service.toggle_publish.return_value = published_event

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.patch(f"/api/events/{event_id}/publish")

        # Assert
        assert response.status_code == 200
        assert response.json()['is_published'] is True
        assert response.json()['status'] == EventStatus.PUBLISHED.value


# ============================================================================
# DELETED EVENTS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_deleted_events(mock_event_service, mock_admin_user, sample_event):
    """Test listing deleted events"""
    # Arrange
    from fastapi.testclient import TestClient

    deleted_event = {
        **sample_event,
        'is_deleted': True,
        'status': EventStatus.DELETED.value
    }

    mock_event_service.get_deleted_events.return_value = {
        "documents": [deleted_event],
        "total": 1
    }

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.get("/api/events/deleted/list")

        # Assert
        assert response.status_code == 200
        assert response.json()['total'] == 1


@pytest.mark.asyncio
async def test_restore_event_success(mock_event_service, mock_admin_user, sample_event):
    """Test successful event restoration"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = sample_event['id']
    restored_event = {
        **sample_event,
        'is_deleted': False,
        'status': EventStatus.DRAFT.value
    }

    mock_event_service.restore_event.return_value = restored_event

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post(f"/api/events/{event_id}/restore")

        # Assert
        assert response.status_code == 200
        assert "restored successfully" in response.json()['message']


# ============================================================================
# IMAGE UPLOAD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_upload_event_image_success(mock_event_service, mock_admin_user):
    """Test successful image upload"""
    # Arrange
    from fastapi.testclient import TestClient

    event_id = str(uuid4())
    image_url = f"https://storage.zerodb.io/events/{event_id}/test.jpg"

    mock_event_service.upload_event_image.return_value = image_url

    client = TestClient(router)

    # Create mock file
    file_content = b"fake image content"
    files = {"file": ("test.jpg", BytesIO(file_content), "image/jpeg")}
    data = {"event_id": event_id}

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post("/api/events/upload-image", files=files, data=data)

        # Assert
        assert response.status_code == 200
        assert response.json()['url'] == image_url


@pytest.mark.asyncio
async def test_upload_event_image_invalid_type(mock_event_service, mock_admin_user):
    """Test image upload with invalid file type"""
    # Arrange
    from fastapi.testclient import TestClient

    client = TestClient(router)

    # Create mock file with invalid type
    file_content = b"fake pdf content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post("/api/events/upload-image", files=files)

        # Assert
        assert response.status_code == 400
        assert "Invalid file type" in response.json()['detail']


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_events_requires_admin():
    """Test that listing events requires admin role"""
    # Arrange
    from fastapi.testclient import TestClient
    from fastapi import HTTPException

    client = TestClient(router)

    non_admin_user = MagicMock(
        id=uuid4(),
        email="user@test.com",
        role=UserRole.MEMBER
    )

    with patch('backend.routes.events.get_current_user', return_value=non_admin_user):
        # Act
        response = client.get("/api/events")

        # Assert
        assert response.status_code == 403


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_event_database_error(mock_event_service, mock_admin_user):
    """Test event creation with database error"""
    # Arrange
    from fastapi.testclient import TestClient
    from backend.services.zerodb_service import ZeroDBError

    now = datetime.utcnow()
    create_data = {
        "title": "New Event",
        "event_type": EventType.SEMINAR.value,
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat()
    }

    mock_event_service.create_event.side_effect = ZeroDBError("Database connection failed")

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=mock_admin_user):
        # Act
        response = client.post("/api/events", json=create_data)

        # Assert
        assert response.status_code == 500
