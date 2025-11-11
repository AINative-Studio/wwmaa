"""
OpenTelemetry Tracing Configuration for WWMAA Backend

This module provides OpenTelemetry distributed tracing instrumentation
for all API endpoints, database operations, external API calls, and caching.

Features:
- Automatic FastAPI instrumentation
- OTLP exporter (gRPC and HTTP)
- Environment-based sampling strategies
- Resource attributes (service name, version, environment)
- Support for multiple observability backends (Honeycomb, Jaeger, Grafana Tempo)

Environment Variables:
- OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL
- OTEL_EXPORTER_OTLP_HEADERS: Headers (e.g., x-honeycomb-team=api_key)
- OTEL_SERVICE_NAME: Service name for traces
- OTEL_DEPLOYMENT_ENVIRONMENT: Environment (staging, production)
- OTEL_TRACES_SAMPLER: Sampling strategy
- OTEL_TRACES_SAMPLER_ARG: Sampling ratio (0.0-1.0)
"""

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import (
    AlwaysOnSampler,
    ParentBasedTraceIdRatio,
    TraceIdRatioBased,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Configure logging
logger = logging.getLogger(__name__)

# Global tracer provider
_tracer_provider: Optional[TracerProvider] = None
_is_initialized = False


def initialize_tracing(
    app=None,
    service_name: Optional[str] = None,
    service_version: str = "1.0.0",
    environment: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    otlp_headers: Optional[str] = None,
    exporter_type: str = "grpc",  # 'grpc', 'http', or 'console'
    sampling_rate: Optional[float] = None,
) -> TracerProvider:
    """
    Initialize OpenTelemetry tracing for the application.

    This function should be called once at application startup, before
    creating the FastAPI app instance.

    Args:
        app: FastAPI application instance (optional, for auto-instrumentation)
        service_name: Name of the service (defaults to OTEL_SERVICE_NAME env var)
        service_version: Version of the service
        environment: Deployment environment (defaults to PYTHON_ENV)
        otlp_endpoint: OTLP exporter endpoint (defaults to OTEL_EXPORTER_OTLP_ENDPOINT)
        otlp_headers: OTLP headers as comma-separated key=value pairs
        exporter_type: Type of exporter ('grpc', 'http', or 'console')
        sampling_rate: Sampling rate 0.0-1.0 (None for environment-based)

    Returns:
        TracerProvider instance
    """
    global _tracer_provider, _is_initialized

    if _is_initialized:
        logger.warning("OpenTelemetry tracing already initialized")
        return _tracer_provider

    # Get configuration from environment or parameters
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "wwmaa-backend")
    environment = environment or os.getenv("PYTHON_ENV", "development")
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    otlp_headers_str = otlp_headers or os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")

    # Parse OTLP headers
    headers_dict = {}
    if otlp_headers_str:
        for header in otlp_headers_str.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers_dict[key.strip()] = value.strip()

    # Create resource attributes
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
        "service.namespace": "wwmaa",
        "service.instance.id": os.getenv("HOSTNAME", "local"),
    })

    # Determine sampling strategy
    if sampling_rate is not None:
        # Explicit sampling rate provided
        if sampling_rate >= 1.0:
            sampler = AlwaysOnSampler()
            logger.info("Using AlwaysOnSampler (100% sampling)")
        else:
            sampler = ParentBasedTraceIdRatio(sampling_rate)
            logger.info(f"Using ParentBasedTraceIdRatio with rate={sampling_rate}")
    elif environment == "staging":
        # Staging: 100% sampling
        sampler = AlwaysOnSampler()
        logger.info("Staging environment: Using AlwaysOnSampler (100% sampling)")
    elif environment == "production":
        # Production: 10% sampling by default
        sampler_arg = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "0.1"))
        sampler = ParentBasedTraceIdRatio(sampler_arg)
        logger.info(f"Production environment: Using ParentBasedTraceIdRatio (rate={sampler_arg})")
    else:
        # Development: 100% sampling
        sampler = AlwaysOnSampler()
        logger.info("Development environment: Using AlwaysOnSampler (100% sampling)")

    # Create tracer provider
    _tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Configure span exporter
    if exporter_type == "console" or not otlp_endpoint:
        # Console exporter (for development/testing)
        exporter = ConsoleSpanExporter()
        logger.info("Using ConsoleSpanExporter (development mode)")
    elif exporter_type == "http":
        # HTTP OTLP exporter
        exporter = HTTPExporter(
            endpoint=otlp_endpoint,
            headers=headers_dict,
            timeout=10,
        )
        logger.info(f"Using HTTP OTLPSpanExporter: {otlp_endpoint}")
    else:
        # gRPC OTLP exporter (default)
        exporter = GRPCExporter(
            endpoint=otlp_endpoint,
            headers=tuple(headers_dict.items()) if headers_dict else None,
            timeout=10,
        )
        logger.info(f"Using gRPC OTLPSpanExporter: {otlp_endpoint}")

    # Add batch span processor
    span_processor = BatchSpanProcessor(exporter)
    _tracer_provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Auto-instrument libraries
    try:
        # Instrument requests library (for external API calls)
        RequestsInstrumentor().instrument()
        logger.info("Instrumented requests library")
    except Exception as e:
        logger.warning(f"Failed to instrument requests library: {e}")

    try:
        # Instrument Redis (for caching)
        RedisInstrumentor().instrument()
        logger.info("Instrumented Redis client")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis client: {e}")

    # Auto-instrument FastAPI application
    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                excluded_urls="/health,/metrics",  # Exclude health/metrics endpoints
                tracer_provider=_tracer_provider,
            )
            logger.info("Instrumented FastAPI application")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI application: {e}")

    _is_initialized = True
    logger.info(
        f"OpenTelemetry tracing initialized: "
        f"service={service_name}, "
        f"environment={environment}, "
        f"exporter={exporter_type}"
    )

    return _tracer_provider


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance for creating custom spans.

    Args:
        name: Name of the tracer (typically __name__ of the module)

    Returns:
        Tracer instance

    Example:
        >>> tracer = get_tracer(__name__)
        >>> with tracer.start_as_current_span("my_operation") as span:
        >>>     span.set_attribute("key", "value")
        >>>     do_work()
    """
    return trace.get_tracer(name)


def is_tracing_enabled() -> bool:
    """
    Check if tracing is enabled.

    Returns:
        True if tracing is initialized, False otherwise
    """
    return _is_initialized


def shutdown_tracing():
    """
    Shutdown tracing and flush all pending spans.

    This should be called during application shutdown to ensure
    all spans are exported before the application exits.
    """
    global _tracer_provider, _is_initialized

    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
            logger.info("OpenTelemetry tracing shutdown successfully")
        except Exception as e:
            logger.error(f"Error during tracing shutdown: {e}")

    _is_initialized = False
    _tracer_provider = None
