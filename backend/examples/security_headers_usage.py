"""
Security Headers Usage Examples

This file demonstrates how to use the security headers middleware
and related functionality in the WWMAA application.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from backend.middleware.security_headers import (
    SecurityHeadersMiddleware,
    get_csp_nonce
)

# =============================================================================
# Example 1: Basic Setup
# =============================================================================
# The middleware is already configured in app.py, but here's how to add it
# to a new FastAPI application:

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)


# =============================================================================
# Example 2: Using CSP Nonce in HTML Responses
# =============================================================================
@app.get("/page", response_class=HTMLResponse)
async def serve_page(request: Request):
    """
    Serve an HTML page with inline scripts that require CSP nonces.

    The nonce must be included in the script tag for it to execute
    when CSP is enforced (production mode).
    """
    # Get the CSP nonce for this request
    nonce = get_csp_nonce(request)

    # Build HTML with nonce in inline script
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Secure Page</title>
        <!-- Inline styles need nonce in production -->
        <style nonce="{nonce}">
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to WWMAA</h1>
            <p>This page uses CSP nonces for security.</p>
        </div>

        <!-- Inline scripts need nonce in production -->
        <script nonce="{nonce}">
            console.log('This script is allowed because it has a nonce!');

            // Example: Initialize analytics
            window.analytics = {{
                userId: 'user123',
                timestamp: new Date().toISOString()
            }};
        </script>

        <!-- External scripts don't need nonces (they're in CSP allowlist) -->
        <script src="https://js.stripe.com/v3/"></script>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


# =============================================================================
# Example 3: Using CSP Nonce in JSON Responses (for SPA)
# =============================================================================
@app.get("/api/page-data")
async def get_page_data(request: Request):
    """
    API endpoint that returns page data including CSP nonce.

    Useful for Single Page Applications (SPAs) that need to
    dynamically create script elements.
    """
    nonce = get_csp_nonce(request)

    return JSONResponse({
        "title": "Dashboard",
        "user": {"name": "Jane Doe", "id": "user123"},
        "cspNonce": nonce,  # Include nonce for client-side use
        "data": [1, 2, 3, 4, 5]
    })


# =============================================================================
# Example 4: Checking Security Configuration
# =============================================================================
@app.get("/api/security/config")
async def get_security_config(request: Request):
    """
    Get security configuration (development only).

    This is useful for debugging and verifying that security
    headers are configured correctly.
    """
    from backend.config import get_settings

    settings = get_settings()

    if not settings.is_development:
        return JSONResponse(
            {"error": "This endpoint is only available in development"},
            status_code=404
        )

    config = settings.get_security_headers_config()
    nonce = get_csp_nonce(request)

    return JSONResponse({
        "security_headers": config,
        "current_nonce": nonce,
        "environment": settings.PYTHON_ENV,
        "info": {
            "hsts_enabled": config["enabled"],
            "hsts_max_age_years": config["hsts_max_age"] / 31536000,
            "csp_reporting": config["csp_report_uri"],
            "preload_eligible": config["hsts_preload"]
        }
    })


# =============================================================================
# Example 5: Handling CSP Violations (Already Implemented)
# =============================================================================
# The CSP violation reporting is already handled in routes/security.py
# Here's what happens when a violation occurs:

"""
1. Browser detects CSP violation (e.g., script from untrusted domain)
2. Browser sends POST request to /api/csp-report with violation details
3. Backend logs the violation with WARNING level
4. Violation is sent to Sentry for tracking
5. In development, violation is written to csp_violations.log

Example violation report:
{
    "csp-report": {
        "document-uri": "https://wwmaa.com/dashboard",
        "violated-directive": "script-src",
        "blocked-uri": "https://evil.com/malicious.js",
        "effective-directive": "script-src",
        "original-policy": "default-src 'self'; script-src 'self' 'nonce-...'",
        "disposition": "enforce",
        "status-code": 200
    }
}
"""


# =============================================================================
# Example 6: Next.js Integration (Frontend)
# =============================================================================
"""
For Next.js frontend, you'll need to:

1. Configure security headers in next.config.js:

module.exports = {
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'X-Frame-Options',
                        value: 'DENY'
                    },
                    // ... other headers
                ]
            }
        ]
    }
}

2. Use nonces in pages (_document.tsx):

import { Html, Head, Main, NextScript } from 'next/document'

export default function Document({ nonce }: { nonce?: string }) {
    return (
        <Html>
            <Head nonce={nonce}>
                <style nonce={nonce}>
                    {/* Your inline styles */}
                </style>
            </Head>
            <body>
                <Main />
                <NextScript nonce={nonce} />
            </body>
        </Html>
    )
}

3. Fetch nonce from API:

async function getCSPNonce() {
    const response = await fetch('/api/page-data');
    const data = await response.json();
    return data.cspNonce;
}
"""


# =============================================================================
# Example 7: Testing Security Headers
# =============================================================================
"""
You can test security headers in multiple ways:

1. Automated Testing Script:
   $ python scripts/test_security_headers.py
   $ python scripts/test_security_headers.py --url https://staging.wwmaa.com

2. Manual Testing with curl:
   $ curl -I http://localhost:8000/health | grep -i "strict-transport"
   $ curl -I http://localhost:8000/health | grep -i "content-security"

3. Browser DevTools:
   - Open DevTools (F12)
   - Go to Network tab
   - Click on any request
   - View Response Headers

4. Python Testing:
   import requests

   response = requests.get('http://localhost:8000/health')
   print('HSTS:', response.headers.get('Strict-Transport-Security'))
   print('CSP:', response.headers.get('Content-Security-Policy'))
   print('X-Frame-Options:', response.headers.get('X-Frame-Options'))
"""


# =============================================================================
# Example 8: Adding New Trusted Domain
# =============================================================================
"""
If you need to add a new trusted domain (e.g., new CDN or API):

1. Edit backend/middleware/security_headers.py
2. Find the appropriate CSP directive (script-src, style-src, etc.)
3. Add the domain to the list
4. Test in development first
5. Deploy and monitor

Example (adding new script source):

def _build_production_csp(self, nonce: str) -> str:
    directives = {
        "script-src": [
            "'self'",
            f"'nonce-{nonce}'",
            "https://js.stripe.com",
            "https://new-trusted-cdn.com",  # <- Add here
        ],
        # ... other directives
    }

Remember to:
- Only add domains you completely trust
- Verify the domain uses HTTPS
- Test thoroughly before deploying
- Document why the domain was added
"""


# =============================================================================
# Example 9: Environment-Specific Behavior
# =============================================================================
@app.get("/api/environment-info")
async def get_environment_info(request: Request):
    """
    Show how CSP differs between environments.
    """
    from backend.config import get_settings

    settings = get_settings()

    # Get the CSP header that would be applied
    csp = request.headers.get("Content-Security-Policy", "Not set")

    return JSONResponse({
        "environment": settings.PYTHON_ENV,
        "is_development": settings.is_development,
        "is_production": settings.is_production,
        "csp_includes_unsafe_eval": "'unsafe-eval'" in csp,
        "csp_includes_unsafe_inline": "'unsafe-inline'" in csp,
        "csp_uses_nonces": "'nonce-" in csp,
        "csp_length": len(csp),
        "explanation": {
            "development": "Permissive CSP with unsafe-eval and unsafe-inline for Next.js HMR",
            "production": "Strict CSP with nonces, no unsafe directives"
        }
    })


# =============================================================================
# Example 10: Monitoring CSP Violations
# =============================================================================
"""
To monitor CSP violations in production:

1. Check Sentry:
   - Go to Sentry dashboard
   - Filter by tag: violation_type=csp
   - View violation details and trends

2. Query API (development only):
   $ curl http://localhost:8000/api/security/csp-violations

3. Check logs:
   $ tail -f /var/log/wwmaa/csp_violations.log

4. Set up alerts:
   - Configure Sentry alerts for high violation rates
   - Monitor for new violation patterns
   - Alert on violations from trusted pages (potential issues)

5. Analyze patterns:
   - Group by blocked-uri to find common violations
   - Group by document-uri to find problematic pages
   - Track violations over time to measure improvement
"""


# =============================================================================
# Example 11: Testing with pytest
# =============================================================================
"""
You can test security headers in your own tests:

from fastapi.testclient import TestClient
from backend.app import app

def test_security_headers():
    client = TestClient(app)
    response = client.get("/health")

    # Test HSTS
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    # Test CSP
    assert "Content-Security-Policy" in response.headers

    # Test X-Frame-Options
    assert response.headers["X-Frame-Options"] == "DENY"

    # Test nonce uniqueness
    response1 = client.get("/test")
    response2 = client.get("/test")

    nonce1 = response1.json().get("nonce")
    nonce2 = response2.json().get("nonce")

    assert nonce1 != nonce2  # Each request gets unique nonce
"""


# =============================================================================
# Example 12: Debugging CSP Issues
# =============================================================================
"""
When you encounter CSP violations:

1. Check browser console:
   - Open DevTools (F12)
   - Look for messages like: "Refused to load script..."
   - Note the blocked-uri and violated-directive

2. Temporarily use report-only mode:
   # In .env
   CSP_REPORT_ONLY=true

   This reports violations without blocking, so you can:
   - Test in production safely
   - Identify all violations before enforcing
   - Gradually tighten policy

3. Test locally:
   - Run your app in production mode locally
   - Try to trigger the issue
   - Check csp_violations.log

4. Use the testing script:
   $ python scripts/test_security_headers.py --verbose

5. Check external tools:
   - https://csp-evaluator.withgoogle.com/
   - https://securityheaders.com/
"""


if __name__ == "__main__":
    """
    This example file is for documentation purposes.

    The actual security headers are configured in:
    - backend/middleware/security_headers.py
    - backend/routes/security.py
    - backend/config.py
    - backend/app.py

    For testing, use:
    - pytest tests/test_security_headers.py
    - python scripts/test_security_headers.py

    For documentation, see:
    - docs/security/security-headers-guide.md
    - docs/security/hsts-preload.md
    """
    print("This is an example file for documentation purposes.")
    print("See backend/app.py for actual implementation.")
