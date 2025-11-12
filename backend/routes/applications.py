"""
Application Management Routes for WWMAA Backend

Provides endpoints for managing membership applications and the board approval workflow.
Implements the complete application lifecycle from submission to approval/rejection.

Key Features:
- Application submission and management
- Board member approval queue
- Multi-stage approval workflow (requires 2 board approvals)
- Self-approval prevention
- Duplicate approval detection
- Email notifications for applicants
- Approval history tracking

Endpoints:
- GET /api/applications/pending - List applications awaiting approval (board/admin only)
- GET /api/applications/:id - Get single application details
- GET /api/applications/:id/approvals - Get approval history for application
- POST /api/applications/:id/approve - Approve application (board/admin only)
- POST /api/applications/:id/reject - Reject application (board/admin only)
- POST /api/applications/:id/request-info - Request additional info (board/admin only)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.middleware.auth_middleware import RoleChecker, get_current_user
from backend.middleware.permissions import can_approve_application, can_view_application
from backend.models.schemas import (
    Application,
    ApplicationStatus,
    Approval,
    ApprovalStatus,
    UserRole
)
from backend.services.zerodb_service import get_zerodb_client
from backend.services.email_service import get_email_service
import logging

# Initialize router
router = APIRouter(prefix="/api/applications", tags=["applications"])

# Initialize logger
logger = logging.getLogger(__name__)

# Get ZeroDB client
zerodb_client = get_zerodb_client()

# Initialize email service
email_service = get_email_service()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ApprovalRequest(BaseModel):
    """Request model for approval actions"""
    notes: Optional[str] = Field(None, max_length=2000, description="Approval notes or reason")


class RejectionRequest(BaseModel):
    """Request model for rejection with comprehensive details"""
    rejection_reason: str = Field(..., min_length=1, max_length=2000, description="Required reason for rejection")
    recommended_improvements: Optional[str] = Field(None, max_length=2000, description="Optional improvement suggestions")
    allow_reapplication: bool = Field(default=True, description="Whether to allow reapplication (default: True)")


class AppealRequest(BaseModel):
    """Request model for submitting an appeal"""
    appeal_reason: str = Field(..., min_length=1, max_length=2000, description="Reason for appeal")


class RequestInfoRequest(BaseModel):
    """Request model for requesting additional information"""
    message: str = Field(..., min_length=1, max_length=2000, description="Message to applicant")


class ApprovalResponse(BaseModel):
    """Response model for approval actions"""
    application_id: UUID
    status: ApplicationStatus
    approvals_count: int
    approvals_needed: int
    message: str


class PendingApplicationResponse(BaseModel):
    """Response model for pending applications list"""
    id: UUID
    first_name: str
    last_name: str
    email: str
    status: ApplicationStatus
    submitted_at: Optional[datetime]
    disciplines: List[str]
    experience_years: Optional[int]
    current_rank: Optional[str]
    school_affiliation: Optional[str]
    motivation: Optional[str]
    approvals_count: int
    approvals_needed: int = 2
    created_at: datetime


class ApprovalHistoryItem(BaseModel):
    """Individual approval record in history"""
    id: UUID
    approver_id: UUID
    approver_name: Optional[str]
    approver_email: Optional[str]
    status: ApprovalStatus
    notes: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime


class ApprovalHistoryResponse(BaseModel):
    """Response model for approval history"""
    application_id: UUID
    approvals: List[ApprovalHistoryItem]
    total_approvals: int
    approvals_needed: int = 2


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_application_by_id(application_id: UUID) -> Application:
    """
    Fetch application by ID from ZeroDB.

    Args:
        application_id: UUID of the application

    Returns:
        Application object

    Raises:
        HTTPException: If application not found
    """
    try:
        result = zerodb_client.query_documents(
            collection="applications",
            filter={"id": str(application_id)}
        )

        if not result or len(result) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )

        return Application(**result[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch application"
        )


async def get_approvals_for_application(application_id: UUID) -> List[Approval]:
    """
    Fetch all approvals for an application.

    Args:
        application_id: UUID of the application

    Returns:
        List of Approval objects
    """
    try:
        results = zerodb_client.query_documents(
            collection="approvals",
            filter={"application_id": str(application_id)}
        )

        return [Approval(**approval) for approval in results]
    except Exception as e:
        logger.error(f"Error fetching approvals for application {application_id}: {e}")
        return []


async def get_user_info(user_id: UUID) -> Optional[dict]:
    """
    Fetch user information from ZeroDB.

    Args:
        user_id: UUID of the user

    Returns:
        User information dict or None
    """
    try:
        result = zerodb_client.query_documents(
            collection="users",
            filter={"id": str(user_id)}
        )

        if result and len(result) > 0:
            return result[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None


async def check_self_approval(application: Application, board_member_id: UUID) -> bool:
    """
    Check if a board member is trying to approve their own application.

    Args:
        application: Application object
        board_member_id: UUID of the board member

    Returns:
        True if this is a self-approval attempt
    """
    return application.user_id == board_member_id


async def check_duplicate_approval(application_id: UUID, board_member_id: UUID) -> bool:
    """
    Check if a board member has already approved this application.

    Args:
        application_id: UUID of the application
        board_member_id: UUID of the board member

    Returns:
        True if board member has already approved
    """
    try:
        existing_approvals = zerodb_client.query_documents(
            collection="approvals",
            filter={
                "application_id": str(application_id),
                "approver_id": str(board_member_id),
                "status": ApprovalStatus.APPROVED.value
            }
        )

        return len(existing_approvals) > 0
    except Exception as e:
        logger.error(f"Error checking duplicate approval: {e}")
        return False


async def count_approvals(application_id: UUID) -> int:
    """
    Count approved approvals for an application.

    Args:
        application_id: UUID of the application

    Returns:
        Number of approvals
    """
    try:
        approvals = zerodb_client.query_documents(
            collection="approvals",
            filter={
                "application_id": str(application_id),
                "status": ApprovalStatus.APPROVED.value
            }
        )

        return len(approvals)
    except Exception as e:
        logger.error(f"Error counting approvals: {e}")
        return 0


async def auto_approve_application(application_id: UUID, approvals_count: int) -> bool:
    """
    Automatically approve application if it has reached required approvals.

    Args:
        application_id: UUID of the application
        approvals_count: Current number of approvals

    Returns:
        True if application was auto-approved
    """
    REQUIRED_APPROVALS = 2

    if approvals_count >= REQUIRED_APPROVALS:
        try:
            # Update application status to approved
            zerodb_client.update_document(
                collection="applications",
                filter={"id": str(application_id)},
                update={
                    "status": ApplicationStatus.APPROVED.value,
                    "reviewed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Application {application_id} auto-approved with {approvals_count} approvals")
            return True
        except Exception as e:
            logger.error(f"Error auto-approving application {application_id}: {e}")
            return False

    return False


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=List[PendingApplicationResponse],
    summary="List applications with filters",
    description="Get applications with optional status filtering (board members and admins only)"
)
async def list_applications(
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"])),
    status: Optional[str] = Query(None, description="Filter by status: 'pending', 'approved', 'rejected', or specific status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List applications with optional status filtering.

    Query Parameters:
    - status: 'pending' (submitted + under_review), 'approved', 'rejected', or specific status
    - limit: Maximum results (1-100, default 50)
    - offset: Pagination offset

    Returns applications sorted by submission date (oldest first).
    """
    try:
        query_filter = {}

        if status:
            status_lower = status.lower()
            if status_lower == "pending":
                query_filter["status"] = {"$in": ["submitted", "under_review"]}
            elif status_lower == "all":
                pass  # No filter
            elif status_lower in ["submitted", "under_review", "approved", "rejected", "withdrawn", "draft"]:
                query_filter["status"] = status_lower
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: '{status}'. Valid: 'pending', 'approved', 'rejected', 'all', or specific status"
                )
        else:
            # Default: show pending
            query_filter["status"] = {"$in": ["submitted", "under_review"]}

        logger.info(f"User {current_user['email']} querying applications with filter: {query_filter}")

        applications = zerodb_client.query_documents(
            collection="applications",
            filter=query_filter
        )

        application_responses = []
        for app_data in applications:
            try:
                application = Application(**app_data)
                approvals_count = await count_approvals(application.id)

                application_responses.append(
                    PendingApplicationResponse(
                        id=application.id,
                        first_name=application.first_name,
                        last_name=application.last_name,
                        email=application.email,
                        status=application.status,
                        submitted_at=application.submitted_at,
                        disciplines=application.disciplines,
                        experience_years=application.experience_years,
                        current_rank=application.current_rank,
                        school_affiliation=application.school_affiliation,
                        motivation=application.motivation,
                        approvals_count=approvals_count,
                        created_at=application.created_at
                    )
                )
            except Exception as e:
                logger.error(f"Error processing application {app_data.get('id', 'unknown')}: {e}")
                continue

        application_responses.sort(key=lambda x: x.submitted_at or x.created_at)

        total_count = len(application_responses)
        paginated_results = application_responses[offset:offset + limit]

        logger.info(
            f"User {current_user['email']} retrieved {len(paginated_results)} applications "
            f"(total: {total_count}, status: '{status or 'pending'}', offset: {offset})"
        )

        return paginated_results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing applications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch applications"
        )


@router.get(
    "/pending",
    response_model=List[PendingApplicationResponse],
    summary="List pending applications",
    description="Get all applications awaiting approval (board members and admins only)"
)
async def list_pending_applications(
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"])),
    status_filter: Optional[str] = Query(None, description="Filter by status (submitted, under_review)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all applications awaiting board approval.

    Only accessible by board members and administrators.

    Query Parameters:
    - status_filter: Filter by application status (submitted, under_review)
    - limit: Maximum number of results (1-100, default 50)
    - offset: Number of results to skip for pagination

    Returns applications sorted by:
    1. Priority (if set)
    2. Submission date (oldest first)
    """
    try:
        # Build filter for pending applications
        query_filter = {}

        # Filter by status
        if status_filter:
            if status_filter.lower() in ["submitted", "under_review"]:
                query_filter["status"] = status_filter.lower()
            else:
                query_filter["status"] = {"$in": ["submitted", "under_review"]}
        else:
            query_filter["status"] = {"$in": ["submitted", "under_review"]}

        # Query applications
        applications = zerodb_client.query_documents(
            collection="applications",
            filter=query_filter
        )

        # Build response with approval counts
        pending_applications = []

        for app_data in applications:
            application = Application(**app_data)

            # Count approvals
            approvals_count = await count_approvals(application.id)

            pending_applications.append(
                PendingApplicationResponse(
                    id=application.id,
                    first_name=application.first_name,
                    last_name=application.last_name,
                    email=application.email,
                    status=application.status,
                    submitted_at=application.submitted_at,
                    disciplines=application.disciplines,
                    experience_years=application.experience_years,
                    current_rank=application.current_rank,
                    school_affiliation=application.school_affiliation,
                    motivation=application.motivation,
                    approvals_count=approvals_count,
                    created_at=application.created_at
                )
            )

        # Sort by submission date (oldest first)
        pending_applications.sort(
            key=lambda x: x.submitted_at or x.created_at
        )

        # Apply pagination
        total_count = len(pending_applications)
        paginated_results = pending_applications[offset:offset + limit]

        logger.info(
            f"User {current_user['email']} retrieved {len(paginated_results)} pending applications "
            f"(total: {total_count}, offset: {offset})"
        )

        return paginated_results

    except Exception as e:
        logger.error(f"Error listing pending applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending applications"
        )


@router.get(
    "/{application_id}",
    response_model=Application,
    summary="Get application details",
    description="Get detailed information about a specific application"
)
async def get_application(
    application_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific application.

    Access control:
    - Application owner can view their own application
    - Board members and admins can view all applications
    """
    application = await get_application_by_id(application_id)

    # Check permissions
    if not can_view_application(current_user, application):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this application"
        )

    logger.info(f"User {current_user['email']} viewed application {application_id}")

    return application


@router.get(
    "/{application_id}/approvals",
    response_model=ApprovalHistoryResponse,
    summary="Get approval history",
    description="Get approval history for a specific application"
)
async def get_approval_history(
    application_id: UUID,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"]))
):
    """
    Get approval history for an application.

    Shows all approval actions taken by board members, including:
    - Approvals
    - Rejections
    - Information requests

    Only accessible by board members and administrators.
    """
    # Verify application exists
    application = await get_application_by_id(application_id)

    # Fetch all approvals
    approvals = await get_approvals_for_application(application_id)

    # Build response with approver information
    approval_items = []

    for approval in approvals:
        # Fetch approver information
        approver = await get_user_info(approval.approver_id)

        approval_items.append(
            ApprovalHistoryItem(
                id=approval.id,
                approver_id=approval.approver_id,
                approver_name=f"{approver.get('first_name', '')} {approver.get('last_name', '')}".strip() if approver else None,
                approver_email=approver.get("email") if approver else None,
                status=approval.status,
                notes=approval.notes,
                approved_at=approval.approved_at,
                created_at=approval.created_at
            )
        )

    # Sort by creation date (newest first)
    approval_items.sort(key=lambda x: x.created_at, reverse=True)

    logger.info(f"User {current_user['email']} viewed approval history for application {application_id}")

    return ApprovalHistoryResponse(
        application_id=application_id,
        approvals=approval_items,
        total_approvals=len([a for a in approvals if a.status == ApprovalStatus.APPROVED])
    )


@router.post(
    "/{application_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve application",
    description="Approve a membership application (board members and admins only)"
)
async def approve_application(
    application_id: UUID,
    request: ApprovalRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"]))
):
    """
    Approve a membership application.

    Workflow:
    1. Verify board member has permission to approve
    2. Check for self-approval (board member cannot approve their own application)
    3. Check for duplicate approval (same board member cannot approve twice)
    4. Create approval record
    5. Check if application has reached required approvals (2)
    6. If 2 approvals reached, auto-update application status to 'approved'
    7. Send email notification to applicant

    Only accessible by board members and administrators.
    """
    # Fetch application
    application = await get_application_by_id(application_id)

    # Verify application is in correct status
    if application.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve application in '{application.status}' status"
        )

    # Check for self-approval
    if await check_self_approval(application, current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board members cannot approve their own applications"
        )

    # Check for duplicate approval
    if await check_duplicate_approval(application_id, current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already approved this application"
        )

    # Create approval record
    approval = Approval(
        application_id=application_id,
        approver_id=current_user["id"],
        status=ApprovalStatus.APPROVED,
        notes=request.notes,
        approved_at=datetime.utcnow()
    )

    try:
        # Save approval to ZeroDB
        zerodb_client.insert_document(
            collection="approvals",
            document=approval.model_dump(mode="json")
        )

        # Update application status to under_review if it was submitted
        if application.status == ApplicationStatus.SUBMITTED:
            zerodb_client.update_document(
                collection="applications",
                filter={"id": str(application_id)},
                update={
                    "status": ApplicationStatus.UNDER_REVIEW.value,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

        # Count total approvals
        approvals_count = await count_approvals(application_id)

        # Check for auto-approval
        auto_approved = await auto_approve_application(application_id, approvals_count)

        # Send email notification
        try:
            if auto_approved:
                # Application fully approved - send final approval email
                email_service.send_application_fully_approved_email(
                    email=application.email,
                    applicant_name=f"{application.first_name} {application.last_name}"
                )
                message = f"Application approved! Total approvals: {approvals_count}/2. Application is now fully approved."
            else:
                # First approval - send partial approval email
                email_service.send_application_first_approval_email(
                    email=application.email,
                    applicant_name=f"{application.first_name} {application.last_name}",
                    approver_name=current_user.get("email", "Board Member"),
                    approvals_count=approvals_count
                )
                message = f"Application approved! Total approvals: {approvals_count}/2. One more approval needed."
        except Exception as e:
            logger.error(f"Failed to send approval email: {e}")
            # Don't fail the request if email fails

        logger.info(
            f"Board member {current_user['email']} approved application {application_id}. "
            f"Total approvals: {approvals_count}/2. Auto-approved: {auto_approved}"
        )

        return ApprovalResponse(
            application_id=application_id,
            status=ApplicationStatus.APPROVED if auto_approved else ApplicationStatus.UNDER_REVIEW,
            approvals_count=approvals_count,
            approvals_needed=2,
            message=message
        )

    except Exception as e:
        logger.error(f"Error approving application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve application"
        )


@router.post(
    "/{application_id}/reject",
    response_model=ApprovalResponse,
    summary="Reject application",
    description="Reject a membership application with detailed reason and reapplication handling (board members and admins only)"
)
async def reject_application(
    application_id: UUID,
    request: RejectionRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"]))
):
    """
    Reject a membership application with comprehensive rejection handling.

    Enhanced Workflow (US-018):
    1. Verify board member has permission to reject
    2. Validate rejection reason is provided
    3. Update application status to 'rejected'
    4. Set rejected_at timestamp and rejected_by board member ID
    5. Store rejection_reason and recommended_improvements
    6. Create rejection record in 'approvals' collection with action='reject'
    7. Invalidate any existing approvals
    8. Set reapplication eligibility (30-day wait period if allowed)
    9. Update user's reapplication_count
    10. Send professional rejection email to applicant with:
        - Rejection reason
        - Recommended improvements (if provided)
        - Reapplication instructions (if allowed)
        - Contact information for questions

    Required Fields:
    - rejection_reason: Detailed reason for rejection (required)

    Optional Fields:
    - recommended_improvements: Suggestions for future application
    - allow_reapplication: Whether to allow reapplication (default: True, 30-day wait)

    Only accessible by board members and administrators.
    """
    try:
        # Use the enhanced approval service for rejection
        result = approval_service.reject_application_with_reason(
            application_id=str(application_id),
            rejected_by_user_id=str(current_user["id"]),
            rejection_reason=request.rejection_reason,
            recommended_improvements=request.recommended_improvements,
            allow_reapplication=request.allow_reapplication
        )

        logger.info(
            f"Board member {current_user['email']} rejected application {application_id}. "
            f"Allow reapplication: {request.allow_reapplication}. "
            f"Invalidated {result.get('approvals_invalidated', 0)} approvals."
        )

        # Build response message
        message_parts = ["Application has been rejected"]
        if request.allow_reapplication:
            reapp_date = result.get('reapplication_allowed_at')
            if reapp_date:
                message_parts.append(f"Applicant can reapply after {reapp_date}")
        else:
            message_parts.append("Applicant cannot reapply")

        return ApprovalResponse(
            application_id=application_id,
            status=ApplicationStatus.REJECTED,
            approvals_count=0,
            approvals_needed=2,
            message=". ".join(message_parts)
        )

    except ValueError as e:
        # Validation error (e.g., empty rejection reason)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject application: {str(e)}"
        )


@router.post(
    "/{application_id}/request-info",
    response_model=ApprovalResponse,
    summary="Request additional information",
    description="Request additional information from applicant (board members and admins only)"
)
async def request_additional_info(
    application_id: UUID,
    request: RequestInfoRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"]))
):
    """
    Request additional information from an applicant.

    Workflow:
    1. Verify board member has permission
    2. Create information request record
    3. Send email to applicant with the request

    Only accessible by board members and administrators.
    """
    # Fetch application
    application = await get_application_by_id(application_id)

    # Verify application is in correct status
    if application.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot request info for application in '{application.status}' status"
        )

    # Create information request record
    approval = Approval(
        application_id=application_id,
        approver_id=current_user["id"],
        status=ApprovalStatus.PENDING,
        notes=f"INFO REQUEST: {request.message}",
        approved_at=None
    )

    try:
        # Save request to ZeroDB
        zerodb_client.insert_document(
            collection="approvals",
            document=approval.model_dump(mode="json")
        )

        # Send email notification
        try:
            email_service.send_application_info_request_email(
                email=application.email,
                applicant_name=f"{application.first_name} {application.last_name}",
                request_message=request.message,
                reviewer_name=current_user.get("email", "Board Member")
            )
        except Exception as e:
            logger.error(f"Failed to send info request email: {e}")
            # Don't fail the request if email fails

        logger.info(f"Board member {current_user['email']} requested info for application {application_id}")

        return ApprovalResponse(
            application_id=application_id,
            status=application.status,
            approvals_count=await count_approvals(application_id),
            approvals_needed=2,
            message="Information request sent to applicant"
        )

    except Exception as e:
        logger.error(f"Error requesting info for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send information request"
        )


@router.post(
    "/{application_id}/appeal",
    response_model=ApprovalResponse,
    summary="Submit appeal for rejected application",
    description="Submit an appeal for a rejected membership application (applicant only)"
)
async def submit_application_appeal(
    application_id: UUID,
    request: AppealRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit an appeal for a rejected application.

    Workflow (US-018 Enhancement):
    1. Verify application exists and is rejected
    2. Verify user is the application owner
    3. Check if appeal already submitted
    4. Store appeal reason in application
    5. Mark appeal_submitted flag as true
    6. Set appeal_submitted_at timestamp
    7. Create audit log entry
    8. Notify admins of new appeal (future enhancement)

    Appeals require admin review and can potentially overturn a rejection.

    Required Fields:
    - appeal_reason: Detailed reason for the appeal

    Only accessible by the application owner.

    Example appeal reasons:
    - "I have completed the recommended training"
    - "I have addressed all feedback from the initial review"
    - "Additional information that was not available during initial review"
    """
    try:
        # Fetch application
        application = await get_application_by_id(application_id)

        # Verify user is the application owner
        if application.user_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only appeal your own applications"
            )

        # Use the approval service for appeal submission
        result = approval_service.submit_appeal(
            application_id=str(application_id),
            appeal_reason=request.appeal_reason
        )

        logger.info(
            f"User {current_user['email']} submitted appeal for application {application_id}"
        )

        return ApprovalResponse(
            application_id=application_id,
            status=ApplicationStatus.REJECTED,  # Status remains rejected until admin reviews
            approvals_count=0,
            approvals_needed=2,
            message="Appeal has been submitted and will be reviewed by an administrator"
        )

    except ValueError as e:
        # Validation error (e.g., empty appeal reason)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting appeal for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit appeal: {str(e)}"
        )
