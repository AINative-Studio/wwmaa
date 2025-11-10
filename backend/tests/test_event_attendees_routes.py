"""
Tests for Event Attendees Routes

Test coverage for:
- Admin access control
- Attendee listing with filters
- CSV export
- Bulk email
- Check-in functionality
- Waitlist promotion
- Statistics endpoint
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.models.schemas import UserRole, RSVPStatus


class TestEventAttendeesRoutes:
    """Test event attendees API routes"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.routes import event_attendees

        app = FastAPI()
        app.include_router(event_attendees.router)
        return TestClient(app)

    @pytest.fixture
    def admin_user(self):
        """Sample admin user"""
        return {
            "id": str(uuid4()),
            "email": "admin@wwmaa.org",
            "role": UserRole.ADMIN.value
        }

    @pytest.fixture
    def board_member_user(self):
        """Sample board member user"""
        return {
            "id": str(uuid4()),
            "email": "board@wwmaa.org",
            "role": UserRole.BOARD_MEMBER.value
        }

    @pytest.fixture
    def member_user(self):
        """Sample regular member user"""
        return {
            "id": str(uuid4()),
            "email": "member@wwmaa.org",
            "role": UserRole.MEMBER.value
        }

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
                "user_name": "Alice Smith",
                "user_email": "alice@example.com",
                "status": RSVPStatus.CONFIRMED.value,
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": str(uuid4()),
                "user_name": "Bob Johnson",
                "user_email": "bob@example.com",
                "status": RSVPStatus.WAITLIST.value,
                "created_at": "2024-01-16T11:00:00Z"
            }
        ]

    @pytest.fixture
    def auth_token_admin(self, admin_user):
        """Mock admin auth token"""
        with patch("backend.middleware.auth_middleware.verify_token") as mock_verify:
            mock_verify.return_value = admin_user
            yield "Bearer valid_admin_token"

    @pytest.fixture
    def auth_token_board(self, board_member_user):
        """Mock board member auth token"""
        with patch("backend.middleware.auth_middleware.verify_token") as mock_verify:
            mock_verify.return_value = board_member_user
            yield "Bearer valid_board_token"

    @pytest.fixture
    def auth_token_member(self, member_user):
        """Mock member auth token"""
        with patch("backend.middleware.auth_middleware.verify_token") as mock_verify:
            mock_verify.return_value = member_user
            yield "Bearer valid_member_token"

    # ========================================================================
    # LIST ATTENDEES TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_list_attendees_admin_success(
        self, mock_service, client, sample_event_id, sample_attendees, auth_token_admin
    ):
        """Test listing attendees as admin"""
        mock_service.get_attendees.return_value = {
            "attendees": sample_attendees,
            "total": 2,
            "limit": 100,
            "offset": 0
        }

        response = client.get(
            f"/api/events/{sample_event_id}/attendees",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["attendees"]) == 2

    @patch("backend.routes.event_attendees.attendee_service")
    def test_list_attendees_board_member(
        self, mock_service, client, sample_event_id, sample_attendees, auth_token_board
    ):
        """Test listing attendees as board member"""
        mock_service.get_attendees.return_value = {
            "attendees": sample_attendees,
            "total": 2,
            "limit": 100,
            "offset": 0
        }

        response = client.get(
            f"/api/events/{sample_event_id}/attendees",
            headers={"Authorization": auth_token_board}
        )

        assert response.status_code == 200

    @patch("backend.routes.event_attendees.attendee_service")
    def test_list_attendees_member_forbidden(
        self, mock_service, client, sample_event_id, auth_token_member
    ):
        """Test that regular members cannot list attendees"""
        response = client.get(
            f"/api/events/{sample_event_id}/attendees",
            headers={"Authorization": auth_token_member}
        )

        assert response.status_code == 403

    def test_list_attendees_no_auth(self, client, sample_event_id):
        """Test that unauthenticated users cannot list attendees"""
        response = client.get(f"/api/events/{sample_event_id}/attendees")

        assert response.status_code == 401

    @patch("backend.routes.event_attendees.attendee_service")
    def test_list_attendees_with_filters(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test listing attendees with status filter"""
        mock_service.get_attendees.return_value = {
            "attendees": [],
            "total": 0,
            "limit": 100,
            "offset": 0
        }

        response = client.get(
            f"/api/events/{sample_event_id}/attendees?status=confirmed&search=alice",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        mock_service.get_attendees.assert_called_once()

        # Verify filters were passed
        call_kwargs = mock_service.get_attendees.call_args[1]
        assert call_kwargs["status"] == "confirmed"
        assert call_kwargs["search"] == "alice"

    @patch("backend.routes.event_attendees.attendee_service")
    def test_list_attendees_service_error(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test handling service error"""
        from backend.services.attendee_service import AttendeeServiceError

        mock_service.get_attendees.side_effect = AttendeeServiceError("Database error")

        response = client.get(
            f"/api/events/{sample_event_id}/attendees",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 500

    # ========================================================================
    # EXPORT CSV TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_export_attendees_csv(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test CSV export"""
        mock_service.export_attendees_csv.return_value = "Name,Email\nAlice,alice@example.com"

        response = client.get(
            f"/api/events/{sample_event_id}/attendees/export",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "Alice" in response.text

    @patch("backend.routes.event_attendees.attendee_service")
    def test_export_attendees_member_forbidden(
        self, mock_service, client, sample_event_id, auth_token_member
    ):
        """Test that members cannot export CSV"""
        response = client.get(
            f"/api/events/{sample_event_id}/attendees/export",
            headers={"Authorization": auth_token_member}
        )

        assert response.status_code == 403

    # ========================================================================
    # BULK EMAIL TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_send_bulk_email_success(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test sending bulk email"""
        mock_service.send_bulk_email.return_value = {
            "sent": 2,
            "failed": 0,
            "total": 2,
            "errors": []
        }

        response = client.post(
            f"/api/events/{sample_event_id}/attendees/bulk-email",
            json={
                "subject": "Event Update",
                "message": "Important update about the event"
            },
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sent"] == 2
        assert data["failed"] == 0

    @patch("backend.routes.event_attendees.attendee_service")
    def test_send_bulk_email_with_filter(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test bulk email with status filter"""
        mock_service.send_bulk_email.return_value = {
            "sent": 1,
            "failed": 0,
            "total": 1,
            "errors": []
        }

        response = client.post(
            f"/api/events/{sample_event_id}/attendees/bulk-email",
            json={
                "subject": "Confirmed Only",
                "message": "Message for confirmed",
                "status_filter": "confirmed"
            },
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        assert response.json()["sent"] == 1

    @patch("backend.routes.event_attendees.attendee_service")
    def test_send_bulk_email_validation_error(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test bulk email with invalid data"""
        response = client.post(
            f"/api/events/{sample_event_id}/attendees/bulk-email",
            json={
                "subject": "",  # Empty subject
                "message": "Test"
            },
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 422  # Validation error

    @patch("backend.routes.event_attendees.attendee_service")
    def test_send_bulk_email_member_forbidden(
        self, mock_service, client, sample_event_id, auth_token_member
    ):
        """Test that members cannot send bulk email"""
        response = client.post(
            f"/api/events/{sample_event_id}/attendees/bulk-email",
            json={"subject": "Test", "message": "Test"},
            headers={"Authorization": auth_token_member}
        )

        assert response.status_code == 403

    # ========================================================================
    # CHECK-IN TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_check_in_attendee_success(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test checking in attendee"""
        rsvp_id = uuid4()

        mock_service.check_in_attendee.return_value = {
            "id": str(rsvp_id),
            "checked_in_at": "2024-01-20T18:00:00Z"
        }

        response = client.post(
            f"/api/events/{sample_event_id}/attendees/{rsvp_id}/check-in",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "checked_in_at" in data["rsvp"]

    @patch("backend.routes.event_attendees.attendee_service")
    def test_check_in_instructor_allowed(
        self, mock_service, client, sample_event_id
    ):
        """Test that instructors can check in attendees"""
        instructor_user = {
            "id": str(uuid4()),
            "email": "instructor@wwmaa.org",
            "role": UserRole.INSTRUCTOR.value
        }

        rsvp_id = uuid4()

        with patch("backend.middleware.auth_middleware.verify_token") as mock_verify:
            mock_verify.return_value = instructor_user

            mock_service.check_in_attendee.return_value = {"id": str(rsvp_id)}

            response = client.post(
                f"/api/events/{sample_event_id}/attendees/{rsvp_id}/check-in",
                headers={"Authorization": "Bearer instructor_token"}
            )

            assert response.status_code == 200

    @patch("backend.routes.event_attendees.attendee_service")
    def test_check_in_member_forbidden(
        self, mock_service, client, sample_event_id, auth_token_member
    ):
        """Test that regular members cannot check in"""
        rsvp_id = uuid4()

        response = client.post(
            f"/api/events/{sample_event_id}/attendees/{rsvp_id}/check-in",
            headers={"Authorization": auth_token_member}
        )

        assert response.status_code == 403

    # ========================================================================
    # NO-SHOW TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_mark_no_show_success(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test marking attendee as no-show"""
        rsvp_id = uuid4()

        mock_service.mark_no_show.return_value = {
            "id": str(rsvp_id),
            "no_show": True
        }

        response = client.post(
            f"/api/events/{sample_event_id}/attendees/{rsvp_id}/no-show",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("backend.routes.event_attendees.attendee_service")
    def test_mark_no_show_instructor_forbidden(
        self, mock_service, client, sample_event_id
    ):
        """Test that instructors cannot mark no-show (admin/board only)"""
        instructor_user = {
            "id": str(uuid4()),
            "email": "instructor@wwmaa.org",
            "role": UserRole.INSTRUCTOR.value
        }

        rsvp_id = uuid4()

        with patch("backend.middleware.auth_middleware.verify_token") as mock_verify:
            mock_verify.return_value = instructor_user

            response = client.post(
                f"/api/events/{sample_event_id}/attendees/{rsvp_id}/no-show",
                headers={"Authorization": "Bearer instructor_token"}
            )

            assert response.status_code == 403

    # ========================================================================
    # WAITLIST PROMOTION TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_promote_from_waitlist_success(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test promoting from waitlist"""
        mock_service.promote_from_waitlist.return_value = {
            "promoted": 2,
            "attendees": [
                {"id": str(uuid4()), "name": "User 1", "email": "user1@example.com"},
                {"id": str(uuid4()), "name": "User 2", "email": "user2@example.com"}
            ],
            "message": "Promoted 2 attendee(s) from waitlist"
        }

        response = client.post(
            f"/api/events/{sample_event_id}/waitlist/promote",
            json={"count": 2},
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["promoted"] == 2
        assert len(data["attendees"]) == 2

    @patch("backend.routes.event_attendees.attendee_service")
    def test_promote_from_waitlist_validation(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test waitlist promotion with invalid count"""
        response = client.post(
            f"/api/events/{sample_event_id}/waitlist/promote",
            json={"count": 0},  # Invalid: must be >= 1
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 422

    @patch("backend.routes.event_attendees.attendee_service")
    def test_promote_from_waitlist_member_forbidden(
        self, mock_service, client, sample_event_id, auth_token_member
    ):
        """Test that members cannot promote waitlist"""
        response = client.post(
            f"/api/events/{sample_event_id}/waitlist/promote",
            json={"count": 1},
            headers={"Authorization": auth_token_member}
        )

        assert response.status_code == 403

    # ========================================================================
    # STATISTICS TESTS
    # ========================================================================

    @patch("backend.routes.event_attendees.attendee_service")
    def test_get_attendee_stats_success(
        self, mock_service, client, sample_event_id, auth_token_admin
    ):
        """Test getting attendee statistics"""
        mock_service.get_attendee_stats.return_value = {
            "total": 10,
            "confirmed": 7,
            "waitlist": 2,
            "canceled": 1,
            "checked_in": 5,
            "no_show": 2,
            "pending": 0
        }

        response = client.get(
            f"/api/events/{sample_event_id}/attendees/stats",
            headers={"Authorization": auth_token_admin}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["confirmed"] == 7
        assert data["checked_in"] == 5

    @patch("backend.routes.event_attendees.attendee_service")
    def test_get_attendee_stats_instructor_allowed(
        self, mock_service, client, sample_event_id
    ):
        """Test that instructors can view stats"""
        instructor_user = {
            "id": str(uuid4()),
            "email": "instructor@wwmaa.org",
            "role": UserRole.INSTRUCTOR.value
        }

        with patch("backend.middleware.auth_middleware.verify_token") as mock_verify:
            mock_verify.return_value = instructor_user

            mock_service.get_attendee_stats.return_value = {
                "total": 5,
                "confirmed": 5,
                "waitlist": 0,
                "canceled": 0,
                "checked_in": 0,
                "no_show": 0,
                "pending": 0
            }

            response = client.get(
                f"/api/events/{sample_event_id}/attendees/stats",
                headers={"Authorization": "Bearer instructor_token"}
            )

            assert response.status_code == 200

    @patch("backend.routes.event_attendees.attendee_service")
    def test_get_attendee_stats_member_forbidden(
        self, mock_service, client, sample_event_id, auth_token_member
    ):
        """Test that members cannot view stats"""
        response = client.get(
            f"/api/events/{sample_event_id}/attendees/stats",
            headers={"Authorization": auth_token_member}
        )

        assert response.status_code == 403
