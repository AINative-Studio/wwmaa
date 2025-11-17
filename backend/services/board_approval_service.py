"""
Board Approval Service for WWMAA Backend

Implements two-board approval workflow for membership applications.
Requires 2 board member approvals before application is fully approved.

Features:
- Submit application for board review
- Cast votes (approve/reject)
- Track approval counts and sequences
- Handle concurrent voting
- Automatic status updates
- Complete audit trail

Business Rules:
- 2 approvals required for application approval
- 1 rejection immediately rejects application
- Board members can only vote once per application
- No vote changes after casting
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from backend.models.schemas import (
    Application,
    Approval,
    ApplicationStatus,
    ApprovalStatus,
    ApprovalAction
)
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError

# Configure logging
logger = logging.getLogger(__name__)


class BoardApprovalError(Exception):
    """Base exception for board approval operations"""
    pass


class AlreadyVotedError(BoardApprovalError):
    """Board member has already voted on this application"""
    pass


class InvalidStatusError(BoardApprovalError):
    """Application is not in a valid status for this operation"""
    pass


class BoardApprovalService:
    """
    Service for managing board approval workflow.

    Handles the complete lifecycle of application approvals from
    submission to final decision.
    """

    def __init__(self):
        """Initialize board approval service"""
        self.db_client = get_zerodb_client()
        logger.info("BoardApprovalService initialized")

    def submit_for_board_review(
        self,
        application_id: UUID,
        board_member_ids: List[UUID]
    ) -> Application:
        """
        Submit application for board member review.

        Creates pending approval records for all board members and
        updates application status to UNDER_REVIEW.

        Args:
            application_id: ID of application to submit
            board_member_ids: List of board member IDs who will review

        Returns:
            Updated application

        Raises:
            BoardApprovalError: If submission fails
            InvalidStatusError: If application not in SUBMITTED status
        """
        try:
            # Get application
            application = self._get_application(application_id)

            # Validate status
            if application.status != ApplicationStatus.SUBMITTED:
                raise InvalidStatusError(
                    f"Application must be SUBMITTED to start board review. "
                    f"Current status: {application.status}"
                )

            # Update application status
            application.status = ApplicationStatus.UNDER_REVIEW
            application.pending_board_review = True
            application.board_review_started_at = datetime.utcnow()

            # Save application
            self._save_application(application)

            # Create pending approvals for all board members
            for board_member_id in board_member_ids:
                approval = Approval(
                    application_id=application_id,
                    approver_id=board_member_id,
                    status=ApprovalStatus.PENDING,
                    is_active=True
                )
                self._save_approval(approval)

            logger.info(
                f"Application {application_id} submitted for board review. "
                f"Created {len(board_member_ids)} pending approvals."
            )

            return application

        except InvalidStatusError:
            raise
        except Exception as e:
            logger.error(f"Failed to submit application for review: {e}")
            raise BoardApprovalError(f"Failed to submit for review: {e}")

    def cast_vote(
        self,
        application_id: UUID,
        board_member_id: UUID,
        action: ApprovalAction,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cast a vote (approve/reject) on an application.

        Implements the core voting logic including duplicate checking,
        approval counting, and status updates.

        Args:
            application_id: ID of application to vote on
            board_member_id: ID of board member casting vote
            action: APPROVE or REJECT
            notes: Optional notes/comments

        Returns:
            Dictionary with vote results:
            {
                "application_id": UUID,
                "vote": str,
                "approval_count": int,
                "required_approvals": int,
                "application_status": str,
                "fully_approved": bool
            }

        Raises:
            AlreadyVotedError: If board member already voted
            InvalidStatusError: If application not in reviewable state
            BoardApprovalError: If vote fails
        """
        try:
            # Get application
            application = self._get_application(application_id)

            # Validate application status
            if application.status != ApplicationStatus.UNDER_REVIEW:
                raise InvalidStatusError(
                    f"Application must be UNDER_REVIEW to vote. "
                    f"Current status: {application.status}"
                )

            # Check if already voted
            if board_member_id in application.board_votes:
                raise AlreadyVotedError(
                    f"Board member {board_member_id} has already voted on "
                    f"application {application_id}"
                )

            # Get pending approval
            approval = self._get_pending_approval(application_id, board_member_id)

            # Process vote based on action
            if action == ApprovalAction.APPROVE:
                result = self._process_approval(application, approval, board_member_id, notes)
            elif action == ApprovalAction.REJECT:
                result = self._process_rejection(application, approval, board_member_id, notes)
            else:
                raise BoardApprovalError(f"Unsupported action: {action}")

            logger.info(
                f"Vote cast successfully: {action} by {board_member_id} "
                f"on application {application_id}"
            )

            return result

        except (AlreadyVotedError, InvalidStatusError) as e:
            logger.warning(f"Vote validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to cast vote: {e}")
            raise BoardApprovalError(f"Failed to cast vote: {e}")

    def _process_approval(
        self,
        application: Application,
        approval: Approval,
        board_member_id: UUID,
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process an approval vote.

        Updates application and approval records, checks if fully approved.

        Args:
            application: Application being voted on
            approval: Approval record
            board_member_id: ID of board member
            notes: Vote notes

        Returns:
            Vote result dictionary
        """
        # Update approval record
        approval.status = ApprovalStatus.APPROVED
        approval.action = ApprovalAction.APPROVE
        approval.approved_at = datetime.utcnow()
        approval.vote_cast_at = datetime.utcnow()
        approval.sequence = application.approval_count + 1
        approval.notes = notes

        # Update application
        application.approval_count += 1
        application.approver_ids.append(board_member_id)
        application.board_votes.append(board_member_id)

        # Track first approval
        if application.approval_count == 1:
            application.first_approval_at = datetime.utcnow()

        # Check if fully approved
        fully_approved = application.approval_count >= application.required_approvals

        if fully_approved:
            application.status = ApplicationStatus.APPROVED
            application.fully_approved_at = datetime.utcnow()
            application.pending_board_review = False
            application.reviewed_at = datetime.utcnow()
            application.reviewed_by = board_member_id

        # Save both records
        self._save_approval(approval)
        self._save_application(application)

        return {
            "application_id": str(application.id),
            "vote": "APPROVED",
            "approval_count": application.approval_count,
            "required_approvals": application.required_approvals,
            "application_status": application.status,
            "fully_approved": fully_approved
        }

    def _process_rejection(
        self,
        application: Application,
        approval: Approval,
        board_member_id: UUID,
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process a rejection vote.

        Updates application and approval records. Single rejection rejects application.

        Args:
            application: Application being voted on
            approval: Approval record
            board_member_id: ID of board member
            notes: Vote notes

        Returns:
            Vote result dictionary
        """
        # Update approval record
        approval.status = ApprovalStatus.REJECTED
        approval.action = ApprovalAction.REJECT
        approval.rejected_at = datetime.utcnow()
        approval.vote_cast_at = datetime.utcnow()
        approval.sequence = len(application.board_votes) + 1
        approval.notes = notes

        # Update application - single rejection = rejected
        application.rejection_count += 1
        application.rejector_ids.append(board_member_id)
        application.board_votes.append(board_member_id)
        application.status = ApplicationStatus.REJECTED
        application.pending_board_review = False
        application.rejected_at = datetime.utcnow()
        application.rejected_by = board_member_id
        application.rejection_reason = notes or "Rejected by board member"

        # Save both records
        self._save_approval(approval)
        self._save_application(application)

        return {
            "application_id": str(application.id),
            "vote": "REJECTED",
            "approval_count": application.approval_count,
            "required_approvals": application.required_approvals,
            "application_status": application.status,
            "fully_approved": False
        }

    def get_pending_applications_for_board_member(
        self,
        board_member_id: UUID
    ) -> List[Application]:
        """
        Get applications pending this board member's vote.

        Args:
            board_member_id: ID of board member

        Returns:
            List of applications awaiting vote
        """
        try:
            # Query approvals collection for pending approvals
            result = self.db_client.query_table(
                table_name="approvals",
                filter={
                    "approver_id": str(board_member_id),
                    "status": ApprovalStatus.PENDING,
                    "is_active": True
                }
            )

            approval_rows = result.get("rows", [])
            application_ids = [row["application_id"] for row in approval_rows]

            if not application_ids:
                return []

            # Get corresponding applications
            apps_result = self.db_client.query_table(
                table_name="applications",
                filter={
                    "id": {"$in": application_ids},
                    "status": ApplicationStatus.UNDER_REVIEW,
                    "pending_board_review": True
                }
            )

            applications = []
            for row in apps_result.get("rows", []):
                app = Application(**row)
                applications.append(app)

            logger.info(
                f"Found {len(applications)} pending applications for "
                f"board member {board_member_id}"
            )

            return applications

        except Exception as e:
            logger.error(f"Failed to get pending applications: {e}")
            raise BoardApprovalError(f"Failed to get pending applications: {e}")

    def get_vote_history(self, application_id: UUID) -> List[Approval]:
        """
        Get complete vote history for an application.

        Args:
            application_id: ID of application

        Returns:
            List of approvals ordered by sequence
        """
        try:
            result = self.db_client.query_table(
                table_name="approvals",
                filter={"application_id": str(application_id)},
                sort={"sequence": 1}  # Sort by sequence ascending
            )

            approvals = []
            for row in result.get("rows", []):
                approval = Approval(**row)
                approvals.append(approval)

            return approvals

        except Exception as e:
            logger.error(f"Failed to get vote history: {e}")
            raise BoardApprovalError(f"Failed to get vote history: {e}")

    def get_board_member_stats(self, board_member_id: UUID) -> Dict[str, int]:
        """
        Get voting statistics for a board member.

        Args:
            board_member_id: ID of board member

        Returns:
            Dictionary with voting stats
        """
        try:
            result = self.db_client.query_table(
                table_name="approvals",
                filter={"approver_id": str(board_member_id)}
            )

            approvals = [Approval(**row) for row in result.get("rows", [])]

            stats = {
                "total_votes": len(approvals),
                "approved": len([a for a in approvals if a.status == ApprovalStatus.APPROVED]),
                "rejected": len([a for a in approvals if a.status == ApprovalStatus.REJECTED]),
                "pending": len([a for a in approvals if a.status == ApprovalStatus.PENDING]),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get board member stats: {e}")
            raise BoardApprovalError(f"Failed to get stats: {e}")

    def _get_application(self, application_id: UUID) -> Application:
        """Get application from database"""
        result = self.db_client.query_table(
            table_name="applications",
            filter={"id": str(application_id)}
        )

        rows = result.get("rows", [])
        if not rows:
            raise BoardApprovalError(f"Application {application_id} not found")

        return Application(**rows[0])

    def _get_pending_approval(
        self,
        application_id: UUID,
        board_member_id: UUID
    ) -> Approval:
        """Get pending approval for board member"""
        result = self.db_client.query_table(
            table_name="approvals",
            filter={
                "application_id": str(application_id),
                "approver_id": str(board_member_id),
                "status": ApprovalStatus.PENDING
            }
        )

        rows = result.get("rows", [])
        if not rows:
            raise BoardApprovalError(
                f"No pending approval found for board member {board_member_id} "
                f"on application {application_id}"
            )

        return Approval(**rows[0])

    def _save_application(self, application: Application):
        """Save application to database"""
        self.db_client.update_document(
            table_name="applications",
            document_id=str(application.id),
            data=application.dict(exclude={"id"})
        )

    def _save_approval(self, approval: Approval):
        """Save approval to database"""
        if approval.id:
            # Update existing
            self.db_client.update_document(
                table_name="approvals",
                document_id=str(approval.id),
                data=approval.dict(exclude={"id"})
            )
        else:
            # Create new
            result = self.db_client.create_document(
                table_name="approvals",
                data=approval.dict(exclude={"id"})
            )
            approval.id = UUID(result["id"])


# Global service instance (singleton pattern)
_service_instance: Optional[BoardApprovalService] = None


def get_board_approval_service() -> BoardApprovalService:
    """
    Get or create the global BoardApprovalService instance.

    Returns:
        BoardApprovalService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = BoardApprovalService()

    return _service_instance
