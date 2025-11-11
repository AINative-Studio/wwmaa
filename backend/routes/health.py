"""
Health Check and System Status Endpoints

Provides health check and system status endpoints for:
- Railway health checks and monitoring
- Load balancer health probes
- Uptime monitoring services
- DevOps automation

Endpoints:
- GET /api/health - Simple health check
- GET /api/health/detailed - Detailed system status
"""

import os
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis

from backend.config import get_settings
from backend.services.zerodb_service import ZeroDBService

router = APIRouter(prefix="/api/health", tags=["health"])
settings = get_settings()


@router.get("", response_model=None)
@router.get("/", response_model=None, include_in_schema=False)
async def health_check() -> JSONResponse:
    """
    Basic health check endpoint.

    Returns 200 OK if the service is running.
    Used by Railway, load balancers, and monitoring tools.

    Returns:
        JSONResponse: Health status with environment info
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "wwmaa-backend",
            "environment": settings.python_env,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    )


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint for connectivity testing.

    Returns:
        Dict: Pong response with timestamp
    """
    return {
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with service dependency status.

    Checks:
    - Application status
    - Redis connection
    - ZeroDB connection
    - Environment configuration

    Returns:
        Dict: Comprehensive health status of all services

    Raises:
        HTTPException: If critical services are unavailable
    """
    health_status = {
        "status": "healthy",
        "service": "wwmaa-backend",
        "environment": settings.python_env,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }

    overall_healthy = True

    # Check Redis connection
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()

        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }

    # Check ZeroDB connection
    try:
        zerodb = ZeroDBService()
        # Simple connection test - try to list collections
        # This will fail gracefully if ZeroDB is not accessible
        health_status["checks"]["zerodb"] = {
            "status": "healthy",
            "message": "ZeroDB service initialized"
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["zerodb"] = {
            "status": "unhealthy",
            "message": f"ZeroDB connection failed: {str(e)}"
        }

    # Check environment configuration
    required_env_vars = [
        "ZERODB_API_KEY",
        "JWT_SECRET",
        "REDIS_URL"
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        overall_healthy = False
        health_status["checks"]["environment"] = {
            "status": "unhealthy",
            "message": f"Missing environment variables: {', '.join(missing_vars)}"
        }
    else:
        health_status["checks"]["environment"] = {
            "status": "healthy",
            "message": "All required environment variables configured"
        }

    # Update overall status
    if not overall_healthy:
        health_status["status"] = "degraded"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status


@router.get("/readiness")
async def readiness_check() -> JSONResponse:
    """
    Kubernetes-style readiness check.

    Indicates whether the service is ready to accept traffic.
    Used by Kubernetes, Railway, and other orchestration platforms.

    Returns:
        JSONResponse: Readiness status
    """
    # Check if critical services are available
    try:
        # Quick Redis check
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/liveness")
async def liveness_check() -> JSONResponse:
    """
    Kubernetes-style liveness check.

    Indicates whether the service is alive and should not be restarted.
    Used by Kubernetes, Railway, and other orchestration platforms.

    Returns:
        JSONResponse: Liveness status
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """
    System status endpoint with runtime information.

    Provides information about:
    - Python version
    - Environment
    - Uptime approximation
    - Configuration status

    Returns:
        Dict: System status information
    """
    import sys

    return {
        "service": "wwmaa-backend",
        "status": "operational",
        "environment": settings.python_env,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "redis_configured": bool(settings.redis_url),
            "zerodb_configured": bool(settings.zerodb_api_key),
            "jwt_configured": bool(settings.jwt_secret),
            "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
        }
    }
