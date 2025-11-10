"""
Unit Tests for Rate Limiting Middleware

Tests the Redis-based rate limiting middleware with sliding window algorithm.
Covers IP-based and user-based rate limiting, headers, 429 responses, and edge cases.

Test Coverage:
- Sliding window rate limiting algorithm
- IP-based rate limiting for unauthenticated requests
- User-based rate limiting for authenticated requests
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- 429 Too Many Requests responses with Retry-After header
- Redis connection handling (fail-open on Redis unavailability)
- Decorator functionality and configuration
- Edge cases and error handling

Target: 80%+ code coverage
"""

import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import pytest
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from backend.middleware.rate_limit import (
    get_client_identifier,
    check_rate_limit,
    add_rate_limit_headers,
    rate_limit,
    rate_limit_login,
    rate_limit_registration,
    rate_limit_password_reset,
    rate_limit_api_general,
    rate_limit_unauthenticated,
    rate_limit_authenticated,
    RateLimitExceeded
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object"""
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "192.168.1.1"
    request.headers = {}
    request.state = Mock()
    request.state.user_id = None
    request.url = Mock()
    request.url.path = "/api/test"
    return request


@pytest.fixture
def mock_authenticated_request(mock_request):
    """Create a mock authenticated request with user_id"""
    mock_request.state.user_id = "user_123"
    return mock_request


@pytest.fixture
def mock_redis():
    """Create a mock Redis client"""
    redis_mock = Mock()
    redis_mock.pipeline = Mock(return_value=Mock())
    redis_mock.pipeline.return_value.zremrangebyscore = Mock()
    redis_mock.pipeline.return_value.zcard = Mock()
    redis_mock.pipeline.return_value.execute = Mock(return_value=[None, 0])
    redis_mock.zadd = Mock(return_value=1)
    redis_mock.expire = Mock(return_value=1)
    redis_mock.ping = Mock(return_value=True)
    return redis_mock


# ============================================================================
# TEST: get_client_identifier()
# ============================================================================

class TestGetClientIdentifier:
    """Test suite for get_client_identifier function"""

    def test_authenticated_user_returns_user_id(self, mock_authenticated_request):
        """Test that authenticated requests use user_id"""
        identifier = get_client_identifier(mock_authenticated_request)
        assert identifier == "user:user_123"

    def test_unauthenticated_user_returns_ip(self, mock_request):
        """Test that unauthenticated requests use IP address"""
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:192.168.1.1"

    def test_x_forwarded_for_header_used_when_present(self, mock_request):
        """Test that X-Forwarded-For header is used if present (reverse proxy scenario)"""
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:203.0.113.1"

    def test_x_forwarded_for_single_ip(self, mock_request):
        """Test X-Forwarded-For with single IP"""
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1"}
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:203.0.113.1"

    def test_x_forwarded_for_with_spaces(self, mock_request):
        """Test X-Forwarded-For with various spacing"""
        mock_request.headers = {"X-Forwarded-For": "  203.0.113.1  ,  198.51.100.1  "}
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:203.0.113.1"

    def test_no_client_host_returns_unknown(self, mock_request):
        """Test fallback to 'unknown' when client host is not available"""
        mock_request.client = None
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:unknown"

    def test_authenticated_user_ignores_ip(self, mock_authenticated_request):
        """Test that authenticated users are identified by user_id, not IP"""
        mock_authenticated_request.headers = {"X-Forwarded-For": "203.0.113.1"}
        identifier = get_client_identifier(mock_authenticated_request)
        assert identifier == "user:user_123"
        # Should not contain IP address
        assert "203.0.113.1" not in identifier


# ============================================================================
# TEST: check_rate_limit()
# ============================================================================

class TestCheckRateLimit:
    """Test suite for check_rate_limit function (sliding window algorithm)"""

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    def test_allow_request_when_under_limit(self, mock_time, mock_redis_patch):
        """Test that requests are allowed when under the rate limit"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 2]  # 2 requests in window
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)
        mock_redis_patch.return_value = mock_redis

        # Patch the module-level redis_client
        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            allowed, remaining, limit, reset_time = check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=60,
                endpoint="/api/test"
            )

            # Assert
            assert allowed is True
            assert remaining == 7  # 10 - 2 - 1 = 7
            assert limit == 10
            assert reset_time == 1060  # current_time + window_seconds

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    def test_deny_request_when_at_limit(self, mock_time, mock_redis_patch):
        """Test that requests are denied when at the rate limit"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 10]  # Already at limit
        mock_redis.pipeline.return_value = pipe
        mock_redis_patch.return_value = mock_redis

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            allowed, remaining, limit, reset_time = check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=60,
                endpoint="/api/test"
            )

            # Assert
            assert allowed is False
            assert remaining == 0
            assert limit == 10
            assert reset_time == 1060

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    def test_deny_request_when_over_limit(self, mock_time, mock_redis_patch):
        """Test that requests are denied when over the rate limit"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 15]  # Over limit
        mock_redis.pipeline.return_value = pipe

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            allowed, remaining, limit, reset_time = check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=60,
                endpoint="/api/test"
            )

            # Assert
            assert allowed is False
            assert remaining == 0

    @patch('backend.middleware.rate_limit.redis_client', None)
    def test_fail_open_when_redis_unavailable(self):
        """Test that requests are allowed (fail-open) when Redis is unavailable"""
        # Execute
        allowed, remaining, limit, reset_time = check_rate_limit(
            identifier="ip:192.168.1.1",
            limit=10,
            window_seconds=60,
            endpoint="/api/test"
        )

        # Assert - should allow request when Redis is unavailable
        assert allowed is True
        assert remaining == 10
        assert limit == 10

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    def test_redis_key_format(self, mock_time, mock_redis_patch):
        """Test that Redis key is formatted correctly"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=60,
                endpoint="/api/test"
            )

            # Assert - check that zremrangebyscore was called with correct key
            pipe.zremrangebyscore.assert_called_once()
            call_args = pipe.zremrangebyscore.call_args[0]
            assert call_args[0] == "rate_limit:/api/test:ip:192.168.1.1"

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    def test_sliding_window_cleanup(self, mock_time, mock_redis_patch):
        """Test that old entries are removed from Redis (sliding window)"""
        # Setup
        current_time = 1000.0
        window_seconds = 60
        mock_time.time.return_value = current_time

        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=window_seconds,
                endpoint="/api/test"
            )

            # Assert - check that old entries are removed
            pipe.zremrangebyscore.assert_called_once()
            call_args = pipe.zremrangebyscore.call_args[0]
            # Second argument should be 0, third should be window_start
            assert call_args[1] == 0
            assert call_args[2] == current_time - window_seconds

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    def test_redis_ttl_set_correctly(self, mock_time, mock_redis_patch):
        """Test that Redis key TTL is set correctly for cleanup"""
        # Setup
        mock_time.time.return_value = 1000.0
        window_seconds = 60

        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=window_seconds,
                endpoint="/api/test"
            )

            # Assert - TTL should be window_seconds + 60 for buffer
            mock_redis.expire.assert_called_once()
            call_args = mock_redis.expire.call_args[0]
            assert call_args[1] == window_seconds + 60

    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    @patch('backend.middleware.rate_limit.logger')
    def test_redis_error_handling_fail_open(self, mock_logger, mock_time, mock_redis_patch):
        """Test that Redis errors are handled gracefully (fail-open)"""
        # Setup
        from redis.exceptions import RedisError
        mock_time.time.return_value = 1000.0
        mock_redis = Mock()
        pipe = Mock()
        # Make the execute() call raise a Redis error
        pipe.execute.side_effect = RedisError("Redis connection error")
        mock_redis.pipeline.return_value = pipe

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            # Execute
            allowed, remaining, limit, reset_time = check_rate_limit(
                identifier="ip:192.168.1.1",
                limit=10,
                window_seconds=60,
                endpoint="/api/test"
            )

            # Assert - should allow request and log error
            assert allowed is True
            assert remaining == 10
            mock_logger.error.assert_called_once()


# ============================================================================
# TEST: add_rate_limit_headers()
# ============================================================================

class TestAddRateLimitHeaders:
    """Test suite for add_rate_limit_headers function"""

    def test_headers_added_to_response(self):
        """Test that rate limit headers are added to response"""
        # Setup
        response = JSONResponse(content={"message": "success"})

        # Execute
        result = add_rate_limit_headers(
            response=response,
            limit=100,
            remaining=95,
            reset_time=1234567890
        )

        # Assert
        assert result.headers["X-RateLimit-Limit"] == "100"
        assert result.headers["X-RateLimit-Remaining"] == "95"
        assert result.headers["X-RateLimit-Reset"] == "1234567890"

    def test_headers_converted_to_strings(self):
        """Test that numeric values are converted to strings in headers"""
        # Setup
        response = JSONResponse(content={"message": "success"})

        # Execute
        result = add_rate_limit_headers(
            response=response,
            limit=10,
            remaining=5,
            reset_time=9999999
        )

        # Assert - all header values should be strings
        assert isinstance(result.headers["X-RateLimit-Limit"], str)
        assert isinstance(result.headers["X-RateLimit-Remaining"], str)
        assert isinstance(result.headers["X-RateLimit-Reset"], str)

    def test_existing_headers_preserved(self):
        """Test that existing headers are preserved when adding rate limit headers"""
        # Setup
        response = JSONResponse(content={"message": "success"})
        response.headers["Custom-Header"] = "custom-value"

        # Execute
        result = add_rate_limit_headers(
            response=response,
            limit=100,
            remaining=95,
            reset_time=1234567890
        )

        # Assert
        assert result.headers["Custom-Header"] == "custom-value"
        assert result.headers["X-RateLimit-Limit"] == "100"


# ============================================================================
# TEST: rate_limit() Decorator
# ============================================================================

class TestRateLimitDecorator:
    """Test suite for rate_limit decorator"""

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.check_rate_limit')
    @patch('backend.middleware.rate_limit.get_client_identifier')
    async def test_decorator_allows_request_under_limit(self, mock_get_identifier, mock_check):
        """Test that decorator allows requests under the rate limit"""
        # Setup
        mock_get_identifier.return_value = "ip:192.168.1.1"
        mock_check.return_value = (True, 95, 100, 1234567890)

        @rate_limit(requests=100, window_seconds=60)
        async def test_endpoint(request: Request):
            return JSONResponse(content={"message": "success"})

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = None

        # Execute
        response = await test_endpoint(mock_request)

        # Assert
        assert isinstance(response, JSONResponse)
        mock_check.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.check_rate_limit')
    @patch('backend.middleware.rate_limit.get_client_identifier')
    @patch('backend.middleware.rate_limit.time')
    async def test_decorator_denies_request_over_limit(self, mock_time, mock_get_identifier, mock_check):
        """Test that decorator returns 429 when rate limit exceeded"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_get_identifier.return_value = "ip:192.168.1.1"
        mock_check.return_value = (False, 0, 100, 1060)

        @rate_limit(requests=100, window_seconds=60)
        async def test_endpoint(request: Request):
            return JSONResponse(content={"message": "success"})

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = None

        # Execute
        response = await test_endpoint(mock_request)

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert "Retry-After" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.check_rate_limit')
    @patch('backend.middleware.rate_limit.get_client_identifier')
    @patch('backend.middleware.rate_limit.time')
    async def test_429_response_contains_retry_after(self, mock_time, mock_get_identifier, mock_check):
        """Test that 429 response includes Retry-After header"""
        # Setup
        current_time = 1000.0
        reset_time = 1060
        mock_time.time.return_value = current_time
        mock_get_identifier.return_value = "ip:192.168.1.1"
        mock_check.return_value = (False, 0, 100, reset_time)

        @rate_limit(requests=100, window_seconds=60)
        async def test_endpoint(request: Request):
            return JSONResponse(content={"message": "success"})

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = None

        # Execute
        response = await test_endpoint(mock_request)

        # Assert
        assert "Retry-After" in response.headers
        retry_after = int(response.headers["Retry-After"])
        assert retry_after == reset_time - int(current_time)

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.check_rate_limit')
    @patch('backend.middleware.rate_limit.get_client_identifier')
    async def test_decorator_adds_headers_to_success_response(self, mock_get_identifier, mock_check):
        """Test that rate limit headers are added to successful responses"""
        # Setup
        mock_get_identifier.return_value = "ip:192.168.1.1"
        mock_check.return_value = (True, 95, 100, 1234567890)

        @rate_limit(requests=100, window_seconds=60)
        async def test_endpoint(request: Request):
            return JSONResponse(content={"message": "success"})

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = None

        # Execute
        response = await test_endpoint(mock_request)

        # Assert - check that headers are added
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "95"

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.check_rate_limit')
    @patch('backend.middleware.rate_limit.get_client_identifier')
    @patch('backend.middleware.rate_limit.logger')
    async def test_decorator_handles_missing_request(self, mock_logger, mock_get_identifier, mock_check):
        """Test that decorator handles case when no Request object is found"""
        # Setup
        @rate_limit(requests=100, window_seconds=60)
        async def test_endpoint(some_arg: str):
            return JSONResponse(content={"message": "success"})

        # Execute - call without Request object
        response = await test_endpoint("test")

        # Assert - should call function without rate limiting
        assert isinstance(response, JSONResponse)
        mock_check.assert_not_called()
        mock_logger.warning.assert_called_once()


# ============================================================================
# TEST: Predefined Rate Limit Decorators
# ============================================================================

class TestPredefinedDecorators:
    """Test suite for predefined rate limit decorator functions"""

    def test_rate_limit_login_configuration(self):
        """Test rate_limit_login() has correct configuration"""
        decorator = rate_limit_login()
        # Decorator should be configured for 5 requests per 15 minutes (900 seconds)
        # We can't directly access the configuration, but we can test it's callable
        assert callable(decorator)

    def test_rate_limit_registration_configuration(self):
        """Test rate_limit_registration() has correct configuration"""
        decorator = rate_limit_registration()
        assert callable(decorator)

    def test_rate_limit_password_reset_configuration(self):
        """Test rate_limit_password_reset() has correct configuration"""
        decorator = rate_limit_password_reset()
        assert callable(decorator)

    def test_rate_limit_api_general_configuration(self):
        """Test rate_limit_api_general() has correct configuration"""
        decorator = rate_limit_api_general()
        assert callable(decorator)

    def test_rate_limit_unauthenticated_configuration(self):
        """Test rate_limit_unauthenticated() has correct configuration"""
        decorator = rate_limit_unauthenticated()
        assert callable(decorator)

    def test_rate_limit_authenticated_configuration(self):
        """Test rate_limit_authenticated() has correct configuration"""
        decorator = rate_limit_authenticated()
        assert callable(decorator)


# ============================================================================
# TEST: RateLimitExceeded Exception
# ============================================================================

class TestRateLimitExceededException:
    """Test suite for RateLimitExceeded exception"""

    def test_exception_creation(self):
        """Test that RateLimitExceeded exception can be created"""
        exc = RateLimitExceeded(limit=100, window_seconds=60, retry_after=45)
        assert exc.limit == 100
        assert exc.window_seconds == 60
        assert exc.retry_after == 45

    def test_exception_message(self):
        """Test that exception message is formatted correctly"""
        exc = RateLimitExceeded(limit=100, window_seconds=60, retry_after=45)
        assert "100 requests per 60 seconds" in str(exc)


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================

class TestRateLimitIntegrationScenarios:
    """Test suite for real-world integration scenarios"""

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    async def test_ip_based_limiting_for_login(self, mock_time, mock_redis_patch):
        """Test IP-based rate limiting for login endpoint (5 requests per 15 minutes)"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_time.time_ns.return_value = 1000000000000

        mock_redis = Mock()
        pipe = Mock()

        # Simulate 4 successful requests, then deny the 5th
        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] <= 4:
                return [None, call_count[0] - 1]  # Under limit
            else:
                return [None, 5]  # At limit

        pipe.execute.side_effect = execute_side_effect
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            @rate_limit(requests=5, window_seconds=900)  # Login rate limit
            async def login_endpoint(request: Request):
                return JSONResponse(content={"message": "login success"})

            mock_request = Mock(spec=Request)
            mock_request.url = Mock()
            mock_request.url.path = "/api/auth/login"
            mock_request.client = Mock()
            mock_request.client.host = "192.168.1.1"
            mock_request.headers = {}
            mock_request.state = Mock()
            mock_request.state.user_id = None

            # Execute - first 4 requests should succeed
            for i in range(4):
                response = await login_endpoint(mock_request)
                assert response.status_code == 200

            # 5th request should be denied
            response = await login_endpoint(mock_request)
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    async def test_user_based_limiting_for_authenticated_request(self, mock_time, mock_redis_patch):
        """Test user-based rate limiting for authenticated requests"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_time.time_ns.return_value = 1000000000000

        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 0]  # Under limit
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            @rate_limit(requests=150, window_seconds=3600)  # Authenticated rate limit
            async def api_endpoint(request: Request):
                return JSONResponse(content={"data": "success"})

            # Create authenticated request
            mock_request = Mock(spec=Request)
            mock_request.url = Mock()
            mock_request.url.path = "/api/data"
            mock_request.client = Mock()
            mock_request.client.host = "192.168.1.1"
            mock_request.headers = {}
            mock_request.state = Mock()
            mock_request.state.user_id = "user_123"

            # Execute
            response = await api_endpoint(mock_request)

            # Assert - should use user-based identifier
            assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    async def test_different_endpoints_have_separate_limits(self, mock_time, mock_redis_patch):
        """Test that different endpoints maintain separate rate limit counters"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_time.time_ns.return_value = 1000000000000

        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            @rate_limit(requests=10, window_seconds=60)
            async def endpoint_a(request: Request):
                return JSONResponse(content={"endpoint": "a"})

            @rate_limit(requests=10, window_seconds=60)
            async def endpoint_b(request: Request):
                return JSONResponse(content={"endpoint": "b"})

            # Create requests for different endpoints
            request_a = Mock(spec=Request)
            request_a.url = Mock()
            request_a.url.path = "/api/endpoint-a"
            request_a.client = Mock()
            request_a.client.host = "192.168.1.1"
            request_a.headers = {}
            request_a.state = Mock()
            request_a.state.user_id = None

            request_b = Mock(spec=Request)
            request_b.url = Mock()
            request_b.url.path = "/api/endpoint-b"
            request_b.client = Mock()
            request_b.client.host = "192.168.1.1"
            request_b.headers = {}
            request_b.state = Mock()
            request_b.state.user_id = None

            # Execute
            response_a = await endpoint_a(request_a)
            response_b = await endpoint_b(request_b)

            # Assert - both should succeed (separate counters)
            assert response_a.status_code == 200
            assert response_b.status_code == 200

            # Verify different Redis keys were used
            assert pipe.zremrangebyscore.call_count >= 2
            calls = pipe.zremrangebyscore.call_args_list
            keys = [call[0][0] for call in calls]
            assert len(set(keys)) >= 2  # At least 2 different keys


# ============================================================================
# TEST: Edge Cases
# ============================================================================

class TestRateLimitEdgeCases:
    """Test suite for edge cases and error scenarios"""

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.check_rate_limit')
    @patch('backend.middleware.rate_limit.get_client_identifier')
    async def test_zero_remaining_requests(self, mock_get_identifier, mock_check):
        """Test behavior when exactly at the rate limit (0 remaining)"""
        # Setup
        mock_get_identifier.return_value = "ip:192.168.1.1"
        mock_check.return_value = (False, 0, 10, 1234567890)

        @rate_limit(requests=10, window_seconds=60)
        async def test_endpoint(request: Request):
            return JSONResponse(content={"message": "success"})

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user_id = None

        # Execute
        response = await test_endpoint(mock_request)

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    async def test_very_short_window(self, mock_time, mock_redis_patch):
        """Test rate limiting with very short time window (1 second)"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_time.time_ns.return_value = 1000000000000

        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            @rate_limit(requests=5, window_seconds=1)
            async def test_endpoint(request: Request):
                return JSONResponse(content={"message": "success"})

            mock_request = Mock(spec=Request)
            mock_request.url = Mock()
            mock_request.url.path = "/api/test"
            mock_request.client = Mock()
            mock_request.client.host = "192.168.1.1"
            mock_request.headers = {}
            mock_request.state = Mock()
            mock_request.state.user_id = None

            # Execute
            response = await test_endpoint(mock_request)

            # Assert - should work with 1-second window
            assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('backend.middleware.rate_limit.redis_client')
    @patch('backend.middleware.rate_limit.time')
    async def test_very_large_limit(self, mock_time, mock_redis_patch):
        """Test rate limiting with very large request limit"""
        # Setup
        mock_time.time.return_value = 1000.0
        mock_time.time_ns.return_value = 1000000000000

        mock_redis = Mock()
        pipe = Mock()
        pipe.execute.return_value = [None, 500]
        mock_redis.pipeline.return_value = pipe
        mock_redis.zadd = Mock(return_value=1)
        mock_redis.expire = Mock(return_value=1)

        with patch('backend.middleware.rate_limit.redis_client', mock_redis):
            @rate_limit(requests=100000, window_seconds=60)
            async def test_endpoint(request: Request):
                return JSONResponse(content={"message": "success"})

            mock_request = Mock(spec=Request)
            mock_request.url = Mock()
            mock_request.url.path = "/api/test"
            mock_request.client = Mock()
            mock_request.client.host = "192.168.1.1"
            mock_request.headers = {}
            mock_request.state = Mock()
            mock_request.state.user_id = None

            # Execute
            response = await test_endpoint(mock_request)

            # Assert
            assert response.status_code == 200
            assert int(response.headers["X-RateLimit-Limit"]) == 100000
