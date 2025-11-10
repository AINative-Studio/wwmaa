"""
Approval Workflow Service - Two-Approval Quorum Logic

This service implements the two-approval workflow for membership applications:
- Requires exactly 2 approvals from different board members
- Prevents self-approval and duplicate approvals
- Implements state machine transitions
- Supports conditional approvals
- Tracks audit logs for all approval actions
- Auto-promotes applications to 'approved' status after 2 approvals
- Auto-upgrades user roles to 'Member' upon approval

Business Rules:
1. Board member cannot approve their own application
2. Board member cannot approve the same application twice
3. Any rejection immediately moves application to 'rejected' status
4. Two approvals automatically move application to 'approved' status
5. Conditional approvals count toward the 2-approval quorum
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4

from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError, ZeroDBValidationError
from backend.services.email_service import get_email_service
from backend.models.schemas import (
    ApplicationStatus,
    ApprovalStatus,
    ApprovalAction,
    UserRole,
    AuditAction
)

logger = logging.getLogger(__name__)


class ApprovalServiceError(Exception):
    """Base exception for approval service errors"""
    pass


class SelfApprovalError(ApprovalServiceError):
    """Exception raised when a board member tries to approve their own application"""
    pass


class DuplicateApprovalError(ApprovalServiceError):
    """Exception raised when a board member tries to approve the same application twice"""
    pass


class IneligibleApprovalError(ApprovalServiceError):
    """Exception raised when an approval is not allowed"""
    pass


class ApplicationNotFoundError(ApprovalServiceError):
    """Exception raised when an application is not found"""
    pass


class ApprovalService:
    """
    Service for managing two-approval workflow for membership applications.

    Implements:
    - Two-approval quorum logic
    - Self-approval prevention
    - Duplicate approval prevention
    - State machine transitions
    - Conditional approval support
    - Audit logging
    - Auto-promotion to approved status
    """

    # State machine transitions
    STATE_TRANSITIONS = {
        ApplicationStatus.SUBMITTED: [ApplicationStatus.UNDER_REVIEW, ApplicationStatus.REJECTED],
        ApplicationStatus.UNDER_REVIEW: [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED],
        ApplicationStatus.APPROVED: [],  # Terminal state
        ApplicationStatus.REJECTED: [],  # Terminal state
        ApplicationStatus.WITHDRAWN: [],  # Terminal state
    }

    # Required number of approvals for quorum
    REQUIRED_APPROVALS = 2

    def __init__(self, zerodb_client: Optional[ZeroDBClient] = None):
        """
        Initialize approval service

        Args:
            zerodb_client: Optional ZeroDB client instance (creates new if not provided)
        """
        self.db = zerodb_client or ZeroDBClient()
        logger.info("ApprovalService initialized")

    def validate_approval_eligibility(
        self,
        application_id: str,
        board_member_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a board member can approve an application.

        Checks:
        1. Application exists
        2. Application is in approvable state (submitted or under_review)
        3. Board member is not the applicant (no self-approval)
        4. Board member hasn't already approved this application

        Args:
            application_id: UUID of the application
            board_member_id: UUID of the board member

        Returns:
            Tuple of (is_eligible, error_message)

        Raises:
            ApplicationNotFoundError: If application doesn't exist
        """
        try:
            # Get application
            app_result = self.db.get_document("applications", application_id)
            application = app_result.get("data", {})

            if not application:
                raise ApplicationNotFoundError(f"Application {application_id} not found")

            current_status = application.get("status")
            applicant_user_id = str(application.get("user_id", ""))

            # Check if application is in approvable state
            if current_status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
                return False, f"Application status '{current_status}' is not eligible for approval"

            # Check for self-approval
            if applicant_user_id == str(board_member_id):
                return False, "Board member cannot approve their own application"

            # Check for duplicate approval
            existing_approvals = self._get_approvals(application_id)
            for approval in existing_approvals:
                if str(approval.get("approver_id")) == str(board_member_id):
                    return False, "Board member has already approved this application"

            return True, None

        except ZeroDBNotFoundError:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

    def process_approval(
        self,
        application_id: str,
        board_member_id: str,
        action: str,
        notes: Optional[str] = None,
        conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a single approval or rejection by a board member.

        Business Logic:
        - For APPROVAL: Creates approval record, checks quorum, may auto-approve
        - For REJECTION: Immediately sets application status to 'rejected'
        - Updates application timestamps
        - Creates audit log entries

        Args:
            application_id: UUID of the application
            board_member_id: UUID of the board member
            action: "approve" or "reject"
            notes: Optional approval/rejection notes
            conditions: Optional list of conditions for approval (only for approve action)

        Returns:
            Dict containing:
            - application: Updated application data
            - approval: Created approval record (if action is approve)
            - quorum_reached: Whether 2-approval quorum is reached
            - approval_count: Current number of approvals

        Raises:
            IneligibleApprovalError: If approval is not allowed
            ApplicationNotFoundError: If application doesn't exist
            ValueError: If action is invalid
        """
        if action not in ["approve", "reject"]:
            raise ValueError(f"Invalid action: {action}. Must be 'approve' or 'reject'")

        # Validate eligibility
        is_eligible, error_message = self.validate_approval_eligibility(
            application_id,
            board_member_id
        )

        if not is_eligible:
            logger.warning(
                f"Approval not eligible for application {application_id} "
                f"by board member {board_member_id}: {error_message}"
            )
            if "own application" in error_message:
                raise SelfApprovalError(error_message)
            elif "already approved" in error_message:
                raise DuplicateApprovalError(error_message)
            else:
                raise IneligibleApprovalError(error_message)

        # Get current application
        app_result = self.db.get_document("applications", application_id)
        application = app_result.get("data", {})
        current_status = application.get("status")

        if action == "reject":
            # REJECTION: Immediately set status to rejected
            updated_app = self._handle_rejection(
                application_id,
                board_member_id,
                notes
            )

            return {
                "application": updated_app,
                "approval": None,
                "quorum_reached": False,
                "approval_count": 0,
                "action": "rejected"
            }

        else:  # action == "approve"
            # APPROVAL: Create approval record
            approval_data = {
                "application_id": application_id,
                "approver_id": board_member_id,
                "status": ApprovalStatus.APPROVED,
                "notes": notes or "",
                "conditions": conditions or [],
                "approved_at": datetime.utcnow().isoformat(),
                "priority": 0
            }

            # Create approval record
            approval_result = self.db.create_document("approvals", approval_data)
            approval = approval_result.get("data", {})

            logger.info(
                f"Approval created: {approval_result.get('id')} "
                f"for application {application_id} by {board_member_id}"
            )

            # Update application state based on approval count
            new_status = None
            if current_status == ApplicationStatus.SUBMITTED:
                # First approval: move to UNDER_REVIEW
                new_status = ApplicationStatus.UNDER_REVIEW

            # Check if quorum is reached
            quorum_result = self.check_approval_quorum(application_id)
            quorum_reached = quorum_result["quorum_reached"]

            if quorum_reached:
                # Second approval: move to APPROVED
                new_status = ApplicationStatus.APPROVED

            # Update application if state changed
            updated_app = application
            if new_status:
                update_data = {
                    "status": new_status,
                    "updated_at": datetime.utcnow().isoformat()
                }

                if new_status == ApplicationStatus.UNDER_REVIEW:
                    update_data["reviewed_at"] = datetime.utcnow().isoformat()
                    update_data["reviewed_by"] = board_member_id

                update_result = self.db.update_document(
                    "applications",
                    application_id,
                    update_data,
                    merge=True
                )
                updated_app = update_result.get("data", {})

                logger.info(
                    f"Application {application_id} status updated: "
                    f"{current_status} -> {new_status}"
                )

            # If approved, auto-promote application
            if quorum_reached:
                self.auto_approve_application(application_id)

            # Create audit log
            self._create_audit_log(
                user_id=board_member_id,
                action=AuditAction.APPROVE,
                resource_type="applications",
                resource_id=application_id,
                description=f"Board member approved application with {len(conditions or [])} conditions",
                changes={
                    "old_status": current_status,
                    "new_status": new_status or current_status,
                    "notes": notes,
                    "conditions": conditions
                }
            )

            return {
                "application": updated_app,
                "approval": approval,
                "quorum_reached": quorum_reached,
                "approval_count": quorum_result["approval_count"],
                "action": "approved"
            }

    def check_approval_quorum(self, application_id: str) -> Dict[str, Any]:
        """
        Check if application has reached 2-approval quorum.

        Args:
            application_id: UUID of the application

        Returns:
            Dict containing:
            - quorum_reached: Boolean indicating if 2 approvals reached
            - approval_count: Number of approvals
            - required_approvals: Required number (always 2)
            - approvals: List of approval records
        """
        approvals = self._get_approvals(application_id)

        # Only count approved (not rejected or pending)
        approved_count = sum(
            1 for a in approvals
            if a.get("status") == ApprovalStatus.APPROVED
        )

        quorum_reached = approved_count >= self.REQUIRED_APPROVALS

        return {
            "quorum_reached": quorum_reached,
            "approval_count": approved_count,
            "required_approvals": self.REQUIRED_APPROVALS,
            "approvals": approvals,
            "progress_percentage": (approved_count / self.REQUIRED_APPROVALS) * 100
        }

    def calculate_approval_progress(self, application_id: str) -> Dict[str, Any]:
        """
        Calculate approval progress for an application.

        Args:
            application_id: UUID of the application

        Returns:
            Dict with approval count, progress percentage, and details
        """
        return self.check_approval_quorum(application_id)

    def auto_approve_application(self, application_id: str) -> Dict[str, Any]:
        """
        Auto-approve application when 2-approval quorum is reached.

        Actions:
        1. Update application status to 'approved'
        2. Set approved_at timestamp
        3. Upgrade user role to 'member'
        4. Create audit log entry

        Args:
            application_id: UUID of the application

        Returns:
            Updated application data

        Raises:
            ApplicationNotFoundError: If application doesn't exist
        """
        try:
            # Get application
            app_result = self.db.get_document("applications", application_id)
            application = app_result.get("data", {})

            if not application:
                raise ApplicationNotFoundError(f"Application {application_id} not found")

            user_id = application.get("user_id")

            # Update application to approved
            update_data = {
                "status": ApplicationStatus.APPROVED,
                "approved_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            updated_result = self.db.update_document(
                "applications",
                application_id,
                update_data,
                merge=True
            )

            # Upgrade user role to member
            try:
                user_update = self.db.update_document(
                    "users",
                    str(user_id),
                    {"role": UserRole.MEMBER},
                    merge=True
                )
                logger.info(f"User {user_id} role upgraded to MEMBER")
            except ZeroDBNotFoundError:
                logger.error(f"User {user_id} not found, cannot upgrade role")

            # Create audit log
            self._create_audit_log(
                user_id=None,  # System action
                action=AuditAction.APPROVE,
                resource_type="applications",
                resource_id=application_id,
                description="Application auto-approved after reaching 2-approval quorum",
                changes={
                    "status": ApplicationStatus.APPROVED,
                    "approved_at": update_data["approved_at"],
                    "user_role": UserRole.MEMBER
                }
            )

            logger.info(f"Application {application_id} auto-approved successfully")

            # Trigger checkout session creation and payment email
            self._trigger_payment_flow(application_id, application)

            return updated_result.get("data", {})

        except ZeroDBNotFoundError:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

    def _get_approvals(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Get all approval records for an application.

        Args:
            application_id: UUID of the application

        Returns:
            List of approval records
        """
        try:
            result = self.db.query_documents(
                "approvals",
                filters={"application_id": application_id},
                limit=100
            )
            return result.get("documents", [])
        except Exception as e:
            logger.error(f"Error fetching approvals for {application_id}: {e}")
            return []

    def _handle_rejection(
        self,
        application_id: str,
        board_member_id: str,
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """
        Handle application rejection.

        Args:
            application_id: UUID of the application
            board_member_id: UUID of the board member
            notes: Rejection notes

        Returns:
            Updated application data
        """
        # Create rejection approval record
        rejection_data = {
            "application_id": application_id,
            "approver_id": board_member_id,
            "status": ApprovalStatus.REJECTED,
            "notes": notes or "",
            "approved_at": datetime.utcnow().isoformat(),
            "conditions": [],
            "priority": 0
        }

        self.db.create_document("approvals", rejection_data)

        # Update application to rejected
        update_data = {
            "status": ApplicationStatus.REJECTED,
            "reviewed_at": datetime.utcnow().isoformat(),
            "reviewed_by": board_member_id,
            "decision_notes": notes or "",
            "updated_at": datetime.utcnow().isoformat()
        }

        result = self.db.update_document(
            "applications",
            application_id,
            update_data,
            merge=True
        )

        # Create audit log
        self._create_audit_log(
            user_id=board_member_id,
            action=AuditAction.REJECT,
            resource_type="applications",
            resource_id=application_id,
            description=f"Board member rejected application: {notes or 'No notes provided'}",
            changes={
                "status": ApplicationStatus.REJECTED,
                "notes": notes
            }
        )

        logger.info(f"Application {application_id} rejected by {board_member_id}")

        return result.get("data", {})

    def _trigger_payment_flow(
        self,
        application_id: str,
        application: Dict[str, Any]
    ) -> None:
        """
        Trigger payment flow after application approval

        Creates Stripe checkout session and sends payment link email to applicant.

        Args:
            application_id: UUID of the application
            application: Application data dictionary
        """
        try:
            # Import here to avoid circular dependency
            from backend.services.stripe_service import get_stripe_service

            user_id = application.get("user_id")
            user_email = application.get("email")
            tier_id = application.get("subscription_tier", "basic")
            applicant_name = f"{application.get('first_name', '')} {application.get('last_name', '')}".strip()

            if not user_id or not user_email:
                logger.error(f"Cannot trigger payment flow: missing user_id or email for application {application_id}")
                return

            # Create Stripe checkout session
            stripe_service = get_stripe_service()

            try:
                session_data = stripe_service.create_checkout_session(
                    user_id=str(user_id),
                    application_id=application_id,
                    tier_id=tier_id,
                    customer_email=user_email
                )

                checkout_url = session_data.get("url")
                amount_cents = session_data.get("amount")
                amount_dollars = amount_cents / 100 if amount_cents else 0

                logger.info(
                    f"Checkout session created for application {application_id}: "
                    f"{session_data.get('session_id')}"
                )

                # Get tier name for email
                tier_names = {
                    "basic": "Basic Membership",
                    "premium": "Premium Membership",
                    "lifetime": "Instructor Membership"
                }
                tier_name = tier_names.get(tier_id, tier_id.title())

                # Format amount for email
                if tier_id == "lifetime":
                    amount_str = f"${amount_dollars:.2f} one-time"
                else:
                    amount_str = f"${amount_dollars:.2f}/year"

                # Send payment link email
                try:
                    email_service = get_email_service()
                    email_service.send_payment_link_email(
                        email=user_email,
                        applicant_name=applicant_name,
                        payment_url=checkout_url,
                        tier_name=tier_name,
                        amount=amount_str
                    )
                    logger.info(f"Payment link email sent to {user_email} for application {application_id}")
                except Exception as e:
                    logger.error(f"Failed to send payment link email: {e}")
                    # Don't fail the approval if email fails

            except Exception as e:
                logger.error(f"Failed to create checkout session: {e}")
                # Don't fail the approval if checkout creation fails

        except Exception as e:
            logger.error(f"Error in payment flow trigger: {e}")
            # Don't fail the approval if payment flow fails

    def _create_audit_log(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        description: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create an audit log entry.

        Args:
            user_id: UUID of user performing action (None for system)
            action: Action type (approve, reject, etc.)
            resource_type: Type of resource (applications, etc.)
            resource_id: UUID of the resource
            description: Human-readable description
            changes: Dict of changes made
        """
        try:
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "changes": changes or {},
                "success": True,
                "severity": "info",
                "tags": ["approval_workflow"],
                "metadata": {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

    def get_application_approval_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get comprehensive approval status for an application.

        Args:
            application_id: UUID of the application

        Returns:
            Dict with application data, approvals, and progress
        """
        try:
            # Get application
            app_result = self.db.get_document("applications", application_id)
            application = app_result.get("data", {})

            # Get approval progress
            progress = self.calculate_approval_progress(application_id)

            return {
                "application": application,
                "status": application.get("status"),
                "approval_progress": progress,
                "is_approved": application.get("status") == ApplicationStatus.APPROVED,
                "is_rejected": application.get("status") == ApplicationStatus.REJECTED,
                "approved_at": application.get("approved_at")
            }
        except ZeroDBNotFoundError:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

    def reject_application_with_reason(
        self,
        application_id: str,
        rejected_by_user_id: str,
        rejection_reason: str,
        recommended_improvements: Optional[str] = None,
        allow_reapplication: bool = True
    ) -> Dict[str, Any]:
        """
        Reject an application with detailed reason and reapplication handling.

        This enhanced rejection method includes:
        - Required rejection reason
        - Optional recommended improvements
        - Reapplication eligibility (30-day wait period)
        - Email notification to applicant
        - Invalidation of existing approvals
        - Audit logging

        Args:
            application_id: UUID of the application to reject
            rejected_by_user_id: UUID of board member/admin performing rejection
            rejection_reason: Required reason for rejection
            recommended_improvements: Optional suggestions for future application
            allow_reapplication: Whether to allow reapplication (default: True)

        Returns:
            Dict containing:
            - success: Boolean indicating success
            - application_id: The application ID
            - status: New status (rejected)
            - rejected_at: Rejection timestamp
            - allow_reapplication: Whether reapplication is allowed
            - reapplication_allowed_at: Date when reapplication is permitted

        Raises:
            ApplicationNotFoundError: If application doesn't exist
            IneligibleApprovalError: If application already processed
            ValueError: If rejection_reason is empty

        Example:
            >>> result = service.reject_application_with_reason(
            ...     application_id="123e4567-e89b-12d3-a456-426614174000",
            ...     rejected_by_user_id="board-member-uuid",
            ...     rejection_reason="Application incomplete - missing martial arts experience details",
            ...     recommended_improvements="Please provide detailed information about your training background",
            ...     allow_reapplication=True
            ... )
        """
        # Validate rejection reason
        if not rejection_reason or not rejection_reason.strip():
            raise ValueError("Rejection reason is required and cannot be empty")

        # Validate user can reject (board member or admin)
        is_eligible, error_message = self.validate_approval_eligibility(
            application_id,
            rejected_by_user_id
        )
        # For rejection, we only care if application is in valid state
        # We don't enforce self-rejection check as strictly

        try:
            # Get application
            app_result = self.db.get_document("applications", application_id)
            application = app_result.get("data", {})

            if not application:
                raise ApplicationNotFoundError(f"Application {application_id} not found")

            # Check if already processed
            current_status = application.get("status")
            if current_status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]:
                raise IneligibleApprovalError(
                    f"Application already {current_status} and cannot be rejected again"
                )

            now = datetime.utcnow()

            # Calculate reapplication date (30 days from now)
            reapplication_date = None
            if allow_reapplication:
                from datetime import timedelta
                reapplication_date = now + timedelta(days=30)

            # Update application with rejection details
            update_data = {
                "status": ApplicationStatus.REJECTED,
                "rejected_at": now.isoformat(),
                "rejected_by": rejected_by_user_id,
                "rejection_reason": rejection_reason,
                "recommended_improvements": recommended_improvements or "",
                "allow_reapplication": allow_reapplication,
                "reapplication_allowed_at": reapplication_date.isoformat() if reapplication_date else None,
                "reviewed_at": now.isoformat(),
                "reviewed_by": rejected_by_user_id,
                "updated_at": now.isoformat()
            }

            updated_result = self.db.update_document(
                "applications",
                application_id,
                update_data,
                merge=True
            )
            updated_app = updated_result.get("data", {})

            # Create rejection record in approvals collection
            rejection_approval = {
                "application_id": application_id,
                "approver_id": rejected_by_user_id,
                "status": ApprovalStatus.REJECTED,
                "action": ApprovalAction.REJECT,
                "notes": rejection_reason,
                "rejected_at": now.isoformat(),
                "is_active": True,
                "conditions": [],
                "priority": 0
            }

            self.db.create_document("approvals", rejection_approval)

            # Invalidate any existing approvals
            invalidated_count = self.invalidate_active_approvals(application_id, rejected_by_user_id)

            # Update user's reapplication count
            user_id = application.get("user_id")
            if user_id:
                try:
                    user_result = self.db.get_document("users", str(user_id))
                    user = user_result.get("data", {})
                    current_count = user.get("reapplication_count", 0)

                    self.db.update_document(
                        "users",
                        str(user_id),
                        {
                            "reapplication_count": current_count + 1,
                            "updated_at": now.isoformat()
                        },
                        merge=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to update user reapplication count: {e}")

            # Send rejection email
            email_sent = False
            try:
                email_service = get_email_service()
                email_service.send_application_rejection_email(
                    email=application.get("email"),
                    user_name=f"{application.get('first_name', '')} {application.get('last_name', '')}",
                    rejection_reason=rejection_reason,
                    recommended_improvements=recommended_improvements,
                    allow_reapplication=allow_reapplication,
                    reapplication_date=reapplication_date
                )
                email_sent = True
                logger.info(f"Rejection email sent for application {application_id}")
            except Exception as e:
                logger.error(f"Failed to send rejection email: {e}")
                # Don't fail the rejection if email fails

            # Create audit log
            self._create_audit_log(
                user_id=rejected_by_user_id,
                action=AuditAction.REJECT,
                resource_type="applications",
                resource_id=application_id,
                description=f"Application rejected with reason: {rejection_reason[:100]}",
                changes={
                    "old_status": current_status,
                    "new_status": ApplicationStatus.REJECTED,
                    "rejection_reason": rejection_reason,
                    "allow_reapplication": allow_reapplication,
                    "reapplication_date": reapplication_date.isoformat() if reapplication_date else None,
                    "approvals_invalidated": invalidated_count
                }
            )

            logger.info(
                f"Application {application_id} rejected by {rejected_by_user_id} "
                f"(allow_reapplication={allow_reapplication}, invalidated={invalidated_count} approvals)"
            )

            return {
                "success": True,
                "application_id": application_id,
                "status": "rejected",
                "rejected_at": now.isoformat(),
                "rejected_by": rejected_by_user_id,
                "rejection_reason": rejection_reason,
                "allow_reapplication": allow_reapplication,
                "reapplication_allowed_at": reapplication_date.isoformat() if reapplication_date else None,
                "approvals_invalidated": invalidated_count,
                "email_sent": email_sent
            }

        except ZeroDBNotFoundError:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

    def invalidate_active_approvals(
        self,
        application_id: str,
        invalidated_by_user_id: str
    ) -> int:
        """
        Invalidate all active approvals for an application.

        Called when an application is rejected to ensure any previous
        approvals are marked as inactive and no longer count toward quorum.

        Args:
            application_id: UUID of the application
            invalidated_by_user_id: UUID of user triggering invalidation

        Returns:
            Number of approvals invalidated

        Example:
            >>> count = service.invalidate_active_approvals(app_id, user_id)
            >>> print(f"Invalidated {count} approvals")
        """
        try:
            # Get all active approvals for this application
            approvals = self._get_approvals(application_id)

            invalidated_count = 0
            now = datetime.utcnow()

            for approval in approvals:
                # Skip if already inactive
                if not approval.get("is_active", True):
                    continue

                # Skip rejections (they're already invalid)
                if approval.get("status") == ApprovalStatus.REJECTED:
                    continue

                approval_id = approval.get("id")
                if not approval_id:
                    continue

                # Mark as invalidated
                update_data = {
                    "is_active": False,
                    "action": ApprovalAction.INVALIDATE,
                    "invalidated_at": now.isoformat(),
                    "updated_at": now.isoformat()
                }

                try:
                    self.db.update_document(
                        "approvals",
                        str(approval_id),
                        update_data,
                        merge=True
                    )
                    invalidated_count += 1
                except Exception as e:
                    logger.error(f"Failed to invalidate approval {approval_id}: {e}")

            logger.info(
                f"Invalidated {invalidated_count} active approvals for application {application_id}"
            )

            return invalidated_count

        except Exception as e:
            logger.error(f"Error invalidating approvals: {e}")
            return 0

    def submit_appeal(
        self,
        application_id: str,
        appeal_reason: str
    ) -> Dict[str, Any]:
        """
        Submit an appeal for a rejected application.

        Appeals require admin review and can potentially overturn a rejection.

        Args:
            application_id: UUID of the rejected application
            appeal_reason: Reason for the appeal

        Returns:
            Dict containing appeal submission details

        Raises:
            ApplicationNotFoundError: If application doesn't exist
            IneligibleApprovalError: If application not rejected or appeal already submitted
            ValueError: If appeal_reason is empty

        Example:
            >>> result = service.submit_appeal(
            ...     application_id="123e4567-e89b-12d3-a456-426614174000",
            ...     appeal_reason="I have completed the recommended training and updated my credentials"
            ... )
        """
        # Validate appeal reason
        if not appeal_reason or not appeal_reason.strip():
            raise ValueError("Appeal reason is required and cannot be empty")

        try:
            # Get application
            app_result = self.db.get_document("applications", application_id)
            application = app_result.get("data", {})

            if not application:
                raise ApplicationNotFoundError(f"Application {application_id} not found")

            # Validate application is rejected
            if application.get("status") != ApplicationStatus.REJECTED:
                raise IneligibleApprovalError(
                    "Only rejected applications can be appealed"
                )

            # Check if appeal already submitted
            if application.get("appeal_submitted"):
                raise IneligibleApprovalError(
                    "Appeal already submitted for this application"
                )

            now = datetime.utcnow()

            # Update application with appeal details
            update_data = {
                "appeal_submitted": True,
                "appeal_reason": appeal_reason,
                "appeal_submitted_at": now.isoformat(),
                "updated_at": now.isoformat()
            }

            updated_result = self.db.update_document(
                "applications",
                application_id,
                update_data,
                merge=True
            )

            # Create audit log
            self._create_audit_log(
                user_id=application.get("user_id"),
                action=AuditAction.UPDATE,
                resource_type="applications",
                resource_id=application_id,
                description=f"Appeal submitted: {appeal_reason[:100]}",
                changes={
                    "appeal_submitted": True,
                    "appeal_reason": appeal_reason
                }
            )

            logger.info(f"Appeal submitted for application {application_id}")

            return {
                "success": True,
                "application_id": application_id,
                "appeal_submitted": True,
                "appeal_submitted_at": now.isoformat(),
                "appeal_reason": appeal_reason
            }

        except ZeroDBNotFoundError:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

    def check_reapplication_eligibility(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Check if a user is eligible to reapply for membership.

        Checks:
        - Most recent application status
        - Reapplication allowed flag
        - Reapplication date (30-day waiting period)

        Args:
            user_id: UUID of the user

        Returns:
            Dict containing:
            - eligible: Boolean indicating eligibility
            - reason: Explanation of eligibility status
            - reapplication_allowed_at: Date when reapplication permitted (if applicable)
            - previous_rejection_reason: Reason from previous rejection
            - recommended_improvements: Suggestions from previous rejection

        Example:
            >>> eligibility = service.check_reapplication_eligibility(user_id)
            >>> if eligibility["eligible"]:
            ...     # User can submit new application
        """
        try:
            # Query all applications for this user
            result = self.db.query_documents(
                "applications",
                filters={"user_id": user_id},
                limit=100
            )

            applications = result.get("documents", [])

            if not applications:
                return {
                    "eligible": True,
                    "reason": "No previous applications found"
                }

            # Sort by created_at to get most recent
            sorted_apps = sorted(
                applications,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            most_recent = sorted_apps[0]
            status = most_recent.get("status")

            # If not rejected, user can't reapply (need to complete current)
            if status != ApplicationStatus.REJECTED:
                return {
                    "eligible": False,
                    "reason": f"Current application is {status}"
                }

            # Check if reapplication allowed
            if not most_recent.get("allow_reapplication", True):
                return {
                    "eligible": False,
                    "reason": "Reapplication not permitted"
                }

            # Check reapplication date
            reapp_date_str = most_recent.get("reapplication_allowed_at")
            if reapp_date_str:
                from dateutil import parser
                reapp_date = parser.parse(reapp_date_str)
                now = datetime.utcnow()

                if now < reapp_date:
                    return {
                        "eligible": False,
                        "reason": f"Cannot reapply until {reapp_date.isoformat()}",
                        "reapplication_allowed_at": reapp_date_str
                    }

            return {
                "eligible": True,
                "reason": "User is eligible to reapply",
                "previous_rejection_reason": most_recent.get("rejection_reason"),
                "recommended_improvements": most_recent.get("recommended_improvements")
            }

        except Exception as e:
            logger.error(f"Error checking reapplication eligibility: {e}")
            return {
                "eligible": False,
                "reason": f"Error checking eligibility: {str(e)}"
            }
