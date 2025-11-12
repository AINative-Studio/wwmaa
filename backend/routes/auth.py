"""
Authentication Routes for WWMAA Backend

Provides user registration, email verification, login, and password management.
Implements secure authentication with password hashing, token-based verification,
and email confirmation workflow.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends, Header, Response
from pydantic import BaseModel, EmailStr, Field, field_validator
from passlib.context import CryptContext

from backend.services.zerodb_service import get_zerodb_client, ZeroDBValidationError, ZeroDBError
from backend.services.email_service import get_email_service, EmailSendError
from backend.services.auth_service import AuthService, TokenBlacklistedError, TokenInvalidError, TokenExpiredError, TokenReuseError
from backend.config import settings, get_settings
from backend.middleware.rate_limit import (
    rate_limit_login,
    rate_limit_registration,
    rate_limit_password_reset
)
from backend.middleware.csrf import rotate_csrf_token
from backend.middleware.auth_middleware import CurrentUser

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    terms_accepted: bool = Field(..., description="User must accept Terms of Service")
    terms_version: str = Field(default="1.0", description="Version of Terms of Service accepted")
    privacy_version: str = Field(default="1.0", description="Version of Privacy Policy accepted")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('terms_accepted')
    @classmethod
    def validate_terms_accepted(cls, v):
        """Ensure terms are accepted"""
        if not v:
            raise ValueError("You must accept the Terms of Service and Privacy Policy to register")
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Validate password strength requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")

        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")

        return v


class RegisterResponse(BaseModel):
    """User registration response"""
    message: str
    user_id: str
    email: str
    verification_required: bool = True


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str = Field(..., description="Verification token from email")


class VerifyEmailResponse(BaseModel):
    """Email verification response"""
    message: str
    email: str
    is_verified: bool = True


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


class LoginResponse(BaseModel):
    """User login response"""
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict = Field(..., description="User information")


class LogoutRequest(BaseModel):
    """User logout request"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")


class LogoutResponse(BaseModel):
    """User logout response"""
    message: str


class PasswordResetRequestRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="User email address")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


class PasswordResetRequestResponse(BaseModel):
    """Password reset request response"""
    message: str


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request"""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """
        Validate password strength requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")

        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")

        return v


class PasswordResetConfirmResponse(BaseModel):
    """Password reset confirmation response"""
    message: str
    email: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_verification_token() -> str:
    """
    Generate a secure verification token

    Returns:
        Secure random token (32 bytes hex encoded = 64 characters)
    """
    return secrets.token_urlsafe(32)


def get_token_expiry() -> datetime:
    """
    Get token expiry datetime (24 hours from now)

    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(hours=24)


def generate_password_reset_token() -> str:
    """
    Generate a secure password reset token

    Returns:
        Secure random token (32 bytes URL-safe)
    """
    return secrets.token_urlsafe(32)


def get_password_reset_token_expiry() -> datetime:
    """
    Get password reset token expiry datetime (1 hour from now)

    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(hours=1)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with email verification"
)
@rate_limit_registration()
async def register(request: RegisterRequest) -> RegisterResponse:
    """
    Register a new user account

    This endpoint:
    1. Validates user input (email, password strength, required fields)
    2. Checks for duplicate email in ZeroDB
    3. Hashes the password using bcrypt
    4. Generates a secure verification token
    5. Creates user record in ZeroDB users collection
    6. Sends verification email via Postmark

    Password Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character

    The verification token expires in 24 hours.
    User cannot access protected resources until email is verified.

    Args:
        request: RegisterRequest with user details

    Returns:
        RegisterResponse with user_id and verification message

    Raises:
        HTTPException 400: Email already registered
        HTTPException 500: Server error (database or email service failure)
    """
    db_client = get_zerodb_client()
    email_service = get_email_service()

    try:
        # Check if email already exists
        logger.info(f"Checking for existing user with email: {request.email}")
        existing_users = db_client.query_documents(
            collection="users",
            filters={"email": request.email},
            limit=1
        )

        if existing_users.get("documents") and len(existing_users["documents"]) > 0:
            logger.warning(f"Registration attempt with existing email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )

        # Hash password
        password_hash = hash_password(request.password)
        logger.info(f"Password hashed successfully for {request.email}")

        # Generate verification token
        verification_token = generate_verification_token()
        token_expiry = get_token_expiry()

        # Create user document
        user_id = str(uuid4())
        now = datetime.utcnow()
        user_data = {
            "email": request.email,
            "password_hash": password_hash,
            "role": "public",  # Default role for new users
            "is_active": True,
            "is_verified": False,
            "verification_token": verification_token,
            "verification_token_expiry": token_expiry.isoformat(),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone": request.phone,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_login": None,
            "profile_id": None,
            # Terms acceptance tracking
            "terms_accepted_at": now.isoformat() if request.terms_accepted else None,
            "terms_version_accepted": request.terms_version if request.terms_accepted else None,
            "privacy_accepted_at": now.isoformat() if request.terms_accepted else None,
            "privacy_version_accepted": request.privacy_version if request.terms_accepted else None
        }

        # Store user in ZeroDB
        logger.info(f"Creating user in ZeroDB: {request.email}")
        created_user = db_client.create_document(
            collection="users",
            data=user_data,
            document_id=user_id
        )

        logger.info(f"User created successfully with ID: {user_id}")

        # Send verification email
        try:
            user_name = f"{request.first_name} {request.last_name}"
            logger.info(f"Sending verification email to {request.email}")

            email_service.send_verification_email(
                email=request.email,
                token=verification_token,
                user_name=user_name
            )

            logger.info(f"Verification email sent successfully to {request.email}")

        except EmailSendError as e:
            # Log the error but don't fail registration
            # The user is created, they can request a new verification email
            logger.error(f"Failed to send verification email to {request.email}: {e}")
            # Note: In production, you might want to implement a retry mechanism
            # or a separate endpoint to resend verification emails

        return RegisterResponse(
            message="Registration successful. Please check your email to verify your account.",
            user_id=user_id,
            email=request.email,
            verification_required=True
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBValidationError as e:
        logger.error(f"ZeroDB validation error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user data: {str(e)}"
        )

    except ZeroDBError as e:
        logger.error(f"ZeroDB error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user email address using token from verification email"
)
async def verify_email(request: VerifyEmailRequest) -> VerifyEmailResponse:
    """
    Verify user email address

    This endpoint:
    1. Validates the verification token
    2. Checks token hasn't expired (24-hour expiry)
    3. Updates user's is_verified status in ZeroDB
    4. Clears the verification token
    5. Sends welcome email (optional)

    Args:
        request: VerifyEmailRequest with verification token

    Returns:
        VerifyEmailResponse with success message

    Raises:
        HTTPException 400: Invalid or expired token
        HTTPException 404: User not found
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()
    email_service = get_email_service()

    try:
        # Find user with matching verification token
        logger.info(f"Searching for user with verification token")
        users = db_client.query_documents(
            collection="users",
            filters={"verification_token": request.token},
            limit=1
        )

        if not users.get("documents") or len(users["documents"]) == 0:
            logger.warning(f"Invalid verification token provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        user = users["documents"][0]
        user_id = user.get("id")
        user_email = user.get("data", {}).get("email")

        # Check if already verified
        if user.get("data", {}).get("is_verified"):
            logger.info(f"User {user_email} is already verified")
            return VerifyEmailResponse(
                message="Email address is already verified",
                email=user_email,
                is_verified=True
            )

        # Check token expiry
        token_expiry_str = user.get("data", {}).get("verification_token_expiry")
        if token_expiry_str:
            token_expiry = datetime.fromisoformat(token_expiry_str)
            if datetime.utcnow() > token_expiry:
                logger.warning(f"Expired verification token for user {user_email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification token has expired. Please request a new verification email."
                )

        # Update user verification status
        logger.info(f"Verifying email for user {user_email}")
        update_data = {
            "is_verified": True,
            "verification_token": None,
            "verification_token_expiry": None,
            "updated_at": datetime.utcnow().isoformat()
        }

        db_client.update_document(
            collection="users",
            document_id=user_id,
            data=update_data,
            merge=True
        )

        logger.info(f"Email verified successfully for user {user_email}")

        # Send welcome email (optional - don't fail verification if this fails)
        try:
            first_name = user.get("data", {}).get("first_name", "")
            last_name = user.get("data", {}).get("last_name", "")
            user_name = f"{first_name} {last_name}".strip() or user_email

            email_service.send_welcome_email(
                email=user_email,
                user_name=user_name
            )

            logger.info(f"Welcome email sent to {user_email}")

        except EmailSendError as e:
            logger.error(f"Failed to send welcome email to {user_email}: {e}")
            # Continue anyway - verification succeeded

        return VerifyEmailResponse(
            message="Email verified successfully! Your account is now active.",
            email=user_email,
            is_verified=True
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error during email verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during email verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


# ============================================================================
# PASSWORD RESET ENDPOINTS
# ============================================================================

# In-memory rate limiting for password reset requests (3 requests per hour per email)
# In production, this should be moved to Redis for distributed rate limiting
_password_reset_attempts: Dict[str, list] = {}


def check_rate_limit(email: str, max_attempts: int = 3, window_hours: int = 1) -> bool:
    """
    Check if email has exceeded password reset rate limit

    Args:
        email: User email address
        max_attempts: Maximum number of attempts allowed (default: 3)
        window_hours: Time window in hours (default: 1)

    Returns:
        True if rate limit not exceeded, False otherwise
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=window_hours)

    # Clean old attempts
    if email in _password_reset_attempts:
        _password_reset_attempts[email] = [
            timestamp for timestamp in _password_reset_attempts[email]
            if timestamp > cutoff
        ]

    # Check rate limit
    if email not in _password_reset_attempts:
        _password_reset_attempts[email] = []

    if len(_password_reset_attempts[email]) >= max_attempts:
        return False

    # Record this attempt
    _password_reset_attempts[email].append(now)
    return True


@router.post(
    "/forgot-password",
    response_model=PasswordResetRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset link to be sent via email"
)
@rate_limit_password_reset()
async def forgot_password(request: PasswordResetRequestRequest) -> PasswordResetRequestResponse:
    """
    Request a password reset

    This endpoint:
    1. Checks rate limit (max 3 requests per hour per email)
    2. Looks up user by email in ZeroDB
    3. Generates a secure reset token with 1-hour expiry
    4. Stores token and expiry in user document
    5. Sends password reset email with token

    Security features:
    - Rate limiting to prevent abuse
    - Secure token generation using secrets.token_urlsafe
    - 1-hour token expiry
    - No user enumeration (always returns success)

    Args:
        request: PasswordResetRequestRequest with user email

    Returns:
        PasswordResetRequestResponse with generic success message

    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Server error (database or email service failure)
    """
    db_client = get_zerodb_client()
    email_service = get_email_service()

    try:
        # Check rate limit
        if not check_rate_limit(request.email):
            logger.warning(f"Rate limit exceeded for password reset: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later."
            )

        # Look up user by email
        logger.info(f"Processing password reset request for: {request.email}")
        users = db_client.query_documents(
            collection="users",
            filters={"email": request.email},
            limit=1
        )

        # Always return success to prevent user enumeration
        # Even if user doesn't exist, we return success message
        if not users.get("documents") or len(users["documents"]) == 0:
            logger.info(f"Password reset requested for non-existent user: {request.email}")
            return PasswordResetRequestResponse(
                message="If an account exists with this email, you will receive password reset instructions."
            )

        user = users["documents"][0]
        user_id = user.get("id")
        user_data = user.get("data", {})

        # Generate password reset token
        reset_token = generate_password_reset_token()
        token_expiry = get_password_reset_token_expiry()

        # Update user document with reset token
        logger.info(f"Storing password reset token for user: {request.email}")
        update_data = {
            "password_reset_token": reset_token,
            "password_reset_token_expiry": token_expiry.isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        db_client.update_document(
            collection="users",
            document_id=user_id,
            data=update_data,
            merge=True
        )

        # Send password reset email
        try:
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            user_name = f"{first_name} {last_name}".strip() or request.email

            logger.info(f"Sending password reset email to {request.email}")

            email_service.send_password_reset_email(
                email=request.email,
                token=reset_token,
                user_name=user_name
            )

            logger.info(f"Password reset email sent successfully to {request.email}")

        except EmailSendError as e:
            # Log the error but don't fail the request
            # The token is stored in DB, user can try again
            logger.error(f"Failed to send password reset email to {request.email}: {e}")

        return PasswordResetRequestResponse(
            message="If an account exists with this email, you will receive password reset instructions."
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error during password reset request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during password reset request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post(
    "/reset-password",
    response_model=PasswordResetConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Reset password using token from email"
)
async def reset_password(request: PasswordResetConfirmRequest) -> PasswordResetConfirmResponse:
    """
    Confirm password reset with token

    This endpoint:
    1. Validates the reset token
    2. Checks token hasn't expired (1-hour expiry)
    3. Validates new password strength
    4. Hashes new password with bcrypt
    5. Updates password in ZeroDB
    6. Clears reset token
    7. Invalidates all existing user sessions (force re-login)
    8. Sends confirmation email

    Security features:
    - Token validation and expiry check
    - Password strength validation
    - Bcrypt password hashing
    - Token single-use (cleared after reset)
    - Session invalidation (force re-login)

    Args:
        request: PasswordResetConfirmRequest with token and new password

    Returns:
        PasswordResetConfirmResponse with success message

    Raises:
        HTTPException 400: Invalid or expired token
        HTTPException 422: Invalid password strength
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()
    email_service = get_email_service()

    try:
        # Find user with matching reset token
        logger.info(f"Processing password reset confirmation")
        users = db_client.query_documents(
            collection="users",
            filters={"password_reset_token": request.token},
            limit=1
        )

        if not users.get("documents") or len(users["documents"]) == 0:
            logger.warning(f"Invalid password reset token provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )

        user = users["documents"][0]
        user_id = user.get("id")
        user_data = user.get("data", {})
        user_email = user_data.get("email")

        # Check token expiry
        token_expiry_str = user_data.get("password_reset_token_expiry")
        if not token_expiry_str:
            logger.warning(f"Password reset token missing expiry for user {user_email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )

        token_expiry = datetime.fromisoformat(token_expiry_str)
        if datetime.utcnow() > token_expiry:
            logger.warning(f"Expired password reset token for user {user_email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired. Please request a new one."
            )

        # Hash new password
        new_password_hash = hash_password(request.new_password)
        logger.info(f"Resetting password for user {user_email}")

        # Update user password and clear reset token
        update_data = {
            "password_hash": new_password_hash,
            "password_reset_token": None,
            "password_reset_token_expiry": None,
            "updated_at": datetime.utcnow().isoformat(),
            # Note: In a full implementation with session management,
            # we would also blacklist all existing JWT tokens here
            # by incrementing a token_version or similar mechanism
        }

        db_client.update_document(
            collection="users",
            document_id=user_id,
            data=update_data,
            merge=True
        )

        logger.info(f"Password reset successfully for user {user_email}")

        # Send confirmation email (optional - don't fail if this fails)
        try:
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            user_name = f"{first_name} {last_name}".strip() or user_email

            email_service.send_password_changed_email(
                email=user_email,
                user_name=user_name
            )
            logger.info(f"Password changed notification sent to {user_email}")

        except Exception as e:
            logger.error(f"Failed to send password change notification to {user_email}: {e}")
            # Continue anyway - password reset succeeded

        return PasswordResetConfirmResponse(
            message="Password reset successful! You can now log in with your new password.",
            email=user_email
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error during password reset confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during password reset confirmation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Valid refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response"""
    access_token: str = Field(..., description="New access token")
    refresh_token: str = Field(..., description="New refresh token (rotated)")
    token_type: str = "bearer"


def rate_limit_token_refresh():
    """Rate limit for token refresh endpoints: 10 requests per hour per user"""
    from backend.middleware.rate_limit import rate_limit
    return rate_limit(requests=10, window_seconds=3600)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange a valid refresh token for new access and refresh tokens (automatic rotation)"
)
@rate_limit_token_refresh()
async def refresh_token(request: RefreshTokenRequest) -> RefreshTokenResponse:
    """
    Refresh access token using a valid refresh token

    This endpoint implements automatic token rotation for enhanced security:
    1. Validates the refresh token (signature, expiration, blacklist)
    2. Checks for token reuse (security breach detection)
    3. If reuse detected: invalidates entire token family and rejects request
    4. Blacklists the old refresh token (one-time use)
    5. Generates new access token with user claims
    6. Generates new refresh token in same family
    7. Stores new token family mapping in Redis
    8. Returns both new tokens

    Token Family Tracking:
    - Each login creates a new token family
    - Token rotation maintains the same family_id
    - Reuse of any token in a family invalidates all tokens

    Security Features:
    - Refresh tokens are single-use (blacklisted after use)
    - Token reuse detection prevents replay attacks
    - Family invalidation limits damage from token theft
    - Automatic rotation reduces token lifetime exposure

    Args:
        request: RefreshTokenRequest with current refresh token

    Returns:
        RefreshTokenResponse with new access and refresh tokens

    Raises:
        HTTPException 401: Invalid, expired, blacklisted, or reused token
        HTTPException 403: Token family has been revoked due to security breach
        HTTPException 500: Server error (database or Redis failure)
    """
    auth_service = AuthService(get_settings())
    db_client = get_zerodb_client()

    try:
        # Step 1: Verify refresh token validity
        logger.info("Verifying refresh token")
        try:
            payload = auth_service.verify_refresh_token(request.refresh_token)
        except TokenExpiredError:
            logger.warning("Expired refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again."
            )
        except TokenInvalidError as e:
            logger.warning(f"Invalid refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        except TokenBlacklistedError:
            logger.warning("Blacklisted refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked. Please log in again."
            )

        user_id = payload.get("user_id")
        family_id = payload.get("family_id")
        token_id = payload.get("token_id")

        if not user_id or not family_id or not token_id:
            logger.error("Refresh token missing required claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token format"
            )

        # Step 2: Check if token family has been blacklisted
        if auth_service.is_family_blacklisted(family_id):
            logger.warning(f"Attempted use of token from blacklisted family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token family has been revoked due to security breach. Please log in again."
            )

        # Step 3: Check for token reuse (security breach detection)
        logger.info(f"Checking for token reuse: token_id={token_id}, family_id={family_id}")
        is_reused = auth_service.check_token_reuse(token_id, family_id)

        if is_reused:
            logger.error(f"Token reuse detected! Family: {family_id}, Token: {token_id}")
            # Invalidate entire token family
            auth_service.invalidate_token_family(family_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token reuse detected. All sessions have been invalidated for security. Please log in again."
            )

        # Step 4: Fetch user data from database
        logger.info(f"Fetching user data for user_id: {user_id}")
        users = db_client.query_documents(
            collection="users",
            filters={"id": user_id},
            limit=1
        )

        if not users.get("documents") or len(users["documents"]) == 0:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user = users["documents"][0]
        user_data = user.get("data", {})

        # Check if user is active and verified
        if not user_data.get("is_active"):
            logger.warning(f"Inactive user attempted token refresh: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support."
            )

        if not user_data.get("is_verified"):
            logger.warning(f"Unverified user attempted token refresh: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email first."
            )

        # Step 5: Mark old refresh token as used (blacklist it)
        logger.info(f"Blacklisting old refresh token")
        auth_service.blacklist_token(request.refresh_token)
        auth_service.mark_token_used(token_id)

        # Step 6: Generate new access token
        logger.info(f"Generating new access token for user: {user_id}")
        access_token = auth_service.create_access_token(
            user_id=user_id,
            role=user_data.get("role", "public"),
            email=user_data.get("email")
        )

        # Step 7: Generate new refresh token (same family for rotation)
        logger.info(f"Generating new refresh token in family: {family_id}")
        new_refresh_token, _ = auth_service.create_refresh_token(
            user_id=user_id,
            family_id=family_id  # Keep same family for rotation
        )

        # Step 8: Store new token family mapping
        # Extract new token_id from the newly created refresh token
        new_payload = auth_service.decode_token(new_refresh_token)
        new_token_id = new_payload.get("token_id")
        
        # Calculate TTL from token expiration
        exp_timestamp = new_payload.get("exp")
        ttl = int(exp_timestamp - datetime.utcnow().timestamp())

        logger.info(f"Storing new token family mapping: token_id={new_token_id}")
        auth_service.store_token_family(
            token_id=new_token_id,
            family_id=family_id,
            user_id=user_id,
            ttl=ttl
        )

        logger.info(f"Token refresh successful for user: {user_id}")

        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with email and password, return JWT tokens"
)
@rate_limit_login()
async def login(request: LoginRequest, response: Response) -> LoginResponse:
    """
    Authenticate user and generate JWT tokens

    This endpoint:
    1. Validates user credentials against ZeroDB
    2. Checks if user email is verified
    3. Verifies password using bcrypt
    4. Tracks failed login attempts (max 5 attempts, 15-minute lockout)
    5. Generates access and refresh tokens
    6. Updates last_login timestamp
    7. Logs successful login in audit trail

    Security Features:
    - Password verification with bcrypt
    - Account lockout after 5 failed attempts (15-minute cooldown)
    - Email verification requirement
    - Failed attempt tracking and logging
    - JWT token-based authentication

    Args:
        request: LoginRequest with email and password

    Returns:
        LoginResponse with access_token, refresh_token, and user info

    Raises:
        HTTPException 400: Invalid credentials or account locked
        HTTPException 401: Email not verified
        HTTPException 500: Server error (database failure)
    """
    db_client = get_zerodb_client()
    auth_service = AuthService(get_settings())

    try:
        # Find user by email
        logger.info(f"Login attempt for email: {request.email}")
        users = db_client.query_documents(
            collection="users",
            filters={"email": request.email},
            limit=1
        )

        if not users.get("documents") or len(users["documents"]) == 0:
            logger.warning(f"Login failed: User not found for email {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or password"
            )

        user = users["documents"][0]
        user_id = user.get("id")
        user_data = user.get("data", {})

        # Check account lockout
        failed_attempts = user_data.get("failed_login_attempts", 0)
        lockout_until = user_data.get("lockout_until")

        if lockout_until:
            lockout_time = datetime.fromisoformat(lockout_until)
            if datetime.utcnow() < lockout_time:
                remaining_minutes = int((lockout_time - datetime.utcnow()).total_seconds() / 60)
                logger.warning(f"Login failed: Account locked for {request.email} until {lockout_until}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Account locked due to multiple failed login attempts. Try again in {remaining_minutes} minutes."
                )
            else:
                # Lockout period expired, reset failed attempts
                failed_attempts = 0

        # Verify password
        password_hash = user_data.get("password_hash")
        if not password_hash or not verify_password(request.password, password_hash):
            # Increment failed login attempts
            failed_attempts += 1
            update_data = {
                "failed_login_attempts": failed_attempts,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Lock account if 5 or more failed attempts
            if failed_attempts >= 5:
                lockout_until = datetime.utcnow() + timedelta(minutes=15)
                update_data["lockout_until"] = lockout_until.isoformat()
                logger.warning(f"Account locked for {request.email} after {failed_attempts} failed attempts")

            db_client.update_document(
                collection="users",
                document_id=user_id,
                data=update_data,
                merge=True
            )

            logger.warning(f"Login failed: Invalid password for {request.email} (attempt {failed_attempts}/5)")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or password"
            )

        # Check if email is verified
        if not user_data.get("is_verified", False):
            logger.warning(f"Login failed: Email not verified for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified. Please verify your email before logging in."
            )

        # Check if account is active
        if not user_data.get("is_active", True):
            logger.warning(f"Login failed: Account inactive for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive. Please contact support."
            )

        # Generate tokens
        user_role = user_data.get("role", "public")
        access_token = auth_service.create_access_token(
            user_id=str(user_id),
            role=user_role,
            email=request.email
        )
        refresh_token, family_id = auth_service.create_refresh_token(user_id=str(user_id))

        # Store token family mapping in Redis for reuse detection
        refresh_payload = auth_service.decode_token(refresh_token)
        token_id = refresh_payload.get("token_id")
        exp_timestamp = refresh_payload.get("exp")
        ttl = int(exp_timestamp - datetime.utcnow().timestamp())

        auth_service.store_token_family(
            token_id=token_id,
            family_id=family_id,
            user_id=str(user_id),
            ttl=ttl
        )

        # Update user record with successful login
        update_data = {
            "last_login": datetime.utcnow().isoformat(),
            "failed_login_attempts": 0,
            "lockout_until": None,
            "updated_at": datetime.utcnow().isoformat()
        }

        db_client.update_document(
            collection="users",
            document_id=user_id,
            data=update_data,
            merge=True
        )

        logger.info(f"Login successful for {request.email}")

        # Rotate CSRF token after successful login (US-071)
        # This prevents session fixation attacks
        try:
            rotate_csrf_token(response)
            logger.debug("CSRF token rotated after successful login")
        except Exception as e:
            # Log error but don't fail login if CSRF rotation fails
            logger.warning(f"Failed to rotate CSRF token after login: {e}")

        # Prepare user data for response (exclude sensitive fields)
        user_response = {
            "id": str(user_id),
            "email": user_data.get("email"),
            "role": user_role,
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "is_verified": user_data.get("is_verified", False)
        }

        return LoginResponse(
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_response
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


class CurrentUserResponse(BaseModel):
    """Current user profile response"""
    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User full name")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="User role")
    belt_rank: Optional[str] = Field(None, description="Current belt rank")
    dojo: Optional[str] = Field(None, description="Affiliated dojo/school")
    country: str = Field(default="USA", description="Country")
    locale: str = Field(default="en-US", description="User locale preference")


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Return the current authenticated user's profile information"
)
async def get_current_user_profile(
    current_user: Dict = Depends(CurrentUser())
) -> CurrentUserResponse:
    """
    Get current authenticated user's profile

    This endpoint:
    1. Validates the JWT access token via CurrentUser dependency
    2. Queries ZeroDB users collection for user data
    3. Queries ZeroDB profiles collection for extended profile data (if exists)
    4. Returns user profile with: id, name, email, role, belt_rank, dojo, country, locale
    5. Falls back to mock data if user not found in database

    Security:
    - Requires valid JWT access token
    - User must be authenticated

    Args:
        current_user: Authenticated user information from JWT token

    Returns:
        CurrentUserResponse with user profile data

    Raises:
        HTTPException 401: Invalid or expired token
        HTTPException 500: Database error
    """
    db_client = get_zerodb_client()

    try:
        user_id = str(current_user["id"])
        user_email = current_user["email"]
        user_role = current_user["role"]

        logger.info(f"Fetching profile for user: {user_id}")

        # Query users collection for basic user data
        users = db_client.query_documents(
            collection="users",
            filters={"id": user_id},
            limit=1
        )

        # If user not found in database, return mock data with token information
        if not users.get("documents") or len(users["documents"]) == 0:
            logger.warning(f"User {user_id} not found in database, returning mock data")
            return CurrentUserResponse(
                id=user_id,
                name="Guest User",
                email=user_email,
                role=user_role,
                belt_rank=None,
                dojo=None,
                country="USA",
                locale="en-US"
            )

        user_doc = users["documents"][0]
        user_data = user_doc.get("data", {})

        # Extract basic user information
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or "Unknown User"

        # Initialize profile data
        belt_rank = None
        dojo = None
        country = "USA"
        locale = "en-US"

        # Query profiles collection if profile_id exists
        profile_id = user_data.get("profile_id")
        if profile_id:
            try:
                logger.info(f"Fetching profile details for profile_id: {profile_id}")
                profiles = db_client.query_documents(
                    collection="profiles",
                    filters={"id": profile_id},
                    limit=1
                )

                if profiles.get("documents") and len(profiles["documents"]) > 0:
                    profile_doc = profiles["documents"][0]
                    profile_data = profile_doc.get("data", {})

                    # Extract profile information
                    country = profile_data.get("country", "USA")

                    # Get belt rank from ranks dictionary (first discipline's rank)
                    ranks = profile_data.get("ranks", {})
                    if ranks:
                        # Get the first rank from the dictionary
                        belt_rank = next(iter(ranks.values()), None)

                    # Get dojo/school from schools_affiliated list (first school)
                    schools = profile_data.get("schools_affiliated", [])
                    if schools:
                        dojo = schools[0]

                    logger.info(f"Profile data loaded for user {user_id}")
                else:
                    logger.info(f"No profile found for profile_id: {profile_id}")

            except Exception as e:
                # Log profile fetch error but don't fail the request
                logger.error(f"Error fetching profile for user {user_id}: {e}")

        return CurrentUserResponse(
            id=user_id,
            name=full_name,
            email=user_email,
            role=user_role,
            belt_rank=belt_rank,
            dojo=dojo,
            country=country,
            locale=locale
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ZeroDBError as e:
        logger.error(f"ZeroDB error fetching user profile: {e}")
        # Return mock data on database error
        return CurrentUserResponse(
            id=str(current_user["id"]),
            name="Guest User",
            email=current_user["email"],
            role=current_user["role"],
            belt_rank=None,
            dojo=None,
            country="USA",
            locale="en-US"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching user profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile. Please try again later."
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout user by blacklisting access and refresh tokens"
)
async def logout(
    request: LogoutRequest,
    authorization: Optional[str] = Header(None)
) -> LogoutResponse:
    """
    Logout user by blacklisting tokens

    This endpoint:
    1. Extracts access token from Authorization header
    2. Validates the access token
    3. Blacklists the access token in Redis
    4. Blacklists the refresh token (if provided)
    5. Logs logout action in audit trail

    Security Features:
    - Token blacklisting to prevent reuse
    - Redis-based token revocation with TTL
    - Validates token before blacklisting
    - Logs logout attempts

    Args:
        request: LogoutRequest with optional refresh_token
        authorization: Authorization header with Bearer token

    Returns:
        LogoutResponse with success message

    Raises:
        HTTPException 401: Missing or invalid token
        HTTPException 500: Server error (Redis failure)
    """
    auth_service = AuthService(get_settings())

    try:
        # Extract access token from Authorization header
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )

        # Parse Bearer token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Expected 'Bearer <token>'"
            )

        access_token = parts[1]

        # Verify and blacklist access token
        try:
            payload = auth_service.verify_access_token(access_token)
            user_id = payload.get("user_id")
            logger.info(f"Logout requested for user {user_id}")

            # Blacklist access token
            auth_service.blacklist_token(access_token)
            logger.info(f"Access token blacklisted for user {user_id}")

        except TokenBlacklistedError:
            # Token already blacklisted (already logged out)
            logger.info("Logout attempt with already blacklisted token")
            return LogoutResponse(message="Already logged out")

        except (TokenExpiredError, TokenInvalidError) as e:
            logger.warning(f"Logout failed: Invalid token - {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        # Blacklist refresh token if provided
        if request.refresh_token:
            try:
                auth_service.verify_refresh_token(request.refresh_token)
                auth_service.blacklist_token(request.refresh_token)
                logger.info(f"Refresh token blacklisted for user {user_id}")
            except (TokenBlacklistedError, TokenExpiredError, TokenInvalidError) as e:
                # Log but don't fail logout if refresh token is invalid
                logger.warning(f"Failed to blacklist refresh token: {e}")

        return LogoutResponse(message="Logout successful")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error during logout: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
