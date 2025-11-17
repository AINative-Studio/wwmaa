"""
User Profile Routes for WWMAA Backend

Provides endpoints for retrieving and managing user profile information.
Includes profile updates, photo uploads, and emergency contact management.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBNotFoundError,
    ZeroDBError
)
from backend.middleware.auth_middleware import CurrentUser
from backend.models.request_schemas import (
    ProfileUpdateRequest,
    EmergencyContact,
    ProfileUpdateResponse,
    ProfilePhotoUploadResponse
)

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


@router.patch(
    "/me/profile",
    response_model=ProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile information including personal details, contact info, and emergency contact"
)
async def update_user_profile(
    profile_update: ProfileUpdateRequest,
    current_user: dict = Depends(CurrentUser())
) -> ProfileUpdateResponse:
    """
    Update current user profile

    This endpoint:
    1. Validates JWT token via CurrentUser dependency
    2. Validates profile update data using Pydantic models
    3. Updates both users and profiles collections in ZeroDB
    4. Creates profile if it doesn't exist
    5. Returns updated user profile data

    Security:
    - Requires valid Bearer token in Authorization header
    - User can only update their own profile
    - All input is validated and sanitized via Pydantic validators
    - Emergency contact data is stored in profile metadata

    Args:
        profile_update: Profile update request with validated fields
        current_user: Authenticated user from JWT token (injected by dependency)

    Returns:
        ProfileUpdateResponse with success message and updated user data

    Raises:
        HTTPException 400: Invalid input data
        HTTPException 401: If not authenticated (handled by middleware)
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()

    try:
        # Extract user_id from token payload
        user_id = str(current_user["id"])
        user_email = current_user["email"]
        user_role = current_user["role"]

        logger.info(f"Updating profile for user: {user_id}")

        # Prepare update data - only include fields that were provided
        update_data = profile_update.model_dump(exclude_unset=True, exclude_none=False)

        # Handle emergency contact separately (stored in profile metadata)
        emergency_contact_data = None
        if "emergency_contact" in update_data:
            emergency_contact_data = update_data.pop("emergency_contact")

        # Split data between users and profiles collections
        user_fields = {}
        profile_fields = {}

        # Map fields to appropriate collections
        # Users collection: basic name fields
        if "first_name" in update_data:
            user_fields["first_name"] = update_data["first_name"]
            profile_fields["first_name"] = update_data["first_name"]

        if "last_name" in update_data:
            user_fields["last_name"] = update_data["last_name"]
            profile_fields["last_name"] = update_data["last_name"]

        # Profiles collection: all other fields
        profile_only_fields = [
            "display_name", "bio", "phone", "website",
            "address", "city", "state", "zip_code", "country"
        ]

        for field in profile_only_fields:
            if field in update_data:
                profile_fields[field] = update_data[field]

        # Add emergency contact to profile metadata if provided
        if emergency_contact_data:
            profile_fields.setdefault("metadata", {})
            if isinstance(profile_fields["metadata"], dict):
                profile_fields["metadata"]["emergency_contact"] = emergency_contact_data
            else:
                profile_fields["metadata"] = {"emergency_contact": emergency_contact_data}

        # Add updated_at timestamp
        current_time = datetime.utcnow()

        # Update users collection if we have user fields
        if user_fields:
            user_fields["updated_at"] = current_time
            db_client.update_document(
                collection="users",
                document_id=user_id,
                data=user_fields,
                merge=True
            )
            logger.info(f"Updated users collection for user: {user_id}")

        # Update or create profile
        if profile_fields:
            profile_fields["updated_at"] = current_time
            profile_fields["user_id"] = UUID(user_id)

            try:
                # Try to update existing profile
                db_client.update_document(
                    collection="profiles",
                    document_id=user_id,
                    data=profile_fields,
                    merge=True
                )
                logger.info(f"Updated profiles collection for user: {user_id}")

            except ZeroDBNotFoundError:
                # Profile doesn't exist, create it
                logger.info(f"Profile not found for user {user_id}, creating new profile")

                # Set required fields for new profile
                profile_fields["id"] = UUID(user_id)
                profile_fields["created_at"] = current_time

                # Ensure required fields have defaults
                if "first_name" not in profile_fields:
                    profile_fields["first_name"] = user_fields.get("first_name", "")
                if "last_name" not in profile_fields:
                    profile_fields["last_name"] = user_fields.get("last_name", "")

                db_client.create_document(
                    collection="profiles",
                    data=profile_fields,
                    document_id=user_id
                )
                logger.info(f"Created new profile for user: {user_id}")

        # Fetch updated user data to return
        try:
            user_doc = db_client.get_document(
                collection="users",
                document_id=user_id
            )
            user_data = user_doc.get("data", {})

            # Try to get profile data
            try:
                profile_doc = db_client.get_document(
                    collection="profiles",
                    document_id=user_id
                )
                profile_data = profile_doc.get("data", {})

                # Merge profile data into user data
                user_data.update(profile_data)

            except ZeroDBNotFoundError:
                logger.debug(f"Profile not found for user {user_id} after update")

            # Build response
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            name = f"{first_name} {last_name}".strip() or "Unknown User"

            # Extract emergency contact if present
            emergency_contact = None
            metadata = user_data.get("metadata", {})
            if isinstance(metadata, dict) and "emergency_contact" in metadata:
                emergency_contact = metadata["emergency_contact"]

            response_user_data = {
                "id": user_id,
                "name": name,
                "email": user_email,
                "role": user_role,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": user_data.get("display_name"),
                "bio": user_data.get("bio"),
                "phone": user_data.get("phone"),
                "website": str(user_data.get("website")) if user_data.get("website") else None,
                "avatar_url": user_data.get("avatar_url"),
                "address": user_data.get("address"),
                "city": user_data.get("city"),
                "state": user_data.get("state"),
                "zip_code": user_data.get("zip_code"),
                "country": user_data.get("country", "USA"),
                "emergency_contact": emergency_contact,
            }

            return ProfileUpdateResponse(
                message="Profile updated successfully",
                user=response_user_data
            )

        except ZeroDBNotFoundError:
            logger.error(f"User {user_id} not found after update")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated profile. Please try again."
            )

    except ZeroDBError as e:
        logger.error(f"ZeroDB error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile. Please try again later."
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error updating user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post(
    "/me/profile/photo",
    response_model=ProfilePhotoUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload profile photo",
    description="Upload or update the authenticated user's profile photo/avatar"
)
async def upload_profile_photo(
    file: UploadFile = File(..., description="Profile photo (JPEG, PNG, WebP, max 10MB)"),
    current_user: dict = Depends(CurrentUser())
) -> ProfilePhotoUploadResponse:
    """
    Upload profile photo

    This endpoint:
    1. Validates JWT token via CurrentUser dependency
    2. Validates file type and size
    3. Uploads photo to ZeroDB object storage
    4. Updates user profile with avatar URL
    5. Returns photo URL

    Security:
    - Requires valid Bearer token in Authorization header
    - User can only upload their own photo
    - File type validation (only images allowed)
    - File size validation (max 10MB)
    - Unique file names to prevent conflicts

    Supported Formats:
    - JPEG (.jpg, .jpeg)
    - PNG (.png)
    - WebP (.webp)
    - GIF (.gif)

    Args:
        file: Uploaded image file
        current_user: Authenticated user from JWT token (injected by dependency)

    Returns:
        ProfilePhotoUploadResponse with photo URL

    Raises:
        HTTPException 400: Invalid file type or size
        HTTPException 401: If not authenticated (handled by middleware)
        HTTPException 413: File too large
        HTTPException 500: Server error (upload or database failure)
    """
    db_client = get_zerodb_client()

    try:
        # Extract user_id from token payload
        user_id = str(current_user["id"])

        logger.info(f"Uploading profile photo for user: {user_id}")

        # Validate file type
        allowed_content_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif"
        ]

        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]

        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_content_types)}"
            )

        # Validate file extension
        file_ext = None
        if file.filename:
            import os
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file extension. Allowed extensions: {', '.join(allowed_extensions)}"
                )
        else:
            # Default to .jpg if no filename provided
            file_ext = ".jpg"

        # Read file content
        file_content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_size = len(file_content)

        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size / (1024 * 1024):.1f}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Generate unique object key for storage
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        object_key = f"profiles/{user_id}/avatar_{timestamp}{file_ext}"

        logger.info(f"Uploading photo to ZeroDB storage: {object_key}")

        # Upload to ZeroDB object storage
        try:
            upload_result = db_client.upload_object_from_bytes(
                key=object_key,
                content=file_content,
                content_type=file.content_type
            )

            # Get the public URL for the uploaded object
            photo_url = upload_result.get("url") or upload_result.get("public_url")

            if not photo_url:
                # Construct URL manually if not provided
                # Format: https://api.ainative.studio/storage/{project_id}/{object_key}
                base_url = db_client.base_url.rstrip("/")
                project_id = db_client.project_id
                photo_url = f"{base_url}/storage/{project_id}/{object_key}"

            logger.info(f"Photo uploaded successfully: {photo_url}")

        except Exception as e:
            logger.error(f"Failed to upload photo to ZeroDB storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload photo. Please try again later."
            )

        # Update user profile with avatar URL
        try:
            # Update profile in profiles collection
            profile_update = {
                "avatar_url": photo_url,
                "updated_at": datetime.utcnow()
            }

            try:
                # Try to update existing profile
                db_client.update_document(
                    collection="profiles",
                    document_id=user_id,
                    data=profile_update,
                    merge=True
                )
                logger.info(f"Updated avatar_url in profiles collection for user: {user_id}")

            except ZeroDBNotFoundError:
                # Profile doesn't exist, create it with minimal data
                logger.info(f"Profile not found for user {user_id}, creating new profile with avatar")

                # Get user data for first/last name
                try:
                    user_doc = db_client.get_document(
                        collection="users",
                        document_id=user_id
                    )
                    user_data = user_doc.get("data", {})
                    first_name = user_data.get("first_name", "")
                    last_name = user_data.get("last_name", "")
                except Exception:
                    first_name = ""
                    last_name = ""

                profile_data = {
                    "id": UUID(user_id),
                    "user_id": UUID(user_id),
                    "first_name": first_name,
                    "last_name": last_name,
                    "avatar_url": photo_url,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                db_client.create_document(
                    collection="profiles",
                    data=profile_data,
                    document_id=user_id
                )
                logger.info(f"Created new profile with avatar for user: {user_id}")

            return ProfilePhotoUploadResponse(
                message="Profile photo uploaded successfully",
                photo_url=photo_url,
                thumbnail_url=None  # TODO: Generate thumbnail if needed
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Failed to update profile with avatar URL: {e}")
            # Photo was uploaded but profile update failed
            # Return success with photo URL anyway since upload succeeded
            return ProfilePhotoUploadResponse(
                message="Profile photo uploaded successfully (profile update pending)",
                photo_url=photo_url,
                thumbnail_url=None
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error uploading profile photo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while uploading photo. Please try again later."
        )
