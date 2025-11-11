"""
Tests for Training Session Service

Tests all CRUD operations, session lifecycle, and business logic for training sessions.
Achieves 80%+ test coverage as required by US-044.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from backend.services.training_session_service import (
    TrainingSessionService,
    get_training_session_service
)
from backend.services.zerodb_service import (
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.services.cloudflare_calls_service import CloudflareCallsError
from backend.models.schemas import SessionStatus, UserRole


class TestTrainingSessionService:
    """Test suite for TrainingSessionService"""

    @pytest.fixture
    def service(self):
        """Create a fresh TrainingSessionService instance for each test"""
        with patch('backend.services.training_session_service.get_zerodb_client'), \
             patch('backend.services.training_session_service.get_cloudflare_calls_service'):
            return TrainingSessionService()

    @pytest.fixture
    def mock_session_data(self):
        """Sample session data for testing"""
        return {
            "title": "Advanced Karate Training",
            "description": "Advanced techniques for black belts",
            "start_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "duration_minutes": 60,
            "capacity": 20,
            "recording_enabled": True,
            "chat_enabled": True,
            "is_public": False,
            "members_only": True,
            "tags": ["karate", "advanced"]
        }

    @pytest.fixture
    def mock_instructor_id(self):
        """Sample instructor ID for testing"""
        return uuid4()

    # ========================================================================
    # CREATE SESSION TESTS
    # ========================================================================

    def test_create_session_success(self, service, mock_session_data, mock_instructor_id):
        """Test successful session creation"""
        # Mock database response
        session_id = uuid4()
        service.db.create_document = Mock(return_value={
            "id": str(session_id),
            **mock_session_data,
            "status": SessionStatus.SCHEDULED.value,
            "room_id": None
        })

        # Mock Cloudflare room creation
        room_id = "room-123-abc"
        service.cloudflare.create_room = Mock(return_value={
            "room_id": room_id
        })
        service.db.update_document = Mock()

        # Create session
        result = service.create_session(mock_session_data, mock_instructor_id)

        # Assertions
        assert result is not None
        assert result.get("id") == str(session_id)
        assert result.get("title") == mock_session_data["title"]
        service.db.create_document.assert_called_once()
        service.cloudflare.create_room.assert_called_once()

    def test_create_session_missing_title(self, service, mock_session_data, mock_instructor_id):
        """Test session creation fails without title"""
        del mock_session_data["title"]

        with pytest.raises(ZeroDBValidationError, match="title is required"):
            service.create_session(mock_session_data, mock_instructor_id)

    def test_create_session_missing_start_time(self, service, mock_session_data, mock_instructor_id):
        """Test session creation fails without start_time"""
        del mock_session_data["start_time"]

        with pytest.raises(ZeroDBValidationError, match="start_time is required"):
            service.create_session(mock_session_data, mock_instructor_id)

    def test_create_session_past_start_time(self, service, mock_session_data, mock_instructor_id):
        """Test session creation fails with past start_time"""
        mock_session_data["start_time"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        with pytest.raises(ZeroDBValidationError, match="must be in the future"):
            service.create_session(mock_session_data, mock_instructor_id)

    def test_create_session_invalid_duration(self, service, mock_session_data, mock_instructor_id):
        """Test session creation fails with invalid duration"""
        # Test duration too short
        mock_session_data["duration_minutes"] = 0
        with pytest.raises(ZeroDBValidationError, match="duration must be between"):
            service.create_session(mock_session_data, mock_instructor_id)

        # Test duration too long
        mock_session_data["duration_minutes"] = 500
        with pytest.raises(ZeroDBValidationError, match="duration must be between"):
            service.create_session(mock_session_data, mock_instructor_id)

    def test_create_session_invalid_capacity(self, service, mock_session_data, mock_instructor_id):
        """Test session creation fails with invalid capacity"""
        mock_session_data["capacity"] = 0

        with pytest.raises(ZeroDBValidationError, match="capacity must be at least"):
            service.create_session(mock_session_data, mock_instructor_id)

    def test_create_session_with_event(self, service, mock_session_data, mock_instructor_id):
        """Test session creation linked to an event"""
        event_id = uuid4()
        mock_session_data["event_id"] = str(event_id)

        # Mock event exists
        service.db.get_document = Mock(return_value={"id": str(event_id)})
        service.db.create_document = Mock(return_value={
            "id": str(uuid4()),
            **mock_session_data
        })
        service.cloudflare.create_room = Mock(return_value={"room_id": "room-123"})
        service.db.update_document = Mock()

        result = service.create_session(mock_session_data, mock_instructor_id)

        assert result is not None
        service.db.get_document.assert_called_once_with(
            collection="events",
            document_id=str(event_id)
        )

    def test_create_session_event_not_found(self, service, mock_session_data, mock_instructor_id):
        """Test session creation fails if event doesn't exist"""
        mock_session_data["event_id"] = str(uuid4())
        service.db.get_document = Mock(side_effect=ZeroDBNotFoundError("Event not found"))

        with pytest.raises(ZeroDBValidationError, match="Event not found"):
            service.create_session(mock_session_data, mock_instructor_id)

    def test_create_session_cloudflare_failure(self, service, mock_session_data, mock_instructor_id):
        """Test session creation continues even if Cloudflare room creation fails"""
        session_id = uuid4()
        service.db.create_document = Mock(return_value={
            "id": str(session_id),
            **mock_session_data
        })
        service.cloudflare.create_room = Mock(side_effect=CloudflareCallsError("API error"))

        # Should not raise exception
        result = service.create_session(mock_session_data, mock_instructor_id)
        assert result is not None

    # ========================================================================
    # GET SESSION TESTS
    # ========================================================================

    def test_get_session_success(self, service):
        """Test successful session retrieval"""
        session_id = str(uuid4())
        mock_session = {
            "id": session_id,
            "title": "Test Session",
            "status": SessionStatus.SCHEDULED.value
        }
        service.db.get_document = Mock(return_value=mock_session)

        result = service.get_session(session_id)

        assert result == mock_session
        service.db.get_document.assert_called_once_with(
            collection="training_sessions",
            document_id=session_id
        )

    def test_get_session_not_found(self, service):
        """Test session retrieval with non-existent ID"""
        service.db.get_document = Mock(side_effect=ZeroDBNotFoundError("Not found"))

        with pytest.raises(ZeroDBNotFoundError):
            service.get_session("non-existent-id")

    # ========================================================================
    # UPDATE SESSION TESTS
    # ========================================================================

    def test_update_session_success(self, service):
        """Test successful session update"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "title": "Old Title",
            "status": SessionStatus.SCHEDULED.value
        }

        updates = {
            "title": "New Title",
            "description": "Updated description"
        }

        service.db.get_document = Mock(return_value=existing_session)
        service.db.update_document = Mock(return_value={**existing_session, **updates})

        result = service.update_session(session_id, updates, instructor_id)

        assert result["title"] == "New Title"
        service.db.update_document.assert_called_once()

    def test_update_session_ended(self, service):
        """Test updating an ended session fails"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "status": SessionStatus.ENDED.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="Cannot update ended"):
            service.update_session(session_id, {"title": "New"}, uuid4())

    def test_update_session_canceled(self, service):
        """Test updating a canceled session fails"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "status": SessionStatus.CANCELED.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="Cannot update"):
            service.update_session(session_id, {"title": "New"}, uuid4())

    def test_update_session_invalid_duration(self, service):
        """Test session update fails with invalid duration"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "status": SessionStatus.SCHEDULED.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="duration must be between"):
            service.update_session(session_id, {"duration_minutes": 0}, uuid4())

    # ========================================================================
    # DELETE SESSION TESTS
    # ========================================================================

    def test_delete_session_success(self, service):
        """Test successful session deletion"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "room_id": "room-123",
            "status": SessionStatus.SCHEDULED.value
        }

        service.db.get_document = Mock(return_value=existing_session)
        service.cloudflare.delete_room = Mock()
        service.db.update_document = Mock(return_value={
            **existing_session,
            "status": SessionStatus.CANCELED.value
        })

        result = service.delete_session(session_id, instructor_id)

        assert result["status"] == SessionStatus.CANCELED.value
        service.cloudflare.delete_room.assert_called_once_with("room-123")

    def test_delete_session_no_room(self, service):
        """Test deleting session without Cloudflare room"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "room_id": None,
            "status": SessionStatus.SCHEDULED.value
        }

        service.db.get_document = Mock(return_value=existing_session)
        service.cloudflare.delete_room = Mock()
        service.db.update_document = Mock(return_value={
            **existing_session,
            "status": SessionStatus.CANCELED.value
        })

        result = service.delete_session(session_id, uuid4())

        service.cloudflare.delete_room.assert_not_called()

    def test_delete_session_cloudflare_error(self, service):
        """Test session deletion continues even if Cloudflare deletion fails"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "room_id": "room-123",
            "status": SessionStatus.SCHEDULED.value
        }

        service.db.get_document = Mock(return_value=existing_session)
        service.cloudflare.delete_room = Mock(side_effect=CloudflareCallsError("API error"))
        service.db.update_document = Mock(return_value={
            **existing_session,
            "status": SessionStatus.CANCELED.value
        })

        # Should not raise exception
        result = service.delete_session(session_id, uuid4())
        assert result["status"] == SessionStatus.CANCELED.value

    # ========================================================================
    # LIST SESSIONS TESTS
    # ========================================================================

    def test_list_sessions_success(self, service):
        """Test successful session listing"""
        mock_result = {
            "documents": [
                {"id": "1", "title": "Session 1"},
                {"id": "2", "title": "Session 2"}
            ],
            "total": 2
        }

        service.db.query_documents = Mock(return_value=mock_result)

        result = service.list_sessions(limit=10, offset=0)

        assert len(result["documents"]) == 2
        assert result["total"] == 2

    def test_list_sessions_with_filters(self, service):
        """Test session listing with filters"""
        filters = {
            "status": SessionStatus.SCHEDULED.value,
            "instructor_id": str(uuid4())
        }

        service.db.query_documents = Mock(return_value={"documents": [], "total": 0})

        service.list_sessions(filters=filters)

        service.db.query_documents.assert_called_once()
        call_args = service.db.query_documents.call_args
        assert call_args[1]["filters"] == filters

    # ========================================================================
    # GET UPCOMING SESSIONS TESTS
    # ========================================================================

    def test_get_upcoming_sessions(self, service):
        """Test getting upcoming sessions"""
        service.db.query_documents = Mock(return_value={
            "documents": [{"id": "1", "title": "Upcoming Session"}],
            "total": 1
        })

        result = service.get_upcoming_sessions(limit=5)

        assert len(result) == 1
        assert result[0]["title"] == "Upcoming Session"

    def test_get_upcoming_sessions_by_instructor(self, service):
        """Test getting upcoming sessions filtered by instructor"""
        instructor_id = uuid4()
        service.db.query_documents = Mock(return_value={"documents": [], "total": 0})

        service.get_upcoming_sessions(instructor_id=instructor_id)

        call_args = service.db.query_documents.call_args
        assert call_args[1]["filters"]["instructor_id"] == str(instructor_id)

    # ========================================================================
    # START SESSION TESTS
    # ========================================================================

    def test_start_session_success(self, service):
        """Test successfully starting a session"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.SCHEDULED.value,
            "room_id": "room-123"
        }

        service.db.get_document = Mock(return_value=existing_session)
        service.db.update_document = Mock(return_value={
            **existing_session,
            "status": SessionStatus.LIVE.value
        })

        result = service.start_session(session_id, instructor_id)

        assert result["status"] == SessionStatus.LIVE.value
        service.db.update_document.assert_called_once()

    def test_start_session_wrong_instructor(self, service):
        """Test starting session fails if wrong instructor"""
        session_id = str(uuid4())
        instructor_id = uuid4()
        wrong_instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.SCHEDULED.value,
            "room_id": "room-123"
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="Only the session instructor"):
            service.start_session(session_id, wrong_instructor_id)

    def test_start_session_wrong_status(self, service):
        """Test starting session fails if not scheduled"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.LIVE.value,
            "room_id": "room-123"
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="Cannot start session"):
            service.start_session(session_id, instructor_id)

    def test_start_session_no_room(self, service):
        """Test starting session fails without room"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.SCHEDULED.value,
            "room_id": None
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="room has not been created"):
            service.start_session(session_id, instructor_id)

    # ========================================================================
    # END SESSION TESTS
    # ========================================================================

    def test_end_session_success(self, service):
        """Test successfully ending a session"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.LIVE.value
        }

        service.db.get_document = Mock(return_value=existing_session)
        service.db.update_document = Mock(return_value={
            **existing_session,
            "status": SessionStatus.ENDED.value
        })

        result = service.end_session(session_id, instructor_id)

        assert result["status"] == SessionStatus.ENDED.value

    def test_end_session_wrong_instructor(self, service):
        """Test ending session fails if wrong instructor"""
        session_id = str(uuid4())
        instructor_id = uuid4()
        wrong_instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.LIVE.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="Only the session instructor"):
            service.end_session(session_id, wrong_instructor_id)

    def test_end_session_not_live(self, service):
        """Test ending session fails if not live"""
        session_id = str(uuid4())
        instructor_id = uuid4()

        existing_session = {
            "id": session_id,
            "instructor_id": str(instructor_id),
            "status": SessionStatus.SCHEDULED.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        with pytest.raises(ZeroDBValidationError, match="Cannot end session"):
            service.end_session(session_id, instructor_id)

    # ========================================================================
    # CAN USER JOIN TESTS
    # ========================================================================

    def test_can_user_join_session_live(self, service):
        """Test user can join live session"""
        session_id = str(uuid4())
        user_id = uuid4()

        existing_session = {
            "id": session_id,
            "status": SessionStatus.LIVE.value,
            "capacity": 20,
            "current_participants": 10,
            "members_only": True
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, user_id, UserRole.MEMBER.value)

        assert result["can_join"] is True

    def test_can_user_join_session_canceled(self, service):
        """Test user cannot join canceled session"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "status": SessionStatus.CANCELED.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, uuid4(), UserRole.MEMBER.value)

        assert result["can_join"] is False
        assert "canceled" in result["reason"]

    def test_can_user_join_session_ended(self, service):
        """Test user cannot join ended session"""
        session_id = str(uuid4())
        existing_session = {
            "id": session_id,
            "status": SessionStatus.ENDED.value
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, uuid4(), UserRole.MEMBER.value)

        assert result["can_join"] is False
        assert "ended" in result["reason"]

    def test_can_user_join_too_early(self, service):
        """Test user cannot join more than 10 minutes before start"""
        session_id = str(uuid4())
        start_time = datetime.utcnow() + timedelta(minutes=15)

        existing_session = {
            "id": session_id,
            "status": SessionStatus.SCHEDULED.value,
            "start_time": start_time.isoformat(),
            "capacity": 20,
            "current_participants": 10
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, uuid4(), UserRole.MEMBER.value)

        assert result["can_join"] is False
        assert "10 minutes before" in result["reason"]

    def test_can_user_join_capacity_full(self, service):
        """Test user cannot join at-capacity session"""
        session_id = str(uuid4())
        start_time = datetime.utcnow() + timedelta(minutes=5)

        existing_session = {
            "id": session_id,
            "status": SessionStatus.SCHEDULED.value,
            "start_time": start_time.isoformat(),
            "capacity": 20,
            "current_participants": 20
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, uuid4(), UserRole.MEMBER.value)

        assert result["can_join"] is False
        assert "full capacity" in result["reason"]

    def test_can_user_join_members_only(self, service):
        """Test public user cannot join members-only session"""
        session_id = str(uuid4())
        start_time = datetime.utcnow() + timedelta(minutes=5)

        existing_session = {
            "id": session_id,
            "status": SessionStatus.SCHEDULED.value,
            "start_time": start_time.isoformat(),
            "capacity": 20,
            "current_participants": 10,
            "members_only": True
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, uuid4(), UserRole.PUBLIC.value)

        assert result["can_join"] is False
        assert "members only" in result["reason"]

    def test_can_user_join_within_window(self, service):
        """Test user can join within 10-minute window"""
        session_id = str(uuid4())
        start_time = datetime.utcnow() + timedelta(minutes=5)

        existing_session = {
            "id": session_id,
            "status": SessionStatus.SCHEDULED.value,
            "start_time": start_time.isoformat(),
            "capacity": 20,
            "current_participants": 10,
            "members_only": True
        }

        service.db.get_document = Mock(return_value=existing_session)

        result = service.can_user_join(session_id, uuid4(), UserRole.MEMBER.value)

        assert result["can_join"] is True

    # ========================================================================
    # SERVICE SINGLETON TESTS
    # ========================================================================

    def test_get_training_session_service_singleton(self):
        """Test service singleton pattern"""
        with patch('backend.services.training_session_service.get_zerodb_client'), \
             patch('backend.services.training_session_service.get_cloudflare_calls_service'):
            service1 = get_training_session_service()
            service2 = get_training_session_service()

            assert service1 is service2
