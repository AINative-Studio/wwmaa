"""
Unit Tests - Approval Workflow Logic

Tests the two-approval quorum system and approval workflow business logic.

Test Coverage:
- Adding approvals to workflow
- Checking if quorum is met (2 approvals required)
- Preventing duplicate approvals
- Preventing self-approval
- Status transitions
- Edge cases and error handling
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List


# Mock classes - These will be replaced with actual implementation
class ApprovalWorkflow:
    """Mock ApprovalWorkflow class for demonstration"""

    def __init__(self, entity_id: str, entity_type: str, required_approvals: int = 2):
        self.id = f"approval_{entity_id}"
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.required_approvals = required_approvals
        self.approvals: List[Dict[str, Any]] = []
        self.status = "pending"
        self.created_at = datetime.utcnow()

    def add_approval(self, approver_id: str, approver_role: str) -> Dict[str, Any]:
        """Add an approval to the workflow"""
        # Prevent duplicate approvals
        if any(a["approver_id"] == approver_id for a in self.approvals):
            raise ValueError(f"User {approver_id} has already approved")

        approval = {
            "approver_id": approver_id,
            "approver_role": approver_role,
            "approved_at": datetime.utcnow().isoformat(),
        }

        self.approvals.append(approval)

        # Check if quorum is met
        if self.is_quorum_met():
            self.status = "approved"

        return approval

    def is_quorum_met(self) -> bool:
        """Check if the required number of approvals is met"""
        return len(self.approvals) >= self.required_approvals

    def reject(self, rejector_id: str, reason: str) -> None:
        """Reject the approval workflow"""
        self.status = "rejected"
        self.rejection_reason = reason
        self.rejected_by = rejector_id
        self.rejected_at = datetime.utcnow()

    def can_approve(self, user_id: str, entity_creator_id: str) -> bool:
        """Check if a user can approve (prevent self-approval)"""
        # Users cannot approve their own submissions
        if user_id == entity_creator_id:
            return False

        # Users cannot approve twice
        if any(a["approver_id"] == user_id for a in self.approvals):
            return False

        return True


# ============================================================================
# TEST CLASS: Approval Workflow Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.approval
class TestApprovalWorkflow:
    """Test suite for approval workflow logic"""

    def test_create_approval_workflow(self):
        """Test creating a new approval workflow"""
        # Arrange
        entity_id = "promo_123"
        entity_type = "promotion"

        # Act
        workflow = ApprovalWorkflow(entity_id, entity_type)

        # Assert
        assert workflow.entity_id == entity_id
        assert workflow.entity_type == entity_type
        assert workflow.status == "pending"
        assert workflow.required_approvals == 2
        assert len(workflow.approvals) == 0

    def test_add_single_approval(self):
        """Test adding a single approval to workflow"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion")
        approver_id = "admin_001"
        approver_role = "state_admin"

        # Act
        approval = workflow.add_approval(approver_id, approver_role)

        # Assert
        assert len(workflow.approvals) == 1
        assert approval["approver_id"] == approver_id
        assert approval["approver_role"] == approver_role
        assert "approved_at" in approval
        assert workflow.status == "pending"  # Still needs one more approval

    def test_quorum_met_with_two_approvals(self):
        """Test that quorum is met when 2 approvals are received"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion")

        # Act
        workflow.add_approval("admin_001", "state_admin")
        workflow.add_approval("admin_002", "national_admin")

        # Assert
        assert len(workflow.approvals) == 2
        assert workflow.is_quorum_met() is True
        assert workflow.status == "approved"

    def test_prevent_duplicate_approval(self):
        """Test that a user cannot approve the same item twice"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion")
        approver_id = "admin_001"

        # Act
        workflow.add_approval(approver_id, "state_admin")

        # Assert - should raise ValueError on duplicate
        with pytest.raises(ValueError, match="has already approved"):
            workflow.add_approval(approver_id, "state_admin")

    def test_prevent_self_approval(self):
        """Test that a user cannot approve their own submission"""
        # Arrange
        creator_id = "user_123"
        workflow = ApprovalWorkflow("promo_123", "promotion")

        # Act
        can_approve = workflow.can_approve(creator_id, creator_id)

        # Assert
        assert can_approve is False

    def test_different_user_can_approve(self):
        """Test that a different user can approve"""
        # Arrange
        creator_id = "user_123"
        approver_id = "admin_001"
        workflow = ApprovalWorkflow("promo_123", "promotion")

        # Act
        can_approve = workflow.can_approve(approver_id, creator_id)

        # Assert
        assert can_approve is True

    def test_reject_workflow(self):
        """Test rejecting an approval workflow"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion")
        rejector_id = "admin_001"
        reason = "Invalid promotion terms"

        # Act
        workflow.reject(rejector_id, reason)

        # Assert
        assert workflow.status == "rejected"
        assert workflow.rejection_reason == reason
        assert workflow.rejected_by == rejector_id
        assert hasattr(workflow, "rejected_at")

    def test_quorum_not_met_with_one_approval(self):
        """Test that quorum is not met with only one approval"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion")

        # Act
        workflow.add_approval("admin_001", "state_admin")

        # Assert
        assert len(workflow.approvals) == 1
        assert workflow.is_quorum_met() is False
        assert workflow.status == "pending"

    def test_custom_approval_threshold(self):
        """Test workflow with custom approval threshold"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion", required_approvals=3)

        # Act
        workflow.add_approval("admin_001", "state_admin")
        workflow.add_approval("admin_002", "national_admin")

        # Assert - should still be pending with only 2 approvals
        assert len(workflow.approvals) == 2
        assert workflow.is_quorum_met() is False
        assert workflow.status == "pending"

        # Act - add third approval
        workflow.add_approval("admin_003", "regional_admin")

        # Assert - now should be approved
        assert len(workflow.approvals) == 3
        assert workflow.is_quorum_met() is True
        assert workflow.status == "approved"

    @pytest.mark.parametrize("num_approvals,expected_status", [
        (0, "pending"),
        (1, "pending"),
        (2, "approved"),
        (3, "approved"),
    ])
    def test_approval_status_transitions(self, num_approvals, expected_status):
        """Test status transitions based on number of approvals"""
        # Arrange
        workflow = ApprovalWorkflow("promo_123", "promotion")

        # Act
        for i in range(num_approvals):
            workflow.add_approval(f"admin_{i:03d}", "admin")

        # Assert
        assert workflow.status == expected_status
