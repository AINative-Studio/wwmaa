"""
Rate Limiting Middleware for WWMAA Backend

Implements Redis-based rate limiting with sliding window algorithm.
Supports both IP-based and user-based rate limiting with configurable
limits per endpoint.

Features:
- Sliding window rate limiting algorithm
- IP-based rate limiting for unauthenticated requests
- User-based rate limiting for authenticated requests
- Custom rate limits per endpoint
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- 429 Too Many Requests response when limit exceeded
- Redis for distributed rate limit tracking

Usage:
    from backend.middleware.rate_limit import rate_limit

    @router.post("/login")
    @rate_limit(requests=5, window_seconds=900)  # 5 requests per 15 minutes
    async def login(request: LoginRequest):
        pass
"""

import time
import logging
from functools import wraps
from typing import Optional, Callable
import redis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from backend.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize Redis client
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    logger.info(f"Redis connection established: {settings.REDIS_URL}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, limit: int, window_seconds: int, retry_after: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {limit} requests per {window_seconds} seconds")


def get_client_identifier(request: Request) -> str:
    """
    Get unique identifier for the client making the request.

    For authenticated requests, uses user_id from request.state.
    For unauthenticated requests, uses client IP address.

    Args:
        request: FastAPI request object

    Returns:
        Unique identifier string (user_id or IP address)
    """
    # Check if user is authenticated (set by auth middleware)
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"

    # Fall back to IP address for unauthenticated requests
    # Get real IP from X-Forwarded-For header (for reverse proxy scenarios)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, use the first one
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"


def check_rate_limit(
    identifier: str,
    limit: int,
    window_seconds: int,
    endpoint: str
) -> tuple[bool, int, int, int]:
    """
    Check if request should be rate limited using sliding window algorithm.

    This implements a sliding window counter algorithm using Redis sorted sets:
    1. Current timestamp is used as score
    2. Remove entries older than the window
    3. Count remaining entries
    4. If count < limit, allow request and add new entry
    5. If count >= limit, reject request

    Args:
        identifier: Unique client identifier (IP or user_id)
        limit: Maximum number of requests allowed
        window_seconds: Time window in seconds
        endpoint: API endpoint path (for namespacing)

    Returns:
        Tuple of (allowed, remaining, limit, reset_time)
        - allowed: True if request is allowed, False if rate limited
        - remaining: Number of requests remaining in current window
        - limit: Maximum requests allowed
        - reset_time: Unix timestamp when rate limit resets
    """
    if not redis_client:
        # If Redis is unavailable, allow the request (fail open)
        logger.warning("Redis unavailable, bypassing rate limit check")
        return True, limit, limit, int(time.time() + window_seconds)

    # Create unique Redis key for this identifier + endpoint
    redis_key = f"rate_limit:{endpoint}:{identifier}"

    current_time = time.time()
    window_start = current_time - window_seconds

    try:
        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()

        # Remove entries older than the window
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count entries in current window
        pipe.zcard(redis_key)

        # Execute pipeline
        results = pipe.execute()
        current_count = results[1]

        # Calculate remaining requests
        remaining = max(0, limit - current_count)

        # Calculate reset time (end of current window)
        reset_time = int(current_time + window_seconds)

        if current_count < limit:
            # Allow request - add new entry with current timestamp as score
            # Use unique value to avoid collisions (timestamp + random component)
            entry_value = f"{current_time}:{time.time_ns()}"
            redis_client.zadd(redis_key, {entry_value: current_time})

            # Set expiry on the key to clean up old data
            redis_client.expire(redis_key, window_seconds + 60)

            remaining = max(0, limit - current_count - 1)

            logger.debug(
                f"Rate limit check passed for {identifier} on {endpoint}: "
                f"{current_count + 1}/{limit} requests"
            )

            return True, remaining, limit, reset_time
        else:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {identifier} on {endpoint}: "
                f"{current_count}/{limit} requests in {window_seconds}s"
            )

            return False, 0, limit, reset_time

    except redis.RedisError as e:
        # If Redis operation fails, log error and allow request (fail open)
        logger.error(f"Redis error during rate limit check: {e}")
        return True, limit, limit, int(time.time() + window_seconds)


def add_rate_limit_headers(
    response: JSONResponse,
    limit: int,
    remaining: int,
    reset_time: int
) -> JSONResponse:
    """
    Add rate limit headers to response.

    Args:
        response: FastAPI JSONResponse object
        limit: Maximum requests allowed
        remaining: Number of requests remaining
        reset_time: Unix timestamp when rate limit resets

    Returns:
        Response with rate limit headers added
    """
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)
    return response


def rate_limit(requests: int, window_seconds: int):
    """
    Rate limiting decorator for FastAPI endpoints.

    Implements sliding window rate limiting with Redis backend.
    Adds rate limit headers to all responses.
    Returns 429 status code when limit is exceeded.

    Args:
        requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds

    Returns:
        Decorated function with rate limiting applied

    Example:
        @router.post("/login")
        @rate_limit(requests=5, window_seconds=900)  # 5 requests per 15 minutes
        async def login(request: LoginRequest):
            pass

    Raises:
        HTTPException 429: Too Many Requests when rate limit exceeded
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object from arguments
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request object found, call function without rate limiting
                logger.warning(f"No request object found for rate limiting on {func.__name__}")
                return await func(*args, **kwargs)

            # Get client identifier (IP or user_id)
            identifier = get_client_identifier(request)

            # Get endpoint path for namespacing
            endpoint = request.url.path

            # Check rate limit
            allowed, remaining, limit, reset_time = check_rate_limit(
                identifier=identifier,
                limit=requests,
                window_seconds=window_seconds,
                endpoint=endpoint
            )

            if not allowed:
                # Rate limit exceeded - return 429
                retry_after = reset_time - int(time.time())

                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Maximum {limit} requests per {window_seconds} seconds.",
                        "retry_after": retry_after,
                        "limit": limit,
                        "window_seconds": window_seconds
                    }
                )

                # Add rate limit headers
                response = add_rate_limit_headers(response, limit, remaining, reset_time)

                # Add Retry-After header (in seconds)
                response.headers["Retry-After"] = str(retry_after)

                return response

            # Rate limit not exceeded - call the endpoint
            result = await func(*args, **kwargs)

            # Add rate limit headers to successful response
            if isinstance(result, JSONResponse):
                result = add_rate_limit_headers(result, limit, remaining, reset_time)
            elif hasattr(result, "headers"):
                # If result has headers attribute, add rate limit headers
                result.headers["X-RateLimit-Limit"] = str(limit)
                result.headers["X-RateLimit-Remaining"] = str(remaining)
                result.headers["X-RateLimit-Reset"] = str(reset_time)

            return result

        return wrapper
    return decorator


# Predefined rate limit decorators for common use cases
def rate_limit_login():
    """Rate limit for login endpoints: 5 requests per 15 minutes"""
    return rate_limit(requests=5, window_seconds=900)


def rate_limit_registration():
    """Rate limit for registration endpoints: 3 requests per hour"""
    return rate_limit(requests=3, window_seconds=3600)


def rate_limit_password_reset():
    """Rate limit for password reset endpoints: 3 requests per hour"""
    return rate_limit(requests=3, window_seconds=3600)


def rate_limit_api_general():
    """Rate limit for general API endpoints: 100 requests per minute"""
    return rate_limit(requests=100, window_seconds=60)


def rate_limit_unauthenticated():
    """Rate limit for unauthenticated requests: 50 requests per hour"""
    return rate_limit(requests=50, window_seconds=3600)


def rate_limit_authenticated():
    """Rate limit for authenticated requests: 150 requests per hour"""
    return rate_limit(requests=150, window_seconds=3600)
