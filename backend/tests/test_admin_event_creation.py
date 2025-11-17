"""
Integration Tests for Admin Event Creation (GitHub Issue #12)

Tests the complete flow of event creation from API endpoint to database storage.
Verifies:
- POST /api/events endpoint exists
- Admin/instructor authorization
- Required field validation
- Event is saved to ZeroDB
- Event appears in list after creation
- Returns created event with ID
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch

from backend.routes.events import router, EventCreateRequest
from backend.models.schemas import EventType, EventVisibility, UserRole
from backend.services.zerodb_service import get_zerodb_client


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_user():
    """Create a mock admin user"""
    return MagicMock(
        id=uuid4(),
        email="admin@test.com",
        role=UserRole.ADMIN
    )


@pytest.fixture
def instructor_user():
    """Create a mock instructor user"""
    return MagicMock(
        id=uuid4(),
        email="instructor@test.com",
        role=UserRole.INSTRUCTOR
    )


@pytest.fixture
def member_user():
    """Create a mock member user (non-admin)"""
    return MagicMock(
        id=uuid4(),
        email="member@test.com",
        role=UserRole.MEMBER
    )


@pytest.fixture
def valid_event_data():
    """Create valid event data"""
    now = datetime.utcnow()
    return {
        "title": "Test Event",
        "description": "Test event description",
        "event_type": "training",
        "visibility": "public",
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat(),
        "timezone": "America/Los_Angeles",
        "location": "Test Location",
        "is_online": False,
        "capacity": 50,
        "price": 25.00,
        "instructor_info": "Test Instructor"
    }


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_event_requires_authentication():
    """Test that event creation requires authentication"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    # Act - attempt to create event without authentication
    response = client.post("/api/events", json={
        "title": "Test Event",
        "event_type": "training",
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(hours=2)).isoformat()
    })

    # Assert
    assert response.status_code in [401, 403], "Should require authentication"


@pytest.mark.asyncio
async def test_create_event_requires_admin_or_instructor(member_user, valid_event_data):
    """Test that event creation requires admin or instructor role"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    # Mock authentication with member user (should fail)
    with patch('backend.routes.events.get_current_user', return_value=member_user):
        response = client.post("/api/events", json=valid_event_data)

        # Assert
        assert response.status_code == 403, "Members should not be able to create events"
        assert "admin" in response.json().get("detail", "").lower() or \
               "forbidden" in response.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_admin_can_create_event(admin_user, valid_event_data):
    """Test that admin users can create events"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.get_current_user', return_value=admin_user):
        with patch('backend.routes.events.require_admin', return_value=admin_user):
            with patch('backend.routes.events.get_event_service') as mock_service:
                # Mock the event service to return a created event
                created_event = valid_event_data.copy()
                created_event["id"] = str(uuid4())
                created_event["created_at"] = datetime.utcnow().isoformat()
                created_event["created_by"] = str(admin_user.id)
                created_event["status"] = "draft"
                created_event["is_published"] = False

                mock_service.return_value.create_event.return_value = created_event

                # Act
                response = client.post("/api/events", json=valid_event_data)

                # Assert
                assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
                mock_service.return_value.create_event.assert_called_once()


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_event_validates_required_fields(admin_user):
    """Test that required fields are validated"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        # Missing title
        response = client.post("/api/events", json={
            "event_type": "training",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        })
        assert response.status_code == 422, "Should validate required title"

        # Missing event_type
        response = client.post("/api/events", json={
            "title": "Test Event",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        })
        assert response.status_code == 422, "Should validate required event_type"

        # Missing dates
        response = client.post("/api/events", json={
            "title": "Test Event",
            "event_type": "training"
        })
        assert response.status_code == 422, "Should validate required dates"


@pytest.mark.asyncio
async def test_create_event_validates_end_date_after_start(admin_user):
    """Test that end_date must be after start_date"""
    from fastapi.testclient import TestClient

    client = TestClient(router)
    now = datetime.utcnow()

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        # End date before start date
        response = client.post("/api/events", json={
            "title": "Test Event",
            "event_type": "training",
            "start_date": now.isoformat(),
            "end_date": (now - timedelta(hours=1)).isoformat()
        })

        # Should fail validation (either at Pydantic or service level)
        assert response.status_code in [400, 422], "Should validate end_date > start_date"


@pytest.mark.asyncio
async def test_create_event_validates_capacity(admin_user, valid_event_data):
    """Test that capacity must be positive if provided"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        # Zero capacity
        invalid_data = valid_event_data.copy()
        invalid_data["capacity"] = 0

        response = client.post("/api/events", json=invalid_data)
        assert response.status_code in [400, 422], "Should validate capacity > 0"

        # Negative capacity
        invalid_data["capacity"] = -5
        response = client.post("/api/events", json=invalid_data)
        assert response.status_code in [400, 422], "Should validate capacity >= 0"


@pytest.mark.asyncio
async def test_create_event_validates_price(admin_user, valid_event_data):
    """Test that price must be non-negative if provided"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        # Negative price
        invalid_data = valid_event_data.copy()
        invalid_data["price"] = -10.00

        response = client.post("/api/events", json=invalid_data)
        assert response.status_code in [400, 422], "Should validate price >= 0"


# ============================================================================
# DATABASE PERSISTENCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_event_is_saved_to_database(admin_user, valid_event_data):
    """Test that created event is actually saved to ZeroDB"""
    from fastapi.testclient import TestClient
    from backend.services.event_service import EventService

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        with patch('backend.services.zerodb_service.get_zerodb_client') as mock_db:
            # Setup mock database
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance

            created_event = valid_event_data.copy()
            created_event["id"] = str(uuid4())
            created_event["created_at"] = datetime.utcnow().isoformat()
            created_event["created_by"] = str(admin_user.id)
            created_event["status"] = "draft"

            mock_db_instance.create_document.return_value = created_event

            # Act
            response = client.post("/api/events", json=valid_event_data)

            # Assert
            assert response.status_code == 201

            # Verify database was called
            mock_db_instance.create_document.assert_called_once()
            call_args = mock_db_instance.create_document.call_args

            assert call_args[1]["collection"] == "events"
            assert "title" in call_args[1]["data"]
            assert call_args[1]["data"]["title"] == "Test Event"


@pytest.mark.asyncio
async def test_created_event_has_id(admin_user, valid_event_data):
    """Test that created event returns with an ID"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        with patch('backend.routes.events.get_event_service') as mock_service:
            # Setup mock service
            created_event = valid_event_data.copy()
            event_id = str(uuid4())
            created_event["id"] = event_id
            created_event["created_at"] = datetime.utcnow().isoformat()
            created_event["created_by"] = str(admin_user.id)
            created_event["status"] = "draft"
            created_event["is_published"] = False

            mock_service.return_value.create_event.return_value = created_event

            # Act
            response = client.post("/api/events", json=valid_event_data)

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["id"] == event_id


@pytest.mark.asyncio
async def test_created_event_appears_in_list(admin_user, valid_event_data):
    """Test that created event appears in events list"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        with patch('backend.routes.events.get_event_service') as mock_service:
            # Setup mock service
            created_event = valid_event_data.copy()
            created_event["id"] = str(uuid4())
            created_event["created_at"] = datetime.utcnow().isoformat()
            created_event["created_by"] = str(admin_user.id)
            created_event["status"] = "draft"
            created_event["is_published"] = False

            mock_service.return_value.create_event.return_value = created_event
            mock_service.return_value.list_events.return_value = {
                "documents": [created_event],
                "total": 1
            }

            # Act - Create event
            create_response = client.post("/api/events", json=valid_event_data)
            assert create_response.status_code == 201

            # Act - List events
            list_response = client.get("/api/events")

            # Assert
            assert list_response.status_code == 200
            data = list_response.json()
            assert data["total"] >= 1
            assert any(event["id"] == created_event["id"] for event in data["events"])


# ============================================================================
# DEFAULT VALUES TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_created_event_has_default_status_draft(admin_user, valid_event_data):
    """Test that newly created events have status=draft and is_published=false"""
    from fastapi.testclient import TestClient
    from backend.services.event_service import EventService

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        with patch('backend.services.zerodb_service.get_zerodb_client') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance

            # Capture what gets saved
            saved_data = None
            def capture_data(collection, data):
                nonlocal saved_data
                saved_data = data
                result = data.copy()
                result["id"] = str(uuid4())
                result["created_at"] = datetime.utcnow().isoformat()
                return result

            mock_db_instance.create_document.side_effect = capture_data

            # Act
            response = client.post("/api/events", json=valid_event_data)

            # Assert
            assert response.status_code == 201
            assert saved_data is not None
            assert saved_data["status"] == "draft"
            assert saved_data["is_published"] == False


# ============================================================================
# AUDIT FIELDS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_created_event_has_audit_fields(admin_user, valid_event_data):
    """Test that created event has proper audit fields"""
    from fastapi.testclient import TestClient

    client = TestClient(router)

    with patch('backend.routes.events.require_admin', return_value=admin_user):
        with patch('backend.services.zerodb_service.get_zerodb_client') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance

            saved_data = None
            def capture_data(collection, data):
                nonlocal saved_data
                saved_data = data
                result = data.copy()
                result["id"] = str(uuid4())
                result["created_at"] = datetime.utcnow().isoformat()
                result["updated_at"] = datetime.utcnow().isoformat()
                return result

            mock_db_instance.create_document.side_effect = capture_data

            # Act
            response = client.post("/api/events", json=valid_event_data)

            # Assert
            assert response.status_code == 201
            assert saved_data is not None
            assert "created_by" in saved_data
            assert saved_data["created_by"] == str(admin_user.id)
            assert "organizer_id" in saved_data
            assert saved_data["organizer_id"] == str(admin_user.id)
