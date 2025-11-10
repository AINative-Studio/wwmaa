"""
Tests for Event Service

Tests all business logic in the event service including:
- Event CRUD operations
- Soft delete and restore functionality
- Event duplication
- Publish/unpublish toggle
- Image upload to ZeroDB Object Storage
- Event filtering and querying
- Validation logic
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch, ANY

from backend.services.event_service import EventService, get_event_service
from backend.services.zerodb_service import (
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.models.schemas import EventStatus, EventType, EventVisibility


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def event_service():
    """Provides an EventService instance with mocked ZeroDB client"""
    with patch('backend.services.event_service.get_zerodb_client') as mock_get_client:
        mock_db = MagicMock()
        mock_get_client.return_value = mock_db
        service = EventService()
        service.db = mock_db
        yield service


@pytest.fixture
def sample_event_data():
    """Provides sample event data for testing"""
    now = datetime.utcnow()
    return {
        "title": "Test Martial Arts Seminar",
        "description": "A test seminar for testing purposes",
        "event_type": EventType.SEMINAR.value,
        "visibility": EventVisibility.PUBLIC.value,
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat(),
        "timezone": "America/Los_Angeles",
        "location": "123 Test St, Test City, CA 90210",
        "is_online": False,
        "capacity": 50,
        "price": 25.00,
        "instructor_info": "Master Test Instructor"
    }


@pytest.fixture
def sample_event_response():
    """Provides sample event response from ZeroDB"""
    event_id = str(uuid4())
    now = datetime.utcnow()
    return {
        "id": event_id,
        "title": "Test Martial Arts Seminar",
        "description": "A test seminar for testing purposes",
        "event_type": EventType.SEMINAR.value,
        "visibility": EventVisibility.PUBLIC.value,
        "status": EventStatus.DRAFT.value,
        "start_date": (now + timedelta(days=7)).isoformat(),
        "end_date": (now + timedelta(days=7, hours=2)).isoformat(),
        "timezone": "America/Los_Angeles",
        "location": "123 Test St, Test City, CA 90210",
        "is_online": False,
        "capacity": 50,
        "price": 25.00,
        "instructor_info": "Master Test Instructor",
        "is_published": False,
        "is_deleted": False,
        "current_attendees": 0,
        "created_by": str(uuid4()),
        "organizer_id": str(uuid4()),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }


# ============================================================================
# EVENT CREATION TESTS
# ============================================================================

def test_create_event_success(event_service, sample_event_data, sample_event_response):
    """Test successful event creation"""
    # Arrange
    user_id = uuid4()
    event_service.db.create_document.return_value = sample_event_response

    # Act
    result = event_service.create_event(sample_event_data, user_id)

    # Assert
    assert result == sample_event_response
    event_service.db.create_document.assert_called_once()
    call_args = event_service.db.create_document.call_args
    assert call_args[1]['collection'] == 'events'
    assert call_args[1]['data']['title'] == sample_event_data['title']
    assert call_args[1]['data']['created_by'] == str(user_id)
    assert call_args[1]['data']['status'] == EventStatus.DRAFT.value
    assert call_args[1]['data']['is_deleted'] is False


def test_create_event_validates_end_after_start(event_service):
    """Test that end_date must be after start_date"""
    # Arrange
    now = datetime.utcnow()
    user_id = uuid4()
    invalid_data = {
        "title": "Test Event",
        "start_date": now.isoformat(),
        "end_date": (now - timedelta(hours=1)).isoformat(),  # End before start!
        "event_type": EventType.SEMINAR.value
    }

    # Act & Assert
    with pytest.raises(ZeroDBValidationError) as exc_info:
        event_service.create_event(invalid_data, user_id)

    assert "end_date must be after start_date" in str(exc_info.value)


def test_create_event_validates_capacity_positive(event_service):
    """Test that capacity must be greater than 0"""
    # Arrange
    now = datetime.utcnow()
    user_id = uuid4()
    invalid_data = {
        "title": "Test Event",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=2)).isoformat(),
        "event_type": EventType.SEMINAR.value,
        "capacity": 0  # Invalid capacity!
    }

    # Act & Assert
    with pytest.raises(ZeroDBValidationError) as exc_info:
        event_service.create_event(invalid_data, user_id)

    assert "capacity must be greater than 0" in str(exc_info.value)


def test_create_event_validates_price_non_negative(event_service):
    """Test that price must be non-negative"""
    # Arrange
    now = datetime.utcnow()
    user_id = uuid4()
    invalid_data = {
        "title": "Test Event",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=2)).isoformat(),
        "event_type": EventType.SEMINAR.value,
        "price": -10.00  # Invalid price!
    }

    # Act & Assert
    with pytest.raises(ZeroDBValidationError) as exc_info:
        event_service.create_event(invalid_data, user_id)

    assert "price must be 0 or greater" in str(exc_info.value)


# ============================================================================
# EVENT RETRIEVAL TESTS
# ============================================================================

def test_get_event_success(event_service, sample_event_response):
    """Test successful event retrieval"""
    # Arrange
    event_id = sample_event_response['id']
    event_service.db.get_document.return_value = sample_event_response

    # Act
    result = event_service.get_event(event_id)

    # Assert
    assert result == sample_event_response
    event_service.db.get_document.assert_called_once_with(
        collection='events',
        document_id=event_id
    )


def test_get_event_excludes_deleted_by_default(event_service, sample_event_response):
    """Test that deleted events are excluded by default"""
    # Arrange
    event_id = sample_event_response['id']
    deleted_event = {**sample_event_response, 'is_deleted': True}
    event_service.db.get_document.return_value = deleted_event

    # Act & Assert
    with pytest.raises(ZeroDBNotFoundError) as exc_info:
        event_service.get_event(event_id)

    assert event_id in str(exc_info.value)


def test_get_event_includes_deleted_when_requested(event_service, sample_event_response):
    """Test that deleted events can be retrieved when explicitly requested"""
    # Arrange
    event_id = sample_event_response['id']
    deleted_event = {**sample_event_response, 'is_deleted': True}
    event_service.db.get_document.return_value = deleted_event

    # Act
    result = event_service.get_event(event_id, include_deleted=True)

    # Assert
    assert result == deleted_event
    assert result['is_deleted'] is True


def test_get_event_not_found(event_service):
    """Test event not found error"""
    # Arrange
    event_id = str(uuid4())
    event_service.db.get_document.side_effect = ZeroDBNotFoundError(f"Event not found: {event_id}")

    # Act & Assert
    with pytest.raises(ZeroDBNotFoundError):
        event_service.get_event(event_id)


# ============================================================================
# EVENT LISTING TESTS
# ============================================================================

def test_list_events_success(event_service, sample_event_response):
    """Test successful event listing"""
    # Arrange
    query_result = {
        "documents": [sample_event_response],
        "total": 1,
        "limit": 20,
        "offset": 0
    }
    event_service.db.query_documents.return_value = query_result

    # Act
    result = event_service.list_events(limit=20, offset=0)

    # Assert
    assert result == query_result
    event_service.db.query_documents.assert_called_once()
    call_args = event_service.db.query_documents.call_args
    assert call_args[1]['collection'] == 'events'
    assert call_args[1]['filters']['is_deleted'] is False


def test_list_events_with_filters(event_service):
    """Test event listing with filters"""
    # Arrange
    filters = {
        "event_type": EventType.SEMINAR.value,
        "visibility": EventVisibility.PUBLIC.value
    }
    query_result = {"documents": [], "total": 0}
    event_service.db.query_documents.return_value = query_result

    # Act
    result = event_service.list_events(filters=filters)

    # Assert
    call_args = event_service.db.query_documents.call_args
    assert call_args[1]['filters']['event_type'] == EventType.SEMINAR.value
    assert call_args[1]['filters']['visibility'] == EventVisibility.PUBLIC.value
    assert call_args[1]['filters']['is_deleted'] is False


def test_list_events_includes_deleted_when_requested(event_service):
    """Test that deleted events can be included in listing"""
    # Arrange
    query_result = {"documents": [], "total": 0}
    event_service.db.query_documents.return_value = query_result

    # Act
    result = event_service.list_events(include_deleted=True)

    # Assert
    call_args = event_service.db.query_documents.call_args
    # is_deleted filter should not be set
    assert 'is_deleted' not in call_args[1]['filters'] or call_args[1]['filters'].get('is_deleted') is True


# ============================================================================
# EVENT UPDATE TESTS
# ============================================================================

def test_update_event_success(event_service, sample_event_response):
    """Test successful event update"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()
    update_data = {"title": "Updated Title", "price": 30.00}

    event_service.db.get_document.return_value = sample_event_response
    updated_event = {**sample_event_response, **update_data}
    event_service.db.update_document.return_value = updated_event

    # Act
    result = event_service.update_event(event_id, update_data, user_id)

    # Assert
    assert result['title'] == "Updated Title"
    assert result['price'] == 30.00
    event_service.db.update_document.assert_called_once()
    call_args = event_service.db.update_document.call_args
    assert call_args[1]['data']['updated_by'] == str(user_id)


def test_update_event_validates_dates(event_service, sample_event_response):
    """Test date validation on update"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()
    now = datetime.utcnow()
    update_data = {
        "start_date": now.isoformat(),
        "end_date": (now - timedelta(hours=1)).isoformat()  # Invalid!
    }

    event_service.db.get_document.return_value = sample_event_response

    # Act & Assert
    with pytest.raises(ZeroDBValidationError) as exc_info:
        event_service.update_event(event_id, update_data, user_id)

    assert "end_date must be after start_date" in str(exc_info.value)


def test_update_event_not_found(event_service):
    """Test update of non-existent event"""
    # Arrange
    event_id = str(uuid4())
    user_id = uuid4()
    update_data = {"title": "Updated Title"}

    event_service.db.get_document.side_effect = ZeroDBNotFoundError(f"Event not found: {event_id}")

    # Act & Assert
    with pytest.raises(ZeroDBNotFoundError):
        event_service.update_event(event_id, update_data, user_id)


# ============================================================================
# EVENT DELETION TESTS
# ============================================================================

def test_soft_delete_event(event_service, sample_event_response):
    """Test soft delete event"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()

    event_service.db.get_document.return_value = sample_event_response
    deleted_event = {
        **sample_event_response,
        'is_deleted': True,
        'status': EventStatus.DELETED.value,
        'deleted_by': str(user_id)
    }
    event_service.db.update_document.return_value = deleted_event

    # Act
    result = event_service.delete_event(event_id, user_id, hard_delete=False)

    # Assert
    event_service.db.update_document.assert_called_once()
    call_args = event_service.db.update_document.call_args
    assert call_args[1]['data']['is_deleted'] is True
    assert call_args[1]['data']['status'] == EventStatus.DELETED.value
    assert call_args[1]['data']['deleted_by'] == str(user_id)
    assert call_args[1]['data']['is_published'] is False


def test_hard_delete_event(event_service, sample_event_response):
    """Test hard delete event"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()

    event_service.db.get_document.return_value = sample_event_response
    event_service.db.delete_document.return_value = {"success": True}

    # Act
    result = event_service.delete_event(event_id, user_id, hard_delete=True)

    # Assert
    event_service.db.delete_document.assert_called_once_with(
        collection='events',
        document_id=event_id
    )


# ============================================================================
# EVENT RESTORE TESTS
# ============================================================================

def test_restore_event_success(event_service, sample_event_response):
    """Test successful event restoration"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()
    deleted_event = {
        **sample_event_response,
        'is_deleted': True,
        'status': EventStatus.DELETED.value
    }

    event_service.db.get_document.return_value = deleted_event
    restored_event = {
        **deleted_event,
        'is_deleted': False,
        'status': EventStatus.DRAFT.value,
        'deleted_at': None,
        'deleted_by': None
    }
    event_service.db.update_document.return_value = restored_event

    # Act
    result = event_service.restore_event(event_id, user_id)

    # Assert
    event_service.db.update_document.assert_called_once()
    call_args = event_service.db.update_document.call_args
    assert call_args[1]['data']['is_deleted'] is False
    assert call_args[1]['data']['status'] == EventStatus.DRAFT.value
    assert call_args[1]['data']['updated_by'] == str(user_id)


def test_restore_event_not_deleted(event_service, sample_event_response):
    """Test that restoring a non-deleted event raises error"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()

    event_service.db.get_document.return_value = sample_event_response  # Not deleted

    # Act & Assert
    with pytest.raises(ZeroDBValidationError) as exc_info:
        event_service.restore_event(event_id, user_id)

    assert "not deleted" in str(exc_info.value).lower()


# ============================================================================
# EVENT DUPLICATION TESTS
# ============================================================================

def test_duplicate_event_success(event_service, sample_event_response):
    """Test successful event duplication"""
    # Arrange
    original_id = sample_event_response['id']
    user_id = uuid4()

    event_service.db.get_document.return_value = sample_event_response

    duplicated_event = {**sample_event_response}
    duplicated_event['id'] = str(uuid4())
    duplicated_event['title'] = sample_event_response['title'] + " (Copy)"
    duplicated_event['status'] = EventStatus.DRAFT.value
    duplicated_event['is_published'] = False

    event_service.db.create_document.return_value = duplicated_event

    # Act
    result = event_service.duplicate_event(original_id, user_id)

    # Assert
    assert result['id'] != original_id
    assert result['title'] == sample_event_response['title'] + " (Copy)"
    assert result['status'] == EventStatus.DRAFT.value
    assert result['is_published'] is False
    event_service.db.create_document.assert_called_once()


def test_duplicate_event_custom_suffix(event_service, sample_event_response):
    """Test event duplication with custom title suffix"""
    # Arrange
    original_id = sample_event_response['id']
    user_id = uuid4()
    custom_suffix = " - Duplicate"

    event_service.db.get_document.return_value = sample_event_response

    duplicated_event = {**sample_event_response}
    duplicated_event['id'] = str(uuid4())
    duplicated_event['title'] = sample_event_response['title'] + custom_suffix

    event_service.db.create_document.return_value = duplicated_event

    # Act
    result = event_service.duplicate_event(original_id, user_id, title_suffix=custom_suffix)

    # Assert
    assert result['title'] == sample_event_response['title'] + custom_suffix


# ============================================================================
# PUBLISH TOGGLE TESTS
# ============================================================================

def test_toggle_publish_to_published(event_service, sample_event_response):
    """Test toggling event from draft to published"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()

    draft_event = {**sample_event_response, 'is_published': False}
    event_service.db.get_document.return_value = draft_event

    published_event = {
        **draft_event,
        'is_published': True,
        'status': EventStatus.PUBLISHED.value
    }
    event_service.db.update_document.return_value = published_event

    # Act
    result = event_service.toggle_publish(event_id, user_id)

    # Assert
    assert result['is_published'] is True
    assert result['status'] == EventStatus.PUBLISHED.value
    call_args = event_service.db.update_document.call_args
    assert call_args[1]['data']['is_published'] is True
    assert call_args[1]['data']['status'] == EventStatus.PUBLISHED.value


def test_toggle_publish_to_unpublished(event_service, sample_event_response):
    """Test toggling event from published to draft"""
    # Arrange
    event_id = sample_event_response['id']
    user_id = uuid4()

    published_event = {
        **sample_event_response,
        'is_published': True,
        'status': EventStatus.PUBLISHED.value
    }
    event_service.db.get_document.return_value = published_event

    draft_event = {
        **published_event,
        'is_published': False,
        'status': EventStatus.DRAFT.value,
        'published_at': None
    }
    event_service.db.update_document.return_value = draft_event

    # Act
    result = event_service.toggle_publish(event_id, user_id)

    # Assert
    assert result['is_published'] is False
    assert result['status'] == EventStatus.DRAFT.value
    call_args = event_service.db.update_document.call_args
    assert call_args[1]['data']['is_published'] is False
    assert call_args[1]['data']['status'] == EventStatus.DRAFT.value


# ============================================================================
# IMAGE UPLOAD TESTS
# ============================================================================

def test_upload_event_image_success(event_service):
    """Test successful event image upload"""
    # Arrange
    file_path = "/tmp/test_image.jpg"
    event_id = str(uuid4())
    expected_url = f"https://storage.zerodb.io/events/{event_id}/test_image.jpg"

    event_service.db.upload_object.return_value = {"url": expected_url}

    # Act
    with patch('os.path.basename', return_value="test_image.jpg"):
        result = event_service.upload_event_image(file_path, event_id)

    # Assert
    assert result == expected_url
    event_service.db.upload_object.assert_called_once()
    call_args = event_service.db.upload_object.call_args
    assert call_args[1]['file_path'] == file_path


def test_upload_event_image_without_event_id(event_service):
    """Test image upload without event ID generates temp path"""
    # Arrange
    file_path = "/tmp/test_image.jpg"
    expected_url = "https://storage.zerodb.io/events/temp/test_image.jpg"

    event_service.db.upload_object.return_value = {"url": expected_url}

    # Act
    with patch('os.path.basename', return_value="test_image.jpg"):
        result = event_service.upload_event_image(file_path)

    # Assert
    assert result == expected_url


# ============================================================================
# DELETED EVENTS ARCHIVE TESTS
# ============================================================================

def test_get_deleted_events(event_service, sample_event_response):
    """Test getting deleted events archive"""
    # Arrange
    deleted_event = {
        **sample_event_response,
        'is_deleted': True,
        'status': EventStatus.DELETED.value
    }
    query_result = {
        "documents": [deleted_event],
        "total": 1
    }
    event_service.db.query_documents.return_value = query_result

    # Act
    result = event_service.get_deleted_events()

    # Assert
    assert result == query_result
    event_service.db.query_documents.assert_called_once()
    call_args = event_service.db.query_documents.call_args
    assert call_args[1]['filters']['is_deleted'] is True


# ============================================================================
# SINGLETON PATTERN TEST
# ============================================================================

def test_get_event_service_singleton():
    """Test that get_event_service returns singleton instance"""
    # Act
    service1 = get_event_service()
    service2 = get_event_service()

    # Assert
    assert service1 is service2
