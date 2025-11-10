"""
Comprehensive Unit Tests for JWT Authentication Service

This test suite provides comprehensive coverage of the AuthService class,
testing all token operations, error conditions, and edge cases.

Test Categories:
- Token Generation (access and refresh tokens)
- Token Verification (valid, expired, invalid)
- Token Blacklisting
- Error Handling
- Edge Cases and Security Scenarios

Coverage Target: 80%+
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import redis

from backend.services.auth_service import (
    AuthService,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenBlacklistedError
)
from backend.config import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.JWT_SECRET = "test_secret_key_minimum_32_characters_long_for_security"
    settings.JWT_ALGORITHM = "HS256"
    settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
    settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    settings.REDIS_URL = "redis://localhost:6379/0"
    return settings


@pytest.fixture
def mock_redis():
    """Create mock Redis client for testing."""
    redis_mock = Mock(spec=redis.Redis)
    redis_mock.setex = Mock()
    redis_mock.exists = Mock(return_value=0)
    return redis_mock


@pytest.fixture
def auth_service(mock_settings, mock_redis):
    """Create AuthService instance with mocked dependencies."""
    service = AuthService(mock_settings, redis_client=mock_redis)
    return service


class TestTokenGeneration:
    """Test suite for token generation functionality."""

    def test_create_access_token_basic(self, auth_service):
        """Test creating a basic access token with required fields."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_email(self, auth_service):
        """Test creating an access token with email claim."""
        user_id = "user123"
        role = "member"
        email = "user@example.com"

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            email=email
        )

        # Decode token to verify claims
        payload = jwt.decode(
            token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        assert payload["user_id"] == user_id
        assert payload["role"] == role
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_create_access_token_expiration(self, auth_service):
        """Test access token has correct expiration time."""
        user_id = "user123"
        role = "member"

        before_time = datetime.utcnow()
        token = auth_service.create_access_token(user_id=user_id, role=role)
        after_time = datetime.utcnow()

        payload = jwt.decode(
            token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        # Verify expiration is in the future and within expected range
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]

        # Calculate the actual delta in seconds
        actual_delta = exp_timestamp - iat_timestamp
        expected_delta = auth_service.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # Allow 2 second tolerance for test execution time
        assert abs(actual_delta - expected_delta) < 2

    def test_create_access_token_custom_expiration(self, auth_service):
        """Test access token with custom expiration time."""
        user_id = "user123"
        role = "member"
        custom_expiration = timedelta(minutes=60)

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=custom_expiration
        )

        payload = jwt.decode(
            token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        # Verify expiration delta
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        actual_delta = exp_timestamp - iat_timestamp
        expected_delta = custom_expiration.total_seconds()

        assert abs(actual_delta - expected_delta) < 2

    def test_create_refresh_token_basic(self, auth_service):
        """Test creating a basic refresh token."""
        user_id = "user123"

        token = auth_service.create_refresh_token(user_id=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_claims(self, auth_service):
        """Test refresh token contains correct claims."""
        user_id = "user123"

        token = auth_service.create_refresh_token(user_id=user_id)

        payload = jwt.decode(
            token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        assert payload["user_id"] == user_id
        assert payload["type"] == "refresh"
        assert "role" not in payload
        assert "email" not in payload

    def test_create_refresh_token_expiration(self, auth_service):
        """Test refresh token has correct expiration time."""
        user_id = "user123"

        token = auth_service.create_refresh_token(user_id=user_id)

        payload = jwt.decode(
            token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        # Verify expiration delta
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        actual_delta = exp_timestamp - iat_timestamp
        expected_delta = auth_service.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        # Allow 2 second tolerance
        assert abs(actual_delta - expected_delta) < 2

    def test_create_refresh_token_custom_expiration(self, auth_service):
        """Test refresh token with custom expiration time."""
        user_id = "user123"
        custom_expiration = timedelta(days=30)

        token = auth_service.create_refresh_token(
            user_id=user_id,
            expires_delta=custom_expiration
        )

        payload = jwt.decode(
            token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        exp_datetime = datetime.fromtimestamp(payload["exp"])
        iat_datetime = datetime.fromtimestamp(payload["iat"])

        actual_delta = exp_datetime - iat_datetime
        expected_seconds = custom_expiration.total_seconds()

        assert abs(actual_delta.total_seconds() - expected_seconds) < 2

    def test_tokens_include_issued_at(self, auth_service):
        """Test that both token types include iat (issued at) claim."""
        user_id = "user123"

        access_token = auth_service.create_access_token(
            user_id=user_id,
            role="member"
        )
        refresh_token = auth_service.create_refresh_token(user_id=user_id)

        access_payload = jwt.decode(
            access_token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )
        refresh_payload = jwt.decode(
            refresh_token,
            auth_service.settings.JWT_SECRET,
            algorithms=[auth_service.settings.JWT_ALGORITHM]
        )

        assert "iat" in access_payload
        assert "iat" in refresh_payload


class TestTokenVerification:
    """Test suite for token verification functionality."""

    def test_verify_access_token_valid(self, auth_service):
        """Test verifying a valid access token."""
        user_id = "user123"
        role = "member"
        email = "user@example.com"

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            email=email
        )

        payload = auth_service.verify_access_token(token)

        assert payload["user_id"] == user_id
        assert payload["role"] == role
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_verify_refresh_token_valid(self, auth_service):
        """Test verifying a valid refresh token."""
        user_id = "user123"

        token = auth_service.create_refresh_token(user_id=user_id)

        payload = auth_service.verify_refresh_token(token)

        assert payload["user_id"] == user_id
        assert payload["type"] == "refresh"

    def test_verify_access_token_expired(self, auth_service):
        """Test verifying an expired access token raises TokenExpiredError."""
        user_id = "user123"
        role = "member"

        # Create token with 1 second expiration
        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=timedelta(seconds=1)
        )

        # Wait for token to expire
        time.sleep(2)

        with pytest.raises(TokenExpiredError) as exc_info:
            auth_service.verify_access_token(token)

        assert "expired" in str(exc_info.value).lower()

    def test_verify_refresh_token_expired(self, auth_service):
        """Test verifying an expired refresh token raises TokenExpiredError."""
        user_id = "user123"

        # Create token with 1 second expiration
        token = auth_service.create_refresh_token(
            user_id=user_id,
            expires_delta=timedelta(seconds=1)
        )

        # Wait for token to expire
        time.sleep(2)

        with pytest.raises(TokenExpiredError) as exc_info:
            auth_service.verify_refresh_token(token)

        assert "expired" in str(exc_info.value).lower()

    def test_verify_access_token_invalid_signature(self, auth_service):
        """Test verifying a token with invalid signature raises TokenInvalidError."""
        user_id = "user123"
        role = "member"

        # Create token with different secret
        fake_token = jwt.encode(
            {"user_id": user_id, "role": role, "type": "access"},
            "wrong_secret_key_that_is_also_32_characters_long",
            algorithm="HS256"
        )

        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.verify_access_token(fake_token)

        assert "invalid" in str(exc_info.value).lower()

    def test_verify_access_token_wrong_type(self, auth_service):
        """Test verifying a refresh token as access token raises TokenInvalidError."""
        user_id = "user123"

        # Create refresh token
        refresh_token = auth_service.create_refresh_token(user_id=user_id)

        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.verify_access_token(refresh_token)

        assert "type" in str(exc_info.value).lower()

    def test_verify_refresh_token_wrong_type(self, auth_service):
        """Test verifying an access token as refresh token raises TokenInvalidError."""
        user_id = "user123"
        role = "member"

        # Create access token
        access_token = auth_service.create_access_token(
            user_id=user_id,
            role=role
        )

        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.verify_refresh_token(access_token)

        assert "type" in str(exc_info.value).lower()

    def test_verify_token_malformed(self, auth_service):
        """Test verifying a malformed token raises TokenInvalidError."""
        malformed_token = "not.a.valid.jwt.token"

        with pytest.raises(TokenInvalidError):
            auth_service.verify_access_token(malformed_token)

    def test_decode_token_valid(self, auth_service):
        """Test decode_token helper method with valid token."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        payload = auth_service.decode_token(token)

        assert payload["user_id"] == user_id
        assert payload["role"] == role

    def test_decode_token_expired(self, auth_service):
        """Test decode_token with expired token raises TokenExpiredError."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=timedelta(seconds=1)
        )

        time.sleep(2)

        with pytest.raises(TokenExpiredError):
            auth_service.decode_token(token)

    def test_decode_token_invalid(self, auth_service):
        """Test decode_token with invalid token raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            auth_service.decode_token("invalid.token.here")


class TestTokenBlacklisting:
    """Test suite for token blacklisting functionality."""

    def test_blacklist_token_doesnt_raise_exception(self, auth_service):
        """Test that blacklisting a token doesn't raise any exceptions."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        # Should not raise any exception
        try:
            auth_service.blacklist_token(token)
        except Exception as e:
            pytest.fail(f"blacklist_token raised an unexpected exception: {e}")

    def test_blacklist_token_with_long_expiration(self, auth_service):
        """Test blacklisting a token with long expiration time."""
        user_id = "user123"
        role = "member"

        # Create token with 1 hour expiration
        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=timedelta(hours=1)
        )

        # Should not raise any exception
        auth_service.blacklist_token(token)

    def test_verify_blacklisted_access_token(self, auth_service, mock_redis):
        """Test that blacklisted access token raises TokenBlacklistedError."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        # Simulate token being blacklisted
        mock_redis.exists.return_value = 1

        with pytest.raises(TokenBlacklistedError) as exc_info:
            auth_service.verify_access_token(token)

        assert "revoked" in str(exc_info.value).lower()

    def test_verify_blacklisted_refresh_token(self, auth_service, mock_redis):
        """Test that blacklisted refresh token raises TokenBlacklistedError."""
        user_id = "user123"

        token = auth_service.create_refresh_token(user_id=user_id)

        # Simulate token being blacklisted
        mock_redis.exists.return_value = 1

        with pytest.raises(TokenBlacklistedError) as exc_info:
            auth_service.verify_refresh_token(token)

        assert "revoked" in str(exc_info.value).lower()

    def test_blacklist_expired_token(self, auth_service, mock_redis):
        """Test blacklisting an expired token (should not store in Redis)."""
        user_id = "user123"
        role = "member"

        # Create token with 1 second expiration
        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=timedelta(seconds=1)
        )

        # Wait for expiration
        time.sleep(2)

        # Reset mock to clear any previous calls
        mock_redis.setex.reset_mock()

        auth_service.blacklist_token(token)

        # Should not store expired token
        assert not mock_redis.setex.called

    def test_blacklist_invalid_token(self, auth_service, mock_redis):
        """Test blacklisting an invalid token (should not raise error)."""
        invalid_token = "invalid.token.here"

        # Should not raise exception
        auth_service.blacklist_token(invalid_token)

        # Should not call Redis
        assert not mock_redis.setex.called

    def test_is_token_blacklisted_returns_false_on_redis_error(
        self,
        auth_service,
        mock_redis
    ):
        """Test that Redis errors fail open (allow authentication)."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        # Simulate Redis error
        mock_redis.exists.side_effect = redis.RedisError("Connection failed")

        # Should not raise error, should return False (fail open)
        result = auth_service._is_token_blacklisted(token)

        assert result is False


class TestHelperMethods:
    """Test suite for helper methods and utilities."""

    def test_get_user_id_from_token_valid(self, auth_service):
        """Test extracting user_id from valid token."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        extracted_user_id = auth_service.get_user_id_from_token(token)

        assert extracted_user_id == user_id

    def test_get_user_id_from_expired_token(self, auth_service):
        """Test extracting user_id from expired token (should still work)."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=timedelta(seconds=1)
        )

        time.sleep(2)

        # Should still extract user_id even though token is expired
        extracted_user_id = auth_service.get_user_id_from_token(token)

        assert extracted_user_id == user_id

    def test_get_user_id_from_token_invalid(self, auth_service):
        """Test extracting user_id from invalid token raises TokenInvalidError."""
        invalid_token = "invalid.token.here"

        with pytest.raises(TokenInvalidError):
            auth_service.get_user_id_from_token(invalid_token)

    def test_get_user_id_from_token_missing_user_id(self, auth_service):
        """Test extracting user_id from token without user_id claim."""
        # Create token without user_id
        token = jwt.encode(
            {"role": "member", "type": "access"},
            auth_service.settings.JWT_SECRET,
            algorithm=auth_service.settings.JWT_ALGORITHM
        )

        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.get_user_id_from_token(token)

        assert "user_id" in str(exc_info.value).lower()


class TestRedisIntegration:
    """Test suite for Redis integration."""

    def test_redis_lazy_loading(self, mock_settings):
        """Test that Redis client is lazily loaded."""
        service = AuthService(mock_settings, redis_client=None)

        # Redis client should not be created yet
        assert service._redis_client is None

        # Access redis_client property
        with patch("redis.from_url") as mock_from_url:
            mock_from_url.return_value = Mock(spec=redis.Redis)
            client = service.redis_client

            # Verify Redis was created
            assert client is not None
            mock_from_url.assert_called_once()

    def test_redis_client_reuse(self, mock_settings):
        """Test that Redis client is reused after first access."""
        service = AuthService(mock_settings, redis_client=None)

        with patch("redis.from_url") as mock_from_url:
            mock_from_url.return_value = Mock(spec=redis.Redis)

            # Access multiple times
            client1 = service.redis_client
            client2 = service.redis_client

            # Should be same instance
            assert client1 is client2

            # Should only create once
            assert mock_from_url.call_count == 1

    def test_provided_redis_client_used(self, mock_settings, mock_redis):
        """Test that provided Redis client is used instead of creating new one."""
        service = AuthService(mock_settings, redis_client=mock_redis)

        # Should use provided client
        assert service.redis_client is mock_redis


class TestSecurityScenarios:
    """Test suite for security scenarios and edge cases."""

    def test_different_roles_in_tokens(self, auth_service):
        """Test creating tokens with different user roles."""
        roles = ["member", "admin", "instructor", "guest"]

        for role in roles:
            token = auth_service.create_access_token(
                user_id="user123",
                role=role
            )

            payload = auth_service.verify_access_token(token)
            assert payload["role"] == role

    def test_tokens_for_different_users(self, auth_service):
        """Test creating tokens for different users."""
        user_ids = ["user1", "user2", "user3"]

        tokens = []
        for user_id in user_ids:
            token = auth_service.create_access_token(
                user_id=user_id,
                role="member"
            )
            tokens.append(token)

        # Verify each token contains correct user_id
        for i, token in enumerate(tokens):
            payload = auth_service.verify_access_token(token)
            assert payload["user_id"] == user_ids[i]

    def test_token_without_email_optional(self, auth_service):
        """Test creating token without email (optional field)."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(user_id=user_id, role=role)

        payload = auth_service.verify_access_token(token)

        assert "email" not in payload

    def test_special_characters_in_claims(self, auth_service):
        """Test tokens with special characters in claims."""
        user_id = "user-123_test@domain"
        role = "member"
        email = "user+test@example.com"

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            email=email
        )

        payload = auth_service.verify_access_token(token)

        assert payload["user_id"] == user_id
        assert payload["email"] == email

    def test_very_short_expiration(self, auth_service):
        """Test token with very short expiration (1 second)."""
        user_id = "user123"
        role = "member"

        token = auth_service.create_access_token(
            user_id=user_id,
            role=role,
            expires_delta=timedelta(seconds=1)
        )

        # Should be valid immediately
        payload = auth_service.verify_access_token(token)
        assert payload["user_id"] == user_id

        # Wait and verify it expires
        time.sleep(2)

        with pytest.raises(TokenExpiredError):
            auth_service.verify_access_token(token)


class TestExceptionHierarchy:
    """Test suite for exception hierarchy and error handling."""

    def test_token_error_base_exception(self):
        """Test that TokenError is base exception for all token errors."""
        assert issubclass(TokenExpiredError, TokenError)
        assert issubclass(TokenInvalidError, TokenError)
        assert issubclass(TokenBlacklistedError, TokenError)

    def test_catch_all_token_errors(self, auth_service):
        """Test catching all token errors with base exception."""
        invalid_token = "invalid.token"

        try:
            auth_service.verify_access_token(invalid_token)
            assert False, "Should have raised exception"
        except TokenError:
            # Should catch TokenInvalidError
            pass

    def test_specific_exception_messages(self, auth_service):
        """Test that exceptions have meaningful messages."""
        # Test expired token
        token = auth_service.create_access_token(
            user_id="user123",
            role="member",
            expires_delta=timedelta(seconds=1)
        )
        time.sleep(2)

        with pytest.raises(TokenExpiredError) as exc_info:
            auth_service.verify_access_token(token)

        assert "expired" in str(exc_info.value).lower()

        # Test invalid token
        with pytest.raises(TokenInvalidError) as exc_info:
            auth_service.verify_access_token("invalid")

        assert "invalid" in str(exc_info.value).lower()
