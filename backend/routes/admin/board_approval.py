"""
Board Approval Routes for WWMAA Backend

Provides board member voting functionality for membership applications.
Implements two-board approval workflow requiring 2 approvals for final approval.

Endpoints:
- GET /api/admin/board/applications/pending - Get pending applications for voting
- POST /api/admin/board/applications/{id}/vote - Cast vote (approve/reject)
- GET /api/admin/board/applications/{id}/votes - Get vote history
- GET /api/admin/board/stats - Get board member voting statistics
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from backend.services.board_approval_service import (
    get_board_approval_service,
    BoardApprovalService,
    BoardApprovalError,
    AlreadyVotedError,
    InvalidStatusError
)
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import (
    User,
    UserRole,
    Application,
    Approval,
    ApprovalAction,
    ApprovalStatus,
    ApplicationStatus
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/admin/board",
    tags=["admin-board-approval"]
)


# ============================================================================
# PERMISSION HELPERS
# ============================================================================

def require_board_member(current_user: User = Depends(get_current_user)) -> User:
    """
    Require board member or admin role for board voting access

    Args:
        current_user: Currently authenticated user

    Returns:
        User object if board member or admin

    Raises:
        HTTPException: If user is not board member or admin
    """
    if current_user.role not in [UserRole.BOARD_MEMBER.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Board member or admin role required."
        )
    return current_user


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VoteRequest(BaseModel):
    """Request model for casting a vote"""
    action: ApprovalAction = Field(..., description="Vote action: APPROVE or REJECT")
    notes: Optional[str] = Field(None, description="Optional vote notes/comments", max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "action": "APPROVE",
                "notes": "Excellent application. Strong martial arts background."
            }
        }


class VoteResponse(BaseModel):
    """Response model for vote submission"""
    application_id: str = Field(..., description="Application ID")
    vote: str = Field(..., description="Vote result: APPROVED or REJECTED")
    approval_count: int = Field(..., description="Current approval count")
    required_approvals: int = Field(..., description="Required approvals for full approval")
    application_status: ApplicationStatus = Field(..., description="Updated application status")
    fully_approved: bool = Field(..., description="Whether application is fully approved")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "550e8400-e29b-41d4-a716-446655440000",
                "vote": "APPROVED",
                "approval_count": 1,
                "required_approvals": 2,
                "application_status": "UNDER_REVIEW",
                "fully_approved": False,
                "message": "Vote cast successfully. Application needs 1 more approval."
            }
        }


class PendingApplicationResponse(BaseModel):
    """Response model for pending applications list"""
    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    email: str
    status: ApplicationStatus
    submitted_at: Optional[datetime]
    approval_count: int
    required_approvals: int
    rejection_count: int
    board_review_started_at: Optional[datetime]

    class Config:
        from_attributes = True


class VoteHistoryItem(BaseModel):
    """Individual vote in history"""
    id: UUID
    approver_id: UUID
    action: ApprovalAction
    status: ApprovalStatus
    vote_cast_at: Optional[datetime]
    sequence: int
    notes: Optional[str]

    class Config:
        from_attributes = True


class VoteHistoryResponse(BaseModel):
    """Response model for vote history"""
    application_id: UUID
    votes: List[VoteHistoryItem]
    total_votes: int

    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "550e8400-e29b-41d4-a716-446655440000",
                "votes": [
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440001",
                        "approver_id": "770e8400-e29b-41d4-a716-446655440002",
                        "action": "APPROVE",
                        "status": "APPROVED",
                        "vote_cast_at": "2025-01-14T10:30:00",
                        "sequence": 1,
                        "notes": "Strong application"
                    }
                ],
                "total_votes": 1
            }
        }


class BoardStatsResponse(BaseModel):
    """Response model for board member statistics"""
    board_member_id: UUID
    total_votes: int
    approved: int
    rejected: int
    pending: int

    class Config:
        json_schema_extra = {
            "example": {
                "board_member_id": "770e8400-e29b-41d4-a716-446655440002",
                "total_votes": 15,
                "approved": 12,
                "rejected": 2,
                "pending": 1
            }
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/applications/pending",
    response_model=List[PendingApplicationResponse],
    summary="Get Pending Applications",
    description="Retrieve applications pending this board member's vote. "
                "Returns applications in UNDER_REVIEW status that the board member has not yet voted on.",
    responses={
        200: {
            "description": "Pending applications retrieved successfully"
        },
        403: {
            "description": "Not authorized - board member role required"
        },
        500: {
            "description": "Server error retrieving applications"
        }
    }
)
async def get_pending_applications(
    current_user: User = Depends(require_board_member),
    service: BoardApprovalService = Depends(get_board_approval_service)
) -> List[PendingApplicationResponse]:
    """
    Get applications pending this board member's vote.

    Returns applications that:
    - Are in UNDER_REVIEW status
    - Have pending_board_review = True
    - Board member has not yet voted on

    Args:
        current_user: Currently authenticated board member
        service: Board approval service instance

    Returns:
        List of pending applications
    """
    try:
        applications = service.get_pending_applications_for_board_member(current_user.id)

        logger.info(
            f"Board member {current_user.id} retrieved {len(applications)} pending applications"
        )

        return [
            PendingApplicationResponse(
                id=app.id,
                user_id=app.user_id,
                first_name=app.first_name,
                last_name=app.last_name,
                email=app.email,
                status=app.status,
                submitted_at=app.submitted_at,
                approval_count=app.approval_count,
                required_approvals=app.required_approvals,
                rejection_count=app.rejection_count,
                board_review_started_at=app.board_review_started_at
            )
            for app in applications
        ]

    except BoardApprovalError as e:
        logger.error(f"Error retrieving pending applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pending applications: {str(e)}"
        )


@router.post(
    "/applications/{application_id}/vote",
    response_model=VoteResponse,
    summary="Cast Vote on Application",
    description="Cast a vote (approve or reject) on a membership application. "
                "Board member can only vote once per application. "
                "2 approvals required for final approval, 1 rejection immediately rejects.",
    responses={
        200: {
            "description": "Vote cast successfully"
        },
        400: {
            "description": "Invalid request - already voted or invalid status"
        },
        403: {
            "description": "Not authorized - board member role required"
        },
        404: {
            "description": "Application not found"
        },
        500: {
            "description": "Server error casting vote"
        }
    }
)
async def cast_vote(
    application_id: UUID,
    vote_request: VoteRequest,
    current_user: User = Depends(require_board_member),
    service: BoardApprovalService = Depends(get_board_approval_service)
) -> VoteResponse:
    """
    Cast a vote (approve/reject) on an application.

    Business Rules:
    - Board member can only vote once per application
    - Application must be in UNDER_REVIEW status
    - 2 approvals required for final approval
    - 1 rejection immediately rejects application

    Args:
        application_id: ID of application to vote on
        vote_request: Vote action and optional notes
        current_user: Currently authenticated board member
        service: Board approval service instance

    Returns:
        Vote result with updated application status

    Raises:
        400: If already voted or invalid status
        404: If application not found
        500: If database error
    """
    try:
        result = service.cast_vote(
            application_id=application_id,
            board_member_id=current_user.id,
            action=vote_request.action,
            notes=vote_request.notes
        )

        # Generate appropriate message
        if result["fully_approved"]:
            message = "Vote cast successfully. Application is now fully approved!"
        elif result["vote"] == "REJECTED":
            message = "Vote cast successfully. Application has been rejected."
        else:
            remaining = result["required_approvals"] - result["approval_count"]
            message = f"Vote cast successfully. Application needs {remaining} more approval(s)."

        logger.info(
            f"Board member {current_user.id} voted {vote_request.action} "
            f"on application {application_id}"
        )

        return VoteResponse(
            application_id=result["application_id"],
            vote=result["vote"],
            approval_count=result["approval_count"],
            required_approvals=result["required_approvals"],
            application_status=result["application_status"],
            fully_approved=result["fully_approved"],
            message=message
        )

    except AlreadyVotedError as e:
        logger.warning(f"Duplicate vote attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidStatusError as e:
        logger.warning(f"Invalid status for voting: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BoardApprovalError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        logger.error(f"Error casting vote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cast vote: {str(e)}"
        )


@router.get(
    "/applications/{application_id}/votes",
    response_model=VoteHistoryResponse,
    summary="Get Vote History",
    description="Retrieve complete vote history for an application, ordered by sequence. "
                "Provides audit trail of all votes cast.",
    responses={
        200: {
            "description": "Vote history retrieved successfully"
        },
        403: {
            "description": "Not authorized - board member role required"
        },
        500: {
            "description": "Server error retrieving vote history"
        }
    }
)
async def get_vote_history(
    application_id: UUID,
    current_user: User = Depends(require_board_member),
    service: BoardApprovalService = Depends(get_board_approval_service)
) -> VoteHistoryResponse:
    """
    Get complete vote history for an application.

    Returns all votes in chronological order (by sequence).
    Provides complete audit trail of the approval process.

    Args:
        application_id: ID of application
        current_user: Currently authenticated board member
        service: Board approval service instance

    Returns:
        Vote history with all votes
    """
    try:
        votes = service.get_vote_history(application_id)

        logger.info(
            f"Board member {current_user.id} retrieved vote history "
            f"for application {application_id}"
        )

        return VoteHistoryResponse(
            application_id=application_id,
            votes=[
                VoteHistoryItem(
                    id=vote.id,
                    approver_id=vote.approver_id,
                    action=vote.action,
                    status=vote.status,
                    vote_cast_at=vote.vote_cast_at,
                    sequence=vote.sequence,
                    notes=vote.notes
                )
                for vote in votes
            ],
            total_votes=len(votes)
        )

    except BoardApprovalError as e:
        logger.error(f"Error retrieving vote history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vote history: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=BoardStatsResponse,
    summary="Get Board Member Statistics",
    description="Retrieve voting statistics for the current board member. "
                "Includes total votes, approved, rejected, and pending counts.",
    responses={
        200: {
            "description": "Statistics retrieved successfully"
        },
        403: {
            "description": "Not authorized - board member role required"
        },
        500: {
            "description": "Server error retrieving statistics"
        }
    }
)
async def get_board_stats(
    current_user: User = Depends(require_board_member),
    service: BoardApprovalService = Depends(get_board_approval_service)
) -> BoardStatsResponse:
    """
    Get voting statistics for the current board member.

    Returns:
    - Total votes cast
    - Number of approvals
    - Number of rejections
    - Number of pending votes

    Args:
        current_user: Currently authenticated board member
        service: Board approval service instance

    Returns:
        Voting statistics
    """
    try:
        stats = service.get_board_member_stats(current_user.id)

        logger.info(f"Board member {current_user.id} retrieved voting statistics")

        return BoardStatsResponse(
            board_member_id=current_user.id,
            total_votes=stats["total_votes"],
            approved=stats["approved"],
            rejected=stats["rejected"],
            pending=stats["pending"]
        )

    except BoardApprovalError as e:
        logger.error(f"Error retrieving board member stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )
