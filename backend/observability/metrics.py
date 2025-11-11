"""
Performance Metrics Module for WWMAA Backend

Provides Prometheus metrics for monitoring application performance,
including HTTP requests, database queries, external API calls, and cache operations.

Metrics exported:
- http_request_duration_seconds: HTTP request latency by endpoint, method, status
- http_requests_total: Total HTTP requests by endpoint, method, status
- zerodb_query_duration_seconds: ZeroDB query latency by collection, operation
- zerodb_slow_queries_total: Count of slow ZeroDB queries (> 1 second)
- external_api_duration_seconds: External API call latency by service, endpoint
- cache_operations_total: Cache operations by operation type and result
- cache_duration_seconds: Cache operation latency
- background_job_duration_seconds: Background job execution time by job name
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)
from fastapi import Response

# Configure logging
logger = logging.getLogger(__name__)

# ==========================================
# HTTP Request Metrics
# ==========================================

# Define histogram buckets for latency measurements
# Buckets: 10ms, 50ms, 100ms, 500ms, 1s, 2.5s, 5s, 10s
LATENCY_BUCKETS = [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]

http_request_duration = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request latency in seconds",
    labelnames=["method", "endpoint", "status_code"],
    buckets=LATENCY_BUCKETS,
)

http_requests_total = Counter(
    name="http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
)

# ==========================================
# ZeroDB Query Metrics
# ==========================================

zerodb_query_duration = Histogram(
    name="zerodb_query_duration_seconds",
    documentation="ZeroDB query duration in seconds",
    labelnames=["collection", "operation"],
    buckets=LATENCY_BUCKETS,
)

zerodb_slow_queries_total = Counter(
    name="zerodb_slow_queries_total",
    documentation="Total number of slow ZeroDB queries (> 1 second)",
    labelnames=["collection", "operation"],
)

zerodb_query_errors_total = Counter(
    name="zerodb_query_errors_total",
    documentation="Total number of ZeroDB query errors",
    labelnames=["collection", "operation", "error_type"],
)

# ==========================================
# External API Metrics
# ==========================================

external_api_duration = Histogram(
    name="external_api_duration_seconds",
    documentation="External API call duration in seconds",
    labelnames=["service", "operation", "status_code"],
    buckets=LATENCY_BUCKETS,
)

external_api_requests_total = Counter(
    name="external_api_requests_total",
    documentation="Total external API requests",
    labelnames=["service", "operation", "status_code"],
)

external_api_errors_total = Counter(
    name="external_api_errors_total",
    documentation="Total external API errors",
    labelnames=["service", "operation", "error_type"],
)

# ==========================================
# Cache Metrics
# ==========================================

cache_operations_total = Counter(
    name="cache_operations_total",
    documentation="Total cache operations",
    labelnames=["operation", "result"],  # result: hit, miss, error
)

cache_duration = Histogram(
    name="cache_duration_seconds",
    documentation="Cache operation duration in seconds",
    labelnames=["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],  # Faster operations
)

cache_hit_ratio = Gauge(
    name="cache_hit_ratio",
    documentation="Cache hit ratio (hits / total operations)",
)

# ==========================================
# Background Job Metrics
# ==========================================

background_job_duration = Histogram(
    name="background_job_duration_seconds",
    documentation="Background job execution duration in seconds",
    labelnames=["job_name", "status"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],  # Up to 5 minutes
)

background_job_runs_total = Counter(
    name="background_job_runs_total",
    documentation="Total background job executions",
    labelnames=["job_name", "status"],
)

background_job_errors_total = Counter(
    name="background_job_errors_total",
    documentation="Total background job errors",
    labelnames=["job_name", "error_type"],
)

# ==========================================
# Application Health Metrics
# ==========================================

app_info = Gauge(
    name="app_info",
    documentation="Application information",
    labelnames=["version", "environment"],
)

active_requests = Gauge(
    name="active_requests",
    documentation="Number of currently active HTTP requests",
)

# ==========================================
# Decorator Functions
# ==========================================


def track_time(metric: Histogram, labels: Dict[str, str]):
    """
    Decorator to track execution time of a function.

    Args:
        metric: Prometheus Histogram metric to record time
        labels: Labels to apply to the metric

    Example:
        @track_time(zerodb_query_duration, {"collection": "users", "operation": "query"})
        def query_users():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.labels(**labels).observe(duration)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.labels(**labels).observe(duration)

        # Return appropriate wrapper based on function type
        if hasattr(func, "__await__") or hasattr(func, "__aiter__"):
            return async_wrapper
        return sync_wrapper

    return decorator


@contextmanager
def track_operation_time(metric: Histogram, labels: Dict[str, str]):
    """
    Context manager to track operation time.

    Args:
        metric: Prometheus Histogram metric to record time
        labels: Labels to apply to the metric

    Example:
        with track_operation_time(cache_duration, {"operation": "get"}):
            redis_client.get(key)
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metric.labels(**labels).observe(duration)


@contextmanager
def track_zerodb_query(collection: str, operation: str, slow_query_threshold: float = 1.0):
    """
    Context manager to track ZeroDB query performance.

    Args:
        collection: ZeroDB collection name
        operation: Operation type (query, create, update, delete, vector_search)
        slow_query_threshold: Threshold in seconds for slow query logging (default: 1.0)

    Example:
        with track_zerodb_query("users", "query"):
            result = zerodb_client.query_documents("users", filters)
    """
    start_time = time.time()
    labels = {"collection": collection, "operation": operation}

    try:
        yield
    except Exception as e:
        # Track error
        error_type = type(e).__name__
        zerodb_query_errors_total.labels(
            collection=collection, operation=operation, error_type=error_type
        ).inc()
        raise
    finally:
        duration = time.time() - start_time

        # Record query duration
        zerodb_query_duration.labels(**labels).observe(duration)

        # Track slow queries
        if duration > slow_query_threshold:
            zerodb_slow_queries_total.labels(**labels).inc()
            logger.warning(
                f"Slow ZeroDB query detected: collection={collection}, "
                f"operation={operation}, duration={duration:.3f}s"
            )


@contextmanager
def track_external_api_call(service: str, operation: str):
    """
    Context manager to track external API call performance.

    Args:
        service: Service name (stripe, beehiiv, cloudflare, ai_registry)
        operation: Operation name (create_payment, get_subscriber, etc.)

    Example:
        with track_external_api_call("stripe", "create_payment"):
            stripe.PaymentIntent.create(...)
    """
    start_time = time.time()
    status_code = "unknown"

    try:
        yield
        status_code = "200"
    except Exception as e:
        # Determine status code from exception if available
        status_code = getattr(e, "status_code", "error")
        error_type = type(e).__name__
        external_api_errors_total.labels(
            service=service, operation=operation, error_type=error_type
        ).inc()
        raise
    finally:
        duration = time.time() - start_time

        # Record API call duration
        external_api_duration.labels(
            service=service, operation=operation, status_code=str(status_code)
        ).observe(duration)

        # Record total requests
        external_api_requests_total.labels(
            service=service, operation=operation, status_code=str(status_code)
        ).inc()


@contextmanager
def track_cache_operation(operation: str):
    """
    Context manager to track cache operation performance.

    Args:
        operation: Operation type (get, set, delete, exists)

    Returns:
        Context manager that yields a result tracker function

    Example:
        with track_cache_operation("get") as track_result:
            result = redis_client.get(key)
            track_result("hit" if result else "miss")
    """
    start_time = time.time()
    result = "unknown"

    class ResultTracker:
        def __call__(self, operation_result: str):
            nonlocal result
            result = operation_result

    tracker = ResultTracker()

    try:
        yield tracker
    except Exception as e:
        result = "error"
        raise
    finally:
        duration = time.time() - start_time

        # Record operation duration
        cache_duration.labels(operation=operation).observe(duration)

        # Record operation result
        cache_operations_total.labels(operation=operation, result=result).inc()


@contextmanager
def track_background_job(job_name: str):
    """
    Context manager to track background job execution.

    Args:
        job_name: Name of the background job

    Example:
        with track_background_job("dunning_reminder"):
            send_dunning_emails()
    """
    start_time = time.time()
    status = "success"

    try:
        yield
    except Exception as e:
        status = "error"
        error_type = type(e).__name__
        background_job_errors_total.labels(job_name=job_name, error_type=error_type).inc()
        raise
    finally:
        duration = time.time() - start_time

        # Record job duration
        background_job_duration.labels(job_name=job_name, status=status).observe(duration)

        # Record job execution
        background_job_runs_total.labels(job_name=job_name, status=status).inc()


# ==========================================
# Metrics Endpoint Handler
# ==========================================


def get_metrics_handler() -> Response:
    """
    Handler function for /metrics endpoint.

    Returns:
        Response with Prometheus metrics in text format
    """
    metrics = generate_latest(REGISTRY)
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


# ==========================================
# Utility Functions
# ==========================================


def update_cache_hit_ratio():
    """
    Update the cache hit ratio gauge based on cache operations.
    Should be called periodically or after cache operations.
    """
    try:
        # Get metrics from registry
        hits = 0
        misses = 0

        for metric in REGISTRY.collect():
            if metric.name == "cache_operations_total":
                for sample in metric.samples:
                    if sample.labels.get("result") == "hit":
                        hits += sample.value
                    elif sample.labels.get("result") == "miss":
                        misses += sample.value

        total = hits + misses
        if total > 0:
            ratio = hits / total
            cache_hit_ratio.set(ratio)
    except Exception as e:
        logger.error(f"Failed to update cache hit ratio: {e}")


def set_app_info(version: str, environment: str):
    """
    Set application information metric.

    Args:
        version: Application version
        environment: Environment (development, staging, production)
    """
    app_info.labels(version=version, environment=environment).set(1)


def record_http_request(
    method: str, endpoint: str, status_code: int, duration: float
):
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint path
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    labels = {
        "method": method,
        "endpoint": endpoint,
        "status_code": str(status_code),
    }

    http_request_duration.labels(**labels).observe(duration)
    http_requests_total.labels(**labels).inc()


# ==========================================
# Metrics Summary Functions
# ==========================================


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of current metrics for health checks or debugging.

    Returns:
        Dictionary with metric summaries
    """
    summary = {
        "http_requests": {},
        "zerodb_queries": {},
        "external_apis": {},
        "cache": {},
        "background_jobs": {},
    }

    try:
        for metric in REGISTRY.collect():
            # Process HTTP request metrics
            if metric.name == "http_requests_total":
                total = sum(sample.value for sample in metric.samples)
                summary["http_requests"]["total"] = total

            # Process ZeroDB metrics
            elif metric.name == "zerodb_slow_queries_total":
                total = sum(sample.value for sample in metric.samples)
                summary["zerodb_queries"]["slow_queries"] = total

            # Process external API metrics
            elif metric.name == "external_api_requests_total":
                total = sum(sample.value for sample in metric.samples)
                summary["external_apis"]["total_requests"] = total

            # Process cache metrics
            elif metric.name == "cache_hit_ratio":
                for sample in metric.samples:
                    summary["cache"]["hit_ratio"] = sample.value

            # Process background job metrics
            elif metric.name == "background_job_runs_total":
                total = sum(sample.value for sample in metric.samples)
                summary["background_jobs"]["total_runs"] = total

    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        summary["error"] = str(e)

    return summary
