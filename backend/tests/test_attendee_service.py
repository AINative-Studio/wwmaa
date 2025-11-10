"""
Tests for Attendee Service

Test coverage for:
- Attendee listing with filters
- CSV export
- Bulk email sending
- Check-in functionality
- No-show tracking
- Waitlist promotion
- Statistics calculation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.services.attendee_service import (
    AttendeeService,
    AttendeeServiceError,
    get_attendee_service
)
from backend.models.schemas import RSVPStatus


class TestAttendeeService:
    """Test AttendeeService class"""

    @pytest.fixture
    def attendee_service(self):
        """Create AttendeeService instance with mocked dependencies"""
        with patch("backend.services.attendee_service.get_zerodb_client") as mock_db, \
             patch("backend.services.attendee_service.get_email_service") as mock_email:
            service = AttendeeService()
            service.db = mock_db.return_value
            service.email_service = mock_email.return_value
            yield service

    @pytest.fixture
    def sample_event_id(self):
        """Sample event UUID"""
        return uuid4()

    @pytest.fixture
    def sample_attendees(self):
        """Sample attendee data"""
        return [
            {
                "id": str(uuid4()),
                "event_id": str(uuid4()),
                "user_id": str(uuid4()),
                "user_name": "Alice Smith",
                "user_email": "alice@example.com",
                "user_phone": "555-0101",
                "status": RSVPStatus.CONFIRMED.value,
                "guests_count": 2,
                "notes": "Bringing a friend",
                "created_at": "2024-01-15T10:00:00Z",
                "checked_in_at": None,
                "no_show": False
            },
            {
                "id": str(uuid4()),
                "event_id": str(uuid4()),
                "user_id": str(uuid4()),
                "user_name": "Bob Johnson",
                "user_email": "bob@example.com",
                "user_phone": "555-0102",
                "status": RSVPStatus.WAITLIST.value,
                "guests_count": 0,
                "notes": "",
                "created_at": "2024-01-16T11:00:00Z",
                "checked_in_at": None,
                "no_show": False
            },
            {
                "id": str(uuid4()),
                "event_id": str(uuid4()),
                "user_id": str(uuid4()),
                "user_name": "Carol Williams",
                "user_email": "carol@example.com",
                "user_phone": "555-0103",
                "status": RSVPStatus.CONFIRMED.value,
                "guests_count": 1,
                "notes": "",
                "created_at": "2024-01-17T12:00:00Z",
                "checked_in_at": "2024-01-20T18:00:00Z",
                "no_show": False
            }
        ]

    # ========================================================================
    # GET ATTENDEES TESTS
    # ========================================================================

    def test_get_attendees_success(self, attendee_service, sample_event_id, sample_attendees):
        """Test successfully getting attendees"""
        attendee_service.db.query_documents = Mock(return_value={
            "documents": sample_attendees
        })

        result = attendee_service.get_attendees(event_id=sample_event_id)

        assert result["total"] == 3
        assert len(result["attendees"]) == 3
        assert result["limit"] == 100
        assert result["offset"] == 0

        attendee_service.db.query_documents.assert_called_once()

    def test_get_attendees_with_status_filter(self, attendee_service, sample_event_id, sample_attendees):
        """Test getting attendees with status filter"""
        confirmed_attendees = [a for a in sample_attendees if a["status"] == RSVPStatus.CONFIRMED.value]

        attendee_service.db.query_documents = Mock(return_value={
            "documents": confirmed_attendees
        })

        result = attendee_service.get_attendees(
            event_id=sample_event_id,
            status="confirmed"
        )

        assert result["total"] == 2
        attendee_service.db.query_documents.assert_called_once()

    def test_get_attendees_with_search(self, attendee_service, sample_event_id, sample_attendees):
        """Test searching attendees by name or email"""
        attendee_service.db.query_documents = Mock(return_value={
            "documents": sample_attendees
        })

        result = attendee_service.get_attendees(
            event_id=sample_event_id,
            search="alice"
        )

        # Should filter to just Alice
        assert result["total"] == 1
        assert result["attendees"][0]["user_name"] == "Alice Smith"

    def test_get_attendees_checked_in_filter(self, attendee_service, sample_event_id, sample_attendees):
        """Test filtering checked-in attendees"""
        checked_in = [a for a in sample_attendees if a.get("checked_in_at")]

        attendee_service.db.query_documents = Mock(return_value={
            "documents": checked_in
        })

        result = attendee_service.get_attendees(
            event_id=sample_event_id,
            status="checked-in"
        )

        assert result["total"] == 1
        assert result["attendees"][0]["user_name"] == "Carol Williams"

    def test_get_attendees_db_error(self, attendee_service, sample_event_id):
        """Test handling database error"""
        from backend.services.zerodb_service import ZeroDBError

        attendee_service.db.query_documents = Mock(side_effect=ZeroDBError("DB error"))

        with pytest.raises(AttendeeServiceError, match="Failed to fetch attendees"):
            attendee_service.get_attendees(event_id=sample_event_id)

    # ========================================================================
    # CSV EXPORT TESTS
    # ========================================================================

    def test_export_attendees_csv_success(self, attendee_service, sample_event_id, sample_attendees):
        """Test successfully exporting attendees to CSV"""
        attendee_service.get_attendees = Mock(return_value={
            "attendees": sample_attendees,
            "total": len(sample_attendees)
        })

        csv_content = attendee_service.export_attendees_csv(event_id=sample_event_id)

        assert "Name,Email,Phone" in csv_content
        assert "Alice Smith" in csv_content
        assert "alice@example.com" in csv_content
        assert "Bob Johnson" in csv_content
        assert "Carol Williams" in csv_content

    def test_export_attendees_csv_empty(self, attendee_service, sample_event_id):
        """Test exporting with no attendees"""
        attendee_service.get_attendees = Mock(return_value={
            "attendees": [],
            "total": 0
        })

        csv_content = attendee_service.export_attendees_csv(event_id=sample_event_id)

        # Should still have headers
        assert "Name,Email,Phone" in csv_content
        # Should not have data rows
        assert "Alice" not in csv_content

    def test_export_attendees_csv_with_filter(self, attendee_service, sample_event_id, sample_attendees):
        """Test CSV export with status filter"""
        confirmed = [a for a in sample_attendees if a["status"] == RSVPStatus.CONFIRMED.value]

        attendee_service.get_attendees = Mock(return_value={
            "attendees": confirmed,
            "total": len(confirmed)
        })

        csv_content = attendee_service.export_attendees_csv(
            event_id=sample_event_id,
            status="confirmed"
        )

        assert "Alice Smith" in csv_content
        assert "Carol Williams" in csv_content
        assert "Bob Johnson" not in csv_content  # Waitlist

    # ========================================================================
    # BULK EMAIL TESTS
    # ========================================================================

    def test_send_bulk_email_success(self, attendee_service, sample_event_id, sample_attendees):
        """Test successfully sending bulk email"""
        attendee_service.get_attendees = Mock(return_value={
            "attendees": sample_attendees,
            "total": len(sample_attendees)
        })

        attendee_service.email_service._send_email = Mock(return_value={"MessageID": "test-123"})

        result = attendee_service.send_bulk_email(
            event_id=sample_event_id,
            subject="Test Event Update",
            message="This is a test message"
        )

        assert result["sent"] == 3
        assert result["failed"] == 0
        assert result["total"] == 3
        assert attendee_service.email_service._send_email.call_count == 3

    def test_send_bulk_email_with_filter(self, attendee_service, sample_event_id, sample_attendees):
        """Test sending bulk email with status filter"""
        confirmed = [a for a in sample_attendees if a["status"] == RSVPStatus.CONFIRMED.value]

        attendee_service.get_attendees = Mock(return_value={
            "attendees": confirmed,
            "total": len(confirmed)
        })

        attendee_service.email_service._send_email = Mock(return_value={"MessageID": "test-123"})

        result = attendee_service.send_bulk_email(
            event_id=sample_event_id,
            subject="Confirmed Only",
            message="Message for confirmed attendees",
            status_filter="confirmed"
        )

        assert result["sent"] == 2
        assert result["failed"] == 0
        assert attendee_service.email_service._send_email.call_count == 2

    def test_send_bulk_email_no_attendees(self, attendee_service, sample_event_id):
        """Test bulk email with no attendees"""
        attendee_service.get_attendees = Mock(return_value={
            "attendees": [],
            "total": 0
        })

        result = attendee_service.send_bulk_email(
            event_id=sample_event_id,
            subject="Test",
            message="Test"
        )

        assert result["sent"] == 0
        assert result["failed"] == 0
        assert "No attendees found" in result["message"]

    def test_send_bulk_email_partial_failure(self, attendee_service, sample_event_id, sample_attendees):
        """Test bulk email with some failures"""
        from backend.services.email_service import EmailSendError

        attendee_service.get_attendees = Mock(return_value={
            "attendees": sample_attendees,
            "total": len(sample_attendees)
        })

        # First call succeeds, second fails, third succeeds
        attendee_service.email_service._send_email = Mock(
            side_effect=[
                {"MessageID": "test-1"},
                EmailSendError("Send failed"),
                {"MessageID": "test-3"}
            ]
        )

        result = attendee_service.send_bulk_email(
            event_id=sample_event_id,
            subject="Test",
            message="Test"
        )

        assert result["sent"] == 2
        assert result["failed"] == 1
        assert len(result["errors"]) == 1

    # ========================================================================
    # CHECK-IN TESTS
    # ========================================================================

    def test_check_in_attendee_success(self, attendee_service):
        """Test successfully checking in an attendee"""
        rsvp_id = uuid4()

        attendee_service.db.update_document = Mock(return_value={
            "id": str(rsvp_id),
            "checked_in_at": datetime.utcnow().isoformat()
        })

        result = attendee_service.check_in_attendee(rsvp_id=rsvp_id)

        assert "checked_in_at" in result
        attendee_service.db.update_document.assert_called_once()

        # Verify correct update data
        call_args = attendee_service.db.update_document.call_args
        assert call_args[1]["collection"] == "rsvps"
        assert "checked_in_at" in call_args[1]["data"]

    def test_check_in_attendee_with_user(self, attendee_service):
        """Test check-in with user who performed check-in"""
        rsvp_id = uuid4()
        checked_in_by = uuid4()

        attendee_service.db.update_document = Mock(return_value={
            "id": str(rsvp_id),
            "checked_in_at": datetime.utcnow().isoformat(),
            "checked_in_by": str(checked_in_by)
        })

        result = attendee_service.check_in_attendee(
            rsvp_id=rsvp_id,
            checked_in_by=checked_in_by
        )

        assert "checked_in_at" in result
        assert "checked_in_by" in result

    def test_check_in_attendee_db_error(self, attendee_service):
        """Test check-in with database error"""
        from backend.services.zerodb_service import ZeroDBError

        rsvp_id = uuid4()
        attendee_service.db.update_document = Mock(side_effect=ZeroDBError("Update failed"))

        with pytest.raises(AttendeeServiceError, match="Check-in failed"):
            attendee_service.check_in_attendee(rsvp_id=rsvp_id)

    # ========================================================================
    # NO-SHOW TESTS
    # ========================================================================

    def test_mark_no_show_success(self, attendee_service):
        """Test marking attendee as no-show"""
        rsvp_id = uuid4()

        attendee_service.db.update_document = Mock(return_value={
            "id": str(rsvp_id),
            "no_show": True,
            "no_show_marked_at": datetime.utcnow().isoformat()
        })

        result = attendee_service.mark_no_show(rsvp_id=rsvp_id)

        assert result["no_show"] is True
        assert "no_show_marked_at" in result

    def test_mark_no_show_with_user(self, attendee_service):
        """Test no-show marking with user tracking"""
        rsvp_id = uuid4()
        marked_by = uuid4()

        attendee_service.db.update_document = Mock(return_value={
            "id": str(rsvp_id),
            "no_show": True,
            "no_show_marked_by": str(marked_by)
        })

        result = attendee_service.mark_no_show(
            rsvp_id=rsvp_id,
            marked_by=marked_by
        )

        assert result["no_show"] is True
        assert "no_show_marked_by" in result

    # ========================================================================
    # WAITLIST PROMOTION TESTS
    # ========================================================================

    def test_promote_from_waitlist_success(self, attendee_service, sample_event_id):
        """Test promoting attendees from waitlist"""
        waitlist_attendees = [
            {
                "id": str(uuid4()),
                "event_id": str(sample_event_id),
                "user_name": "Waitlist User 1",
                "user_email": "wait1@example.com",
                "status": RSVPStatus.WAITLIST.value,
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]

        attendee_service.db.query_documents = Mock(return_value={
            "documents": waitlist_attendees
        })

        attendee_service.db.update_document = Mock(return_value={
            "id": waitlist_attendees[0]["id"],
            "status": RSVPStatus.CONFIRMED.value
        })

        result = attendee_service.promote_from_waitlist(
            event_id=sample_event_id,
            count=1
        )

        assert result["promoted"] == 1
        assert len(result["attendees"]) == 1
        assert "Promoted 1 attendee" in result["message"]

    def test_promote_from_waitlist_multiple(self, attendee_service, sample_event_id):
        """Test promoting multiple attendees"""
        waitlist_attendees = [
            {
                "id": str(uuid4()),
                "user_name": f"User {i}",
                "user_email": f"user{i}@example.com",
                "status": RSVPStatus.WAITLIST.value,
                "created_at": f"2024-01-{15+i}T10:00:00Z"
            }
            for i in range(3)
        ]

        attendee_service.db.query_documents = Mock(return_value={
            "documents": waitlist_attendees
        })

        attendee_service.db.update_document = Mock(return_value={
            "status": RSVPStatus.CONFIRMED.value
        })

        result = attendee_service.promote_from_waitlist(
            event_id=sample_event_id,
            count=2
        )

        assert result["promoted"] == 2
        assert len(result["attendees"]) == 2

    def test_promote_from_waitlist_empty(self, attendee_service, sample_event_id):
        """Test promoting with no waitlist"""
        attendee_service.db.query_documents = Mock(return_value={
            "documents": []
        })

        result = attendee_service.promote_from_waitlist(
            event_id=sample_event_id,
            count=1
        )

        assert result["promoted"] == 0
        assert "No attendees on waitlist" in result["message"]

    # ========================================================================
    # STATISTICS TESTS
    # ========================================================================

    def test_get_attendee_stats(self, attendee_service, sample_event_id, sample_attendees):
        """Test getting attendee statistics"""
        attendee_service.get_attendees = Mock(return_value={
            "attendees": sample_attendees,
            "total": len(sample_attendees)
        })

        stats = attendee_service.get_attendee_stats(event_id=sample_event_id)

        assert stats["total"] == 3
        assert stats["confirmed"] == 2
        assert stats["waitlist"] == 1
        assert stats["checked_in"] == 1
        assert stats["no_show"] == 0

    def test_get_attendee_stats_empty(self, attendee_service, sample_event_id):
        """Test statistics with no attendees"""
        attendee_service.get_attendees = Mock(return_value={
            "attendees": [],
            "total": 0
        })

        stats = attendee_service.get_attendee_stats(event_id=sample_event_id)

        assert stats["total"] == 0
        assert stats["confirmed"] == 0
        assert stats["waitlist"] == 0


class TestAttendeeServiceSingleton:
    """Test singleton pattern"""

    def test_get_attendee_service_singleton(self):
        """Test that get_attendee_service returns same instance"""
        with patch("backend.services.attendee_service.get_zerodb_client"), \
             patch("backend.services.attendee_service.get_email_service"):

            service1 = get_attendee_service()
            service2 = get_attendee_service()

            assert service1 is service2
