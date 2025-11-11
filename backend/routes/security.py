"""
Security Routes for WWMAA Backend

This module provides security-related endpoints, including:
- CSP violation reporting
- Security headers testing
- Security configuration information

Routes:
    POST /api/csp-report - Receive and log Content Security Policy violations
    GET /api/security/headers - Test security headers configuration (dev only)
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
import logging
from datetime import datetime
from backend.config import get_settings
from backend.observability import capture_message

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(tags=["security"])


class CSPViolation(BaseModel):
    """
    Content Security Policy violation report.

    This model matches the CSP violation report format sent by browsers
    when a CSP directive is violated.
    """
    model_config = ConfigDict(populate_by_name=True)

    document_uri: str = Field(..., alias="document-uri", description="URL of the page where violation occurred")
    referrer: Optional[str] = Field(default="", description="Referrer URL")
    violated_directive: str = Field(..., alias="violated-directive", description="The directive that was violated")
    effective_directive: str = Field(..., alias="effective-directive", description="The effective directive")
    original_policy: str = Field(..., alias="original-policy", description="Full CSP policy")
    disposition: str = Field(default="enforce", description="Report or enforce")
    blocked_uri: str = Field(..., alias="blocked-uri", description="URI that was blocked")
    status_code: int = Field(..., alias="status-code", description="HTTP status code")
    script_sample: Optional[str] = Field(default="", alias="script-sample", description="Sample of blocked script")


class CSPReport(BaseModel):
    """Wrapper for CSP violation report."""
    model_config = ConfigDict(populate_by_name=True)

    csp_report: CSPViolation = Field(..., alias="csp-report")


@router.post("/api/csp-report", status_code=204, include_in_schema=False)
async def csp_report(request: Request):
    """
    Receive and log Content Security Policy violation reports.

    This endpoint is called automatically by browsers when they detect
    a CSP violation. It logs the violation for analysis and debugging.

    The endpoint accepts both JSON and form-urlencoded data, as different
    browsers may send reports in different formats.

    Args:
        request: The FastAPI request object containing the CSP report

    Returns:
        204 No Content (as per CSP specification)

    Note:
        This endpoint is excluded from API documentation and returns 204
        to comply with CSP reporting specification.
    """
    try:
        # Try to parse as JSON first
        try:
            body = await request.json()
        except Exception:
            # If JSON parsing fails, try form data
            form_data = await request.form()
            body = dict(form_data)

        # Extract CSP report
        if "csp-report" in body:
            violation = body["csp-report"]
        else:
            violation = body

        # Log violation details
        logger.warning(
            f"CSP Violation detected",
            extra={
                "csp_violation": {
                    "document_uri": violation.get("document-uri", "unknown"),
                    "violated_directive": violation.get("violated-directive", "unknown"),
                    "blocked_uri": violation.get("blocked-uri", "unknown"),
                    "effective_directive": violation.get("effective-directive", "unknown"),
                    "disposition": violation.get("disposition", "enforce"),
                    "status_code": violation.get("status-code", 0),
                    "script_sample": violation.get("script-sample", "")[:100],  # Limit sample length
                },
                "user_agent": request.headers.get("user-agent", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Send to Sentry for tracking and alerting
        if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
            capture_message(
                message=f"CSP Violation: {violation.get('violated-directive', 'unknown')}",
                level="warning",
                context={
                    "csp_violation": violation,
                    "document_uri": violation.get("document-uri", "unknown"),
                    "blocked_uri": violation.get("blocked-uri", "unknown"),
                },
                tags={
                    "violation_type": "csp",
                    "directive": violation.get("violated-directive", "unknown"),
                    "environment": settings.PYTHON_ENV,
                }
            )

        # Also write to file for later analysis
        if settings.is_development:
            _log_csp_violation_to_file(violation)

    except Exception as e:
        # Don't let CSP reporting errors break the application
        logger.error(f"Error processing CSP report: {e}", exc_info=True)

    # Always return 204 No Content as per CSP spec
    return JSONResponse(content=None, status_code=204)


def _log_csp_violation_to_file(violation: Dict[str, Any]) -> None:
    """
    Log CSP violation to a file for analysis.

    This is useful in development for debugging CSP issues.

    Args:
        violation: The CSP violation report dictionary
    """
    try:
        import json
        from pathlib import Path

        # Create logs directory if it doesn't exist
        log_dir = Path("/var/log/wwmaa")
        if not log_dir.exists():
            # Fall back to current directory in development
            log_dir = Path(".")

        log_file = log_dir / "csp_violations.log"

        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "violation": violation
            }) + "\n")

    except Exception as e:
        logger.debug(f"Could not write CSP violation to file: {e}")


@router.get("/api/security/headers")
async def test_security_headers(request: Request):
    """
    Test security headers configuration.

    This endpoint returns information about the security headers
    that would be applied to responses. Useful for development and testing.

    Only available in development environment.

    Args:
        request: The FastAPI request object

    Returns:
        Dictionary with security headers information

    Raises:
        HTTPException: If not in development environment
    """
    if not settings.is_development:
        raise HTTPException(
            status_code=404,
            detail="This endpoint is only available in development mode"
        )

    # Get CSP nonce from request
    from backend.middleware.security_headers import get_csp_nonce
    nonce = get_csp_nonce(request)

    return {
        "environment": settings.PYTHON_ENV,
        "csp_nonce": nonce,
        "headers_info": {
            "hsts": {
                "enabled": True,
                "max_age": "31536000",  # 1 year
                "include_subdomains": True,
                "preload": True,
                "description": "Forces HTTPS connections for 1 year"
            },
            "x_frame_options": {
                "value": "DENY",
                "description": "Prevents page from being embedded in frames"
            },
            "x_content_type_options": {
                "value": "nosniff",
                "description": "Prevents MIME sniffing"
            },
            "referrer_policy": {
                "value": "strict-origin-when-cross-origin",
                "description": "Controls referrer information in requests"
            },
            "permissions_policy": {
                "disabled_features": [
                    "geolocation",
                    "microphone",
                    "camera",
                    "payment",
                    "usb"
                ],
                "description": "Restricts browser features to prevent abuse"
            },
            "csp": {
                "enabled": True,
                "nonce_based": True,
                "report_uri": "/api/csp-report",
                "environment_specific": True,
                "development_mode": settings.is_development,
                "description": "Content Security Policy with nonce support"
            }
        },
        "testing_recommendations": {
            "tools": [
                "securityheaders.com - Overall security headers grade",
                "observatory.mozilla.org - Mozilla Observatory scan",
                "Browser DevTools - Check for CSP violations in console"
            ],
            "csp_testing": [
                "Open browser DevTools console",
                "Look for CSP violation messages",
                "Check /api/csp-report endpoint receives violations",
                "Verify no violations in normal operation"
            ],
            "hsts_preload": [
                "Verify HSTS header is present on all HTTPS responses",
                "Consider submitting to hstspreload.org after testing",
                "WARNING: HSTS preload is irreversible, test thoroughly first"
            ]
        }
    }


@router.get("/api/security/csp-violations")
async def get_csp_violations(request: Request, limit: int = 50):
    """
    Get recent CSP violations for analysis.

    This endpoint returns recent CSP violations logged by the application.
    Useful for debugging CSP configuration issues.

    Only available in development environment.

    Args:
        request: The FastAPI request object
        limit: Maximum number of violations to return (default: 50)

    Returns:
        List of recent CSP violations

    Raises:
        HTTPException: If not in development environment
    """
    if not settings.is_development:
        raise HTTPException(
            status_code=404,
            detail="This endpoint is only available in development mode"
        )

    try:
        import json
        from pathlib import Path

        log_dir = Path("/var/log/wwmaa")
        if not log_dir.exists():
            log_dir = Path(".")

        log_file = log_dir / "csp_violations.log"

        if not log_file.exists():
            return {
                "violations": [],
                "message": "No CSP violations logged yet"
            }

        # Read last N lines from file
        violations = []
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    violations.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        # Sort by timestamp (newest first)
        violations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "violations": violations,
            "count": len(violations),
            "total_logged": len(lines)
        }

    except Exception as e:
        logger.error(f"Error reading CSP violations: {e}", exc_info=True)
        return {
            "error": "Could not read CSP violations",
            "message": str(e)
        }
