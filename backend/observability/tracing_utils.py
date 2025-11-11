"""
OpenTelemetry Tracing Utilities

Helper functions and decorators for creating and managing custom spans
throughout the WWMAA backend application.

Provides:
- Decorator for automatic span creation
- Context manager for manual span creation
- Helper functions for span attributes and errors
- Trace ID extraction for log correlation
"""

import functools
import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)


def trace_function(
    span_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """
    Decorator to automatically create a span for a function.

    Args:
        span_name: Name of the span (defaults to function name)
        attributes: Additional attributes to set on the span

    Example:
        >>> @trace_function(span_name="database.query", attributes={"db.system": "zerodb"})
        >>> def query_database(query: str):
        >>>     return execute_query(query)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = span_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                # Set default attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Set custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    set_span_error(span, e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = span_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                # Set default attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Set custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    set_span_error(span, e)
                    raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def with_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    tracer_name: str = __name__,
):
    """
    Context manager for creating a custom span.

    Args:
        name: Name of the span
        attributes: Attributes to set on the span
        tracer_name: Name of the tracer (defaults to __name__)

    Yields:
        Span instance

    Example:
        >>> with with_span("custom_operation", {"operation.type": "batch"}) as span:
        >>>     span.set_attribute("batch.size", 100)
        >>>     process_batch()
    """
    tracer = trace.get_tracer(tracer_name)

    with tracer.start_as_current_span(name) as span:
        # Set initial attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            set_span_error(span, e)
            raise


def add_span_attributes(**kwargs: Any):
    """
    Add attributes to the current span.

    Args:
        **kwargs: Key-value pairs to add as span attributes

    Example:
        >>> add_span_attributes(
        >>>     user_id="user_123",
        >>>     operation="create",
        >>>     resource_type="application"
        >>> )
    """
    span = trace.get_current_span()

    if span is None or not span.is_recording():
        logger.debug("No active span to add attributes to")
        return

    for key, value in kwargs.items():
        if value is not None:
            # Convert non-primitive types to strings
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(key, value)
            else:
                span.set_attribute(key, str(value))


def set_span_error(span: Optional[Span], exception: Exception):
    """
    Set error status and record exception on a span.

    Args:
        span: Span to set error on (if None, uses current span)
        exception: Exception that occurred

    Example:
        >>> try:
        >>>     risky_operation()
        >>> except Exception as e:
        >>>     set_span_error(None, e)
        >>>     raise
    """
    if span is None:
        span = trace.get_current_span()

    if span is None or not span.is_recording():
        logger.debug("No active span to set error on")
        return

    # Set span status to ERROR
    span.set_status(Status(StatusCode.ERROR, str(exception)))

    # Set error attribute
    span.set_attribute("error", True)
    span.set_attribute("error.type", type(exception).__name__)
    span.set_attribute("error.message", str(exception))

    # Record exception event with stack trace
    span.record_exception(
        exception,
        attributes={
            "exception.escaped": False
        }
    )


def get_trace_id() -> Optional[str]:
    """
    Get the trace ID of the current span for log correlation.

    Returns:
        Trace ID as a hex string, or None if no active span

    Example:
        >>> trace_id = get_trace_id()
        >>> logger.info(f"[trace_id={trace_id}] Processing request")
    """
    span = trace.get_current_span()

    if span is None or not span.is_recording():
        return None

    span_context = span.get_span_context()
    if span_context is None or not span_context.is_valid:
        return None

    # Format trace ID as hex string
    trace_id = format(span_context.trace_id, "032x")
    return trace_id


def get_span_id() -> Optional[str]:
    """
    Get the span ID of the current span for log correlation.

    Returns:
        Span ID as a hex string, or None if no active span

    Example:
        >>> span_id = get_span_id()
        >>> logger.info(f"[span_id={span_id}] Operation completed")
    """
    span = trace.get_current_span()

    if span is None or not span.is_recording():
        return None

    span_context = span.get_span_context()
    if span_context is None or not span_context.is_valid:
        return None

    # Format span ID as hex string
    span_id = format(span_context.span_id, "016x")
    return span_id


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into HTTP headers for distributed tracing.

    Args:
        headers: Existing headers dictionary

    Returns:
        Headers with trace context injected

    Example:
        >>> headers = {"Content-Type": "application/json"}
        >>> headers = inject_trace_context(headers)
        >>> response = requests.post(url, headers=headers, json=data)
    """
    propagator = TraceContextTextMapPropagator()
    propagator.inject(headers)
    return headers


def extract_trace_context(headers: Dict[str, str]) -> trace.SpanContext:
    """
    Extract trace context from HTTP headers.

    Args:
        headers: HTTP headers dictionary

    Returns:
        Extracted span context

    Example:
        >>> context = extract_trace_context(request.headers)
        >>> # Use context to create child spans
    """
    propagator = TraceContextTextMapPropagator()
    context = propagator.extract(headers)
    return context


def add_user_context(user_id: Optional[str], role: Optional[str] = None):
    """
    Add user context to the current span.

    Args:
        user_id: User ID from authentication
        role: User role (member, admin, etc.)

    Example:
        >>> add_user_context(user_id="user_123", role="member")
    """
    if user_id:
        add_span_attributes(
            **{
                "user.id": user_id,
                "user.role": role if role else "unknown",
            }
        )


def add_http_context(
    method: str,
    url: str,
    status_code: Optional[int] = None,
    user_agent: Optional[str] = None,
):
    """
    Add HTTP request context to the current span.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL or path
        status_code: HTTP status code (if response)
        user_agent: User-Agent header

    Example:
        >>> add_http_context(
        >>>     method="POST",
        >>>     url="/api/applications",
        >>>     status_code=201
        >>> )
    """
    attributes = {
        "http.method": method,
        "http.url": url,
    }

    if status_code:
        attributes["http.status_code"] = status_code

    if user_agent:
        attributes["http.user_agent"] = user_agent

    add_span_attributes(**attributes)


# Import asyncio for async detection
import asyncio
