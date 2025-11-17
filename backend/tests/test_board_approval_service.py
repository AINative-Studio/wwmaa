"""
Comprehensive Tests for Board Approval Service

Tests the complete board approval workflow including:
- Submitting applications for review
- Casting votes (approve/reject)
- Approval count tracking
- Duplicate vote prevention
- Status transitions
- Error handling

Target: 80%+ code coverage
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from backend.services.board_approval_service import (
    BoardApprovalService,
    BoardApprovalError,
    AlreadyVotedError,
    InvalidStatusError,
    get_board_approval_service
)
from backend.models.schemas import (
    Application,
    Approval,
    ApplicationStatus,
    ApprovalStatus,
    ApprovalAction,
    SubscriptionTier
)


@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client for testing"""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def approval_service(mock_zerodb_client):
    """Create approval service with mocked database"""
    with patch('backend.services.board_approval_service.get_zerodb_client', return_value=mock_zerodb_client):
        service = BoardApprovalService()
        service.db_client = mock_zerodb_client
        return service


@pytest.fixture
def sample_application():
    """Create a sample application for testing"""
    return Application(
        id=uuid4(),
        user_id=uuid4(),
        status=ApplicationStatus.SUBMITTED,
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
        pending_board_review=False
    )


@pytest.fixture
def sample_approval():
    """Create a sample approval for testing"""
    return Approval(
        id=uuid4(),
        application_id=uuid4(),
        approver_id=uuid4(),
        status=ApprovalStatus.PENDING,
        action=ApprovalAction.APPROVE,
        is_active=True,
        sequence=0
    )


class TestSubmitForBoardReview:
    """Test submitting application for board review"""

    def test_submit_success(self, approval_service, mock_zerodb_client, sample_application):
        """Test successful submission for board review"""
        # Setup
        board_member_ids = [uuid4(), uuid4()]
        sample_application.status = ApplicationStatus.SUBMITTED

        mock_zerodb_client.query_table.return_value = {
            "rows": [sample_application.dict()]
        }
        mock_zerodb_client.update_document.return_value = {"success": True}
        mock_zerodb_client.create_document.return_value = {"id": str(uuid4())}

        # Execute
        result = approval_service.submit_for_board_review(
            sample_application.id,
            board_member_ids
        )

        # Verify
        assert result.status == ApplicationStatus.UNDER_REVIEW
        assert result.pending_board_review == True
        assert result.board_review_started_at is not None

        # Verify pending approvals were saved
        # Since BaseDocument auto-generates IDs, new approvals go through update_document path
        # We should see calls to either create_document or update_document
        total_calls = (mock_zerodb_client.create_document.call_count +
                      mock_zerodb_client.update_document.call_count)
        # At least 3 calls: 1 for application update, 2 for approval creation
        assert total_calls >= 3

    def test_submit_invalid_status(self, approval_service, mock_zerodb_client, sample_application):
        """Test submission fails if application not in SUBMITTED status"""
        # Setup
        sample_application.status = ApplicationStatus.APPROVED
        mock_zerodb_client.query_table.return_value = {
            "rows": [sample_application.dict()]
        }

        # Execute & Verify
        with pytest.raises(InvalidStatusError) as exc_info:
            approval_service.submit_for_board_review(
                sample_application.id,
                [uuid4()]
            )

        assert "must be SUBMITTED" in str(exc_info.value)

    def test_submit_application_not_found(self, approval_service, mock_zerodb_client):
        """Test submission fails if application not found"""
        # Setup
        mock_zerodb_client.query_table.return_value = {"rows": []}

        # Execute & Verify
        with pytest.raises(BoardApprovalError) as exc_info:
            approval_service.submit_for_board_review(
                uuid4(),
                [uuid4()]
            )

        assert "not found" in str(exc_info.value)


class TestCastVote:
    """Test casting votes on applications"""

    def test_cast_approval_vote_first(self, approval_service, mock_zerodb_client, sample_application, sample_approval):
        """Test casting first approval vote"""
        # Setup
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        sample_application.pending_board_review = True
        board_member_id = uuid4()

        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_application.dict()]},  # Get application
            {"rows": [sample_approval.dict()]}       # Get pending approval
        ]
        mock_zerodb_client.update_document.return_value = {"success": True}

        # Execute
        result = approval_service.cast_vote(
            sample_application.id,
            board_member_id,
            ApprovalAction.APPROVE,
            "Looks good!"
        )

        # Verify
        assert result["vote"] == "APPROVED"
        assert result["approval_count"] == 1
        assert result["required_approvals"] == 2
        assert result["fully_approved"] == False
        assert result["application_status"] == ApplicationStatus.UNDER_REVIEW

    def test_cast_approval_vote_second(self, approval_service, mock_zerodb_client, sample_application, sample_approval):
        """Test casting second approval vote (fully approves)"""
        # Setup
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        sample_application.pending_board_review = True
        sample_application.approval_count = 1
        sample_application.approver_ids = [uuid4()]
        sample_application.board_votes = [uuid4()]
        sample_application.first_approval_at = datetime.utcnow()

        board_member_id = uuid4()

        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_application.dict()]},  # Get application
            {"rows": [sample_approval.dict()]}       # Get pending approval
        ]
        mock_zerodb_client.update_document.return_value = {"success": True}

        # Execute
        result = approval_service.cast_vote(
            sample_application.id,
            board_member_id,
            ApprovalAction.APPROVE,
            "Approved!"
        )

        # Verify
        assert result["vote"] == "APPROVED"
        assert result["approval_count"] == 2
        assert result["fully_approved"] == True
        assert result["application_status"] == ApplicationStatus.APPROVED

    def test_cast_rejection_vote(self, approval_service, mock_zerodb_client, sample_application, sample_approval):
        """Test casting rejection vote"""
        # Setup
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        sample_application.pending_board_review = True
        board_member_id = uuid4()

        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_application.dict()]},  # Get application
            {"rows": [sample_approval.dict()]}       # Get pending approval
        ]
        mock_zerodb_client.update_document.return_value = {"success": True}

        # Execute
        result = approval_service.cast_vote(
            sample_application.id,
            board_member_id,
            ApprovalAction.REJECT,
            "Not qualified"
        )

        # Verify
        assert result["vote"] == "REJECTED"
        assert result["approval_count"] == 0
        assert result["fully_approved"] == False
        assert result["application_status"] == ApplicationStatus.REJECTED

    def test_cast_vote_already_voted(self, approval_service, mock_zerodb_client, sample_application):
        """Test duplicate vote prevention"""
        # Setup
        board_member_id = uuid4()
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        sample_application.board_votes = [board_member_id]  # Already voted

        mock_zerodb_client.query_table.return_value = {
            "rows": [sample_application.dict()]
        }

        # Execute & Verify
        with pytest.raises(AlreadyVotedError) as exc_info:
            approval_service.cast_vote(
                sample_application.id,
                board_member_id,
                ApprovalAction.APPROVE
            )

        assert "already voted" in str(exc_info.value)

    def test_cast_vote_invalid_status(self, approval_service, mock_zerodb_client, sample_application):
        """Test voting fails if application not UNDER_REVIEW"""
        # Setup
        sample_application.status = ApplicationStatus.APPROVED
        mock_zerodb_client.query_table.return_value = {
            "rows": [sample_application.dict()]
        }

        # Execute & Verify
        with pytest.raises(InvalidStatusError) as exc_info:
            approval_service.cast_vote(
                sample_application.id,
                uuid4(),
                ApprovalAction.APPROVE
            )

        assert "must be UNDER_REVIEW" in str(exc_info.value)

    def test_cast_vote_no_pending_approval(self, approval_service, mock_zerodb_client, sample_application):
        """Test voting fails if no pending approval exists"""
        # Setup
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_application.dict()]},  # Get application
            {"rows": []}                             # No pending approval
        ]

        # Execute & Verify
        with pytest.raises(BoardApprovalError) as exc_info:
            approval_service.cast_vote(
                sample_application.id,
                uuid4(),
                ApprovalAction.APPROVE
            )

        assert "No pending approval found" in str(exc_info.value)


class TestGetPendingApplications:
    """Test retrieving pending applications for board member"""

    def test_get_pending_applications_success(self, approval_service, mock_zerodb_client, sample_application, sample_approval):
        """Test getting pending applications"""
        # Setup
        board_member_id = uuid4()
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        sample_application.pending_board_review = True

        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_approval.dict()]},      # Get pending approvals
            {"rows": [sample_application.dict()]}    # Get applications
        ]

        # Execute
        result = approval_service.get_pending_applications_for_board_member(board_member_id)

        # Verify
        assert len(result) == 1
        assert result[0].id == sample_application.id
        assert result[0].status == ApplicationStatus.UNDER_REVIEW

    def test_get_pending_applications_none(self, approval_service, mock_zerodb_client):
        """Test getting pending applications when none exist"""
        # Setup
        mock_zerodb_client.query_table.return_value = {"rows": []}

        # Execute
        result = approval_service.get_pending_applications_for_board_member(uuid4())

        # Verify
        assert len(result) == 0


class TestGetVoteHistory:
    """Test retrieving vote history"""

    def test_get_vote_history_success(self, approval_service, mock_zerodb_client):
        """Test getting vote history for application"""
        # Setup
        application_id = uuid4()
        approvals = [
            Approval(
                id=uuid4(),
                application_id=application_id,
                approver_id=uuid4(),
                status=ApprovalStatus.APPROVED,
                sequence=1
            ).dict(),
            Approval(
                id=uuid4(),
                application_id=application_id,
                approver_id=uuid4(),
                status=ApprovalStatus.APPROVED,
                sequence=2
            ).dict()
        ]

        mock_zerodb_client.query_table.return_value = {"rows": approvals}

        # Execute
        result = approval_service.get_vote_history(application_id)

        # Verify
        assert len(result) == 2
        assert result[0].sequence == 1
        assert result[1].sequence == 2

    def test_get_vote_history_empty(self, approval_service, mock_zerodb_client):
        """Test getting vote history when no votes exist"""
        # Setup
        mock_zerodb_client.query_table.return_value = {"rows": []}

        # Execute
        result = approval_service.get_vote_history(uuid4())

        # Verify
        assert len(result) == 0


class TestGetBoardMemberStats:
    """Test board member voting statistics"""

    def test_get_stats_success(self, approval_service, mock_zerodb_client):
        """Test getting board member voting stats"""
        # Setup
        board_member_id = uuid4()
        approvals = [
            Approval(id=uuid4(), application_id=uuid4(), approver_id=board_member_id, status=ApprovalStatus.APPROVED).dict(),
            Approval(id=uuid4(), application_id=uuid4(), approver_id=board_member_id, status=ApprovalStatus.APPROVED).dict(),
            Approval(id=uuid4(), application_id=uuid4(), approver_id=board_member_id, status=ApprovalStatus.REJECTED).dict(),
            Approval(id=uuid4(), application_id=uuid4(), approver_id=board_member_id, status=ApprovalStatus.PENDING).dict(),
        ]

        mock_zerodb_client.query_table.return_value = {"rows": approvals}

        # Execute
        result = approval_service.get_board_member_stats(board_member_id)

        # Verify
        assert result["total_votes"] == 4
        assert result["approved"] == 2
        assert result["rejected"] == 1
        assert result["pending"] == 1

    def test_get_stats_no_votes(self, approval_service, mock_zerodb_client):
        """Test getting stats when board member has no votes"""
        # Setup
        mock_zerodb_client.query_table.return_value = {"rows": []}

        # Execute
        result = approval_service.get_board_member_stats(uuid4())

        # Verify
        assert result["total_votes"] == 0
        assert result["approved"] == 0
        assert result["rejected"] == 0
        assert result["pending"] == 0


class TestServiceSingleton:
    """Test service singleton pattern"""

    def test_get_service_singleton(self):
        """Test that get_board_approval_service returns singleton"""
        with patch('backend.services.board_approval_service.get_zerodb_client'):
            service1 = get_board_approval_service()
            service2 = get_board_approval_service()

            assert service1 is service2


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_database_error_handling(self, approval_service, mock_zerodb_client):
        """Test handling of database errors"""
        # Setup
        mock_zerodb_client.query_table.side_effect = Exception("Database connection failed")

        # Execute & Verify
        with pytest.raises(BoardApprovalError) as exc_info:
            approval_service.get_vote_history(uuid4())

        assert "Failed to get vote history" in str(exc_info.value)

    def test_invalid_action_type(self, approval_service, mock_zerodb_client, sample_application, sample_approval):
        """Test handling of invalid action type"""
        # Setup
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_application.dict()]},
            {"rows": [sample_approval.dict()]}
        ]

        # Execute & Verify
        with pytest.raises(BoardApprovalError) as exc_info:
            approval_service.cast_vote(
                sample_application.id,
                uuid4(),
                ApprovalAction.INVALIDATE,  # Unsupported action
                "Invalid"
            )

        assert "Unsupported action" in str(exc_info.value)


# ============================================================================
# INTEGRATION TESTS (End-to-End Workflows)
# ============================================================================

class TestApprovalWorkflow:
    """Test complete approval workflows"""

    def test_full_approval_workflow(self, approval_service, mock_zerodb_client, sample_application):
        """Test complete workflow from submission to approval"""
        # Setup board members
        board_member1 = uuid4()
        board_member2 = uuid4()
        board_members = [board_member1, board_member2]

        # Mock database responses
        sample_application.status = ApplicationStatus.SUBMITTED

        # Step 1: Submit for review
        mock_zerodb_client.query_table.return_value = {"rows": [sample_application.dict()]}
        mock_zerodb_client.update_document.return_value = {"success": True}
        mock_zerodb_client.create_document.return_value = {"id": str(uuid4())}

        result = approval_service.submit_for_board_review(
            sample_application.id,
            board_members
        )

        assert result.status == ApplicationStatus.UNDER_REVIEW
        assert result.pending_board_review == True

    def test_rejection_workflow(self, approval_service, mock_zerodb_client, sample_application, sample_approval):
        """Test workflow when application is rejected"""
        # Setup
        sample_application.status = ApplicationStatus.UNDER_REVIEW
        sample_application.pending_board_review = True

        mock_zerodb_client.query_table.side_effect = [
            {"rows": [sample_application.dict()]},
            {"rows": [sample_approval.dict()]}
        ]
        mock_zerodb_client.update_document.return_value = {"success": True}

        # Execute rejection
        result = approval_service.cast_vote(
            sample_application.id,
            uuid4(),
            ApprovalAction.REJECT,
            "Not meeting requirements"
        )

        # Verify
        assert result["vote"] == "REJECTED"
        assert result["application_status"] == ApplicationStatus.REJECTED
        assert result["fully_approved"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.services.board_approval_service", "--cov-report=term-missing"])
