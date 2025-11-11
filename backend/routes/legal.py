"""
Legal Routes for WWMAA Backend

Provides endpoints for tracking acceptance of Terms of Service and Privacy Policy.
Implements versioned legal document acceptance tracking in ZeroDB.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.middleware.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/legal", tags=["legal"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AcceptTermsRequest(BaseModel):
    """Request to accept Terms of Service and Privacy Policy"""
    terms_version: str = Field(..., description="Version of terms accepted (e.g., '1.0')")
    privacy_version: str = Field(..., description="Version of privacy policy accepted (e.g., '1.0')")
    ip_address: Optional[str] = Field(None, description="User IP address for audit trail")
    user_agent: Optional[str] = Field(None, description="User agent for audit trail")


class AcceptTermsResponse(BaseModel):
    """Response after accepting terms"""
    message: str
    terms_accepted_version: str
    privacy_accepted_version: str
    accepted_at: str


class GetAcceptanceStatusResponse(BaseModel):
    """Response for checking acceptance status"""
    terms_accepted: bool
    privacy_accepted: bool
    terms_accepted_version: Optional[str]
    privacy_accepted_version: Optional[str]
    terms_accepted_at: Optional[str]
    privacy_accepted_at: Optional[str]
    requires_update: bool
    current_terms_version: str = "1.0"
    current_privacy_version: str = "1.0"


# ============================================================================
# LEGAL ENDPOINTS
# ============================================================================

@router.post(
    "/accept-terms",
    response_model=AcceptTermsResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept Terms of Service and Privacy Policy",
    description="Record user acceptance of current Terms of Service and Privacy Policy versions"
)
async def accept_terms(
    request: AcceptTermsRequest,
    current_user: dict = Depends(get_current_user)
) -> AcceptTermsResponse:
    """
    Record acceptance of Terms of Service and Privacy Policy

    This endpoint:
    1. Validates the authenticated user
    2. Records the versions accepted
    3. Stores acceptance timestamp
    4. Optionally logs IP address and user agent for audit trail
    5. Updates user document in ZeroDB

    Args:
        request: AcceptTermsRequest with version information
        current_user: Authenticated user from JWT token

    Returns:
        AcceptTermsResponse with confirmation

    Raises:
        HTTPException 401: User not authenticated
        HTTPException 404: User not found
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()
    user_id = current_user.get("user_id")

    try:
        logger.info(f"Recording legal acceptance for user {user_id}")

        # Get current timestamp
        accepted_at = datetime.utcnow().isoformat()

        # Prepare update data
        update_data = {
            "terms_accepted_version": request.terms_version,
            "privacy_accepted_version": request.privacy_version,
            "terms_accepted_at": accepted_at,
            "privacy_accepted_at": accepted_at,
            "updated_at": accepted_at
        }

        # Add audit trail data if provided
        if request.ip_address or request.user_agent:
            audit_data = {
                "ip_address": request.ip_address,
                "user_agent": request.user_agent,
                "timestamp": accepted_at
            }
            update_data["legal_acceptance_audit"] = audit_data

        # Update user document
        db_client.update_document(
            collection="users",
            document_id=user_id,
            data=update_data,
            merge=True
        )

        logger.info(
            f"Legal acceptance recorded for user {user_id}: "
            f"Terms v{request.terms_version}, Privacy v{request.privacy_version}"
        )

        return AcceptTermsResponse(
            message="Terms of Service and Privacy Policy acceptance recorded successfully",
            terms_accepted_version=request.terms_version,
            privacy_accepted_version=request.privacy_version,
            accepted_at=accepted_at
        )

    except ZeroDBError as e:
        logger.error(f"ZeroDB error recording legal acceptance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record acceptance. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error recording legal acceptance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get(
    "/acceptance-status",
    response_model=GetAcceptanceStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get legal acceptance status",
    description="Check if user has accepted current versions of Terms and Privacy Policy"
)
async def get_acceptance_status(
    current_user: dict = Depends(get_current_user)
) -> GetAcceptanceStatusResponse:
    """
    Get user's legal acceptance status

    This endpoint:
    1. Retrieves user's accepted versions from ZeroDB
    2. Compares with current required versions
    3. Returns acceptance status and update requirements

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        GetAcceptanceStatusResponse with acceptance details

    Raises:
        HTTPException 401: User not authenticated
        HTTPException 404: User not found
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()
    user_id = current_user.get("user_id")

    try:
        logger.info(f"Fetching legal acceptance status for user {user_id}")

        # Fetch user document
        user_doc = db_client.get_document(
            collection="users",
            document_id=user_id
        )

        if not user_doc:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_data = user_doc.get("data", {})

        # Current required versions (should match legal pages)
        current_terms_version = "1.0"
        current_privacy_version = "1.0"

        # Get user's accepted versions
        terms_accepted_version = user_data.get("terms_accepted_version")
        privacy_accepted_version = user_data.get("privacy_accepted_version")
        terms_accepted_at = user_data.get("terms_accepted_at")
        privacy_accepted_at = user_data.get("privacy_accepted_at")

        # Check if user has accepted current versions
        terms_accepted = terms_accepted_version == current_terms_version
        privacy_accepted = privacy_accepted_version == current_privacy_version

        # User needs to accept if either is outdated or missing
        requires_update = not (terms_accepted and privacy_accepted)

        return GetAcceptanceStatusResponse(
            terms_accepted=terms_accepted,
            privacy_accepted=privacy_accepted,
            terms_accepted_version=terms_accepted_version,
            privacy_accepted_version=privacy_accepted_version,
            terms_accepted_at=terms_accepted_at,
            privacy_accepted_at=privacy_accepted_at,
            requires_update=requires_update,
            current_terms_version=current_terms_version,
            current_privacy_version=current_privacy_version
        )

    except HTTPException:
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching acceptance status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch acceptance status. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching acceptance status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get(
    "/version-info",
    status_code=status.HTTP_200_OK,
    summary="Get current legal document versions",
    description="Get current versions of Terms of Service and Privacy Policy"
)
async def get_version_info() -> dict:
    """
    Get current legal document version information

    This is a public endpoint that returns the current versions
    of Terms of Service and Privacy Policy.

    Returns:
        Dictionary with version information and last updated dates
    """
    return {
        "terms_of_service": {
            "version": "1.0",
            "last_updated": "2025-01-01",
            "effective_date": "2025-01-01"
        },
        "privacy_policy": {
            "version": "1.0",
            "last_updated": "2025-01-01",
            "effective_date": "2025-01-01"
        }
    }
