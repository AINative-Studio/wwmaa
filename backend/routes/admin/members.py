"""
Admin Members Management Routes

Provides CRUD endpoints for managing members in the admin dashboard.
Only accessible by users with 'admin' role.

Endpoints:
- POST /api/admin/members - Create a new member
- PUT /api/admin/members/:id - Update an existing member
- DELETE /api/admin/members/:id - Delete a member
- GET /api/admin/members - List all members (with pagination and filtering)
- GET /api/admin/members/:id - Get a single member by ID

Security:
- All endpoints require admin authentication
- Input validation prevents SQL injection and XSS
- Email uniqueness is enforced
- Role changes are validated against allowed roles
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr, field_validator

from backend.middleware.auth_middleware import RoleChecker, get_current_user
from backend.models.schemas import User, UserRole, Profile
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError, ZeroDBNotFoundError
from backend.utils.security import hash_password
from backend.utils.validation import (
    validate_password_strength,
    detect_sql_injection,
    strip_html
)

# Initialize router with admin-only access
router = APIRouter(prefix="/api/admin/members", tags=["admin", "members"])

# Initialize logger
logger = logging.getLogger(__name__)

# Get ZeroDB client
# NOTE: Commented out to prevent module-level authentication during imports (breaks tests)
# Use get_zerodb_client() instead
# zerodb_client = get_zerodb_client()


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class MemberCreateRequest(BaseModel):
    """Request schema for creating a new member"""
    email: EmailStr = Field(..., description="Member email address (must be unique)")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name"
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        description="User role (public, member, instructor, board_member, admin)"
    )
    is_active: bool = Field(default=True, description="Account active status")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v):
        """Validate name fields"""
        if detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected in name")
        return strip_html(v).strip()

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is a valid UserRole"""
        if not isinstance(v, UserRole):
            try:
                # Try to convert string to UserRole
                return UserRole(v.lower() if isinstance(v, str) else v)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}")
        return v


class MemberUpdateRequest(BaseModel):
    """Request schema for updating a member"""
    email: Optional[EmailStr] = Field(None, description="Member email address")
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Last name"
    )
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Account active status")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="New password (optional)"
    )

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        if v:
            return v.lower()
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength if provided"""
        if v:
            is_valid, errors = validate_password_strength(v)
            if not is_valid:
                raise ValueError('; '.join(errors))
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v):
        """Validate name fields"""
        if v:
            if detect_sql_injection(v, strict=False):
                raise ValueError("Invalid characters detected in name")
            return strip_html(v).strip()
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is a valid UserRole"""
        if v is not None:
            if not isinstance(v, UserRole):
                try:
                    return UserRole(v.lower() if isinstance(v, str) else v)
                except (ValueError, AttributeError):
                    raise ValueError(f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}")
        return v


class MemberResponse(BaseModel):
    """Response schema for member operations"""
    id: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: str
    updated_at: str
    last_login: Optional[str] = None


class MemberListResponse(BaseModel):
    """Response schema for member list"""
    members: List[MemberResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_member_response(user: dict, profile: Optional[dict] = None) -> dict:
    """
    Format user and profile data into a member response

    Args:
        user: User document from database
        profile: Optional profile document from database

    Returns:
        Formatted member response dictionary
    """
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "is_active": user.get("is_active", True),
        "is_verified": user.get("is_verified", False),
        "first_name": profile.get("first_name") if profile else None,
        "last_name": profile.get("last_name") if profile else None,
        "phone": profile.get("phone") if profile else None,
        "created_at": user["created_at"].isoformat() if isinstance(user.get("created_at"), datetime) else user.get("created_at"),
        "updated_at": user["updated_at"].isoformat() if isinstance(user.get("updated_at"), datetime) else user.get("updated_at"),
        "last_login": user["last_login"].isoformat() if user.get("last_login") and isinstance(user["last_login"], datetime) else user.get("last_login")
    }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new member",
    description="Create a new member with user account and profile. Admin only."
)
async def create_member(
    member_data: MemberCreateRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
):
    """
    Create a new member

    This endpoint:
    1. Validates the email is unique
    2. Hashes the password securely
    3. Creates a user account
    4. Creates an associated profile
    5. Returns the created member data

    **Required fields:**
    - email: Must be unique
    - password: At least 8 characters
    - first_name: Member's first name
    - last_name: Member's last name

    **Optional fields:**
    - role: Defaults to 'member'
    - is_active: Defaults to True
    - phone: Phone number
    """
    try:
        # Check if email already exists
        existing_user = get_zerodb_client().find_one(
            collection_name="users",
            filter_query={"email": member_data.email}
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with email '{member_data.email}' already exists"
            )

        # Hash the password
        password_hash = hash_password(member_data.password)

        # Create user document
        user_data = {
            "email": member_data.email,
            "password_hash": password_hash,
            "role": member_data.role.value,
            "is_active": member_data.is_active,
            "is_verified": False,
            "last_login": None,
            "profile_id": None
        }

        # Insert user
        created_user = get_zerodb_client().insert_one(
            collection_name="users",
            document=user_data
        )

        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

        user_id = created_user["id"]

        # Create profile document
        profile_data = {
            "user_id": str(user_id),
            "first_name": member_data.first_name,
            "last_name": member_data.last_name,
            "phone": member_data.phone,
            "display_name": f"{member_data.first_name} {member_data.last_name}",
            "bio": None,
            "avatar_url": None,
            "city": None,
            "state": None,
            "country": "USA",
            "disciplines": [],
            "ranks": {},
            "instructor_certifications": [],
            "schools_affiliated": [],
            "newsletter_subscribed": False,
            "public_profile": False,
            "event_notifications": True,
            "social_links": {},
            "member_since": datetime.utcnow(),
            "last_activity": None
        }

        # Insert profile
        created_profile = get_zerodb_client().insert_one(
            collection_name="profiles",
            document=profile_data
        )

        if not created_profile:
            # Rollback: delete the user if profile creation fails
            get_zerodb_client().delete_one(
                collection_name="users",
                filter_query={"id": str(user_id)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )

        profile_id = created_profile["id"]

        # Update user with profile_id
        get_zerodb_client().update_one(
            collection_name="users",
            filter_query={"id": str(user_id)},
            update_data={"profile_id": str(profile_id)}
        )

        # Fetch the complete user data
        created_user = get_zerodb_client().find_one(
            collection_name="users",
            filter_query={"id": str(user_id)}
        )

        logger.info(f"Admin {current_user['email']} created new member: {member_data.email}")

        return format_member_response(created_user, created_profile)

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error creating member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create member: {str(e)}"
        )


@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update a member",
    description="Update an existing member's information. Admin only."
)
async def update_member(
    member_id: str,
    member_data: MemberUpdateRequest,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
):
    """
    Update an existing member

    This endpoint allows updating:
    - Email (must remain unique)
    - First and last name
    - Role
    - Active status
    - Phone number
    - Password (optional)

    Only provided fields will be updated.
    """
    try:
        # Validate member_id is a valid UUID
        try:
            UUID(member_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid member ID format"
            )

        # Check if member exists
        existing_user = get_zerodb_client().find_one(
            collection_name="users",
            filter_query={"id": member_id}
        )

        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found"
            )

        # If email is being updated, check for duplicates
        if member_data.email and member_data.email != existing_user["email"]:
            duplicate_user = get_zerodb_client().find_one(
                collection_name="users",
                filter_query={"email": member_data.email}
            )
            if duplicate_user and str(duplicate_user["id"]) != member_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A user with email '{member_data.email}' already exists"
                )

        # Build update data for user
        user_update = {}
        if member_data.email:
            user_update["email"] = member_data.email
        if member_data.role is not None:
            user_update["role"] = member_data.role.value
        if member_data.is_active is not None:
            user_update["is_active"] = member_data.is_active
        if member_data.password:
            user_update["password_hash"] = hash_password(member_data.password)

        user_update["updated_at"] = datetime.utcnow()

        # Update user if there are changes
        if user_update:
            get_zerodb_client().update_one(
                collection_name="users",
                filter_query={"id": member_id},
                update_data=user_update
            )

        # Build update data for profile
        profile_update = {}
        if member_data.first_name:
            profile_update["first_name"] = member_data.first_name
        if member_data.last_name:
            profile_update["last_name"] = member_data.last_name
        if member_data.phone is not None:
            profile_update["phone"] = member_data.phone

        # Update display name if first or last name changed
        if member_data.first_name or member_data.last_name:
            # Get current profile to construct display name
            current_profile = get_zerodb_client().find_one(
                collection_name="profiles",
                filter_query={"user_id": member_id}
            )
            if current_profile:
                first = member_data.first_name or current_profile.get("first_name", "")
                last = member_data.last_name or current_profile.get("last_name", "")
                profile_update["display_name"] = f"{first} {last}".strip()

        profile_update["updated_at"] = datetime.utcnow()

        # Update profile if there are changes
        if profile_update and len(profile_update) > 1:  # More than just updated_at
            get_zerodb_client().update_one(
                collection_name="profiles",
                filter_query={"user_id": member_id},
                update_data=profile_update
            )

        # Fetch updated user and profile
        updated_user = get_zerodb_client().find_one(
            collection_name="users",
            filter_query={"id": member_id}
        )

        updated_profile = get_zerodb_client().find_one(
            collection_name="profiles",
            filter_query={"user_id": member_id}
        )

        logger.info(f"Admin {current_user['email']} updated member: {member_id}")

        return format_member_response(updated_user, updated_profile)

    except HTTPException:
        raise
    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID '{member_id}' not found"
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error updating member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member: {str(e)}"
        )


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Delete a member and their associated profile. Admin only."
)
async def delete_member(
    member_id: str,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
):
    """
    Delete a member

    This endpoint:
    1. Validates the member exists
    2. Deletes the associated profile
    3. Deletes the user account

    **WARNING:** This is a hard delete and cannot be undone.
    """
    try:
        # Validate member_id is a valid UUID
        try:
            UUID(member_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid member ID format"
            )

        # Check if member exists
        existing_user = get_zerodb_client().find_one(
            collection_name="users",
            filter_query={"id": member_id}
        )

        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found"
            )

        # Prevent admin from deleting themselves
        if str(current_user["id"]) == member_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Delete associated profile first
        try:
            get_zerodb_client().delete_one(
                collection_name="profiles",
                filter_query={"user_id": member_id}
            )
        except ZeroDBNotFoundError:
            # Profile might not exist, continue
            logger.warning(f"No profile found for user {member_id}, continuing with deletion")

        # Delete user
        deleted = get_zerodb_client().delete_one(
            collection_name="users",
            filter_query={"id": member_id}
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete member"
            )

        logger.info(f"Admin {current_user['email']} deleted member: {member_id}")

        return None  # 204 No Content

    except HTTPException:
        raise
    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID '{member_id}' not found"
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error deleting member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete member: {str(e)}"
        )


@router.get(
    "",
    response_model=MemberListResponse,
    summary="List all members",
    description="Get a paginated list of all members with optional filtering. Admin only."
)
async def list_members(
    limit: int = Query(10, ge=1, le=100, description="Number of members per page"),
    offset: int = Query(0, ge=0, description="Number of members to skip"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email, first name, or last name"),
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
):
    """
    List all members with pagination and filtering

    **Query Parameters:**
    - limit: Number of results per page (1-100, default 10)
    - offset: Number of results to skip (default 0)
    - role: Filter by role (public, member, instructor, board_member, admin)
    - is_active: Filter by active status (true/false)
    - search: Search by email, first or last name
    """
    try:
        # Build filter query
        filter_query = {}

        if role:
            # Validate role
            try:
                valid_role = UserRole(role.lower())
                filter_query["role"] = valid_role.value
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}"
                )

        if is_active is not None:
            filter_query["is_active"] = is_active

        # Get users with filtering
        users = get_zerodb_client().find_many(
            collection_name="users",
            filter_query=filter_query,
            limit=limit,
            offset=offset,
            sort_by="created_at",
            sort_order="desc"
        )

        # Get total count for pagination
        total_users = get_zerodb_client().count(
            collection_name="users",
            filter_query=filter_query
        )

        # Fetch profiles for all users
        member_responses = []
        for user in users:
            profile = get_zerodb_client().find_one(
                collection_name="profiles",
                filter_query={"user_id": str(user["id"])}
            )

            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                matches = (
                    search_lower in user["email"].lower() or
                    (profile and profile.get("first_name") and search_lower in profile["first_name"].lower()) or
                    (profile and profile.get("last_name") and search_lower in profile["last_name"].lower())
                )
                if not matches:
                    continue

            member_responses.append(format_member_response(user, profile))

        # Adjust total if search filter was applied
        if search:
            total_users = len(member_responses)

        return {
            "members": member_responses,
            "total": total_users,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"ZeroDB error listing members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error listing members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list members: {str(e)}"
        )


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get a member by ID",
    description="Get detailed information about a specific member. Admin only."
)
async def get_member(
    member_id: str,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
):
    """
    Get a single member by ID

    Returns detailed information about the member including:
    - Email and role
    - Active and verification status
    - Profile information (name, phone)
    - Creation and update timestamps
    - Last login time
    """
    try:
        # Validate member_id is a valid UUID
        try:
            UUID(member_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid member ID format"
            )

        # Get user
        user = get_zerodb_client().find_one(
            collection_name="users",
            filter_query={"id": member_id}
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID '{member_id}' not found"
            )

        # Get profile
        profile = get_zerodb_client().find_one(
            collection_name="profiles",
            filter_query={"user_id": member_id}
        )

        return format_member_response(user, profile)

    except HTTPException:
        raise
    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID '{member_id}' not found"
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error getting member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get member: {str(e)}"
        )
