"""
User Profile Routes for WWMAA Backend

Provides endpoints for retrieving and managing user profile information.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBNotFoundError,
    ZeroDBError
)
from backend.middleware.auth_middleware import CurrentUser

# Configure logging
logger = logging.getLogger(__name__)

# Create router with /api prefix
router = APIRouter(prefix="/api", tags=["profile"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CurrentUserResponse(BaseModel):
    """Current user profile response"""
    id: str
    name: str
    email: EmailStr
    role: str
    belt_rank: Optional[str] = None
    dojo: Optional[str] = None
    country: str = "USA"
    locale: str = "en-US"


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the authenticated user's profile information"
)
async def get_current_user_profile(
    current_user: dict = Depends(CurrentUser())
) -> CurrentUserResponse:
    """
    Get current user profile

    This endpoint:
    1. Validates JWT token via CurrentUser dependency
    2. Fetches user data from ZeroDB users collection
    3. Returns complete user profile with extended fields
    4. Falls back to mock data if user not found in database

    Security:
    - Requires valid Bearer token in Authorization header
    - User can only access their own profile
    - Token validation handled by CurrentUser middleware

    Args:
        current_user: Authenticated user from JWT token (injected by dependency)

    Returns:
        CurrentUserResponse with user profile data

    Raises:
        HTTPException 401: If not authenticated (handled by middleware)
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()

    try:
        # Extract user_id from token payload
        user_id = str(current_user["id"])
        user_email = current_user["email"]
        user_role = current_user["role"]

        logger.info(f"Fetching profile for user: {user_id}")

        # Query ZeroDB for user profile
        try:
            user_doc = db_client.get_document(
                collection="users",
                document_id=user_id
            )

            user_data = user_doc.get("data", {})

            # Build name from first_name and last_name
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            name = f"{first_name} {last_name}".strip() or "Unknown User"

            # Try to get profile data for additional fields
            belt_rank = None
            dojo = None
            country = "USA"
            locale = "en-US"

            try:
                profile_doc = db_client.get_document(
                    collection="profiles",
                    document_id=user_id
                )
                profile_data = profile_doc.get("data", {})

                # Extract belt rank from ranks dict (first entry)
                ranks = profile_data.get("ranks", {})
                if ranks:
                    belt_rank = list(ranks.values())[0]

                # Extract dojo from schools list (first entry)
                schools = profile_data.get("schools_affiliated", [])
                if schools:
                    dojo = schools[0]

                country = profile_data.get("country", "USA")
                locale = profile_data.get("locale", "en-US")

            except ZeroDBNotFoundError:
                # Profile not found, use defaults
                logger.debug(f"Profile not found for user {user_id}, using defaults")

            # Extract profile fields
            response = CurrentUserResponse(
                id=user_id,
                name=name,
                email=user_email,
                role=user_role,
                belt_rank=belt_rank,
                dojo=dojo,
                country=country,
                locale=locale
            )

            logger.info(f"Profile retrieved successfully for user: {user_id}")
            return response

        except ZeroDBNotFoundError:
            # User exists in JWT but not in database - return mock data
            logger.warning(
                f"User {user_id} has valid token but not found in database. "
                "Returning mock profile data."
            )

            # Return mock data with authenticated user's info
            return CurrentUserResponse(
                id=user_id,
                name="John Doe",
                email=user_email,
                role=user_role,
                belt_rank="Black Belt (1st Dan)",
                dojo="WWMAA Headquarters",
                country="USA",
                locale="en-US"
            )

    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
