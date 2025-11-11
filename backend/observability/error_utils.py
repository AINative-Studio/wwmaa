"""
Error Tracking Utility Functions

Provides high-level utility functions for custom error tracking,
breadcrumb management, and context enrichment.

Usage:
    from backend.observability.error_utils import (
        capture_exception,
        capture_message,
        add_breadcrumb,
        set_tag,
        set_context,
        track_payment_error,
        track_auth_error
    )

    # Capture exception with context
    try:
        process_payment(amount)
    except Exception as e:
        capture_exception(e, {
            'payment': {
                'amount': amount,
                'currency': 'usd'
            }
        })
        raise

    # Add breadcrumb for tracking flow
    add_breadcrumb('payment', 'Payment initiated', {'amount': 100})
"""

import logging
from typing import Optional, Dict, Any, Literal
import sentry_sdk
from sentry_sdk import capture_exception as sentry_capture_exception
from sentry_sdk import capture_message as sentry_capture_message

logger = logging.getLogger(__name__)

# Type definitions for breadcrumb categories
BreadcrumbCategory = Literal[
    "auth",
    "payment",
    "subscription",
    "database",
    "cache",
    "api",
    "http",
    "navigation",
    "user",
    "business_logic"
]

# Type definitions for message levels
MessageLevel = Literal["debug", "info", "warning", "error", "fatal"]


def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    level: Optional[str] = None,
    fingerprint: Optional[list] = None
) -> str:
    """
    Capture an exception and send to Sentry with additional context.

    Args:
        exception: Exception to capture
        context: Additional context data (will be added as 'extra' context)
        tags: Tags for filtering and grouping
        level: Error level (debug, info, warning, error, fatal)
        fingerprint: Custom fingerprint for error grouping

    Returns:
        Event ID from Sentry

    Example:
        >>> try:
        ...     result = stripe.Subscription.create(...)
        ... except stripe.error.StripeError as e:
        ...     capture_exception(e, {
        ...         'payment': {
        ...             'customer_id': customer_id,
        ...             'amount': amount
        ...         }
        ...     }, tags={'payment_type': 'subscription'})
    """
    try:
        with sentry_sdk.push_scope() as scope:
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)

            # Add tags
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)

            # Set level
            if level:
                scope.set_level(level)

            # Set custom fingerprint for grouping
            if fingerprint:
                scope.fingerprint = fingerprint

            event_id = sentry_capture_exception(exception)
            logger.debug(f"Exception captured in Sentry: {event_id}")
            return event_id

    except Exception as e:
        logger.error(f"Error capturing exception in Sentry: {e}")
        return ""


def capture_message(
    message: str,
    level: MessageLevel = "info",
    context: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    Capture a message (non-exception event) and send to Sentry.

    Useful for logging important events that aren't errors but should
    be tracked (e.g., successful payments, user registrations).

    Args:
        message: Message to log
        level: Severity level (debug, info, warning, error, fatal)
        context: Additional context data
        tags: Tags for filtering

    Returns:
        Event ID from Sentry

    Example:
        >>> capture_message(
        ...     "Subscription upgraded successfully",
        ...     level="info",
        ...     context={
        ...         'user': {'id': user_id},
        ...         'subscription': {'tier': 'premium'}
        ...     },
        ...     tags={'event': 'subscription_upgrade'}
        ... )
    """
    try:
        with sentry_sdk.push_scope() as scope:
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)

            # Add tags
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)

            # Set level
            scope.set_level(level)

            event_id = sentry_capture_message(message, level=level)
            logger.debug(f"Message captured in Sentry: {event_id}")
            return event_id

    except Exception as e:
        logger.error(f"Error capturing message in Sentry: {e}")
        return ""


def add_breadcrumb(
    category: BreadcrumbCategory,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    level: MessageLevel = "info"
) -> None:
    """
    Add a breadcrumb to track execution flow.

    Breadcrumbs are chronological events that help understand the
    sequence of actions leading to an error.

    Args:
        category: Category of breadcrumb (auth, payment, api, etc.)
        message: Human-readable message
        data: Additional data
        level: Severity level

    Example:
        >>> add_breadcrumb('payment', 'Payment initiated', {
        ...     'amount': 100,
        ...     'currency': 'usd',
        ...     'customer_id': 'cus_123'
        ... })
        >>> add_breadcrumb('api', 'Stripe API called', {
        ...     'endpoint': '/v1/subscriptions',
        ...     'method': 'POST'
        ... })
    """
    try:
        sentry_sdk.add_breadcrumb(
            category=category,
            message=message,
            data=data or {},
            level=level
        )
    except Exception as e:
        logger.error(f"Error adding breadcrumb: {e}")


def set_tag(key: str, value: str) -> None:
    """
    Set a tag on the current scope.

    Tags are key-value pairs for filtering and grouping errors.

    Args:
        key: Tag key
        value: Tag value

    Example:
        >>> set_tag('payment_method', 'stripe')
        >>> set_tag('subscription_tier', 'premium')
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag(key, value)
    except Exception as e:
        logger.error(f"Error setting tag: {e}")


def set_context(name: str, context: Dict[str, Any]) -> None:
    """
    Set additional context data on the current scope.

    Context provides structured data that will be displayed in Sentry.

    Args:
        name: Context name (e.g., 'payment', 'subscription')
        context: Context data dictionary

    Example:
        >>> set_context('payment', {
        ...     'amount': 100,
        ...     'currency': 'usd',
        ...     'payment_method': 'card',
        ...     'customer_id': 'cus_123'
        ... })
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            scope.set_context(name, context)
    except Exception as e:
        logger.error(f"Error setting context: {e}")


# ============================================================================
# Domain-Specific Error Tracking Helpers
# ============================================================================

def track_payment_error(
    error: Exception,
    customer_id: Optional[str] = None,
    amount: Optional[float] = None,
    currency: str = "usd",
    payment_method: Optional[str] = None,
    **extra
) -> str:
    """
    Track payment-related errors with rich context.

    Args:
        error: Payment exception
        customer_id: Stripe customer ID
        amount: Payment amount
        currency: Payment currency
        payment_method: Payment method used
        **extra: Additional payment context

    Returns:
        Event ID from Sentry
    """
    context = {
        'payment': {
            'customer_id': customer_id,
            'amount': amount,
            'currency': currency,
            'payment_method': payment_method,
            **extra
        }
    }

    tags = {
        'error_type': 'payment',
        'currency': currency
    }

    if payment_method:
        tags['payment_method'] = payment_method

    # Critical error - use custom fingerprint for grouping
    fingerprint = ['payment-error', type(error).__name__]

    return capture_exception(
        error,
        context=context,
        tags=tags,
        level='error',
        fingerprint=fingerprint
    )


def track_auth_error(
    error: Exception,
    username: Optional[str] = None,
    auth_method: str = "password",
    reason: Optional[str] = None,
    **extra
) -> str:
    """
    Track authentication-related errors.

    Args:
        error: Authentication exception
        username: Username attempting to authenticate
        auth_method: Authentication method (password, oauth, etc.)
        reason: Failure reason
        **extra: Additional auth context

    Returns:
        Event ID from Sentry
    """
    context = {
        'authentication': {
            'username': username,
            'auth_method': auth_method,
            'reason': reason,
            **extra
        }
    }

    tags = {
        'error_type': 'authentication',
        'auth_method': auth_method
    }

    # Critical error - use custom fingerprint
    fingerprint = ['auth-error', type(error).__name__, auth_method]

    return capture_exception(
        error,
        context=context,
        tags=tags,
        level='error',
        fingerprint=fingerprint
    )


def track_subscription_error(
    error: Exception,
    customer_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    tier: Optional[str] = None,
    action: Optional[str] = None,
    **extra
) -> str:
    """
    Track subscription-related errors.

    Args:
        error: Subscription exception
        customer_id: Stripe customer ID
        subscription_id: Stripe subscription ID
        tier: Subscription tier
        action: Action being performed (create, update, cancel)
        **extra: Additional subscription context

    Returns:
        Event ID from Sentry
    """
    context = {
        'subscription': {
            'customer_id': customer_id,
            'subscription_id': subscription_id,
            'tier': tier,
            'action': action,
            **extra
        }
    }

    tags = {
        'error_type': 'subscription',
        'subscription_tier': tier or 'unknown'
    }

    if action:
        tags['subscription_action'] = action

    fingerprint = ['subscription-error', type(error).__name__, action or 'unknown']

    return capture_exception(
        error,
        context=context,
        tags=tags,
        level='error',
        fingerprint=fingerprint
    )


def track_api_error(
    error: Exception,
    endpoint: str,
    method: str = "GET",
    status_code: Optional[int] = None,
    **extra
) -> str:
    """
    Track external API errors.

    Args:
        error: API exception
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        **extra: Additional API context

    Returns:
        Event ID from Sentry
    """
    context = {
        'api': {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            **extra
        }
    }

    tags = {
        'error_type': 'api',
        'api_endpoint': endpoint,
        'http_method': method
    }

    if status_code:
        tags['status_code'] = str(status_code)

    fingerprint = ['api-error', endpoint, str(status_code or 'unknown')]

    return capture_exception(
        error,
        context=context,
        tags=tags,
        level='error',
        fingerprint=fingerprint
    )


def track_database_error(
    error: Exception,
    operation: str,
    table: Optional[str] = None,
    **extra
) -> str:
    """
    Track database-related errors.

    Args:
        error: Database exception
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table/collection name
        **extra: Additional database context

    Returns:
        Event ID from Sentry
    """
    context = {
        'database': {
            'operation': operation,
            'table': table,
            **extra
        }
    }

    tags = {
        'error_type': 'database',
        'db_operation': operation
    }

    if table:
        tags['db_table'] = table

    fingerprint = ['database-error', operation, table or 'unknown']

    return capture_exception(
        error,
        context=context,
        tags=tags,
        level='error',
        fingerprint=fingerprint
    )


# ============================================================================
# Performance Monitoring Helpers
# ============================================================================

def start_transaction(
    name: str,
    op: str = "http.server",
    **kwargs
) -> Any:
    """
    Start a performance transaction.

    Args:
        name: Transaction name (e.g., endpoint path)
        op: Operation type (e.g., http.server, db.query)
        **kwargs: Additional transaction parameters

    Returns:
        Transaction object

    Example:
        >>> with start_transaction('/api/payments', 'http.server'):
        ...     process_payment()
    """
    try:
        return sentry_sdk.start_transaction(name=name, op=op, **kwargs)
    except Exception as e:
        logger.error(f"Error starting transaction: {e}")
        # Return a no-op context manager
        from contextlib import nullcontext
        return nullcontext()


def start_span(
    op: str,
    description: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Start a performance span within a transaction.

    Args:
        op: Operation type (e.g., db.query, http.client)
        description: Span description
        **kwargs: Additional span parameters

    Returns:
        Span object

    Example:
        >>> with start_span('db.query', 'Fetch user data'):
        ...     user = db.query(User).filter_by(id=user_id).first()
    """
    try:
        return sentry_sdk.start_span(op=op, description=description, **kwargs)
    except Exception as e:
        logger.error(f"Error starting span: {e}")
        from contextlib import nullcontext
        return nullcontext()
