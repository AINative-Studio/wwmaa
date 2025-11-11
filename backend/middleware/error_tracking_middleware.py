"""
Error Tracking Middleware

Automatically tracks user context and request information for all requests.
This middleware enriches Sentry events with user and request data.

Features:
- Automatic user context extraction from JWT tokens
- Request context tracking (URL, method, headers, query params)
- Breadcrumb tracking for request lifecycle
- User context cleanup after request completion
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from jose import jwt, JWTError
from backend.config import get_settings
from backend.observability import (
    add_user_context,
    add_request_context,
    clear_user_context,
    add_breadcrumb,
    set_tag,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically enriches error tracking with user and request context.

    This middleware:
    1. Extracts user information from JWT tokens
    2. Adds request context to Sentry scope
    3. Tracks breadcrumbs for request lifecycle
    4. Cleans up context after request completion
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process each request to add context to error tracking.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response from the route handler
        """
        try:
            # Add request context to Sentry
            add_request_context(request)

            # Add breadcrumb for request start
            add_breadcrumb(
                category="http",
                message=f"{request.method} {request.url.path}",
                data={
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                },
                level="info"
            )

            # Extract and add user context from JWT token
            user_info = self._extract_user_from_token(request)
            if user_info:
                add_user_context(
                    user_id=user_info.get("user_id"),
                    email=user_info.get("email"),
                    username=user_info.get("username"),
                    role=user_info.get("role"),
                    tier=user_info.get("tier"),
                )

                # Add breadcrumb for authenticated user
                add_breadcrumb(
                    category="auth",
                    message=f"Authenticated user: {user_info.get('user_id')}",
                    data={
                        "user_id": user_info.get("user_id"),
                        "role": user_info.get("role"),
                    },
                    level="info"
                )

            # Set tags for filtering
            set_tag("endpoint", request.url.path)
            set_tag("method", request.method)

            # Process request
            response = await call_next(request)

            # Add breadcrumb for successful response
            add_breadcrumb(
                category="http",
                message=f"Response: {response.status_code}",
                data={
                    "status_code": response.status_code,
                    "path": request.url.path,
                },
                level="info" if response.status_code < 400 else "warning"
            )

            # Set response status tag
            set_tag("response_status", str(response.status_code))

            return response

        except Exception as e:
            # Log middleware error but don't break the request
            logger.error(f"Error in ErrorTrackingMiddleware: {e}")

            # Still try to process the request
            try:
                return await call_next(request)
            except Exception as request_error:
                # If request processing also fails, re-raise
                raise request_error

        finally:
            # Clean up user context after request
            clear_user_context()

    def _extract_user_from_token(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract user information from JWT token in Authorization header.

        Args:
            request: FastAPI request

        Returns:
            Dictionary with user information or None if not authenticated
        """
        try:
            # Get Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return None

            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return None

            token = parts[1]

            # Decode JWT token
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM]
                )

                # Extract user information from payload
                user_info = {
                    "user_id": payload.get("sub") or payload.get("user_id"),
                    "email": payload.get("email"),
                    "username": payload.get("username"),
                    "role": payload.get("role"),
                    "tier": payload.get("tier") or payload.get("subscription_tier"),
                }

                # Remove None values
                user_info = {k: v for k, v in user_info.items() if v is not None}

                return user_info if user_info else None

            except JWTError as e:
                # Invalid token - log but don't crash
                logger.debug(f"Invalid JWT token: {e}")
                return None

        except Exception as e:
            logger.error(f"Error extracting user from token: {e}")
            return None


# ============================================================================
# Helper Functions for Manual Context Management
# ============================================================================

def track_business_operation(
    operation: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "info"
) -> None:
    """
    Track a business logic operation with a breadcrumb.

    Use this to track important business operations that help
    understand the flow leading to an error.

    Args:
        operation: Name of the operation (e.g., "payment_initiated", "email_sent")
        details: Additional details about the operation
        level: Breadcrumb level (debug, info, warning, error)

    Example:
        >>> track_business_operation(
        ...     "payment_initiated",
        ...     {"amount": 100, "currency": "usd", "customer_id": "cus_123"}
        ... )
    """
    try:
        add_breadcrumb(
            category="business_logic",
            message=operation,
            data=details or {},
            level=level
        )
    except Exception as e:
        logger.error(f"Error tracking business operation: {e}")


def track_external_api_call(
    service: str,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None
) -> None:
    """
    Track an external API call with a breadcrumb.

    Args:
        service: Service name (e.g., "stripe", "postmark", "openai")
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds

    Example:
        >>> track_external_api_call(
        ...     "stripe",
        ...     "/v1/subscriptions",
        ...     "POST",
        ...     200,
        ...     150.5
        ... )
    """
    try:
        data = {
            "service": service,
            "endpoint": endpoint,
            "method": method,
        }

        if status_code is not None:
            data["status_code"] = status_code
        if duration_ms is not None:
            data["duration_ms"] = duration_ms

        level = "info"
        if status_code and status_code >= 400:
            level = "error" if status_code >= 500 else "warning"

        add_breadcrumb(
            category="api",
            message=f"{service}: {method} {endpoint}",
            data=data,
            level=level
        )

        # Also set tags for the API call
        set_tag(f"external_api.{service}", "called")

    except Exception as e:
        logger.error(f"Error tracking external API call: {e}")


def track_database_operation(
    operation: str,
    table: Optional[str] = None,
    duration_ms: Optional[float] = None,
    records_affected: Optional[int] = None
) -> None:
    """
    Track a database operation with a breadcrumb.

    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table/collection name
        duration_ms: Query duration in milliseconds
        records_affected: Number of records affected

    Example:
        >>> track_database_operation(
        ...     "INSERT",
        ...     "subscriptions",
        ...     25.3,
        ...     1
        ... )
    """
    try:
        data = {
            "operation": operation,
        }

        if table:
            data["table"] = table
        if duration_ms is not None:
            data["duration_ms"] = duration_ms
        if records_affected is not None:
            data["records_affected"] = records_affected

        add_breadcrumb(
            category="database",
            message=f"{operation} {table or 'unknown'}",
            data=data,
            level="info"
        )

    except Exception as e:
        logger.error(f"Error tracking database operation: {e}")


def track_cache_operation(
    operation: str,
    key: Optional[str] = None,
    hit: Optional[bool] = None,
    duration_ms: Optional[float] = None
) -> None:
    """
    Track a cache operation with a breadcrumb.

    Args:
        operation: Cache operation (GET, SET, DELETE, etc.)
        key: Cache key (will be truncated if too long)
        hit: Whether it was a cache hit (for GET operations)
        duration_ms: Operation duration in milliseconds

    Example:
        >>> track_cache_operation("GET", "user:123", hit=True, duration_ms=2.5)
    """
    try:
        data = {
            "operation": operation,
        }

        # Truncate key if too long
        if key:
            data["key"] = key[:100] if len(key) > 100 else key
        if hit is not None:
            data["hit"] = hit
        if duration_ms is not None:
            data["duration_ms"] = duration_ms

        add_breadcrumb(
            category="cache",
            message=f"{operation} {key or ''}",
            data=data,
            level="info"
        )

    except Exception as e:
        logger.error(f"Error tracking cache operation: {e}")
