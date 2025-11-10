"""
Resource-Level Permissions for WWMAA Backend

This module implements fine-grained permission checks for resource-level access control.
While auth_middleware.py handles role-based authentication, this module handles
authorization for specific resources (applications, events, profiles, etc.).

Key Concepts:
- Resource ownership: Users can modify their own resources
- Role-based permissions: Higher roles have broader access
- Visibility-based access: Public vs members-only content
- Application workflow: Board members can review applications

Permission Functions:
- can_approve_application: Check if user can approve membership applications
- can_edit_event: Check if user can edit a specific event
- can_view_member_data: Check if user can view member profile data
- can_edit_profile: Check if user can edit a profile
- can_view_event: Check if user can view an event based on visibility
- is_resource_owner: Check if user owns a resource
"""

from typing import Optional, Union
from uuid import UUID
from fastapi import HTTPException, status

from backend.models.schemas import (
    UserRole,
    Application,
    Event,
    Profile,
    EventVisibility,
    ApplicationStatus,
    RSVP,
    TrainingSession,
    MediaAsset,
)


# ============================================================================
# OWNERSHIP CHECKS
# ============================================================================

def is_resource_owner(user_id: UUID, resource_owner_id: UUID) -> bool:
    """
    Check if a user owns a specific resource.

    Args:
        user_id: ID of the user to check
        resource_owner_id: ID of the resource owner

    Returns:
        True if user owns the resource

    Example:
        >>> is_resource_owner(
        ...     user_id=UUID("..."),
        ...     resource_owner_id=UUID("...")
        ... )
        True
    """
    return user_id == resource_owner_id


def is_profile_owner(user_id: UUID, profile_user_id: UUID) -> bool:
    """
    Check if a user owns a specific profile.

    Args:
        user_id: ID of the user to check
        profile_user_id: user_id field from the Profile document

    Returns:
        True if user owns the profile

    Example:
        >>> profile = get_profile(profile_id)
        >>> is_profile_owner(current_user["id"], profile.user_id)
    """
    return is_resource_owner(user_id, profile_user_id)


# ============================================================================
# APPLICATION PERMISSIONS
# ============================================================================

def can_approve_application(
    user: dict,
    application: Optional[Application] = None
) -> bool:
    """
    Check if a user can approve membership applications.

    Rules:
    - Admins can approve all applications
    - Board members can approve all applications
    - Other roles cannot approve applications

    Args:
        user: Dictionary containing user info (from auth middleware)
        application: Optional application to check (for future use)

    Returns:
        True if user can approve applications

    Raises:
        HTTPException: If user doesn't have permission

    Example:
        >>> if not can_approve_application(current_user, application):
        >>>     raise HTTPException(status_code=403, detail="Permission denied")
    """
    user_role = UserRole(user["role"].lower())

    # Admin and board members can approve
    if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
        return True

    return False


def can_edit_application(
    user: dict,
    application: Application
) -> bool:
    """
    Check if a user can edit a membership application.

    Rules:
    - Application owner can edit their own application (if DRAFT or SUBMITTED)
    - Admins can edit any application
    - Board members can edit applications under review

    Args:
        user: Dictionary containing user info
        application: Application to check

    Returns:
        True if user can edit the application

    Example:
        >>> if can_edit_application(current_user, application):
        >>>     # Allow edit
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins can edit any application
    if user_role == UserRole.ADMIN:
        return True

    # Board members can edit applications under review
    if user_role == UserRole.BOARD_MEMBER:
        if application.status in [
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.SUBMITTED
        ]:
            return True

    # Owners can edit their own applications if DRAFT or SUBMITTED
    if is_resource_owner(user_id, application.user_id):
        if application.status in [ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED]:
            return True

    return False


def can_view_application(
    user: dict,
    application: Application
) -> bool:
    """
    Check if a user can view a membership application.

    Rules:
    - Application owner can view their own application
    - Admins can view all applications
    - Board members can view all applications
    - Others cannot view applications

    Args:
        user: Dictionary containing user info
        application: Application to check

    Returns:
        True if user can view the application

    Example:
        >>> if not can_view_application(current_user, application):
        >>>     raise HTTPException(status_code=404)
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins and board members can view all applications
    if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
        return True

    # Owners can view their own applications
    if is_resource_owner(user_id, application.user_id):
        return True

    return False


# ============================================================================
# EVENT PERMISSIONS
# ============================================================================

def can_view_event(
    event: Event,
    user: Optional[dict] = None
) -> bool:
    """
    Check if a user can view an event based on its visibility.

    Rules:
    - PUBLIC events: Everyone can view
    - MEMBERS_ONLY events: Only authenticated members and higher
    - INVITE_ONLY events: Only instructors, board members, and admins
    - Unpublished events: Only creator, instructors, board members, and admins

    Args:
        event: Event to check
        user: Optional user info dictionary (None for unauthenticated users)

    Returns:
        True if user can view the event

    Example:
        >>> if can_view_event(event, current_user):
        >>>     return event
        >>> else:
        >>>     raise HTTPException(status_code=404)
    """
    # Unpublished events are only visible to privileged users
    if not event.is_published:
        if not user:
            return False
        user_role = UserRole(user["role"].lower())
        # Creator, instructors, board members, and admins can see unpublished
        if user["id"] == event.organizer_id or user_role in [
            UserRole.INSTRUCTOR,
            UserRole.BOARD_MEMBER,
            UserRole.ADMIN
        ]:
            return True
        return False

    # Public events are visible to everyone
    if event.visibility == EventVisibility.PUBLIC:
        return True

    # Members-only events require authentication
    if event.visibility == EventVisibility.MEMBERS_ONLY:
        if not user:
            return False
        user_role = UserRole(user["role"].lower())
        # Members and higher can view
        if user_role in [
            UserRole.MEMBER,
            UserRole.INSTRUCTOR,
            UserRole.BOARD_MEMBER,
            UserRole.ADMIN
        ]:
            return True
        return False

    # Invite-only events require instructor level or higher
    if event.visibility == EventVisibility.INVITE_ONLY:
        if not user:
            return False
        user_role = UserRole(user["role"].lower())
        # Instructors and higher can view
        if user_role in [
            UserRole.INSTRUCTOR,
            UserRole.BOARD_MEMBER,
            UserRole.ADMIN
        ]:
            return True
        return False

    return False


def can_edit_event(
    user: dict,
    event: Event
) -> bool:
    """
    Check if a user can edit an event.

    Rules:
    - Event creator/organizer can edit their own events
    - Admins can edit any event
    - Board members can edit any event

    Args:
        user: Dictionary containing user info
        event: Event to check

    Returns:
        True if user can edit the event

    Example:
        >>> if not can_edit_event(current_user, event):
        >>>     raise HTTPException(status_code=403)
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins and board members can edit any event
    if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
        return True

    # Event organizer can edit their own event
    if is_resource_owner(user_id, event.organizer_id):
        return True

    # Instructors assigned to the event can edit
    if user_id in event.instructors:
        return True

    return False


def can_delete_event(
    user: dict,
    event: Event
) -> bool:
    """
    Check if a user can delete an event.

    Rules:
    - Event creator can delete their own events
    - Admins can delete any event
    - Board members can delete any event

    Args:
        user: Dictionary containing user info
        event: Event to check

    Returns:
        True if user can delete the event
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins and board members can delete any event
    if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
        return True

    # Event organizer can delete their own event
    if is_resource_owner(user_id, event.organizer_id):
        return True

    return False


# ============================================================================
# PROFILE PERMISSIONS
# ============================================================================

def can_view_member_data(
    user: dict,
    member_id: UUID,
    is_public_profile: bool = False
) -> bool:
    """
    Check if a user can view member profile data.

    Rules:
    - Public profiles: Everyone can view
    - Private profiles: Only the owner, board members, and admins
    - Own profile: Always viewable

    Args:
        user: Dictionary containing user info
        member_id: ID of the member (user_id from profile)
        is_public_profile: Whether the profile is marked as public

    Returns:
        True if user can view the member data

    Example:
        >>> profile = get_profile(profile_id)
        >>> if not can_view_member_data(
        ...     current_user,
        ...     profile.user_id,
        ...     profile.public_profile
        ... ):
        ...     raise HTTPException(status_code=403)
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Users can always view their own profile
    if user_id == member_id:
        return True

    # Admins and board members can view all profiles
    if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
        return True

    # Public profiles are viewable by everyone
    if is_public_profile:
        return True

    return False


def can_edit_profile(
    user: dict,
    profile: Profile
) -> bool:
    """
    Check if a user can edit a profile.

    Rules:
    - Profile owner can edit their own profile
    - Admins can edit any profile

    Args:
        user: Dictionary containing user info
        profile: Profile to check

    Returns:
        True if user can edit the profile

    Example:
        >>> if not can_edit_profile(current_user, profile):
        >>>     raise HTTPException(status_code=403)
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins can edit any profile
    if user_role == UserRole.ADMIN:
        return True

    # Profile owner can edit their own profile
    if is_profile_owner(user_id, profile.user_id):
        return True

    return False


# ============================================================================
# TRAINING SESSION PERMISSIONS
# ============================================================================

def can_view_training_session(
    training_session: TrainingSession,
    user: Optional[dict] = None
) -> bool:
    """
    Check if a user can view a training session.

    Rules:
    - Public sessions: Everyone can view
    - Members-only sessions: Only authenticated members and higher
    - Instructors and admins can view all sessions

    Args:
        training_session: Training session to check
        user: Optional user info dictionary

    Returns:
        True if user can view the training session

    Example:
        >>> if can_view_training_session(session, current_user):
        >>>     return session
    """
    # Public sessions are visible to everyone
    if training_session.is_public:
        return True

    # Members-only requires authentication
    if training_session.members_only:
        if not user:
            return False
        user_role = UserRole(user["role"].lower())
        # Members and higher can view
        if user_role in [
            UserRole.MEMBER,
            UserRole.INSTRUCTOR,
            UserRole.BOARD_MEMBER,
            UserRole.ADMIN
        ]:
            return True
        return False

    return False


def can_edit_training_session(
    user: dict,
    training_session: TrainingSession
) -> bool:
    """
    Check if a user can edit a training session.

    Rules:
    - Session instructor can edit their own session
    - Assistant instructors can edit the session
    - Admins can edit any session
    - Board members can edit any session

    Args:
        user: Dictionary containing user info
        training_session: Training session to check

    Returns:
        True if user can edit the training session
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins and board members can edit any session
    if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
        return True

    # Session instructor can edit their own session
    if is_resource_owner(user_id, training_session.instructor_id):
        return True

    # Assistant instructors can edit
    if user_id in training_session.assistant_instructors:
        return True

    return False


# ============================================================================
# MEDIA ASSET PERMISSIONS
# ============================================================================

def can_view_media_asset(
    media_asset: MediaAsset,
    user: Optional[dict] = None
) -> bool:
    """
    Check if a user can view a media asset.

    Rules:
    - Public media: Everyone can view
    - Private media: Only users with matching role or the uploader

    Args:
        media_asset: Media asset to check
        user: Optional user info dictionary

    Returns:
        True if user can view the media asset
    """
    # Public media is visible to everyone
    if media_asset.is_public:
        return True

    # Private media requires authentication
    if not user:
        return False

    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Uploader can always view their own media
    if is_resource_owner(user_id, media_asset.uploaded_by):
        return True

    # Check if user's role is in the access_roles list
    if media_asset.access_roles:
        if user_role in media_asset.access_roles:
            return True

    # Admins can view all media
    if user_role == UserRole.ADMIN:
        return True

    return False


def can_edit_media_asset(
    user: dict,
    media_asset: MediaAsset
) -> bool:
    """
    Check if a user can edit a media asset.

    Rules:
    - Uploader can edit their own media
    - Admins can edit any media

    Args:
        user: Dictionary containing user info
        media_asset: Media asset to check

    Returns:
        True if user can edit the media asset
    """
    user_id = user["id"]
    user_role = UserRole(user["role"].lower())

    # Admins can edit any media
    if user_role == UserRole.ADMIN:
        return True

    # Uploader can edit their own media
    if is_resource_owner(user_id, media_asset.uploaded_by):
        return True

    return False


# ============================================================================
# PERMISSION ENFORCEMENT HELPERS
# ============================================================================

def require_permission(
    has_permission: bool,
    error_message: str = "Permission denied"
) -> None:
    """
    Raise HTTPException if permission check fails.

    Args:
        has_permission: Result of permission check
        error_message: Custom error message

    Raises:
        HTTPException: If permission check fails

    Example:
        >>> require_permission(
        ...     can_edit_event(current_user, event),
        ...     "You don't have permission to edit this event"
        ... )
    """
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )


def require_ownership(
    user_id: UUID,
    resource_owner_id: UUID,
    error_message: str = "You don't own this resource"
) -> None:
    """
    Raise HTTPException if user doesn't own the resource.

    Args:
        user_id: ID of the user to check
        resource_owner_id: ID of the resource owner
        error_message: Custom error message

    Raises:
        HTTPException: If user doesn't own the resource

    Example:
        >>> require_ownership(
        ...     current_user["id"],
        ...     application.user_id,
        ...     "You can only edit your own applications"
        ... )
    """
    if not is_resource_owner(user_id, resource_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )


def filter_by_visibility(
    items: list,
    user: Optional[dict] = None,
    visibility_checker: callable = None
) -> list:
    """
    Filter a list of items based on visibility permissions.

    Args:
        items: List of items to filter
        user: Optional user info dictionary
        visibility_checker: Function that checks if user can view item

    Returns:
        Filtered list of items user can view

    Example:
        >>> events = get_all_events()
        >>> visible_events = filter_by_visibility(
        ...     events,
        ...     current_user,
        ...     lambda event, user: can_view_event(event, user)
        ... )
    """
    if not visibility_checker:
        return items

    return [item for item in items if visibility_checker(item, user)]
