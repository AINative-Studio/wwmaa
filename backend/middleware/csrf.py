"""
CSRF Protection Middleware for WWMAA Backend

This middleware implements Cross-Site Request Forgery (CSRF) protection using
the double-submit cookie pattern with cryptographic tokens. It protects against
CSRF attacks while maintaining a stateless architecture.

Security Features:
- Cryptographic token generation using secrets.token_urlsafe
- Double-submit cookie pattern (cookie + header/form validation)
- SameSite=Strict cookie attribute
- httpOnly cookies to prevent JavaScript access
- Automatic token rotation after login
- Exemption for safe HTTP methods (GET, HEAD, OPTIONS)
- Configurable public endpoint exemptions

Usage:
    from backend.middleware.csrf import CSRFMiddleware

    app.add_middleware(CSRFMiddleware)

    # In route handlers, access CSRF token:
    @app.get("/form")
    async def get_form(request: Request):
        csrf_token = request.state.csrf_token
        return {"csrf_token": csrf_token}
"""

import secrets
import logging
from typing import Callable, List, Optional, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.datastructures import Headers
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CSRFError(Exception):
    """Base exception for CSRF-related errors."""
    pass


class CSRFTokenMissingError(CSRFError):
    """Raised when CSRF token is missing from request."""
    pass


class CSRFTokenInvalidError(CSRFError):
    """Raised when CSRF token is invalid or doesn't match."""
    pass


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware using double-submit cookie pattern.

    This middleware implements CSRF protection by:
    1. Generating a cryptographic token on first request
    2. Storing token in httpOnly cookie with SameSite=Strict
    3. Requiring token in header (X-CSRF-Token) or form field for state-changing requests
    4. Validating token matches cookie value
    5. Rotating token after authentication events

    The double-submit cookie pattern provides CSRF protection without server-side
    state, making it ideal for stateless JWT-based authentication.

    Protected Methods: POST, PUT, DELETE, PATCH
    Safe Methods (Exempt): GET, HEAD, OPTIONS, TRACE

    Token Sources (in priority order):
    1. X-CSRF-Token header (for AJAX requests)
    2. csrf_token form field (for traditional forms)

    Attributes:
        cookie_name: Name of the CSRF cookie (default: "csrf_token")
        header_name: Name of the CSRF header (default: "X-CSRF-Token")
        token_length: Length of the token in bytes (default: 32)
        exempt_paths: Set of paths exempt from CSRF protection
        safe_methods: HTTP methods that don't require CSRF protection
    """

    # Constants
    COOKIE_NAME = "csrf_token"
    HEADER_NAME = "X-CSRF-Token"
    FORM_FIELD_NAME = "csrf_token"
    TOKEN_LENGTH = 32  # 32 bytes = 256 bits

    # Safe HTTP methods that don't modify state (exempt from CSRF)
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    # Default paths exempt from CSRF protection
    DEFAULT_EXEMPT_PATHS = {
        "/health",
        "/metrics",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(
        self,
        app,
        exempt_paths: Optional[List[str]] = None,
        cookie_secure: Optional[bool] = None,
        cookie_domain: Optional[str] = None,
    ):
        """
        Initialize CSRF protection middleware.

        Args:
            app: The FastAPI/Starlette application instance
            exempt_paths: Optional list of paths to exempt from CSRF protection
            cookie_secure: Whether to set Secure flag on cookie (default: True in production)
            cookie_domain: Optional domain for the cookie
        """
        super().__init__(app)

        # Configure exempt paths
        self.exempt_paths: Set[str] = set(self.DEFAULT_EXEMPT_PATHS)
        if exempt_paths:
            self.exempt_paths.update(exempt_paths)

        # Add public API endpoints to exempt paths
        # These are read-only public endpoints that don't require CSRF protection
        self.exempt_paths.update({
            "/api/blog",
            "/api/blog/posts",
            "/api/newsletter/subscribe",  # Uses CORS + rate limiting
        })

        # Cookie configuration
        self.cookie_secure = cookie_secure if cookie_secure is not None else settings.is_production
        self.cookie_domain = cookie_domain

        logger.info(
            f"CSRF middleware initialized: secure={self.cookie_secure}, "
            f"exempt_paths={len(self.exempt_paths)}"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and validate CSRF token for state-changing operations.

        This method:
        1. Checks if request should be exempt from CSRF protection
        2. Extracts or generates CSRF token
        3. For state-changing requests (POST/PUT/DELETE/PATCH):
           - Validates token from header or form matches cookie
           - Returns 403 Forbidden if validation fails
        4. Sets CSRF token in response cookie
        5. Stores token in request.state for access by route handlers

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response with CSRF cookie set (or 403 error if validation fails)
        """
        # Check if path is exempt from CSRF protection
        if self._is_exempt(request):
            logger.debug(f"CSRF check skipped for exempt path: {request.url.path}")
            response = await call_next(request)
            return response

        # Check if method is safe (doesn't modify state)
        if request.method in self.SAFE_METHODS:
            # For safe methods, just ensure token exists and store in state
            token = self._get_token_from_cookie(request)
            if not token:
                token = self._generate_token()

            request.state.csrf_token = token
            response = await call_next(request)
            self._set_token_cookie(response, token)
            return response

        # For state-changing methods (POST, PUT, DELETE, PATCH), validate token
        try:
            # Get token from cookie
            cookie_token = self._get_token_from_cookie(request)
            if not cookie_token:
                logger.warning(
                    f"CSRF validation failed: No token in cookie. "
                    f"Method={request.method}, Path={request.url.path}"
                )
                raise CSRFTokenMissingError("CSRF token missing from cookie")

            # Get token from header or form
            request_token = await self._get_token_from_request(request)
            if not request_token:
                logger.warning(
                    f"CSRF validation failed: No token in request. "
                    f"Method={request.method}, Path={request.url.path}"
                )
                raise CSRFTokenMissingError(
                    f"CSRF token required. Include '{self.HEADER_NAME}' header "
                    f"or '{self.FORM_FIELD_NAME}' form field"
                )

            # Validate tokens match (constant-time comparison)
            if not secrets.compare_digest(cookie_token, request_token):
                logger.warning(
                    f"CSRF validation failed: Token mismatch. "
                    f"Method={request.method}, Path={request.url.path}"
                )
                raise CSRFTokenInvalidError("CSRF token validation failed")

            # Validation successful
            logger.debug(
                f"CSRF validation successful. Method={request.method}, "
                f"Path={request.url.path}"
            )

            # Store token in request state for route handlers
            request.state.csrf_token = cookie_token

            # Process request
            response = await call_next(request)

            # Set cookie in response (refresh expiration)
            self._set_token_cookie(response, cookie_token)

            return response

        except CSRFTokenMissingError as e:
            return self._create_error_response(
                message=str(e),
                status_code=403,
                error_type="csrf_token_missing"
            )

        except CSRFTokenInvalidError as e:
            return self._create_error_response(
                message=str(e),
                status_code=403,
                error_type="csrf_token_invalid"
            )

        except Exception as e:
            logger.error(f"Unexpected error in CSRF middleware: {e}", exc_info=True)
            return self._create_error_response(
                message="CSRF validation error",
                status_code=403,
                error_type="csrf_validation_error"
            )

    def _is_exempt(self, request: Request) -> bool:
        """
        Check if request path should be exempt from CSRF protection.

        Args:
            request: The HTTP request

        Returns:
            True if path is exempt, False otherwise
        """
        path = request.url.path

        # Exact match
        if path in self.exempt_paths:
            return True

        # Prefix match for API documentation and metrics
        exempt_prefixes = ["/docs", "/redoc", "/openapi", "/metrics"]
        for prefix in exempt_prefixes:
            if path.startswith(prefix):
                return True

        return False

    def _generate_token(self) -> str:
        """
        Generate a cryptographically secure CSRF token.

        Uses secrets.token_urlsafe to generate a random token suitable
        for security-sensitive operations. The token is URL-safe base64.

        Returns:
            A cryptographically secure random token (43 characters for 32 bytes)
        """
        return secrets.token_urlsafe(self.TOKEN_LENGTH)

    def _get_token_from_cookie(self, request: Request) -> Optional[str]:
        """
        Extract CSRF token from cookie.

        Args:
            request: The HTTP request

        Returns:
            CSRF token string if present, None otherwise
        """
        return request.cookies.get(self.COOKIE_NAME)

    async def _get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract CSRF token from request header or form data.

        Checks in priority order:
        1. X-CSRF-Token header (for AJAX requests)
        2. csrf_token form field (for traditional form submissions)

        Args:
            request: The HTTP request

        Returns:
            CSRF token string if present, None otherwise
        """
        # Check header first (preferred for AJAX requests)
        token = request.headers.get(self.HEADER_NAME)
        if token:
            return token

        # Check form data (for traditional form submissions)
        # Only parse form for POST requests with form content type
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            try:
                form_data = await request.form()
                token = form_data.get(self.FORM_FIELD_NAME)
                if token:
                    return token
            except Exception as e:
                logger.debug(f"Could not parse form data for CSRF token: {e}")

        # Check JSON body for token (some APIs prefer this)
        if "application/json" in content_type:
            try:
                # Get raw body without consuming the stream
                body = await request.body()
                # Re-populate the stream for downstream handlers
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive

                # Try to extract token from JSON
                import json
                try:
                    json_data = json.loads(body)
                    if isinstance(json_data, dict):
                        token = json_data.get(self.FORM_FIELD_NAME)
                        if token:
                            return token
                except json.JSONDecodeError:
                    pass
            except Exception as e:
                logger.debug(f"Could not parse JSON body for CSRF token: {e}")

        return None

    def _set_token_cookie(self, response: Response, token: str) -> None:
        """
        Set CSRF token in response cookie with secure attributes.

        Cookie attributes:
        - httpOnly: True (prevent JavaScript access)
        - secure: True in production (HTTPS only)
        - samesite: "strict" (prevent cross-site requests)
        - path: "/" (available for all paths)
        - max_age: 1 year (persistent token)

        Args:
            response: The HTTP response
            token: The CSRF token to set
        """
        # Cookie max age: 1 year (31536000 seconds)
        max_age = 31536000

        response.set_cookie(
            key=self.COOKIE_NAME,
            value=token,
            max_age=max_age,
            path="/",
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=True,
            samesite="strict",
        )

    def _create_error_response(
        self,
        message: str,
        status_code: int = 403,
        error_type: str = "csrf_error"
    ) -> JSONResponse:
        """
        Create a standardized error response for CSRF failures.

        Args:
            message: Error message
            status_code: HTTP status code (default: 403)
            error_type: Error type identifier

        Returns:
            JSONResponse with error details
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": message,
                "error_type": error_type,
                "status_code": status_code,
            },
            headers={
                "X-Content-Type-Options": "nosniff",
            }
        )


def get_csrf_token(request: Request) -> Optional[str]:
    """
    Get the CSRF token from request state.

    This utility function allows route handlers to access the CSRF token
    for inclusion in responses (e.g., in forms or API responses).

    Args:
        request: The FastAPI/Starlette request object

    Returns:
        The CSRF token string, or None if not set

    Example:
        @app.get("/form")
        async def get_form(request: Request):
            csrf_token = get_csrf_token(request)
            return {"csrf_token": csrf_token}

        @app.post("/submit")
        async def submit_form(request: Request):
            # Token is automatically validated by middleware
            # Process the form...
            return {"success": True}
    """
    return getattr(request.state, "csrf_token", None)


def rotate_csrf_token(response: Response) -> str:
    """
    Generate and set a new CSRF token in the response.

    This function should be called after successful login or other
    authentication events to rotate the CSRF token and prevent
    session fixation attacks.

    Args:
        response: The HTTP response object

    Returns:
        The newly generated CSRF token

    Example:
        @app.post("/login")
        async def login(request: Request, response: Response):
            # Authenticate user...

            # Rotate CSRF token after successful login
            new_token = rotate_csrf_token(response)

            return {
                "message": "Login successful",
                "csrf_token": new_token
            }
    """
    middleware = CSRFMiddleware(app=None)
    new_token = middleware._generate_token()
    middleware._set_token_cookie(response, new_token)
    logger.info("CSRF token rotated")
    return new_token
