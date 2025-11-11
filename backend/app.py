"""
WWMAA Backend Application

FastAPI application entry point with configuration management,
CORS settings, health check endpoints, performance monitoring,
and error tracking with Sentry.
"""

import warnings
warnings.filterwarnings("ignore", message="on_event is deprecated")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from backend.config import get_settings
from backend.routes import auth
from backend.routes import applications
from backend.routes import application_submission
from backend.routes import payments
from backend.routes import checkout
from backend.routes import billing
from backend.routes import stripe_webhooks
from backend.routes import event_attendees
from backend.routes import event_rsvps
from backend.routes import search
from backend.routes import newsletter
from backend.routes import blog
from backend.routes import security
from backend.routes import privacy
from backend.routes import health
from backend.routes.admin import search_analytics
from backend.routes.admin import indexing
from backend.routes.admin import training_analytics
from backend.routes.webhooks import beehiiv
from backend.middleware.metrics_middleware import MetricsMiddleware, get_request_id
from backend.middleware.security_headers import SecurityHeadersMiddleware
from backend.middleware.csrf import CSRFMiddleware
from backend.observability.metrics import (
    get_metrics_handler,
    set_app_info,
    get_metrics_summary,
)
from backend.observability import init_sentry, capture_exception
import logging
import sentry_sdk

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry tracing (before FastAPI app creation)
# This must be done before creating the FastAPI app to ensure
# auto-instrumentation works correctly
_tracing_enabled = False
try:
    from backend.observability.tracing import initialize_tracing, is_tracing_enabled

    if settings.is_tracing_enabled:
        otel_config = settings.get_opentelemetry_config()
        logger.info(f"Initializing OpenTelemetry tracing: {otel_config['service_name']}")

        # Note: We'll instrument the app after it's created in startup_event
        _tracing_enabled = True
    else:
        logger.info("OpenTelemetry tracing disabled (no endpoint configured)")
except Exception as e:
    logger.warning(f"Failed to initialize OpenTelemetry tracing: {e}")
    _tracing_enabled = False

# Create FastAPI application
app = FastAPI(
    title="WWMAA Backend API",
    description="Women's Martial Arts Association of America - Backend API",
    version="1.0.0",
    debug=settings.debug,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Initialize Sentry error tracking BEFORE adding middleware
# This ensures Sentry can capture all errors
init_sentry(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware (US-069)
# This must be added AFTER CORS to ensure headers are applied to CORS responses
if settings.SECURITY_HEADERS_ENABLED:
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")

# Add CSRF protection middleware (US-071)
# This must be added AFTER CORS and security headers
# CSRF protection uses double-submit cookie pattern with SameSite=Strict
if getattr(settings, 'CSRF_PROTECTION_ENABLED', True):
    app.add_middleware(CSRFMiddleware)
    logger.info("CSRF protection middleware enabled")

# Add metrics middleware for request ID tracking and custom metrics
app.add_middleware(MetricsMiddleware)

# Initialize Prometheus instrumentation
# This auto-instruments all endpoints with basic metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health", "/"],
    env_var_name="PROMETHEUS_ENABLED",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Configure histogram buckets for latency measurements
instrumentator.add(
    lambda info: info.request.headers.get("content-length", 0),
)


# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that captures all unhandled exceptions to Sentry.

    This ensures that any error not explicitly handled is tracked and alerted.
    """
    # Capture exception to Sentry
    event_id = capture_exception(
        exc,
        context={
            "request": {
                "url": str(request.url),
                "method": request.method,
                "client_host": request.client.host if request.client else None,
            }
        },
        tags={
            "endpoint": request.url.path,
            "method": request.method,
        }
    )

    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "sentry_event_id": event_id,
            "path": request.url.path,
            "method": request.method,
        }
    )

    # Return error response
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": event_id,
            "message": "An unexpected error occurred. Our team has been notified."
        }
    )


# HTTP exception handler for 500 errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP exception handler that captures 500-level errors to Sentry.
    """
    # Only capture server errors (5xx)
    if exc.status_code >= 500:
        event_id = capture_exception(
            exc,
            context={
                "request": {
                    "url": str(request.url),
                    "method": request.method,
                    "client_host": request.client.host if request.client else None,
                }
            },
            tags={
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": str(exc.status_code),
            }
        )

        logger.error(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={
                "sentry_event_id": event_id,
                "status_code": exc.status_code,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_id": event_id,
            }
        )

    # For client errors (4xx), return normally without Sentry capture
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Register routers
app.include_router(health.router)  # Health check endpoints (must be first for Railway)
app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(application_submission.router)
app.include_router(payments.router)
app.include_router(checkout.router)
app.include_router(billing.router)
app.include_router(stripe_webhooks.router)
app.include_router(event_attendees.router)
app.include_router(event_rsvps.router)
app.include_router(search.router)
app.include_router(newsletter.router)
app.include_router(blog.router)
app.include_router(security.router)
app.include_router(privacy.router)
app.include_router(beehiiv.router)
app.include_router(search_analytics.router)
app.include_router(indexing.router)
app.include_router(training_analytics.router)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.

    Logs configuration, validates environment, and initializes monitoring on startup.
    """
    logger.info(f"Starting WWMAA Backend in {settings.PYTHON_ENV} environment")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"ZeroDB API: {settings.ZERODB_API_BASE_URL}")

    # Log security headers status
    if settings.SECURITY_HEADERS_ENABLED:
        logger.info("Security headers: ENABLED")
        logger.info(f"HSTS max-age: {settings.HSTS_MAX_AGE} seconds")
        logger.info(f"CSP report URI: {settings.CSP_REPORT_URI}")
    else:
        logger.warning("Security headers: DISABLED")

    # Log Sentry status
    if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
        logger.info("Sentry error tracking: ENABLED")
        logger.info(f"Sentry environment: {getattr(settings, 'SENTRY_ENVIRONMENT', settings.PYTHON_ENV)}")
    else:
        logger.warning("Sentry error tracking: DISABLED (no DSN configured)")

    # Log non-sensitive configuration info
    logger.debug(f"JWT algorithm: {settings.JWT_ALGORITHM}")
    logger.debug(f"Access token expiration: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    logger.debug(f"Refresh token expiration: {settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days")

    # Initialize OpenTelemetry tracing
    if _tracing_enabled:
        try:
            otel_config = settings.get_opentelemetry_config()
            initialize_tracing(
                app=app,
                service_name=otel_config["service_name"],
                service_version="1.0.0",
                environment=otel_config["environment"],
                otlp_endpoint=otel_config["endpoint"],
                otlp_headers=otel_config["headers"],
                exporter_type=otel_config["exporter_type"],
                sampling_rate=None,  # Use environment-based sampling
            )
            logger.info("OpenTelemetry tracing initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")

    # Initialize Prometheus metrics
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics initialized at /metrics endpoint")

    # Set application info metric
    set_app_info(version="1.0.0", environment=settings.PYTHON_ENV)
    logger.info("Application metrics configured successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down WWMAA Backend")

    # Flush Sentry events before shutdown
    if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
        sentry_sdk.flush(timeout=2)
        logger.info("Sentry events flushed")


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Basic API information
    """
    return {
        "name": "WWMAA Backend API",
        "version": "1.0.0",
        "environment": settings.PYTHON_ENV,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status of the application
    """
    return {
        "status": "healthy",
        "environment": settings.PYTHON_ENV,
        "debug": settings.debug
    }


@app.get("/metrics/summary")
async def metrics_summary(request: Request):
    """
    Metrics summary endpoint (development only).

    Returns a human-readable summary of application metrics.
    Only available in development environment.

    Returns:
        Metrics summary with request ID
    """
    if not settings.is_development:
        return {"error": "This endpoint is only available in development mode"}

    request_id = get_request_id(request)
    summary = get_metrics_summary()

    return {
        "request_id": request_id,
        "metrics": summary,
        "environment": settings.PYTHON_ENV,
    }


@app.get("/config/info")
async def config_info():
    """
    Configuration information endpoint (development only).

    Returns non-sensitive configuration information.
    Only available in development environment.

    Returns:
        Configuration information
    """
    if not settings.is_development:
        return {"error": "This endpoint is only available in development mode"}

    return {
        "environment": settings.PYTHON_ENV,
        "debug": settings.debug,
        "log_level": settings.log_level,
        "cors_origins": settings.cors_origins,
        "backend_url": settings.PYTHON_BACKEND_URL,
        "jwt_algorithm": settings.JWT_ALGORITHM,
        "jwt_access_token_expire_minutes": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        "jwt_refresh_token_expire_days": settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        "test_coverage_minimum": settings.TEST_COVERAGE_MINIMUM,
        "zerodb_api_url": str(settings.ZERODB_API_BASE_URL),
        "from_email": settings.FROM_EMAIL,
        "sentry_enabled": bool(hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN),
    }


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
