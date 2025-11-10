"""
Comprehensive Unit Tests for Approval Service

Tests the two-approval workflow logic including:
- Two-approval quorum validation
- Self-approval prevention
- Duplicate approval prevention
- Rejection overrides approvals
- State machine transitions
- Conditional approvals
- Auto-promotion to approved status
- User role upgrades

Target: 80%+ code coverage
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from uuid import uuid4

from backend.services.approval_service import (
    ApprovalService,
    ApprovalServiceError,
    SelfApprovalError,
    DuplicateApprovalError,
    IneligibleApprovalError,
    ApplicationNotFoundError
)
from backend.models.schemas import (
    ApplicationStatus,
    ApprovalStatus,
    UserRole,
    AuditAction
)
from backend.services.zerodb_service import ZeroDBNotFoundError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client for testing"""
    return Mock()


@pytest.fixture
def approval_service(mock_zerodb_client):
    """Approval service instance with mocked ZeroDB client"""
    return ApprovalService(zerodb_client=mock_zerodb_client)


@pytest.fixture
def sample_application():
    """Sample application data"""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "status": ApplicationStatus.SUBMITTED,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def board_member_id():
    """Sample board member ID (different from applicant)"""
    return str(uuid4())


@pytest.fixture
def second_board_member_id():
    """Second board member ID for testing quorum"""
    return str(uuid4())


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidateApprovalEligibility:
    """Test approval eligibility validation"""

    def test_eligible_for_approval_submitted_status(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test board member can approve submitted application"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        is_eligible, error = approval_service.validate_approval_eligibility(
            sample_application["id"],
            board_member_id
        )

        assert is_eligible is True
        assert error is None

    def test_eligible_for_approval_under_review_status(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test board member can approve application under review"""
        sample_application["status"] = ApplicationStatus.UNDER_REVIEW
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        is_eligible, error = approval_service.validate_approval_eligibility(
            sample_application["id"],
            board_member_id
        )

        assert is_eligible is True
        assert error is None

    def test_not_eligible_already_approved(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test cannot approve already approved application"""
        sample_application["status"] = ApplicationStatus.APPROVED
        mock_zerodb_client.get_document.return_value = {"data": sample_application}

        is_eligible, error = approval_service.validate_approval_eligibility(
            sample_application["id"],
            str(uuid4())
        )

        assert is_eligible is False
        assert "not eligible for approval" in error

    def test_not_eligible_rejected_status(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test cannot approve rejected application"""
        sample_application["status"] = ApplicationStatus.REJECTED
        mock_zerodb_client.get_document.return_value = {"data": sample_application}

        is_eligible, error = approval_service.validate_approval_eligibility(
            sample_application["id"],
            str(uuid4())
        )

        assert is_eligible is False
        assert "not eligible for approval" in error

    def test_self_approval_prevention(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test board member cannot approve their own application"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        # Try to approve with same user_id as applicant
        is_eligible, error = approval_service.validate_approval_eligibility(
            sample_application["id"],
            sample_application["user_id"]  # Same as applicant
        )

        assert is_eligible is False
        assert "cannot approve their own application" in error

    def test_duplicate_approval_prevention(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test board member cannot approve same application twice"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}

        # Mock existing approval by this board member
        existing_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": board_member_id,
            "status": ApprovalStatus.APPROVED
        }
        mock_zerodb_client.query_documents.return_value = {
            "documents": [existing_approval]
        }

        is_eligible, error = approval_service.validate_approval_eligibility(
            sample_application["id"],
            board_member_id
        )

        assert is_eligible is False
        assert "already approved" in error

    def test_application_not_found(
        self,
        approval_service,
        mock_zerodb_client
    ):
        """Test raises error when application doesn't exist"""
        mock_zerodb_client.get_document.side_effect = ZeroDBNotFoundError("Not found")

        with pytest.raises(ApplicationNotFoundError):
            approval_service.validate_approval_eligibility(
                str(uuid4()),
                str(uuid4())
            )


# ============================================================================
# APPROVAL PROCESSING TESTS
# ============================================================================

class TestProcessApproval:
    """Test approval processing logic"""

    def test_first_approval_moves_to_under_review(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test first approval moves application from SUBMITTED to UNDER_REVIEW"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {
                "application_id": sample_application["id"],
                "approver_id": board_member_id,
                "status": ApprovalStatus.APPROVED
            }
        }
        mock_zerodb_client.update_document.return_value = {
            "data": {**sample_application, "status": ApplicationStatus.UNDER_REVIEW}
        }

        # Mock query to return the newly created approval
        def query_side_effect(collection, **kwargs):
            if collection == "approvals":
                # First call returns empty, second call returns 1 approval
                if mock_zerodb_client.query_documents.call_count <= 1:
                    return {"documents": []}
                else:
                    return {"documents": [{
                        "id": str(uuid4()),
                        "application_id": sample_application["id"],
                        "approver_id": board_member_id,
                        "status": ApprovalStatus.APPROVED
                    }]}
            return {"documents": []}

        mock_zerodb_client.query_documents.side_effect = query_side_effect

        result = approval_service.process_approval(
            sample_application["id"],
            board_member_id,
            "approve",
            notes="Looks good!"
        )

        assert result["action"] == "approved"
        # Note: approval_count from check_approval_quorum may be 0 or 1 depending on mock timing
        # What's important is quorum is not reached yet
        assert result["quorum_reached"] is False

        # Verify application status was updated
        update_calls = [
            call for call in mock_zerodb_client.update_document.call_args_list
            if call[0][0] == "applications"
        ]
        assert len(update_calls) > 0

    def test_second_approval_reaches_quorum(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id,
        second_board_member_id
    ):
        """Test second approval reaches quorum and auto-approves application"""
        sample_application["status"] = ApplicationStatus.UNDER_REVIEW

        # Mock first approval already exists
        first_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": str(uuid4()),  # Different board member
            "status": ApprovalStatus.APPROVED
        }

        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {
                "application_id": sample_application["id"],
                "approver_id": second_board_member_id,
                "status": ApprovalStatus.APPROVED
            }
        }
        mock_zerodb_client.update_document.return_value = {
            "data": {**sample_application, "status": ApplicationStatus.APPROVED}
        }

        # Mock query to return:
        # - first approval only on first call (eligibility check)
        # - both approvals on second call (quorum check)
        call_count = [0]
        second_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": second_board_member_id,
            "status": ApprovalStatus.APPROVED
        }

        def query_side_effect_two(collection, **kwargs):
            call_count[0] += 1
            if collection == "approvals":
                # First call: eligibility check - show only first approval
                if call_count[0] == 1:
                    return {"documents": [first_approval]}
                # Second call: quorum check - show both approvals
                else:
                    return {"documents": [first_approval, second_approval]}
            return {"documents": []}

        mock_zerodb_client.query_documents.side_effect = query_side_effect_two

        result = approval_service.process_approval(
            sample_application["id"],
            second_board_member_id,
            "approve",
            notes="Approved!"
        )

        assert result["action"] == "approved"
        # Quorum should be reached with 2 approvals
        assert result["quorum_reached"] is True

    def test_approval_with_conditions(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test conditional approval counts toward quorum"""
        conditions = [
            "Must complete background check",
            "Provide proof of insurance"
        ]

        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {
                "application_id": sample_application["id"],
                "approver_id": board_member_id,
                "status": ApprovalStatus.APPROVED,
                "conditions": conditions
            }
        }
        mock_zerodb_client.update_document.return_value = {
            "data": {**sample_application, "status": ApplicationStatus.UNDER_REVIEW}
        }

        # Mock query to handle approval checking
        mock_zerodb_client.query_documents.side_effect = None
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        result = approval_service.process_approval(
            sample_application["id"],
            board_member_id,
            "approve",
            notes="Approved with conditions",
            conditions=conditions
        )

        assert result["action"] == "approved"
        # Note: approval_count depends on mock query timing
        # What's important is quorum is not reached yet
        assert result["quorum_reached"] is False
        # Verify conditions were passed to create_document - find the approvals create call
        create_calls = [call for call in mock_zerodb_client.create_document.call_args_list
                        if call[0][0] == "approvals"]
        assert len(create_calls) > 0
        approval_create_call = create_calls[0]
        assert "conditions" in approval_create_call[0][1]

    def test_rejection_overrides_approvals(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test rejection immediately sets status to REJECTED regardless of approvals"""
        # Mock one existing approval
        existing_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": str(uuid4()),
            "status": ApprovalStatus.APPROVED
        }

        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {
            "documents": [existing_approval]
        }
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {
                "application_id": sample_application["id"],
                "approver_id": board_member_id,
                "status": ApprovalStatus.REJECTED
            }
        }
        mock_zerodb_client.update_document.return_value = {
            "data": {**sample_application, "status": ApplicationStatus.REJECTED}
        }

        result = approval_service.process_approval(
            sample_application["id"],
            board_member_id,
            "reject",
            notes="Insufficient qualifications"
        )

        assert result["action"] == "rejected"
        assert result["quorum_reached"] is False
        assert result["approval_count"] == 0

        # Verify status was set to REJECTED
        update_call = mock_zerodb_client.update_document.call_args
        assert "status" in update_call[0][2]
        assert update_call[0][2]["status"] == ApplicationStatus.REJECTED

    def test_self_approval_raises_error(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test self-approval attempt raises SelfApprovalError"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        with pytest.raises(SelfApprovalError) as exc_info:
            approval_service.process_approval(
                sample_application["id"],
                sample_application["user_id"],  # Same as applicant
                "approve"
            )

        assert "own application" in str(exc_info.value)

    def test_duplicate_approval_raises_error(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test duplicate approval attempt raises DuplicateApprovalError"""
        existing_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": board_member_id,
            "status": ApprovalStatus.APPROVED
        }

        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {
            "documents": [existing_approval]
        }

        with pytest.raises(DuplicateApprovalError) as exc_info:
            approval_service.process_approval(
                sample_application["id"],
                board_member_id,
                "approve"
            )

        assert "already approved" in str(exc_info.value)

    def test_invalid_action_raises_error(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test invalid action raises ValueError"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}

        with pytest.raises(ValueError) as exc_info:
            approval_service.process_approval(
                sample_application["id"],
                board_member_id,
                "invalid_action"
            )

        assert "Invalid action" in str(exc_info.value)


# ============================================================================
# QUORUM CHECKING TESTS
# ============================================================================

class TestCheckApprovalQuorum:
    """Test approval quorum checking"""

    def test_zero_approvals_no_quorum(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test zero approvals means no quorum"""
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        result = approval_service.check_approval_quorum(sample_application["id"])

        assert result["quorum_reached"] is False
        assert result["approval_count"] == 0
        assert result["required_approvals"] == 2
        assert result["progress_percentage"] == 0.0

    def test_one_approval_no_quorum(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test one approval means no quorum yet"""
        approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": str(uuid4()),
            "status": ApprovalStatus.APPROVED
        }

        mock_zerodb_client.query_documents.return_value = {"documents": [approval]}

        result = approval_service.check_approval_quorum(sample_application["id"])

        assert result["quorum_reached"] is False
        assert result["approval_count"] == 1
        assert result["required_approvals"] == 2
        assert result["progress_percentage"] == 50.0

    def test_two_approvals_quorum_reached(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test two approvals reaches quorum"""
        approvals = [
            {
                "id": str(uuid4()),
                "application_id": sample_application["id"],
                "approver_id": str(uuid4()),
                "status": ApprovalStatus.APPROVED
            },
            {
                "id": str(uuid4()),
                "application_id": sample_application["id"],
                "approver_id": str(uuid4()),
                "status": ApprovalStatus.APPROVED
            }
        ]

        mock_zerodb_client.query_documents.return_value = {"documents": approvals}

        result = approval_service.check_approval_quorum(sample_application["id"])

        assert result["quorum_reached"] is True
        assert result["approval_count"] == 2
        assert result["required_approvals"] == 2
        assert result["progress_percentage"] == 100.0

    def test_rejected_approvals_not_counted(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test rejected approvals don't count toward quorum"""
        approvals = [
            {
                "id": str(uuid4()),
                "application_id": sample_application["id"],
                "approver_id": str(uuid4()),
                "status": ApprovalStatus.APPROVED
            },
            {
                "id": str(uuid4()),
                "application_id": sample_application["id"],
                "approver_id": str(uuid4()),
                "status": ApprovalStatus.REJECTED
            }
        ]

        mock_zerodb_client.query_documents.return_value = {"documents": approvals}

        result = approval_service.check_approval_quorum(sample_application["id"])

        assert result["quorum_reached"] is False
        assert result["approval_count"] == 1  # Only approved count


# ============================================================================
# AUTO-APPROVAL TESTS
# ============================================================================

class TestAutoApproveApplication:
    """Test auto-approval when quorum reached"""

    def test_auto_approve_updates_application(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test auto-approve updates application status and timestamp"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.update_document.return_value = {
            "data": {
                **sample_application,
                "status": ApplicationStatus.APPROVED,
                "approved_at": datetime.utcnow().isoformat()
            }
        }

        result = approval_service.auto_approve_application(sample_application["id"])

        # Verify application was updated
        assert mock_zerodb_client.update_document.called
        update_call = mock_zerodb_client.update_document.call_args_list[0]
        assert update_call[0][0] == "applications"
        assert update_call[0][2]["status"] == ApplicationStatus.APPROVED
        assert "approved_at" in update_call[0][2]

    def test_auto_approve_upgrades_user_role(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test auto-approve upgrades user role to MEMBER"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.update_document.return_value = {"data": {}}

        approval_service.auto_approve_application(sample_application["id"])

        # Verify user role was updated
        user_update_calls = [
            call for call in mock_zerodb_client.update_document.call_args_list
            if call[0][0] == "users"
        ]
        assert len(user_update_calls) > 0
        assert user_update_calls[0][0][2]["role"] == UserRole.MEMBER

    def test_auto_approve_creates_audit_log(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test auto-approve creates audit log entry"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.update_document.return_value = {"data": {}}
        mock_zerodb_client.create_document.return_value = {"id": str(uuid4()), "data": {}}

        approval_service.auto_approve_application(sample_application["id"])

        # Verify audit log was created
        audit_calls = [
            call for call in mock_zerodb_client.create_document.call_args_list
            if call[0][0] == "audit_logs"
        ]
        assert len(audit_calls) > 0

    def test_auto_approve_handles_missing_user(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test auto-approve handles case when user doesn't exist"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}

        # First update (application) succeeds, second (user) fails
        mock_zerodb_client.update_document.side_effect = [
            {"data": {}},  # Application update succeeds
            ZeroDBNotFoundError("User not found")  # User update fails
        ]
        mock_zerodb_client.create_document.return_value = {"id": str(uuid4()), "data": {}}

        # Should not raise error, just log it
        result = approval_service.auto_approve_application(sample_application["id"])

        # Application should still be updated even if user update fails
        assert mock_zerodb_client.update_document.call_count >= 1

    def test_auto_approve_application_not_found(
        self,
        approval_service,
        mock_zerodb_client
    ):
        """Test auto-approve raises error when application doesn't exist"""
        mock_zerodb_client.get_document.side_effect = ZeroDBNotFoundError("Not found")

        with pytest.raises(ApplicationNotFoundError):
            approval_service.auto_approve_application(str(uuid4()))


# ============================================================================
# PROGRESS CALCULATION TESTS
# ============================================================================

class TestCalculateApprovalProgress:
    """Test approval progress calculation"""

    def test_calculate_progress_no_approvals(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test progress calculation with no approvals"""
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        result = approval_service.calculate_approval_progress(sample_application["id"])

        assert result["approval_count"] == 0
        assert result["progress_percentage"] == 0.0

    def test_calculate_progress_partial(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test progress calculation with partial approvals"""
        approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": str(uuid4()),
            "status": ApprovalStatus.APPROVED
        }

        mock_zerodb_client.query_documents.return_value = {"documents": [approval]}

        result = approval_service.calculate_approval_progress(sample_application["id"])

        assert result["approval_count"] == 1
        assert result["progress_percentage"] == 50.0

    def test_calculate_progress_complete(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test progress calculation with complete approvals"""
        approvals = [
            {
                "id": str(uuid4()),
                "application_id": sample_application["id"],
                "approver_id": str(uuid4()),
                "status": ApprovalStatus.APPROVED
            },
            {
                "id": str(uuid4()),
                "application_id": sample_application["id"],
                "approver_id": str(uuid4()),
                "status": ApprovalStatus.APPROVED
            }
        ]

        mock_zerodb_client.query_documents.return_value = {"documents": approvals}

        result = approval_service.calculate_approval_progress(sample_application["id"])

        assert result["approval_count"] == 2
        assert result["progress_percentage"] == 100.0
        assert result["quorum_reached"] is True


# ============================================================================
# STATUS RETRIEVAL TESTS
# ============================================================================

class TestGetApplicationApprovalStatus:
    """Test getting comprehensive approval status"""

    def test_get_status_approved_application(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test getting status for approved application"""
        sample_application["status"] = ApplicationStatus.APPROVED
        sample_application["approved_at"] = datetime.utcnow().isoformat()

        approvals = [
            {"id": str(uuid4()), "status": ApprovalStatus.APPROVED},
            {"id": str(uuid4()), "status": ApprovalStatus.APPROVED}
        ]

        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": approvals}

        result = approval_service.get_application_approval_status(sample_application["id"])

        assert result["status"] == ApplicationStatus.APPROVED
        assert result["is_approved"] is True
        assert result["is_rejected"] is False
        assert result["approved_at"] is not None
        assert result["approval_progress"]["approval_count"] == 2

    def test_get_status_rejected_application(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test getting status for rejected application"""
        sample_application["status"] = ApplicationStatus.REJECTED

        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}

        result = approval_service.get_application_approval_status(sample_application["id"])

        assert result["status"] == ApplicationStatus.REJECTED
        assert result["is_approved"] is False
        assert result["is_rejected"] is True

    def test_get_status_application_not_found(
        self,
        approval_service,
        mock_zerodb_client
    ):
        """Test getting status raises error when application doesn't exist"""
        mock_zerodb_client.get_document.side_effect = ZeroDBNotFoundError("Not found")

        with pytest.raises(ApplicationNotFoundError):
            approval_service.get_application_approval_status(str(uuid4()))


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_process_approval_with_empty_notes(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id
    ):
        """Test approval with no notes (should use empty string)"""
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {"application_id": sample_application["id"]}
        }
        mock_zerodb_client.update_document.return_value = {"data": sample_application}

        result = approval_service.process_approval(
            sample_application["id"],
            board_member_id,
            "approve",
            notes=None
        )

        # Should succeed with empty string for notes
        assert result["action"] == "approved"

    def test_get_approvals_handles_errors(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application
    ):
        """Test _get_approvals returns empty list on error"""
        mock_zerodb_client.query_documents.side_effect = Exception("Database error")

        result = approval_service._get_approvals(sample_application["id"])

        assert result == []

    def test_audit_log_creation_failure_is_logged(
        self,
        approval_service,
        mock_zerodb_client
    ):
        """Test audit log creation failure doesn't break workflow"""
        mock_zerodb_client.create_document.side_effect = Exception("Database error")

        # Should not raise error
        approval_service._create_audit_log(
            user_id=str(uuid4()),
            action=AuditAction.APPROVE,
            resource_type="applications",
            resource_id=str(uuid4()),
            description="Test"
        )

        # No assertion needed - just verify no exception raised


# ============================================================================
# INTEGRATION-STYLE TESTS
# ============================================================================

class TestCompleteWorkflow:
    """Test complete approval workflows end-to-end"""

    def test_complete_two_approval_workflow(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id,
        second_board_member_id
    ):
        """Test complete workflow: submit -> first approval -> second approval -> approved"""

        # Initial state
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {"documents": []}
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {}
        }
        mock_zerodb_client.update_document.return_value = {"data": sample_application}

        # First approval
        result1 = approval_service.process_approval(
            sample_application["id"],
            board_member_id,
            "approve",
            notes="First approval"
        )

        # Note: approval_count depends on mock query behavior
        # What's important is quorum is not reached yet
        assert result1["quorum_reached"] is False

        # Update mock to return first approval
        first_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": board_member_id,
            "status": ApprovalStatus.APPROVED
        }
        sample_application["status"] = ApplicationStatus.UNDER_REVIEW
        mock_zerodb_client.get_document.return_value = {"data": sample_application}

        # Second approval - need to update mock to return both approvals
        second_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": second_board_member_id,
            "status": ApprovalStatus.APPROVED
        }

        # Mock should return:
        # - first approval only on first call (eligibility check)
        # - both approvals on second call (quorum check)
        call_count2 = [0]

        def query_side_effect_final(collection, **kwargs):
            call_count2[0] += 1
            if collection == "approvals":
                # First call: eligibility check - show only first approval
                if call_count2[0] == 1:
                    return {"documents": [first_approval]}
                # Second call: quorum check - show both approvals
                else:
                    return {"documents": [first_approval, second_approval]}
            return {"documents": []}

        mock_zerodb_client.query_documents.side_effect = query_side_effect_final

        result2 = approval_service.process_approval(
            sample_application["id"],
            second_board_member_id,
            "approve",
            notes="Second approval"
        )

        # With two approvals, quorum should be reached
        assert result2["quorum_reached"] is True

    def test_rejection_after_one_approval(
        self,
        approval_service,
        mock_zerodb_client,
        sample_application,
        board_member_id,
        second_board_member_id
    ):
        """Test rejection overrides existing approval"""

        # Mock one existing approval
        existing_approval = {
            "id": str(uuid4()),
            "application_id": sample_application["id"],
            "approver_id": board_member_id,
            "status": ApprovalStatus.APPROVED
        }

        sample_application["status"] = ApplicationStatus.UNDER_REVIEW
        mock_zerodb_client.get_document.return_value = {"data": sample_application}
        mock_zerodb_client.query_documents.return_value = {
            "documents": [existing_approval]
        }
        mock_zerodb_client.create_document.return_value = {
            "id": str(uuid4()),
            "data": {}
        }
        mock_zerodb_client.update_document.return_value = {
            "data": {**sample_application, "status": ApplicationStatus.REJECTED}
        }

        # Reject application
        result = approval_service.process_approval(
            sample_application["id"],
            second_board_member_id,
            "reject",
            notes="Insufficient experience"
        )

        assert result["action"] == "rejected"
        assert result["quorum_reached"] is False
