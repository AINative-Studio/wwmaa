"""
Admin Dunning Dashboard Routes

Provides administrative endpoints for monitoring and managing the dunning process.
All endpoints require admin authentication.

Endpoints:
- GET /api/admin/dunning/accounts - List all accounts in dunning
- GET /api/admin/dunning/accounts/{user_id} - Get dunning details for specific user
- GET /api/admin/dunning/stats - Get dunning statistics
- POST /api/admin/dunning/{dunning_record_id}/retry - Manually retry dunning reminder
- POST /api/admin/dunning/{dunning_record_id}/cancel - Cancel dunning for an account
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from backend.services.dunning_service import (
    get_dunning_service,
    DunningService,
    DunningStage,
    DunningServiceError
)
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.models.schemas import SubscriptionStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/admin/dunning",
    tags=["admin", "dunning"]
)


# Response Models
class DunningAccountResponse(BaseModel):
    """Response model for dunning account"""
    dunning_record_id: str
    user_id: str
    user_email: str
    subscription_id: str
    current_stage: str
    amount_due: float
    currency: str
    days_past_due: int
    created_at: str
    last_reminder_sent: Optional[str] = None
    reminder_count: int = 0


class DunningStatsResponse(BaseModel):
    """Response model for dunning statistics"""
    total_accounts_in_dunning: int
    by_stage: dict
    total_amount_at_risk: float
    currency: str = "USD"
    average_days_past_due: float


class DunningActionResponse(BaseModel):
    """Response model for dunning actions"""
    success: bool
    message: str
    dunning_record_id: str
    action: str


# Dependency for admin authentication
# TODO: Implement actual admin authentication
async def require_admin_auth():
    """
    Dependency for requiring admin authentication

    This is a placeholder that should be replaced with actual authentication logic.
    In production, this should verify JWT token and check for admin role.
    """
    # TODO: Implement real authentication
    # For now, this is a placeholder
    return {"user_id": "admin", "role": "admin"}


@router.get(
    "/accounts",
    response_model=List[DunningAccountResponse],
    summary="List Accounts in Dunning"
)
async def list_dunning_accounts(
    stage: Optional[str] = Query(None, description="Filter by dunning stage"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin: dict = Depends(require_admin_auth)
):
    """
    List all accounts currently in the dunning process

    Args:
        stage: Optional filter by dunning stage
        limit: Maximum number of results (default 100, max 500)
        offset: Offset for pagination (default 0)
        admin: Admin authentication dependency

    Returns:
        List of accounts in dunning with details

    Raises:
        HTTPException: If query fails
    """
    logger.info(f"Admin {admin.get('user_id')} listing dunning accounts")

    try:
        dunning_service = get_dunning_service()

        # Parse stage filter if provided
        stage_filter = None
        if stage:
            try:
                stage_filter = DunningStage(stage)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid stage: {stage}. Valid stages: "
                           f"{[s.value for s in DunningStage]}"
                )

        # Get accounts in dunning
        accounts = await dunning_service.get_accounts_in_dunning(
            stage_filter=stage_filter,
            limit=limit,
            offset=offset
        )

        # Format response
        response = []
        for account in accounts:
            dunning_record = account['dunning_record']
            user = account['user']

            response.append(DunningAccountResponse(
                dunning_record_id=str(dunning_record.get('id')),
                user_id=str(user.get('id')),
                user_email=user.get('email'),
                subscription_id=str(dunning_record.get('subscription_id')),
                current_stage=dunning_record.get('current_stage'),
                amount_due=dunning_record.get('amount_due'),
                currency=dunning_record.get('currency', 'USD'),
                days_past_due=account['days_past_due'],
                created_at=dunning_record.get('created_at'),
                last_reminder_sent=dunning_record.get('metadata', {}).get('last_reminder_sent'),
                reminder_count=dunning_record.get('reminder_count', 0)
            ))

        logger.info(f"Returning {len(response)} dunning accounts")
        return response

    except DunningServiceError as e:
        logger.error(f"Dunning service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing dunning accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/accounts/{user_id}",
    response_model=DunningAccountResponse,
    summary="Get Dunning Details for User"
)
async def get_user_dunning_details(
    user_id: str,
    admin: dict = Depends(require_admin_auth)
):
    """
    Get dunning details for a specific user

    Args:
        user_id: User ID to look up
        admin: Admin authentication dependency

    Returns:
        Dunning account details

    Raises:
        HTTPException: If user not found or not in dunning
    """
    logger.info(f"Admin {admin.get('user_id')} requesting dunning details for user {user_id}")

    try:
        db = get_zerodb_client()

        # Query dunning records for this user
        results = db.query(
            collection='dunning_records',
            query={'user_id': user_id},
            limit=1
        )

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No dunning record found for user {user_id}"
            )

        dunning_record = results[0]

        # Get user details
        user = db.get(collection='users', id=user_id)

        # Calculate days past due
        from datetime import datetime
        created_at = datetime.fromisoformat(dunning_record.get('created_at'))
        days_past_due = (datetime.utcnow() - created_at).days

        return DunningAccountResponse(
            dunning_record_id=str(dunning_record.get('id')),
            user_id=str(user.get('id')),
            user_email=user.get('email'),
            subscription_id=str(dunning_record.get('subscription_id')),
            current_stage=dunning_record.get('current_stage'),
            amount_due=dunning_record.get('amount_due'),
            currency=dunning_record.get('currency', 'USD'),
            days_past_due=days_past_due,
            created_at=dunning_record.get('created_at'),
            last_reminder_sent=dunning_record.get('metadata', {}).get('last_reminder_sent'),
            reminder_count=dunning_record.get('reminder_count', 0)
        )

    except ZeroDBError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/stats",
    response_model=DunningStatsResponse,
    summary="Get Dunning Statistics"
)
async def get_dunning_stats(
    admin: dict = Depends(require_admin_auth)
):
    """
    Get statistical summary of dunning process

    Args:
        admin: Admin authentication dependency

    Returns:
        Dunning statistics including counts by stage and total at risk

    Raises:
        HTTPException: If query fails
    """
    logger.info(f"Admin {admin.get('user_id')} requesting dunning statistics")

    try:
        db = get_zerodb_client()

        # Query all active dunning records
        results = db.query(
            collection='dunning_records',
            query={
                'current_stage': {
                    '$ne': DunningStage.CANCELED.value
                }
            },
            limit=1000  # Adjust as needed
        )

        # Calculate statistics
        total_accounts = len(results)
        by_stage = {stage.value: 0 for stage in DunningStage}
        total_amount_at_risk = 0.0
        total_days_past_due = 0

        from datetime import datetime
        for record in results:
            stage = record.get('current_stage')
            if stage in by_stage:
                by_stage[stage] += 1

            total_amount_at_risk += record.get('amount_due', 0)

            created_at = datetime.fromisoformat(record.get('created_at'))
            total_days_past_due += (datetime.utcnow() - created_at).days

        average_days_past_due = (
            total_days_past_due / total_accounts if total_accounts > 0 else 0
        )

        return DunningStatsResponse(
            total_accounts_in_dunning=total_accounts,
            by_stage=by_stage,
            total_amount_at_risk=round(total_amount_at_risk, 2),
            currency="USD",
            average_days_past_due=round(average_days_past_due, 1)
        )

    except ZeroDBError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{dunning_record_id}/retry",
    response_model=DunningActionResponse,
    summary="Manually Retry Dunning Reminder"
)
async def retry_dunning_reminder(
    dunning_record_id: str,
    stage: str = Query(..., description="Stage to retry (e.g., 'first_reminder')"),
    admin: dict = Depends(require_admin_auth)
):
    """
    Manually retry a dunning reminder for a specific account

    This endpoint allows admins to manually trigger a dunning email
    outside the normal schedule.

    Args:
        dunning_record_id: ID of the dunning record
        stage: Dunning stage to process
        admin: Admin authentication dependency

    Returns:
        Action result

    Raises:
        HTTPException: If retry fails
    """
    logger.info(
        f"Admin {admin.get('user_id')} manually retrying dunning reminder "
        f"{dunning_record_id} for stage {stage}"
    )

    try:
        # Parse stage
        try:
            stage_enum = DunningStage(stage)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage: {stage}. Valid stages: "
                       f"{[s.value for s in DunningStage]}"
            )

        # Process dunning reminder
        dunning_service = get_dunning_service()
        result = await dunning_service.process_dunning_reminder(
            dunning_record_id=dunning_record_id,
            stage=stage_enum
        )

        if result.get('success'):
            return DunningActionResponse(
                success=True,
                message=f"Dunning reminder processed successfully for stage {stage}",
                dunning_record_id=dunning_record_id,
                action="retry"
            )
        else:
            return DunningActionResponse(
                success=False,
                message=result.get('reason', 'Processing failed'),
                dunning_record_id=dunning_record_id,
                action="retry"
            )

    except DunningServiceError as e:
        logger.error(f"Dunning service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{dunning_record_id}/cancel",
    response_model=DunningActionResponse,
    summary="Cancel Dunning for Account"
)
async def cancel_dunning(
    dunning_record_id: str,
    reason: str = Query(..., description="Reason for canceling dunning"),
    admin: dict = Depends(require_admin_auth)
):
    """
    Cancel the dunning process for a specific account

    This endpoint allows admins to stop dunning for an account,
    typically when payment has been received manually or special
    arrangements have been made.

    Args:
        dunning_record_id: ID of the dunning record
        reason: Reason for canceling dunning
        admin: Admin authentication dependency

    Returns:
        Action result

    Raises:
        HTTPException: If cancellation fails
    """
    logger.info(
        f"Admin {admin.get('user_id')} canceling dunning {dunning_record_id}, "
        f"reason: {reason}"
    )

    try:
        db = get_zerodb_client()

        # Update dunning record to canceled
        db.update(
            collection='dunning_records',
            id=dunning_record_id,
            data={
                'current_stage': DunningStage.CANCELED.value,
                'metadata': {
                    'canceled_by': admin.get('user_id'),
                    'cancellation_reason': reason,
                    'canceled_at': datetime.utcnow().isoformat()
                }
            }
        )

        logger.info(f"Dunning record {dunning_record_id} canceled successfully")

        return DunningActionResponse(
            success=True,
            message=f"Dunning canceled: {reason}",
            dunning_record_id=dunning_record_id,
            action="cancel"
        )

    except ZeroDBError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
