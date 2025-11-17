"""
Comprehensive Tests for Board Approval API Routes

Tests the complete board approval REST API including:
- GET /api/admin/board/applications/pending - Get pending applications
- POST /api/admin/board/applications/{id}/vote - Cast vote
- GET /api/admin/board/applications/{id}/votes - Get vote history
- GET /api/admin/board/stats - Get board member statistics

Target: 80%+ code coverage
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from backend.app import app
from backend.models.schemas import (
    User,
    UserRole,
    Application,
    Approval,
    ApplicationStatus,
    ApprovalStatus,
    ApprovalAction,
    SubscriptionTier
)
from backend.services.board_approval_service import (
    AlreadyVotedError,
    InvalidStatusError,
    BoardApprovalError
)


# Create test client
client = TestClient(app)


@pytest.fixture
def board_member_user():
    """Create a board member user for testing"""
    return User(
        id=uuid4(),
        email="board@example.com",
        password_hash="hashed_password",
        role=UserRole.BOARD_MEMBER,
        is_verified=True
    )


@pytest.fixture
def admin_user():
    """Create an admin user for testing"""
    return User(
        id=uuid4(),
        email="admin@example.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_verified=True
    )


@pytest.fixture
def regular_user():
    """Create a regular user (not board member)"""
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash="hashed_password",
        role=UserRole.MEMBER,
        is_verified=True
    )


@pytest.fixture
def sample_application():
    """Create a sample application"""
    return Application(
        id=uuid4(),
        user_id=uuid4(),
        status=ApplicationStatus.UNDER_REVIEW,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        subscription_tier=SubscriptionTier.FREE,
        approval_count=0,
        required_approvals=2,
        rejection_count=0,
        board_votes=[],
        approver_ids=[],
        rejector_ids=[],
        pending_board_review=True,
        submitted_at=datetime.utcnow()
    )


@pytest.fixture
def sample_approval():
    """Create a sample approval"""
    return Approval(
        id=uuid4(),
        application_id=uuid4(),
        approver_id=uuid4(),
        status=ApprovalStatus.APPROVED,
        action=ApprovalAction.APPROVE,
        vote_cast_at=datetime.utcnow(),
        sequence=1,
        is_active=True
    )


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

class TestAuthorization:
    """Test authorization requirements"""

    def test_pending_applications_requires_auth(self):
        """Test that pending applications endpoint requires authentication"""
        response = client.get("/api/admin/board/applications/pending")
        assert response.status_code == 401  # Unauthorized

    def test_pending_applications_requires_board_member(self, regular_user):
        """Test that regular users cannot access board endpoints"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=regular_user):
            response = client.get("/api/admin/board/applications/pending")
            assert response.status_code == 403  # Forbidden

    def test_board_member_can_access(self, board_member_user):
        """Test that board members can access endpoints"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_pending_applications_for_board_member.return_value = []
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/applications/pending")
                assert response.status_code == 200

    def test_admin_can_access(self, admin_user):
        """Test that admins can access board endpoints"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=admin_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_pending_applications_for_board_member.return_value = []
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/applications/pending")
                assert response.status_code == 200


# ============================================================================
# GET PENDING APPLICATIONS TESTS
# ============================================================================

class TestGetPendingApplications:
    """Test GET /api/admin/board/applications/pending endpoint"""

    def test_get_pending_applications_success(self, board_member_user, sample_application):
        """Test successfully retrieving pending applications"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_pending_applications_for_board_member.return_value = [sample_application]
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/applications/pending")

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["first_name"] == "John"
                assert data[0]["last_name"] == "Doe"
                assert data[0]["status"] == "UNDER_REVIEW"

    def test_get_pending_applications_empty(self, board_member_user):
        """Test retrieving pending applications when none exist"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_pending_applications_for_board_member.return_value = []
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/applications/pending")

                assert response.status_code == 200
                data = response.json()
                assert data == []

    def test_get_pending_applications_error(self, board_member_user):
        """Test handling of service errors"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_pending_applications_for_board_member.side_effect = BoardApprovalError("Database error")
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/applications/pending")

                assert response.status_code == 500
                assert "Failed to retrieve pending applications" in response.json()["detail"]


# ============================================================================
# CAST VOTE TESTS
# ============================================================================

class TestCastVote:
    """Test POST /api/admin/board/applications/{id}/vote endpoint"""

    def test_cast_approval_vote_success(self, board_member_user, sample_application):
        """Test successfully casting an approval vote"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.cast_vote.return_value = {
                    "application_id": str(sample_application.id),
                    "vote": "APPROVED",
                    "approval_count": 1,
                    "required_approvals": 2,
                    "application_status": ApplicationStatus.UNDER_REVIEW,
                    "fully_approved": False
                }
                mock_service.return_value = mock_service_instance

                response = client.post(
                    f"/api/admin/board/applications/{sample_application.id}/vote",
                    json={
                        "action": "APPROVE",
                        "notes": "Excellent application"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["vote"] == "APPROVED"
                assert data["approval_count"] == 1
                assert data["fully_approved"] is False
                assert "needs 1 more approval" in data["message"]

    def test_cast_rejection_vote_success(self, board_member_user, sample_application):
        """Test successfully casting a rejection vote"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.cast_vote.return_value = {
                    "application_id": str(sample_application.id),
                    "vote": "REJECTED",
                    "approval_count": 0,
                    "required_approvals": 2,
                    "application_status": ApplicationStatus.REJECTED,
                    "fully_approved": False
                }
                mock_service.return_value = mock_service_instance

                response = client.post(
                    f"/api/admin/board/applications/{sample_application.id}/vote",
                    json={
                        "action": "REJECT",
                        "notes": "Does not meet requirements"
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["vote"] == "REJECTED"
                assert data["application_status"] == "REJECTED"
                assert "has been rejected" in data["message"]

    def test_cast_vote_fully_approved(self, board_member_user, sample_application):
        """Test casting vote that results in full approval"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.cast_vote.return_value = {
                    "application_id": str(sample_application.id),
                    "vote": "APPROVED",
                    "approval_count": 2,
                    "required_approvals": 2,
                    "application_status": ApplicationStatus.APPROVED,
                    "fully_approved": True
                }
                mock_service.return_value = mock_service_instance

                response = client.post(
                    f"/api/admin/board/applications/{sample_application.id}/vote",
                    json={"action": "APPROVE"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["fully_approved"] is True
                assert "fully approved" in data["message"]

    def test_cast_vote_already_voted(self, board_member_user, sample_application):
        """Test duplicate vote prevention"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.cast_vote.side_effect = AlreadyVotedError("Already voted")
                mock_service.return_value = mock_service_instance

                response = client.post(
                    f"/api/admin/board/applications/{sample_application.id}/vote",
                    json={"action": "APPROVE"}
                )

                assert response.status_code == 400
                assert "Already voted" in response.json()["detail"]

    def test_cast_vote_invalid_status(self, board_member_user, sample_application):
        """Test voting on application with invalid status"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.cast_vote.side_effect = InvalidStatusError("Invalid status")
                mock_service.return_value = mock_service_instance

                response = client.post(
                    f"/api/admin/board/applications/{sample_application.id}/vote",
                    json={"action": "APPROVE"}
                )

                assert response.status_code == 400
                assert "Invalid status" in response.json()["detail"]

    def test_cast_vote_application_not_found(self, board_member_user):
        """Test voting on non-existent application"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.cast_vote.side_effect = BoardApprovalError("Application not found")
                mock_service.return_value = mock_service_instance

                response = client.post(
                    f"/api/admin/board/applications/{uuid4()}/vote",
                    json={"action": "APPROVE"}
                )

                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()


# ============================================================================
# GET VOTE HISTORY TESTS
# ============================================================================

class TestGetVoteHistory:
    """Test GET /api/admin/board/applications/{id}/votes endpoint"""

    def test_get_vote_history_success(self, board_member_user, sample_application, sample_approval):
        """Test successfully retrieving vote history"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_vote_history.return_value = [sample_approval]
                mock_service.return_value = mock_service_instance

                response = client.get(
                    f"/api/admin/board/applications/{sample_application.id}/votes"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["application_id"] == str(sample_application.id)
                assert data["total_votes"] == 1
                assert len(data["votes"]) == 1
                assert data["votes"][0]["action"] == "APPROVE"
                assert data["votes"][0]["status"] == "APPROVED"
                assert data["votes"][0]["sequence"] == 1

    def test_get_vote_history_empty(self, board_member_user, sample_application):
        """Test retrieving vote history when no votes exist"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_vote_history.return_value = []
                mock_service.return_value = mock_service_instance

                response = client.get(
                    f"/api/admin/board/applications/{sample_application.id}/votes"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["total_votes"] == 0
                assert data["votes"] == []

    def test_get_vote_history_error(self, board_member_user, sample_application):
        """Test handling of service errors"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_vote_history.side_effect = BoardApprovalError("Database error")
                mock_service.return_value = mock_service_instance

                response = client.get(
                    f"/api/admin/board/applications/{sample_application.id}/votes"
                )

                assert response.status_code == 500
                assert "Failed to retrieve vote history" in response.json()["detail"]


# ============================================================================
# GET BOARD STATS TESTS
# ============================================================================

class TestGetBoardStats:
    """Test GET /api/admin/board/stats endpoint"""

    def test_get_stats_success(self, board_member_user):
        """Test successfully retrieving board member statistics"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_board_member_stats.return_value = {
                    "total_votes": 15,
                    "approved": 12,
                    "rejected": 2,
                    "pending": 1
                }
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["total_votes"] == 15
                assert data["approved"] == 12
                assert data["rejected"] == 2
                assert data["pending"] == 1

    def test_get_stats_no_votes(self, board_member_user):
        """Test retrieving stats when board member has no votes"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_board_member_stats.return_value = {
                    "total_votes": 0,
                    "approved": 0,
                    "rejected": 0,
                    "pending": 0
                }
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["total_votes"] == 0

    def test_get_stats_error(self, board_member_user):
        """Test handling of service errors"""
        with patch('backend.middleware.auth_middleware.get_current_user', return_value=board_member_user):
            with patch('backend.services.board_approval_service.get_board_approval_service') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.get_board_member_stats.side_effect = BoardApprovalError("Database error")
                mock_service.return_value = mock_service_instance

                response = client.get("/api/admin/board/stats")

                assert response.status_code == 500
                assert "Failed to retrieve statistics" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.routes.admin.board_approval", "--cov-report=term-missing"])
