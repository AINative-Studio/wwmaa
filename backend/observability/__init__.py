"""
Observability Module for WWMAA Backend

Provides performance monitoring, metrics collection, error tracking,
and alerting capabilities.
"""

from .metrics import (
    http_request_duration,
    http_requests_total,
    zerodb_query_duration,
    zerodb_slow_queries_total,
    external_api_duration,
    cache_operations_total,
    cache_duration,
    background_job_duration,
    get_metrics_handler,
)

from .errors import (
    init_sentry,
    add_request_context,
    add_user_context,
    clear_user_context,
)

from .error_utils import (
    capture_exception,
    capture_message,
    add_breadcrumb,
    set_tag,
    set_context,
    track_payment_error,
    track_auth_error,
    track_subscription_error,
    track_api_error,
    track_database_error,
    start_transaction,
    start_span,
)

__all__ = [
    # Metrics
    "http_request_duration",
    "http_requests_total",
    "zerodb_query_duration",
    "zerodb_slow_queries_total",
    "external_api_duration",
    "cache_operations_total",
    "cache_duration",
    "background_job_duration",
    "get_metrics_handler",

    # Error tracking initialization
    "init_sentry",
    "add_request_context",
    "add_user_context",
    "clear_user_context",

    # Error tracking utilities
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "set_tag",
    "set_context",

    # Domain-specific error tracking
    "track_payment_error",
    "track_auth_error",
    "track_subscription_error",
    "track_api_error",
    "track_database_error",

    # Performance monitoring
    "start_transaction",
    "start_span",
]
