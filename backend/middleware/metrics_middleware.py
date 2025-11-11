"""
Metrics Middleware for FastAPI

Provides automatic instrumentation for HTTP requests with:
- Request duration tracking
- Request counting
- Request ID generation and tracing
- Active request tracking
"""

import time
import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.observability.metrics import (
    record_http_request,
    active_requests,
)

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics and add request ID tracing.

    Automatically tracks:
    - Request duration
    - Request counts by endpoint, method, and status code
    - Active concurrent requests
    - Request ID for distributed tracing
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request and track metrics.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with added headers
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for access in handlers
        request.state.request_id = request_id

        # Track active requests
        active_requests.inc()

        # Start timing
        start_time = time.time()

        # Initialize response
        response = None
        status_code = 500  # Default to error if exception occurs

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            return response

        except Exception as e:
            # Log exception
            logger.error(
                f"Request {request_id} failed with exception: {e}",
                exc_info=True,
            )
            # Re-raise to let FastAPI handle it
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Decrement active requests
            active_requests.dec()

            # Normalize endpoint path to avoid high cardinality
            # Replace path parameters with placeholders
            endpoint = self._normalize_endpoint(request.url.path)

            # Record metrics
            record_http_request(
                method=request.method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
            )

            # Add request ID to response headers
            if response is not None:
                response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                f"Request {request_id} completed: "
                f"{request.method} {endpoint} -> {status_code} "
                f"({duration:.3f}s)"
            )

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path to prevent high cardinality metrics.

        Replaces dynamic path parameters (UUIDs, IDs) with placeholders.

        Args:
            path: Request path

        Returns:
            Normalized path
        """
        # Split path into parts
        parts = path.split("/")
        normalized_parts = []

        for part in parts:
            if not part:
                continue

            # Check if part looks like a UUID
            if self._is_uuid(part):
                normalized_parts.append("{uuid}")
            # Check if part looks like an ID (numeric)
            elif part.isdigit():
                normalized_parts.append("{id}")
            # Check if part looks like a token/hash (long alphanumeric)
            elif len(part) > 20 and part.isalnum():
                normalized_parts.append("{token}")
            else:
                normalized_parts.append(part)

        return "/" + "/".join(normalized_parts)

    def _is_uuid(self, value: str) -> bool:
        """
        Check if a string looks like a UUID.

        Args:
            value: String to check

        Returns:
            True if value looks like a UUID
        """
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests for distributed tracing.

    This is a simplified version if you want request ID without full metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request and response.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with X-Request-ID header
        """
        # Check if request ID already exists (from upstream proxy)
        request_id = request.headers.get("X-Request-ID")

        # Generate new ID if not present
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", "unknown")
