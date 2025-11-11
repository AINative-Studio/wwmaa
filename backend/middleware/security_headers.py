"""
Security Headers Middleware for WWMAA Backend

This middleware adds comprehensive security headers to all HTTP responses,
including Content Security Policy (CSP) with nonce support, HSTS, frame protection,
and other security-related headers to mitigate common web vulnerabilities.

Features:
- Strict Transport Security (HSTS) with preload support
- Content Security Policy (CSP) with cryptographic nonces
- Frame protection (X-Frame-Options, frame-ancestors)
- MIME sniffing prevention (X-Content-Type-Options)
- Referrer policy control
- Permissions policy for browser features
- Environment-specific CSP policies

Usage:
    from backend.middleware.security_headers import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)
"""

import secrets
from typing import Callable, Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.config import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds comprehensive security headers to all responses.

    This middleware implements security best practices by adding headers that:
    - Force HTTPS connections (HSTS)
    - Prevent clickjacking attacks (X-Frame-Options, frame-ancestors)
    - Prevent MIME sniffing (X-Content-Type-Options)
    - Control referrer information (Referrer-Policy)
    - Restrict browser features (Permissions-Policy)
    - Implement Content Security Policy (CSP) with nonces

    The CSP policy is environment-specific, with more permissive policies
    in development for easier debugging and strict policies in production.
    """

    def __init__(self, app):
        """
        Initialize the security headers middleware.

        Args:
            app: The FastAPI/Starlette application instance
        """
        super().__init__(app)
        self.environment = settings.PYTHON_ENV
        self.is_development = settings.is_development
        self.is_production = settings.is_production

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to the response.

        This method:
        1. Generates a cryptographic nonce for CSP
        2. Stores the nonce in request state for use in responses
        3. Processes the request
        4. Adds all security headers to the response

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response with security headers added
        """
        # Generate cryptographic nonce for CSP
        nonce = self._generate_nonce()

        # Store nonce in request state so it can be accessed by routes
        request.state.csp_nonce = nonce

        # Process the request
        response = await call_next(request)

        # Add security headers to response
        self._add_security_headers(response, nonce)

        return response

    def _generate_nonce(self) -> str:
        """
        Generate a cryptographically secure nonce for CSP.

        The nonce is a random base64-encoded string used to allow
        specific inline scripts and styles while blocking all others.
        This provides strong protection against XSS attacks.

        Returns:
            A 32-character base64-encoded random string
        """
        # Generate 24 random bytes (192 bits) which will become 32 base64 characters
        return secrets.token_urlsafe(24)

    def _add_security_headers(self, response: Response, nonce: str) -> None:
        """
        Add all security headers to the response.

        Args:
            response: The HTTP response object
            nonce: The CSP nonce for this request
        """
        # Add standard security headers
        for header, value in self._get_standard_headers().items():
            response.headers[header] = value

        # Add Content Security Policy with nonce
        csp_policy = self._build_csp_policy(nonce)
        response.headers["Content-Security-Policy"] = csp_policy

    def _get_standard_headers(self) -> Dict[str, str]:
        """
        Get standard security headers that don't require nonces.

        Returns:
            Dictionary of header names to values
        """
        headers = {
            # Strict-Transport-Security (HSTS)
            # Force HTTPS for 1 year (31536000 seconds)
            # Include all subdomains
            # Preload eligible (can be submitted to browser preload lists)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

            # X-Frame-Options
            # Prevent the page from being embedded in frames/iframes
            # Protects against clickjacking attacks
            "X-Frame-Options": "DENY",

            # X-Content-Type-Options
            # Prevent MIME sniffing (browsers must respect declared Content-Type)
            # Protects against MIME confusion attacks
            "X-Content-Type-Options": "nosniff",

            # Referrer-Policy
            # Control how much referrer information is sent with requests
            # strict-origin-when-cross-origin: Send full URL for same-origin,
            # only origin for cross-origin HTTPS, nothing for HTTP
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # X-XSS-Protection (Legacy)
            # Enable XSS filtering in older browsers (modern browsers use CSP)
            # mode=block prevents page from rendering if attack detected
            "X-XSS-Protection": "1; mode=block",

            # X-DNS-Prefetch-Control
            # Disable DNS prefetching to prevent potential privacy leaks
            "X-DNS-Prefetch-Control": "off",

            # X-Download-Options
            # Prevent Internet Explorer from executing downloads in site's context
            "X-Download-Options": "noopen",

            # X-Permitted-Cross-Domain-Policies
            # Restrict Adobe Flash and PDF cross-domain access
            "X-Permitted-Cross-Domain-Policies": "none",
        }

        # Add Permissions-Policy
        headers["Permissions-Policy"] = self._build_permissions_policy()

        return headers

    def _build_permissions_policy(self) -> str:
        """
        Build Permissions-Policy header to control browser features.

        This header restricts access to powerful browser features like
        geolocation, camera, microphone, etc. to prevent abuse.

        Returns:
            Permissions-Policy header value
        """
        # Disable all potentially dangerous features
        # Allow fullscreen and picture-in-picture for video playback
        policies = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "fullscreen=(self)",
            "picture-in-picture=(self)",
            "display-capture=()",
            "web-share=()",
            "autoplay=(self)",
        ]

        return ", ".join(policies)

    def _build_csp_policy(self, nonce: str) -> str:
        """
        Build Content Security Policy with environment-specific rules.

        Development: More permissive to allow hot reload and debugging
        Production: Strict policy with nonces for inline scripts/styles

        Args:
            nonce: The CSP nonce for this request

        Returns:
            CSP policy string
        """
        if self.is_development:
            return self._build_development_csp(nonce)
        else:
            return self._build_production_csp(nonce)

    def _build_development_csp(self, nonce: str) -> str:
        """
        Build permissive CSP policy for development environment.

        This policy is more permissive to allow:
        - Next.js hot module replacement (unsafe-eval)
        - Inline styles for development (unsafe-inline)
        - Broader image and connect sources

        Args:
            nonce: The CSP nonce for this request

        Returns:
            Development CSP policy string
        """
        directives = {
            # Allow resources from same origin by default
            "default-src": ["'self'"],

            # Scripts: self, unsafe-eval (for HMR), unsafe-inline (fallback), trusted CDNs
            "script-src": [
                "'self'",
                "'unsafe-inline'",  # Allow inline scripts in dev
                "'unsafe-eval'",    # Required for Next.js hot reload
                "https://js.stripe.com",
                "https://www.googletagmanager.com",
                "https://www.google-analytics.com",
            ],

            # Styles: self, unsafe-inline (for dev), Google Fonts
            "style-src": [
                "'self'",
                "'unsafe-inline'",  # Allow inline styles in dev
                "https://fonts.googleapis.com",
            ],

            # Images: self, data URIs, HTTPS, blob URLs (very permissive for dev)
            "img-src": [
                "'self'",
                "data:",
                "https:",
                "blob:",
            ],

            # Fonts: self, Google Fonts
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com",
            ],

            # AJAX/WebSocket: self, API endpoints
            "connect-src": [
                "'self'",
                "http://localhost:*",
                "http://127.0.0.1:*",
                "ws://localhost:*",
                "ws://127.0.0.1:*",
                "https://api.ainative.studio",
                "https://api.stripe.com",
                "https://api.beehiiv.com",
            ],

            # Media: self, Cloudflare Stream
            "media-src": [
                "'self'",
                "https://*.cloudflarestream.com",
            ],

            # Frames: self, Stripe, Cloudflare Stream
            "frame-src": [
                "'self'",
                "https://js.stripe.com",
                "https://*.cloudflarestream.com",
            ],

            # Workers: self
            "worker-src": [
                "'self'",
                "blob:",
            ],

            # Object/Embed: none (block Flash, Java applets, etc.)
            "object-src": ["'none'"],

            # Base tag: self only
            "base-uri": ["'self'"],

            # Form submissions: self only
            "form-action": ["'self'"],

            # Frame ancestors: none (prevent clickjacking)
            "frame-ancestors": ["'none'"],
        }

        return self._format_csp_directives(directives)

    def _build_production_csp(self, nonce: str) -> str:
        """
        Build strict CSP policy for production environment.

        This policy enforces strong security:
        - No unsafe-inline or unsafe-eval
        - Nonces required for inline scripts/styles
        - Strict allowlist of trusted domains
        - Upgrade insecure requests
        - Block mixed content
        - CSP violation reporting

        Args:
            nonce: The CSP nonce for this request

        Returns:
            Production CSP policy string
        """
        directives = {
            # Default: none (explicit allowlist required)
            "default-src": ["'none'"],

            # Scripts: self, nonce, trusted CDNs (NO unsafe-inline or unsafe-eval)
            "script-src": [
                "'self'",
                f"'nonce-{nonce}'",
                "https://js.stripe.com",
                "https://www.googletagmanager.com",
                "https://www.google-analytics.com",
            ],

            # Styles: self, nonce, Google Fonts
            "style-src": [
                "'self'",
                f"'nonce-{nonce}'",
                "https://fonts.googleapis.com",
            ],

            # Images: self, data URIs, trusted domains
            "img-src": [
                "'self'",
                "data:",
                "https://api.ainative.studio",
                "https://storage.ainative.studio",
                "https://www.googletagmanager.com",
                "https://www.google-analytics.com",
            ],

            # Fonts: self, Google Fonts
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com",
            ],

            # AJAX/WebSocket: self, API endpoints
            "connect-src": [
                "'self'",
                "https://api.ainative.studio",
                "https://api.stripe.com",
                "https://api.beehiiv.com",
                "https://www.google-analytics.com",
            ],

            # Media: self, Cloudflare Stream
            "media-src": [
                "'self'",
                "https://*.cloudflarestream.com",
            ],

            # Frames: self, Stripe, Cloudflare Stream
            "frame-src": [
                "'self'",
                "https://js.stripe.com",
                "https://*.cloudflarestream.com",
            ],

            # Workers: self, blob
            "worker-src": [
                "'self'",
                "blob:",
            ],

            # Object/Embed: none (block Flash, Java applets, etc.)
            "object-src": ["'none'"],

            # Base tag: self only
            "base-uri": ["'self'"],

            # Form submissions: self only
            "form-action": ["'self'"],

            # Frame ancestors: none (prevent clickjacking)
            "frame-ancestors": ["'none'"],
        }

        # Add additional production-only directives
        additional_directives = [
            "upgrade-insecure-requests",      # Upgrade HTTP to HTTPS
            "block-all-mixed-content",        # Block HTTP content on HTTPS pages
            "report-uri /api/csp-report",     # Report violations
        ]

        policy = self._format_csp_directives(directives)

        # Add additional directives (they don't have values)
        for directive in additional_directives:
            policy += f"; {directive}"

        return policy

    def _format_csp_directives(self, directives: Dict[str, list]) -> str:
        """
        Format CSP directives dictionary into a CSP policy string.

        Args:
            directives: Dictionary mapping directive names to lists of values

        Returns:
            Formatted CSP policy string
        """
        policy_parts = []

        for directive, sources in directives.items():
            sources_str = " ".join(sources)
            policy_parts.append(f"{directive} {sources_str}")

        return "; ".join(policy_parts)


def get_csp_nonce(request: Request) -> Optional[str]:
    """
    Get the CSP nonce from the request state.

    This utility function allows routes and templates to access
    the CSP nonce for including in inline scripts and styles.

    Args:
        request: The FastAPI/Starlette request object

    Returns:
        The CSP nonce string, or None if not set

    Example:
        @app.get("/page")
        async def page(request: Request):
            nonce = get_csp_nonce(request)
            return HTMLResponse(f'<script nonce="{nonce}">alert("Safe!");</script>')
    """
    return getattr(request.state, "csp_nonce", None)
