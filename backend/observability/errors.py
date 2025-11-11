"""
Error Tracking and Monitoring with Sentry

This module provides comprehensive error tracking, monitoring, and alerting
functionality using Sentry. It captures unhandled exceptions, API errors,
client-side errors, and provides rich context for debugging.

Features:
- Automatic exception capture
- User context tracking (user_id, email, role)
- Request context (URL, method, headers, body)
- Breadcrumbs for critical flows
- PII filtering for GDPR compliance
- Performance monitoring (transactions)
- Custom error grouping and fingerprinting
- Release tracking with git commits

Usage:
    from backend.observability.errors import init_sentry

    # Initialize at application startup
    init_sentry(app)
"""

import os
import re
import logging
from typing import Optional, Dict, Any
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from fastapi import FastAPI, Request
from backend.config import get_settings

logger = logging.getLogger(__name__)

# PII patterns to filter
PII_PATTERNS = {
    'password': re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.IGNORECASE),
    'api_key': re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.IGNORECASE),
    'token': re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.IGNORECASE),
    'secret': re.compile(r'secret["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.IGNORECASE),
    'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
}


def _sanitize_value(value: Any) -> Any:
    """
    Recursively sanitize values to remove PII.

    Args:
        value: Value to sanitize (can be dict, list, string, etc.)

    Returns:
        Sanitized value with PII removed
    """
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    elif isinstance(value, str):
        # Apply PII filtering patterns
        sanitized = value
        for pattern_name, pattern in PII_PATTERNS.items():
            sanitized = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', sanitized)
        return sanitized
    else:
        return value


def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook called before sending event to Sentry. Used for PII filtering.

    This function sanitizes sensitive data like passwords, API keys, tokens,
    credit card numbers, and other PII before sending to Sentry.

    Args:
        event: Sentry event dictionary
        hint: Additional context about the event

    Returns:
        Modified event or None to drop the event
    """
    try:
        # Sanitize request data
        if 'request' in event:
            request_data = event['request']

            # Sanitize headers
            if 'headers' in request_data:
                headers = request_data['headers']
                # Remove sensitive headers
                sensitive_headers = ['authorization', 'cookie', 'x-api-key', 'x-auth-token']
                for header in sensitive_headers:
                    if header in headers:
                        headers[header] = '[REDACTED]'
                    if header.upper() in headers:
                        headers[header.upper()] = '[REDACTED]'
                    if header.title() in headers:
                        headers[header.title()] = '[REDACTED]'

            # Sanitize query parameters
            if 'query_string' in request_data:
                request_data['query_string'] = _sanitize_value(request_data['query_string'])

            # Sanitize request body
            if 'data' in request_data:
                request_data['data'] = _sanitize_value(request_data['data'])

        # Sanitize extra context
        if 'extra' in event:
            event['extra'] = _sanitize_value(event['extra'])

        # Sanitize breadcrumbs
        if 'breadcrumbs' in event:
            for breadcrumb in event['breadcrumbs']:
                if 'data' in breadcrumb:
                    breadcrumb['data'] = _sanitize_value(breadcrumb['data'])
                if 'message' in breadcrumb:
                    breadcrumb['message'] = _sanitize_value(breadcrumb['message'])

        # Hash IP address for GDPR compliance (if present)
        if 'user' in event and 'ip_address' in event['user']:
            ip = event['user']['ip_address']
            if ip:
                # Simple hash - in production, use a proper hash function
                import hashlib
                event['user']['ip_address'] = hashlib.sha256(ip.encode()).hexdigest()[:16]

        return event
    except Exception as e:
        logger.error(f"Error in before_send hook: {e}")
        # If sanitization fails, drop the event to prevent PII leakage
        return None


def traces_sampler(sampling_context: Dict[str, Any]) -> float:
    """
    Dynamic sampling for performance monitoring.

    Adjusts sample rate based on the type of transaction to focus on
    critical paths while reducing noise.

    Args:
        sampling_context: Context about the transaction

    Returns:
        Sample rate (0.0 to 1.0)
    """
    try:
        # Extract transaction name
        transaction_name = sampling_context.get("transaction_context", {}).get("name", "")

        # Always sample critical endpoints
        critical_endpoints = [
            "/api/payments",
            "/api/checkout",
            "/api/auth/login",
            "/api/auth/register",
            "/api/subscriptions"
        ]

        for endpoint in critical_endpoints:
            if endpoint in transaction_name:
                return 1.0  # 100% sampling for critical paths

        # Lower sampling for health checks and static assets
        if any(x in transaction_name for x in ["/health", "/metrics", "/static"]):
            return 0.01  # 1% sampling

        # Default sampling rate
        return 0.1  # 10% sampling
    except Exception as e:
        logger.error(f"Error in traces_sampler: {e}")
        return 0.1  # Default to 10% if there's an error


def init_sentry(app: FastAPI) -> None:
    """
    Initialize Sentry SDK with comprehensive error tracking.

    Sets up Sentry with:
    - FastAPI integration
    - Redis integration
    - Logging integration
    - Custom before_send hook for PII filtering
    - Dynamic sampling for performance monitoring
    - Release tracking from git commit
    - Environment-specific configuration

    Args:
        app: FastAPI application instance
    """
    settings = get_settings()

    # Check if Sentry is configured
    if not hasattr(settings, 'SENTRY_DSN') or not settings.SENTRY_DSN:
        logger.warning("SENTRY_DSN not configured - error tracking disabled")
        return

    # Get release version from git commit or environment variable
    release_version = os.getenv('SENTRY_RELEASE')
    if not release_version:
        try:
            import subprocess
            git_sha = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode('ascii').strip()
            release_version = f"wwmaa-backend@{git_sha[:8]}"
        except Exception:
            release_version = "wwmaa-backend@unknown"

    # Get environment
    environment = getattr(settings, 'SENTRY_ENVIRONMENT', settings.PYTHON_ENV)

    # Get sample rates
    traces_sample_rate = getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.1)
    profiles_sample_rate = getattr(settings, 'SENTRY_PROFILES_SAMPLE_RATE', 0.1)

    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=environment,
        release=release_version,

        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",  # Group by endpoint
                failed_request_status_codes=[500, 501, 502, 503, 504],  # Track server errors
            ),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above
                event_level=logging.ERROR  # Send errors as events
            ),
        ],

        # Sampling configuration
        traces_sample_rate=traces_sample_rate,  # Default 10% for transactions
        traces_sampler=traces_sampler,  # Dynamic sampling
        profiles_sample_rate=profiles_sample_rate,  # 10% for profiling

        # Error tracking
        before_send=before_send,  # PII filtering

        # Performance
        enable_tracing=True,

        # Additional settings
        attach_stacktrace=True,  # Include stack traces
        send_default_pii=False,  # Don't send PII by default
        max_breadcrumbs=50,  # Keep last 50 breadcrumbs

        # Debug
        debug=settings.is_development,
    )

    logger.info(f"Sentry initialized for {environment} environment")
    logger.info(f"Release: {release_version}")
    logger.info(f"Traces sample rate: {traces_sample_rate}")


def add_request_context(request: Request) -> None:
    """
    Add request context to Sentry scope.

    Captures HTTP method, URL, headers, query parameters, and user agent.
    This context will be included with all errors captured during the request.

    Args:
        request: FastAPI request object
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            # Add request details
            scope.set_context("request", {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
            })

            # Add user agent context
            user_agent = request.headers.get("user-agent", "")
            if user_agent:
                scope.set_context("browser", {
                    "user_agent": user_agent,
                })

            # Add tags for filtering
            scope.set_tag("endpoint", request.url.path)
            scope.set_tag("method", request.method)

    except Exception as e:
        logger.error(f"Error adding request context to Sentry: {e}")


def add_user_context(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    role: Optional[str] = None,
    tier: Optional[str] = None,
    **extra
) -> None:
    """
    Add user context to Sentry scope.

    This information helps identify which users are affected by errors
    and enables filtering by user attributes.

    Args:
        user_id: Unique user identifier
        email: User email (will be hashed)
        username: Username
        role: User role (member, admin, etc.)
        tier: Subscription tier
        **extra: Additional custom user attributes
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            user_data = {}

            if user_id:
                user_data['id'] = user_id
            if email:
                # Hash email for privacy
                import hashlib
                user_data['email'] = hashlib.sha256(email.encode()).hexdigest()[:16]
            if username:
                user_data['username'] = username

            # Add custom fields
            if role:
                user_data['role'] = role
                scope.set_tag("user.role", role)
            if tier:
                user_data['tier'] = tier
                scope.set_tag("user.tier", tier)

            # Add any extra fields
            for key, value in extra.items():
                user_data[key] = value

            scope.set_user(user_data)

    except Exception as e:
        logger.error(f"Error adding user context to Sentry: {e}")


def clear_user_context() -> None:
    """
    Clear user context from Sentry scope.

    Should be called after request completion or on logout.
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            scope.set_user(None)
    except Exception as e:
        logger.error(f"Error clearing user context: {e}")
