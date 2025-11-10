"""
WWMAA Authorization Middleware Package

This package provides authentication and authorization middleware for the WWMAA backend.

Modules:
- auth_middleware: JWT authentication and role-based access control
- permissions: Resource-level permission checks

Quick Start:
    from backend.middleware.auth_middleware import CurrentUser, RoleChecker
    from backend.middleware.permissions import can_edit_event, can_approve_application

    # Use in FastAPI routes
    @app.get("/profile")
    async def get_profile(current_user: dict = Depends(CurrentUser())):
        return current_user

    # Check resource permissions
    if can_edit_event(current_user, event):
        # Allow edit
"""

from backend.middleware.auth_middleware import (
    # FastAPI Dependencies
    CurrentUser,
    RoleChecker,
    get_current_user,
    get_optional_user,

    # Token utilities
    create_access_token,
    create_refresh_token,
    decode_token,

    # Decorators
    require_auth,
    require_role,
    require_admin,
    require_board_member,
    require_instructor,
    require_member,

    # Utilities
    has_role_level,
    check_role_permission,
)

from backend.middleware.permissions import (
    # Ownership checks
    is_resource_owner,
    is_profile_owner,

    # Application permissions
    can_approve_application,
    can_edit_application,
    can_view_application,

    # Event permissions
    can_view_event,
    can_edit_event,
    can_delete_event,

    # Profile permissions
    can_view_member_data,
    can_edit_profile,

    # Training session permissions
    can_view_training_session,
    can_edit_training_session,

    # Media asset permissions
    can_view_media_asset,
    can_edit_media_asset,

    # Enforcement helpers
    require_permission,
    require_ownership,
    filter_by_visibility,
)

__all__ = [
    # FastAPI Dependencies
    "CurrentUser",
    "RoleChecker",
    "get_current_user",
    "get_optional_user",

    # Token utilities
    "create_access_token",
    "create_refresh_token",
    "decode_token",

    # Decorators
    "require_auth",
    "require_role",
    "require_admin",
    "require_board_member",
    "require_instructor",
    "require_member",

    # Role utilities
    "has_role_level",
    "check_role_permission",

    # Ownership checks
    "is_resource_owner",
    "is_profile_owner",

    # Application permissions
    "can_approve_application",
    "can_edit_application",
    "can_view_application",

    # Event permissions
    "can_view_event",
    "can_edit_event",
    "can_delete_event",

    # Profile permissions
    "can_view_member_data",
    "can_edit_profile",

    # Training session permissions
    "can_view_training_session",
    "can_edit_training_session",

    # Media asset permissions
    "can_view_media_asset",
    "can_edit_media_asset",

    # Enforcement helpers
    "require_permission",
    "require_ownership",
    "filter_by_visibility",
]
