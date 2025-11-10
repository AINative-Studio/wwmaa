"""
JWT Authentication Service for WWMAA Backend

This module provides comprehensive JWT token generation and validation functionality
for secure user authentication. It supports both access and refresh tokens with
configurable expiration times, token blacklisting via Redis, and robust error handling.

Security Features:
- HS256 algorithm for token signing
- Configurable token expiration times
- Redis-based token blacklisting
- User ID and role-based claims
- Email claim support
- Secure token validation with comprehensive error handling

Usage:
    from backend.services.auth_service import AuthService
    from backend.config import get_settings

    settings = get_settings()
    auth_service = AuthService(settings)

    # Generate tokens
    access_token = auth_service.create_access_token(
        user_id="user123",
        role="member",
        email="user@example.com"
    )

    # Verify tokens
    payload = auth_service.verify_access_token(access_token)
    user_id = payload["user_id"]
    role = payload["role"]
"""

import jwt
import redis
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from backend.config import Settings


class TokenError(Exception):
    """Base exception for token-related errors."""
    pass


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Raised when a token is invalid or malformed."""
    pass


class TokenBlacklistedError(TokenError):
    """Raised when a token has been blacklisted."""
    pass


class TokenReuseError(TokenError):
    """Raised when a refresh token is reused (potential security breach)."""
    pass


class AuthService:
    """
    JWT Authentication Service for token generation and validation.

    This service handles all JWT operations including:
    - Access token generation with 15-minute expiration (configurable)
    - Refresh token generation with 7-day expiration (configurable)
    - Token validation and verification
    - Token blacklisting using Redis
    - User claims management (user_id, email, role)

    Attributes:
        settings: Application settings containing JWT configuration
        redis_client: Redis client for token blacklisting
    """

    def __init__(self, settings: Settings, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the authentication service.

        Args:
            settings: Application settings instance with JWT configuration
            redis_client: Optional Redis client instance for token blacklisting.
                         If not provided, creates a new connection using REDIS_URL
        """
        self.settings = settings
        self._redis_client = redis_client

    @property
    def redis_client(self) -> redis.Redis:
        """
        Lazy-load Redis client for token blacklisting.

        Returns:
            Redis client instance
        """
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.settings.REDIS_URL,
                decode_responses=True
            )
        return self._redis_client

    def create_access_token(
        self,
        user_id: str,
        role: str,
        email: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Generate a JWT access token with user claims.

        Access tokens are short-lived (default 15 minutes) and contain
        user identification and authorization claims.

        Args:
            user_id: Unique identifier for the user
            role: User's role (e.g., "member", "admin", "instructor")
            email: Optional user email address
            expires_delta: Optional custom expiration time. If not provided,
                          uses JWT_ACCESS_TOKEN_EXPIRE_MINUTES from settings

        Returns:
            Encoded JWT access token string

        Example:
            >>> token = auth_service.create_access_token(
            ...     user_id="user123",
            ...     role="member",
            ...     email="user@example.com"
            ... )
        """
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        expire = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        if email:
            payload["email"] = email

        encoded_jwt = jwt.encode(
            payload,
            self.settings.JWT_SECRET,
            algorithm=self.settings.JWT_ALGORITHM
        )

        return encoded_jwt

    def create_refresh_token(
        self,
        user_id: str,
        family_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, str]:
        """
        Generate a JWT refresh token for long-term authentication with token family tracking.

        Refresh tokens are long-lived (default 7 days) and contain minimal
        claims. They are used to obtain new access tokens without re-authentication.
        Token family tracking enables detection of token reuse attacks.

        Args:
            user_id: Unique identifier for the user
            family_id: Optional token family ID for rotation tracking. If not provided,
                      generates a new family ID.
            expires_delta: Optional custom expiration time. If not provided,
                          uses JWT_REFRESH_TOKEN_EXPIRE_DAYS from settings

        Returns:
            Tuple of (encoded JWT refresh token string, family_id)

        Example:
            >>> refresh_token, family_id = auth_service.create_refresh_token(
            ...     user_id="user123"
            ... )
        """
        if expires_delta is None:
            expires_delta = timedelta(
                days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )

        # Generate new family ID if not provided (new login session)
        if family_id is None:
            family_id = str(uuid.uuid4())

        # Generate unique token ID for this specific token
        token_id = str(uuid.uuid4())

        expire = datetime.utcnow() + expires_delta

        payload = {
            "user_id": user_id,
            "family_id": family_id,
            "token_id": token_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(
            payload,
            self.settings.JWT_SECRET,
            algorithm=self.settings.JWT_ALGORITHM
        )

        return encoded_jwt, family_id

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT access token.

        Validates the token signature, expiration, type, and blacklist status.

        Args:
            token: The JWT access token to verify

        Returns:
            Dictionary containing decoded token payload with user claims

        Raises:
            TokenExpiredError: If the token has expired
            TokenInvalidError: If the token is malformed or has invalid signature
            TokenBlacklistedError: If the token has been blacklisted

        Example:
            >>> payload = auth_service.verify_access_token(token)
            >>> user_id = payload["user_id"]
            >>> role = payload["role"]
        """
        # Check if token is blacklisted
        if self._is_token_blacklisted(token):
            raise TokenBlacklistedError("Token has been revoked")

        payload = self.decode_token(token)

        # Verify token type
        if payload.get("type") != "access":
            raise TokenInvalidError("Invalid token type")

        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT refresh token.

        Validates the token signature, expiration, type, and blacklist status.

        Args:
            token: The JWT refresh token to verify

        Returns:
            Dictionary containing decoded token payload with user_id

        Raises:
            TokenExpiredError: If the token has expired
            TokenInvalidError: If the token is malformed or has invalid signature
            TokenBlacklistedError: If the token has been blacklisted

        Example:
            >>> payload = auth_service.verify_refresh_token(refresh_token)
            >>> user_id = payload["user_id"]
        """
        # Check if token is blacklisted
        if self._is_token_blacklisted(token):
            raise TokenBlacklistedError("Token has been revoked")

        payload = self.decode_token(token)

        # Verify token type
        if payload.get("type") != "refresh":
            raise TokenInvalidError("Invalid token type")

        return payload

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        This is a low-level helper method that decodes any JWT token
        without checking the token type. Use verify_access_token or
        verify_refresh_token for proper validation.

        Args:
            token: The JWT token to decode

        Returns:
            Dictionary containing decoded token payload

        Raises:
            TokenExpiredError: If the token has expired
            TokenInvalidError: If the token is malformed or has invalid signature

        Example:
            >>> payload = auth_service.decode_token(token)
            >>> user_id = payload["user_id"]
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def blacklist_token(self, token: str) -> None:
        """
        Add a token to the blacklist.

        Blacklisted tokens are stored in Redis with TTL matching the token's
        remaining lifetime. This prevents revoked tokens from being used
        while avoiding indefinite storage.

        Args:
            token: The JWT token to blacklist

        Example:
            >>> auth_service.blacklist_token(access_token)
        """
        try:
            # Decode token to get expiration time
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET,
                algorithms=[self.settings.JWT_ALGORITHM],
                options={"verify_exp": False}  # Don't verify expiration when blacklisting
            )

            # Calculate TTL (time until token expires)
            exp = payload.get("exp")
            if exp:
                # exp is a UTC timestamp, so use utcnow() for comparison
                current_time = datetime.utcnow().timestamp()
                ttl = int(exp - current_time)

                # Only blacklist if token hasn't expired yet
                if ttl > 0:
                    key = f"blacklist:{token}"
                    self.redis_client.setex(key, ttl, "1")
        except jwt.InvalidTokenError:
            # If token is already invalid, no need to blacklist
            pass

    def _is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token: The JWT token to check

        Returns:
            True if token is blacklisted, False otherwise
        """
        try:
            key = f"blacklist:{token}"
            return self.redis_client.exists(key) > 0
        except redis.RedisError:
            # If Redis is unavailable, fail open (allow the request)
            # This prevents Redis outages from causing authentication failures
            # Consider logging this error in production
            return False

    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user ID from a token without full verification.

        This is a convenience method that attempts to extract the user_id
        from a token. It does not verify the token signature or expiration.
        Use this only when you need to identify a user from a potentially
        invalid token (e.g., for logging or error handling).

        Args:
            token: The JWT token

        Returns:
            User ID string

        Raises:
            TokenInvalidError: If the token cannot be decoded or has no user_id
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET,
                algorithms=[self.settings.JWT_ALGORITHM],
                options={"verify_exp": False, "verify_signature": False}
            )
            user_id = payload.get("user_id")
            if not user_id:
                raise TokenInvalidError("Token does not contain user_id")
            return user_id
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Cannot extract user_id: {str(e)}")

    def store_token_family(self, token_id: str, family_id: str, user_id: str, ttl: int) -> None:
        """
        Store a refresh token's family membership in Redis.

        This enables tracking of token families for rotation and reuse detection.
        When a token from a family is used, we can detect if it's a reused token
        and invalidate the entire family.

        Args:
            token_id: Unique ID of this specific refresh token
            family_id: Family ID that groups related tokens
            user_id: User ID who owns this token
            ttl: Time-to-live in seconds (should match token expiration)

        Example:
            >>> auth_service.store_token_family(
            ...     token_id="token123",
            ...     family_id="family456",
            ...     user_id="user789",
            ...     ttl=604800  # 7 days
            ... )
        """
        try:
            # Store token ID -> family ID mapping
            key = f"token_family:{token_id}"
            value = f"{family_id}:{user_id}"
            self.redis_client.setex(key, ttl, value)
        except redis.RedisError:
            # If Redis is unavailable, log but don't fail
            # This degrades gracefully (rotation still works, reuse detection disabled)
            pass

    def check_token_reuse(self, token_id: str, family_id: str) -> bool:
        """
        Check if a refresh token has been reused (potential security breach).

        When a refresh token is used, it should be immediately invalidated.
        If we see another request with the same token_id, it means the token
        was reused, which indicates a possible token theft.

        Args:
            token_id: Unique ID of the refresh token being used
            family_id: Family ID of the token

        Returns:
            True if token reuse is detected, False otherwise

        Example:
            >>> is_reused = auth_service.check_token_reuse("token123", "family456")
            >>> if is_reused:
            ...     # Invalidate entire token family
            ...     auth_service.invalidate_token_family("family456")
        """
        try:
            key = f"token_family:{token_id}"
            stored_value = self.redis_client.get(key)

            if stored_value is None:
                # Token ID not found in Redis
                # This could mean:
                # 1. Token was already used and removed (reuse detected)
                # 2. Redis was cleared
                # 3. Token expired naturally
                # We treat this as potential reuse for security
                return True

            # Token exists, check if family_id matches
            stored_family_id = stored_value.split(":")[0]
            if stored_family_id != family_id:
                # Family ID mismatch - suspicious
                return True

            # Token is valid and not reused yet
            return False

        except redis.RedisError:
            # If Redis is unavailable, fail safe (assume no reuse)
            # This prevents false positives when Redis is down
            return False

    def mark_token_used(self, token_id: str) -> None:
        """
        Mark a refresh token as used by removing it from Redis.

        After a token is successfully used for rotation, we delete it
        from Redis. This ensures that if the same token is presented again,
        we can detect it as reuse.

        Args:
            token_id: Unique ID of the refresh token that was used

        Example:
            >>> auth_service.mark_token_used("token123")
        """
        try:
            key = f"token_family:{token_id}"
            self.redis_client.delete(key)
        except redis.RedisError:
            # If Redis is unavailable, log but don't fail
            pass

    def invalidate_token_family(self, family_id: str) -> None:
        """
        Invalidate all tokens in a token family.

        This is used when token reuse is detected to prevent further
        use of any tokens in the compromised family. All tokens with
        the same family_id are blacklisted.

        Args:
            family_id: Family ID to invalidate

        Example:
            >>> auth_service.invalidate_token_family("family456")
        """
        try:
            # Store the family_id in a blacklist set
            # Use a long TTL (30 days) to ensure blacklisting persists
            key = f"blacklisted_family:{family_id}"
            self.redis_client.setex(key, 30 * 24 * 60 * 60, "1")

            # Also clean up all tokens in this family
            # Scan for all token_family keys with this family_id
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(
                    cursor=cursor,
                    match="token_family:*",
                    count=100
                )

                for key in keys:
                    value = self.redis_client.get(key)
                    if value and value.startswith(f"{family_id}:"):
                        self.redis_client.delete(key)

                if cursor == 0:
                    break

        except redis.RedisError:
            # If Redis is unavailable, log but don't fail
            pass

    def is_family_blacklisted(self, family_id: str) -> bool:
        """
        Check if a token family has been blacklisted.

        Args:
            family_id: Family ID to check

        Returns:
            True if family is blacklisted, False otherwise

        Example:
            >>> if auth_service.is_family_blacklisted("family456"):
            ...     raise TokenReuseError("Token family has been revoked")
        """
        try:
            key = f"blacklisted_family:{family_id}"
            return self.redis_client.exists(key) > 0
        except redis.RedisError:
            # If Redis is unavailable, fail open (allow the request)
            return False
