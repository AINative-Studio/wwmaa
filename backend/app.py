"""
WWMAA Backend Application

FastAPI application entry point with configuration management,
CORS settings, and health check endpoints.
"""

import warnings
warnings.filterwarnings("ignore", message="on_event is deprecated")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.routes import auth
from backend.routes import applications
from backend.routes import application_submission
from backend.routes import payments
from backend.routes import checkout
from backend.routes import billing
from backend.routes import webhooks
from backend.routes import event_attendees
from backend.routes import event_rsvps
from backend.routes import search
from backend.routes.admin import search_analytics
from backend.routes.admin import indexing
import logging

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="WWMAA Backend API",
    description="Women's Martial Arts Association of America - Backend API",
    version="1.0.0",
    debug=settings.debug,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(application_submission.router)
app.include_router(payments.router)
app.include_router(checkout.router)
app.include_router(billing.router)
app.include_router(webhooks.router)
app.include_router(event_attendees.router)
app.include_router(event_rsvps.router)
app.include_router(search.router)
app.include_router(search_analytics.router)
app.include_router(indexing.router)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.

    Logs configuration and validates environment on startup.
    """
    logger.info(f"Starting WWMAA Backend in {settings.PYTHON_ENV} environment")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"ZeroDB API: {settings.ZERODB_API_BASE_URL}")

    # Log non-sensitive configuration info
    logger.debug(f"JWT algorithm: {settings.JWT_ALGORITHM}")
    logger.debug(f"Access token expiration: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    logger.debug(f"Refresh token expiration: {settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down WWMAA Backend")


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
        "from_email": settings.FROM_EMAIL
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
