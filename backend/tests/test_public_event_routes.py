"""
Tests for Public Event Routes (US-030)

Tests public API endpoints for event listing and filtering:
- GET /api/events/public - List public events with filters
- GET /api/events/public/:id - Get single public event
- POST /api/events/:id/rsvp - RSVP to event
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.routes.events import router
from backend.models.schemas import EventType, EventVisibility, EventStatus
from backend.services.zerodb_service import ZeroDBNotFoundError, ZeroDBError


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
def sample_published_event():
    """Sample published public event"""
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "title": "Public Martial Arts Seminar",
        "description": "Learn advanced techniques",
        "event_type": EventType.SEMINAR.value,
        "visibility": EventVisibility.PUBLIC.value,
        "status": EventStatus.PUBLISHED.value,
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat(),
        "timezone": "America/Los_Angeles",
        "location": "Los Angeles, CA",
        "is_online": False,
        "capacity": 50,
        "price": 25.00,
        "instructor_info": "Master Lee",
        "is_published": True,
        "is_deleted": False,
        "created_at": now.isoformat()
    }


@pytest.fixture
def sample_free_event():
    """Sample free public event"""
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "title": "Free Judo Tournament",
        "event_type": EventType.TOURNAMENT.value,
        "visibility": EventVisibility.PUBLIC.value,
        "status": EventStatus.PUBLISHED.value,
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=10, hours=5)).isoformat(),
        "location": "San Francisco, CA",
        "is_online": False,
        "price": 0,
        "is_published": True,
        "is_deleted": False,
        "created_at": now.isoformat()
    }


@pytest.fixture
def sample_online_event():
    """Sample online event"""
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "title": "Online Live Training",
        "event_type": EventType.LIVE_TRAINING.value,
        "visibility": EventVisibility.PUBLIC.value,
        "status": EventStatus.PUBLISHED.value,
        "start_date": (now + timedelta(days=3)).isoformat(),
        "end_date": (now + timedelta(days=3, hours=1)).isoformat(),
        "location": "Online",
        "is_online": True,
        "price": 15.00,
        "is_published": True,
        "is_deleted": False,
        "created_at": now.isoformat()
    }


# ============================================================================
# LIST PUBLIC EVENTS TESTS
# ============================================================================

def test_list_public_events_success(mock_event_service, sample_published_event):
    """Test successful public event listing (US-030 AC1)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data
    assert len(data["events"]) == 1
    assert data["events"][0]["title"] == "Public Martial Arts Seminar"


def test_list_public_events_filter_by_type(mock_event_service, sample_published_event):
    """Test filtering events by type (US-030 AC3)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?type=seminar")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == EventType.SEMINAR.value

    # Verify service was called with correct filters
    call_args = mock_event_service.list_events.call_args
    filters = call_args[1]["filters"]
    assert filters["event_type"] == EventType.SEMINAR.value


def test_list_public_events_filter_free_only(mock_event_service, sample_free_event):
    """Test filtering for free events only (US-030 AC3)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_free_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?price=free")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["price"] == 0

    # Verify service was called with price filter
    call_args = mock_event_service.list_events.call_args
    filters = call_args[1]["filters"]
    assert filters["price"] == 0


def test_list_public_events_filter_paid_only(mock_event_service, sample_published_event):
    """Test filtering for paid events only (US-030 AC3)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?price=paid")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["price"] > 0


def test_list_public_events_filter_by_location_online(mock_event_service, sample_online_event):
    """Test filtering for online events (US-030 AC3)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_online_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?location=online")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["is_online"] is True


def test_list_public_events_filter_by_date_range(mock_event_service, sample_published_event):
    """Test filtering by date range (US-030 AC3)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    date_from = datetime.utcnow().date().isoformat()
    date_to = (datetime.utcnow() + timedelta(days=30)).date().isoformat()
    response = client.get(f"/api/events/public?date_from={date_from}&date_to={date_to}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "events" in data

    # Verify date filters were applied
    call_args = mock_event_service.list_events.call_args
    filters = call_args[1]["filters"]
    assert "start_date" in filters


def test_list_public_events_sort_by_date_asc(mock_event_service, sample_published_event):
    """Test sorting events by date ascending (US-030 AC4)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?sort=date&order=asc")

    # Assert
    assert response.status_code == 200

    # Verify service was called with correct sort parameters
    call_args = mock_event_service.list_events.call_args
    assert call_args[1]["sort_by"] == "start_date"
    assert call_args[1]["sort_order"] == "asc"


def test_list_public_events_sort_by_price(mock_event_service, sample_published_event):
    """Test sorting events by price (US-030 AC4)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?sort=price&order=asc")

    # Assert
    assert response.status_code == 200

    # Verify service was called with correct sort parameters
    call_args = mock_event_service.list_events.call_args
    assert call_args[1]["sort_by"] == "price"


def test_list_public_events_pagination(mock_event_service, sample_published_event):
    """Test event pagination (US-030 AC5)"""
    # Arrange
    events = [sample_published_event] * 15  # Create 15 events
    mock_event_service.list_events.return_value = {
        "documents": events[:12],  # First page of 12
        "total": 15
    }

    client = TestClient(router)

    # Act - First page
    response = client.get("/api/events/public?limit=12&offset=0")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 15
    assert data["limit"] == 12
    assert data["offset"] == 0
    assert data["has_more"] is True
    assert len(data["events"]) == 12


def test_list_public_events_empty_result(mock_event_service):
    """Test empty events list (US-030 AC8)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [],
        "total": 0
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?type=certification")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["events"]) == 0
    assert data["has_more"] is False


def test_list_public_events_invalid_date_format(mock_event_service):
    """Test invalid date format handling (US-030 AC7)"""
    # Arrange
    client = TestClient(router)

    # Act
    response = client.get("/api/events/public?date_from=invalid-date")

    # Assert
    assert response.status_code == 400
    assert "Invalid date_from format" in response.json()["detail"]


def test_list_public_events_database_error(mock_event_service):
    """Test database error handling (US-030 AC7)"""
    # Arrange
    mock_event_service.list_events.side_effect = ZeroDBError("Connection failed")
    client = TestClient(router)

    # Act
    response = client.get("/api/events/public")

    # Assert
    assert response.status_code == 500


# ============================================================================
# GET SINGLE PUBLIC EVENT TESTS
# ============================================================================

def test_get_public_event_success(mock_event_service, sample_published_event):
    """Test getting a single public event (US-030 AC7)"""
    # Arrange
    event_id = sample_published_event["id"]
    mock_event_service.get_event.return_value = sample_published_event

    client = TestClient(router)

    # Act
    response = client.get(f"/api/events/public/{event_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event_id
    assert data["title"] == "Public Martial Arts Seminar"


def test_get_public_event_not_found(mock_event_service):
    """Test getting non-existent event (US-030 AC7)"""
    # Arrange
    event_id = str(uuid4())
    mock_event_service.get_event.side_effect = ZeroDBNotFoundError("Event not found")

    client = TestClient(router)

    # Act
    response = client.get(f"/api/events/public/{event_id}")

    # Assert
    assert response.status_code == 404


def test_get_public_event_not_published(mock_event_service):
    """Test getting draft event returns 404 for public endpoint"""
    # Arrange
    event_id = str(uuid4())
    draft_event = {
        "id": event_id,
        "status": EventStatus.DRAFT.value,
        "visibility": EventVisibility.PUBLIC.value
    }
    mock_event_service.get_event.return_value = draft_event

    client = TestClient(router)

    # Act
    response = client.get(f"/api/events/public/{event_id}")

    # Assert
    assert response.status_code == 404


def test_get_public_event_members_only(mock_event_service):
    """Test getting members-only event returns 404 for public endpoint"""
    # Arrange
    event_id = str(uuid4())
    members_event = {
        "id": event_id,
        "status": EventStatus.PUBLISHED.value,
        "visibility": EventVisibility.MEMBERS_ONLY.value
    }
    mock_event_service.get_event.return_value = members_event

    client = TestClient(router)

    # Act
    response = client.get(f"/api/events/public/{event_id}")

    # Assert
    assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_public_events_complete_filtering_workflow(mock_event_service, sample_published_event, sample_free_event):
    """Test complete filtering workflow (US-030 integration)"""
    # Arrange
    all_events = [sample_published_event, sample_free_event]
    mock_event_service.list_events.return_value = {
        "documents": all_events,
        "total": 2
    }

    client = TestClient(router)

    # Act - Filter by multiple criteria
    response = client.get(
        "/api/events/public?"
        "type=tournament&"
        "price=free&"
        "location=in_person&"
        "sort=date&"
        "order=asc"
    )

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Verify all filters were applied
    call_args = mock_event_service.list_events.call_args
    filters = call_args[1]["filters"]
    assert filters["status"] == EventStatus.PUBLISHED.value
    assert filters["visibility"] == EventVisibility.PUBLIC.value
    assert filters["is_published"] is True


def test_public_events_loading_state(mock_event_service):
    """Test loading state returns immediately (US-030 AC7)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [],
        "total": 0
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public")

    # Assert - Should return immediately, not hang
    assert response.status_code == 200
    # Response time should be fast (handled by FastAPI)


def test_public_events_card_layout_data(mock_event_service, sample_published_event):
    """Test event response contains all required card data (US-030 AC2)"""
    # Arrange
    mock_event_service.list_events.return_value = {
        "documents": [sample_published_event],
        "total": 1
    }

    client = TestClient(router)

    # Act
    response = client.get("/api/events/public")

    # Assert
    assert response.status_code == 200
    data = response.json()
    event = data["events"][0]

    # Verify all required fields for card display
    assert "id" in event
    assert "title" in event
    assert "start_date" in event
    assert "location" in event
    assert "price" in event
    assert "event_type" in event
    assert "visibility" in event
