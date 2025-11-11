# CSRF Protection Implementation Guide

## Overview

This document describes the Cross-Site Request Forgery (CSRF) protection implementation for the WWMAA backend API. CSRF protection is implemented using the double-submit cookie pattern with cryptographic tokens, providing robust security without requiring server-side session state.

**Implementation Date:** 2025-11-10
**User Story:** US-071
**Security Level:** High Priority

---

## Table of Contents

1. [What is CSRF?](#what-is-csrf)
2. [Security Architecture](#security-architecture)
3. [Implementation Details](#implementation-details)
4. [Usage Guide](#usage-guide)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

---

## What is CSRF?

Cross-Site Request Forgery (CSRF) is an attack that forces authenticated users to execute unwanted actions on a web application. An attacker tricks a victim's browser into making requests to a web application where the victim is authenticated.

### Example Attack Scenario

1. User logs into `wwmaa.com` and receives authentication cookies
2. User visits malicious site `evil.com` (in another tab)
3. `evil.com` contains hidden form that POSTs to `wwmaa.com/api/profile/delete`
4. Browser automatically includes authentication cookies with the request
5. Without CSRF protection, the request succeeds and deletes the user's profile

### How Our Protection Works

The double-submit cookie pattern prevents this attack by:

1. **Token Generation**: Server generates cryptographic token on first request
2. **Cookie Storage**: Token stored in httpOnly cookie (inaccessible to JavaScript)
3. **Request Validation**: Client must include token in request header or form field
4. **Token Matching**: Server validates that cookie token matches request token
5. **Attack Prevention**: Malicious sites cannot read the cookie (Same-Origin Policy) or inject the header (CORS)

---

## Security Architecture

### Double-Submit Cookie Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                      CSRF Protection Flow                    │
└─────────────────────────────────────────────────────────────┘

1. First Request (GET /api/data)
   ┌─────────┐                          ┌─────────┐
   │ Client  │─────── GET /api/data ───→│ Server  │
   │         │                           │         │
   │         │←─── Response + Cookie ───┤         │
   └─────────┘    csrf_token=ABC123     └─────────┘
                  (httpOnly, SameSite=Strict)

2. State-Changing Request (POST /api/update)
   ┌─────────┐                          ┌─────────┐
   │ Client  │─── POST /api/update ────→│ Server  │
   │         │    Header: X-CSRF-Token: │         │
   │         │            ABC123         │ Validate│
   │         │    Cookie: csrf_token=   │ Match   │
   │         │            ABC123         │ ✓       │
   │         │←─────── Success ─────────┤         │
   └─────────┘                          └─────────┘

3. CSRF Attack Attempt
   ┌─────────┐                          ┌─────────┐
   │Malicious│─── POST /api/delete ────→│ Server  │
   │  Site   │    Cookie: csrf_token=   │         │
   │         │            ABC123         │ Validate│
   │         │    (No header - can't    │ Fail    │
   │         │     access due to CORS)  │ ✗       │
   │         │←───── 403 Forbidden ─────┤         │
   └─────────┘                          └─────────┘
```

### Security Properties

| Property | Implementation | Protection Against |
|----------|---------------|-------------------|
| **Cryptographic Tokens** | `secrets.token_urlsafe(32)` | Token prediction attacks |
| **httpOnly Cookies** | `httponly=True` | XSS token theft |
| **SameSite Strict** | `samesite="strict"` | Cross-site cookie sending |
| **Constant-Time Comparison** | `secrets.compare_digest()` | Timing attacks |
| **Token Rotation** | After login events | Session fixation |
| **HTTPS Only (Production)** | `secure=True` | Man-in-the-middle |

---

## Implementation Details

### Middleware Configuration

The CSRF middleware is configured in `backend/app.py`:

```python
from backend.middleware.csrf import CSRFMiddleware

# Add CSRF protection middleware
if getattr(settings, 'CSRF_PROTECTION_ENABLED', True):
    app.add_middleware(CSRFMiddleware)
    logger.info("CSRF protection middleware enabled")
```

### Protected HTTP Methods

| Method | Protected | Reason |
|--------|-----------|--------|
| GET | ✗ | Read-only (safe method) |
| HEAD | ✗ | Read-only (safe method) |
| OPTIONS | ✗ | Read-only (safe method) |
| POST | ✓ | Creates/modifies data |
| PUT | ✓ | Updates data |
| DELETE | ✓ | Deletes data |
| PATCH | ✓ | Modifies data |

### Exempt Endpoints

The following endpoints are exempt from CSRF protection:

```python
# Health and monitoring
/health
/metrics
/metrics/summary

# API documentation
/docs
/redoc
/openapi.json

# Public read-only endpoints
/api/blog
/api/blog/posts
```

### Cookie Attributes

```python
Set-Cookie: csrf_token=<token>;
            Max-Age=31536000;     # 1 year
            Path=/;               # All paths
            HttpOnly;             # No JavaScript access
            SameSite=Strict;      # No cross-site sending
            Secure;               # HTTPS only (production)
```

---

## Usage Guide

### For Frontend Developers

#### 1. AJAX/Fetch Requests

Include the CSRF token in the `X-CSRF-Token` header:

```javascript
// Get CSRF token from cookie
function getCsrfToken() {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

// Make protected request
async function updateProfile(data) {
  const csrfToken = getCsrfToken();

  const response = await fetch('/api/profile/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,
    },
    credentials: 'include',  // Include cookies
    body: JSON.stringify(data),
  });

  return response.json();
}
```

#### 2. Traditional HTML Forms

Include the CSRF token as a hidden field:

```html
<form action="/api/profile/update" method="POST">
  <!-- Get token from backend endpoint -->
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}" />

  <input type="text" name="name" />
  <button type="submit">Update</button>
</form>
```

#### 3. Getting CSRF Token from Backend

```javascript
// Option 1: Make GET request to any endpoint
const response = await fetch('/api/profile', {
  credentials: 'include'
});
// Token is now in cookie, extract as shown above

// Option 2: Dedicated endpoint (if implemented)
const tokenResponse = await fetch('/api/csrf-token');
const { csrf_token } = await tokenResponse.json();
```

### For Backend Developers

#### 1. Accessing CSRF Token in Route Handlers

```python
from fastapi import Request
from backend.middleware.csrf import get_csrf_token

@app.get("/form")
async def get_form(request: Request):
    """Return form with CSRF token."""
    csrf_token = get_csrf_token(request)

    return {
        "csrf_token": csrf_token,
        "form_html": f'<input type="hidden" name="csrf_token" value="{csrf_token}" />'
    }
```

#### 2. Rotating CSRF Token After Login

The login endpoint automatically rotates the CSRF token:

```python
from fastapi import Response
from backend.middleware.csrf import rotate_csrf_token

@app.post("/login")
async def login(credentials: LoginRequest, response: Response):
    # Authenticate user...

    # Rotate CSRF token after successful login
    new_token = rotate_csrf_token(response)

    return {
        "message": "Login successful",
        "csrf_token": new_token  # Optional: return to client
    }
```

#### 3. Adding Custom Exempt Paths

```python
from backend.middleware.csrf import CSRFMiddleware

app.add_middleware(
    CSRFMiddleware,
    exempt_paths=[
        "/api/webhook/stripe",
        "/api/webhook/beehiiv",
        "/api/public/newsletter",
    ]
)
```

#### 4. Disabling CSRF for Specific Routes

For routes that need to be exempt (e.g., webhooks):

```python
# Option 1: Add to exempt_paths in middleware configuration

# Option 2: Add to DEFAULT_EXEMPT_PATHS in csrf.py
# (requires code change)
```

---

## Testing

### Unit Tests

Run CSRF middleware tests:

```bash
# Run all CSRF tests
pytest backend/tests/test_csrf.py -v

# Run with coverage
pytest backend/tests/test_csrf.py --cov=backend.middleware.csrf --cov-report=html

# Run specific test
pytest backend/tests/test_csrf.py::test_post_with_valid_token_succeeds -v
```

### Integration Tests

Test CSRF protection with authenticated endpoints:

```bash
# Run integration tests
pytest backend/tests/test_csrf_integration.py -v
```

### Manual Testing with cURL

```bash
# 1. Get CSRF token from GET request
curl -v http://localhost:8000/api/profile \
  -c cookies.txt

# Extract token from cookies.txt
TOKEN=$(grep csrf_token cookies.txt | awk '{print $7}')

# 2. Make POST request with token
curl -X POST http://localhost:8000/api/profile/update \
  -H "X-CSRF-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name": "John Doe"}'

# 3. Try POST without token (should fail with 403)
curl -X POST http://localhost:8000/api/profile/update \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name": "John Doe"}'
```

### Testing Token Rotation

```bash
# 1. Get initial token
curl -v http://localhost:8000/api/profile -c cookies1.txt
TOKEN1=$(grep csrf_token cookies1.txt | awk '{print $7}')

# 2. Login (rotates token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "X-CSRF-Token: $TOKEN1" \
  -H "Content-Type: application/json" \
  -b cookies1.txt \
  -c cookies2.txt \
  -d '{"email":"user@example.com","password":"Password123!"}'

# 3. Extract new token
TOKEN2=$(grep csrf_token cookies2.txt | awk '{print $7}')

# 4. Verify tokens are different
echo "Token 1: $TOKEN1"
echo "Token 2: $TOKEN2"
```

---

## Troubleshooting

### Common Issues

#### 1. 403 Forbidden: "CSRF token missing"

**Cause:** Request doesn't include CSRF token

**Solution:**
```javascript
// Add token to request header
headers: {
  'X-CSRF-Token': getCsrfToken()
}
```

#### 2. 403 Forbidden: "CSRF token validation failed"

**Cause:** Token in header doesn't match token in cookie

**Possible Reasons:**
- Using old/cached token
- Cookie was cleared but header token wasn't updated
- Multiple tabs with different tokens
- Token rotation occurred

**Solution:**
```javascript
// Always get fresh token before request
const token = getCsrfToken();
if (!token) {
  // Refresh page or re-fetch token
  window.location.reload();
}
```

#### 3. Token Not Found in Cookie

**Cause:** Cookie not set or httpOnly preventing JavaScript access

**Solution:**
```javascript
// Make initial GET request to set cookie
await fetch('/api/profile', { credentials: 'include' });

// Then make POST request
const token = getCsrfToken();
```

#### 4. CORS Errors with CSRF

**Cause:** CORS headers not properly configured

**Solution:**
```python
# Ensure CORS middleware is configured before CSRF
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,  # Required for cookies
    allow_headers=["X-CSRF-Token"],  # Allow CSRF header
)
```

#### 5. Token Rotation Breaking Concurrent Requests

**Cause:** Multiple requests in flight when token rotates

**Solution:**
```javascript
// Queue requests during login/token rotation
let isRotating = false;
let requestQueue = [];

async function makeRequest(url, options) {
  if (isRotating) {
    // Wait for rotation to complete
    await new Promise(resolve => requestQueue.push(resolve));
  }

  return fetch(url, options);
}

async function login(credentials) {
  isRotating = true;
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
  isRotating = false;

  // Process queued requests
  requestQueue.forEach(resolve => resolve());
  requestQueue = [];

  return response;
}
```

---

## Security Considerations

### Threat Model

| Attack Vector | Mitigation | Status |
|--------------|------------|--------|
| **CSRF Attack** | Double-submit cookie pattern | ✓ Protected |
| **Token Prediction** | Cryptographic randomness (256 bits) | ✓ Protected |
| **Token Theft (XSS)** | httpOnly cookies | ✓ Protected |
| **Token Theft (MITM)** | Secure flag, HTTPS enforcement | ✓ Protected |
| **Cross-Site Cookie** | SameSite=Strict | ✓ Protected |
| **Session Fixation** | Token rotation after login | ✓ Protected |
| **Timing Attacks** | Constant-time comparison | ✓ Protected |
| **Token Replay** | Tokens valid until rotation | ⚠️ Partial |

### Best Practices

#### 1. Always Use HTTPS in Production

```python
# Production configuration
CSRFMiddleware(
    app,
    cookie_secure=True,  # Requires HTTPS
)
```

#### 2. Rotate Tokens on Privilege Change

```python
# After password change
rotate_csrf_token(response)

# After role change
rotate_csrf_token(response)

# After sensitive operations
rotate_csrf_token(response)
```

#### 3. Monitor CSRF Failures

```python
# Add logging for CSRF failures
logger.warning(
    f"CSRF validation failed: {error_type}",
    extra={
        "ip": request.client.host,
        "path": request.url.path,
        "user_agent": request.headers.get("user-agent"),
    }
)
```

#### 4. Rate Limit CSRF Failures

```python
# Implement rate limiting for repeated CSRF failures
# This could indicate an attack in progress
from backend.middleware.rate_limit import rate_limit

@app.post("/protected")
@rate_limit(requests=10, window=60)  # 10 failed attempts per minute
async def protected_route():
    pass
```

### Known Limitations

1. **Token Reuse**: Tokens are valid until rotation (not single-use)
   - **Mitigation**: Short token lifetime, rotation on auth events
   - **Risk Level**: Low (requires successful CSRF attack to matter)

2. **Client-Side Token Storage**: JavaScript can read cookie for header
   - **Mitigation**: httpOnly prevents theft, not reading
   - **Risk Level**: Very Low (legitimate use case)

3. **Subdomain Attacks**: Subdomains can set cookies for parent domain
   - **Mitigation**: Use specific cookie domain, audit subdomains
   - **Risk Level**: Low (requires subdomain compromise)

---

## Compliance

### OWASP Top 10

This implementation addresses:
- **A01:2021 – Broken Access Control**: Prevents unauthorized state changes
- **A02:2021 – Cryptographic Failures**: Uses cryptographically secure tokens
- **A05:2021 – Security Misconfiguration**: Secure cookie defaults

### Security Headers

CSRF protection works in conjunction with:
- **Content-Security-Policy**: Prevents XSS that could steal tokens
- **X-Frame-Options**: Prevents clickjacking attacks
- **Strict-Transport-Security**: Enforces HTTPS
- **SameSite Cookies**: Additional CSRF protection layer

---

## References

- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Double Submit Cookie Pattern](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#double-submit-cookie)
- [SameSite Cookie Attribute](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-10 | 1.0 | Initial implementation (US-071) | Backend Team |

---

## Support

For questions or issues with CSRF protection:

1. **Check Logs**: Review application logs for CSRF validation errors
2. **Review Tests**: Run test suite to verify configuration
3. **Security Team**: Contact security team for policy questions
4. **Documentation**: Review this guide and OWASP resources

---

**Last Updated:** 2025-11-10
**Maintained By:** Backend Security Team
**Security Review:** Required annually
