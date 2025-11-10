"""
Authorization Middleware for WWMAA Backend

This module provides JWT-based authentication and role-based access control (RBAC)
for the FastAPI application. It implements middleware decorators and dependencies
for securing API endpoints.

Key Components:
- require_auth: Validates JWT tokens and adds user info to request
- require_role: Role-based access control decorator
- get_current_user: Extracts authenticated user from request
- CurrentUser: FastAPI dependency for user injection
- RoleChecker: FastAPI dependency for role-based access

Usage:
    from backend.middleware.auth_middleware import require_auth, require_role, CurrentUser

    @app.get("/profile")
    async def get_profile(current_user: User = Depends(CurrentUser())):
        return current_user

    @app.get("/admin/users")
    async def get_users(current_user: User = Depends(RoleChecker(allowed_roles=["admin"]))):
        return {"users": [...]}
"""

from datetime import datetime, timedelta
from typing import Optional, List, Union, Callable
from functools import wraps
from uuid import UUID

from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import ValidationError

from backend.config import get_settings
from backend.models.schemas import User, UserRole

# Initialize settings
settings = get_settings()

# Security scheme for bearer token
security = HTTPBearer()


# ============================================================================
# TOKEN UTILITIES
# ============================================================================

def create_access_token(
    user_id: UUID,
    email: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user_id: User's unique identifier
        email: User's email address
        role: User's role
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token(
        ...     user_id=UUID("..."),
        ...     email="user@example.com",
        ...     role=UserRole.MEMBER
        ... )
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "role": role.value if isinstance(role, UserRole) else role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token for a user.

    Args:
        user_id: User's unique identifier
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string

    Example:
        >>> token = create_refresh_token(user_id=UUID("..."))
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing token payload

    Raises:
        HTTPException: If token is invalid, expired, or malformed

    Example:
        >>> payload = decode_token("eyJ0eXAiOiJKV1QiLCJhbGc...")
        >>> user_id = UUID(payload["sub"])
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_token_from_header(authorization: str) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Extracted token string

    Raises:
        HTTPException: If authorization header is malformed

    Example:
        >>> token = extract_token_from_header("Bearer eyJ0eXAiOiJKV1QiLCJhbGc...")
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# USER EXTRACTION
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Extract and validate the current user from the JWT token.

    This function is used as a FastAPI dependency to get the authenticated user.

    Args:
        credentials: HTTP bearer credentials containing the JWT token

    Returns:
        Dictionary containing user information from token payload

    Raises:
        HTTPException: If token is invalid or user is not authenticated

    Example:
        >>> @app.get("/me")
        >>> async def read_users_me(current_user: dict = Depends(get_current_user)):
        >>>     return current_user
    """
    token = credentials.credentials
    payload = decode_token(token)

    # Validate token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user information
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    if not user_id or not email or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return user information as a dictionary
    return {
        "id": UUID(user_id),
        "email": email,
        "role": role,
        "token_issued_at": payload.get("iat"),
        "token_expires_at": payload.get("exp")
    }


async def get_optional_user(
    request: Request
) -> Optional[dict]:
    """
    Extract user from token if present, otherwise return None.

    This function is useful for endpoints that support both authenticated
    and unauthenticated access.

    Args:
        request: FastAPI request object

    Returns:
        User information dictionary or None if not authenticated

    Example:
        >>> @app.get("/content")
        >>> async def get_content(user: Optional[dict] = Depends(get_optional_user)):
        >>>     if user:
        >>>         # Show member content
        >>>     else:
        >>>         # Show public content
    """
    authorization = request.headers.get("Authorization")

    if not authorization:
        return None

    try:
        token = extract_token_from_header(authorization)
        payload = decode_token(token)

        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        if not user_id or not email or not role:
            return None

        return {
            "id": UUID(user_id),
            "email": email,
            "role": role,
            "token_issued_at": payload.get("iat"),
            "token_expires_at": payload.get("exp")
        }
    except HTTPException:
        return None
    except Exception:
        return None


# ============================================================================
# FASTAPI DEPENDENCIES
# ============================================================================

class CurrentUser:
    """
    FastAPI dependency that injects the current authenticated user.

    Usage:
        >>> @app.get("/profile")
        >>> async def get_profile(current_user: dict = Depends(CurrentUser())):
        >>>     return current_user
    """

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        Extract current user from JWT token.

        Args:
            credentials: HTTP bearer credentials

        Returns:
            User information dictionary

        Raises:
            HTTPException: If user is not authenticated
        """
        return await get_current_user(credentials)


class RoleChecker:
    """
    FastAPI dependency that validates user has required role(s).

    Args:
        allowed_roles: List of roles that are allowed to access the endpoint

    Usage:
        >>> @app.get("/admin/users")
        >>> async def get_users(
        >>>     current_user: dict = Depends(RoleChecker(allowed_roles=["admin"]))
        >>> ):
        >>>     return {"users": [...]}

        >>> @app.get("/board/applications")
        >>> async def get_applications(
        >>>     current_user: dict = Depends(
        >>>         RoleChecker(allowed_roles=["admin", "board_member"])
        >>>     )
        >>> ):
        >>>     return {"applications": [...]}
    """

    def __init__(self, allowed_roles: List[str]):
        """
        Initialize RoleChecker with allowed roles.

        Args:
            allowed_roles: List of role names that are allowed access
        """
        self.allowed_roles = [role.lower() for role in allowed_roles]

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        Validate user has required role.

        Args:
            credentials: HTTP bearer credentials

        Returns:
            User information dictionary

        Raises:
            HTTPException: If user doesn't have required role
        """
        current_user = await get_current_user(credentials)
        user_role = current_user["role"].lower()

        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}",
            )

        return current_user


# ============================================================================
# ROLE-BASED DECORATORS (for non-FastAPI usage)
# ============================================================================

def require_auth(func: Callable) -> Callable:
    """
    Decorator that requires authentication for a function.

    This decorator validates the JWT token and adds user info to kwargs.

    Args:
        func: Function to wrap with authentication requirement

    Returns:
        Wrapped function that validates authentication

    Example:
        >>> @require_auth
        >>> async def protected_function(user: dict, **kwargs):
        >>>     print(f"User {user['email']} is authenticated")

    Note:
        For FastAPI routes, prefer using Depends(CurrentUser()) instead.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract credentials from kwargs (must be passed by caller)
        credentials = kwargs.get("credentials")
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await get_current_user(credentials)
        kwargs["user"] = user

        return await func(*args, **kwargs)

    return wrapper


def require_role(*allowed_roles: str) -> Callable:
    """
    Decorator factory that requires specific role(s) for a function.

    Args:
        *allowed_roles: Variable number of role names that are allowed

    Returns:
        Decorator function that validates role

    Example:
        >>> @require_role("admin", "board_member")
        >>> async def admin_function(user: dict, **kwargs):
        >>>     print(f"User {user['email']} has admin access")

    Note:
        For FastAPI routes, prefer using Depends(RoleChecker()) instead.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract credentials from kwargs (must be passed by caller)
            credentials = kwargs.get("credentials")
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user = await get_current_user(credentials)
            user_role = user["role"].lower()
            allowed_roles_lower = [role.lower() for role in allowed_roles]

            if user_role not in allowed_roles_lower:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
                )

            kwargs["user"] = user

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# CONVENIENCE DECORATORS FOR COMMON ROLES
# ============================================================================

def require_admin(func: Callable) -> Callable:
    """
    Decorator that requires admin role.

    Example:
        >>> @require_admin
        >>> async def delete_user(user: dict, user_id: UUID):
        >>>     # Only admins can delete users
        >>>     pass
    """
    return require_role("admin")(func)


def require_board_member(func: Callable) -> Callable:
    """
    Decorator that requires board_member or admin role.

    Example:
        >>> @require_board_member
        >>> async def approve_application(user: dict, application_id: UUID):
        >>>     # Only board members and admins can approve
        >>>     pass
    """
    return require_role("admin", "board_member")(func)


def require_instructor(func: Callable) -> Callable:
    """
    Decorator that requires instructor, board_member, or admin role.

    Example:
        >>> @require_instructor
        >>> async def create_training_session(user: dict, session_data: dict):
        >>>     # Only instructors and higher can create sessions
        >>>     pass
    """
    return require_role("admin", "board_member", "instructor")(func)


def require_member(func: Callable) -> Callable:
    """
    Decorator that requires member role or higher.

    Example:
        >>> @require_member
        >>> async def view_member_content(user: dict):
        >>>     # Only members and higher can view
        >>>     pass
    """
    return require_role("admin", "board_member", "instructor", "member")(func)


# ============================================================================
# ROLE HIERARCHY UTILITIES
# ============================================================================

ROLE_HIERARCHY = {
    UserRole.PUBLIC: 0,
    UserRole.MEMBER: 1,
    UserRole.INSTRUCTOR: 2,
    UserRole.BOARD_MEMBER: 3,
    UserRole.ADMIN: 4,
}


def has_role_level(user_role: Union[str, UserRole], required_level: Union[str, UserRole]) -> bool:
    """
    Check if a user's role meets or exceeds the required level.

    Args:
        user_role: User's current role
        required_level: Required role level

    Returns:
        True if user role meets or exceeds required level

    Example:
        >>> has_role_level(UserRole.BOARD_MEMBER, UserRole.MEMBER)
        True
        >>> has_role_level(UserRole.MEMBER, UserRole.ADMIN)
        False
    """
    # Convert strings to UserRole enums
    if isinstance(user_role, str):
        user_role = UserRole(user_role.lower())
    if isinstance(required_level, str):
        required_level = UserRole(required_level.lower())

    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level_value = ROLE_HIERARCHY.get(required_level, 0)

    return user_level >= required_level_value


def check_role_permission(
    user_role: Union[str, UserRole],
    allowed_roles: List[Union[str, UserRole]]
) -> bool:
    """
    Check if a user's role is in the list of allowed roles.

    Args:
        user_role: User's current role
        allowed_roles: List of allowed roles

    Returns:
        True if user role is in allowed roles

    Example:
        >>> check_role_permission(
        ...     UserRole.BOARD_MEMBER,
        ...     [UserRole.ADMIN, UserRole.BOARD_MEMBER]
        ... )
        True
    """
    # Convert strings to UserRole enums
    if isinstance(user_role, str):
        user_role = UserRole(user_role.lower())

    normalized_allowed = []
    for role in allowed_roles:
        if isinstance(role, str):
            normalized_allowed.append(UserRole(role.lower()))
        else:
            normalized_allowed.append(role)

    return user_role in normalized_allowed
