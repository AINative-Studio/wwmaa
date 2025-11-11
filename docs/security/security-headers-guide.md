# Security Headers Guide

This guide explains the security headers implemented in the WWMAA backend (US-069) and how to configure, test, and debug them.

## Table of Contents

1. [Overview](#overview)
2. [Security Headers Explained](#security-headers-explained)
3. [Content Security Policy (CSP)](#content-security-policy-csp)
4. [Configuration](#configuration)
5. [Testing Security Headers](#testing-security-headers)
6. [Debugging CSP Violations](#debugging-csp-violations)
7. [Adding Trusted Domains](#adding-trusted-domains)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

Security headers are HTTP response headers that instruct browsers on how to behave when handling your site's content. They help protect against common web vulnerabilities like XSS, clickjacking, and man-in-the-middle attacks.

### Benefits

- **Protection against XSS attacks** - Content Security Policy blocks malicious scripts
- **Clickjacking prevention** - X-Frame-Options and frame-ancestors prevent embedding
- **HTTPS enforcement** - HSTS forces secure connections
- **Privacy protection** - Referrer-Policy controls information leakage
- **Feature restriction** - Permissions-Policy disables unnecessary browser features

## Security Headers Explained

### 1. Strict-Transport-Security (HSTS)

**What it does:** Forces browsers to only connect via HTTPS for a specified period.

**Our configuration:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Components:**
- `max-age=31536000` - Enforce HTTPS for 1 year (31,536,000 seconds)
- `includeSubDomains` - Apply to all subdomains
- `preload` - Eligible for browser preload lists

**Why it's important:**
- Prevents SSL stripping attacks
- Ensures all connections are encrypted
- Protects even on first visit if preloaded

**Risk:** Once set, you cannot easily downgrade to HTTP. Test thoroughly before enabling preload.

### 2. X-Frame-Options

**What it does:** Prevents your site from being embedded in frames/iframes.

**Our configuration:**
```
X-Frame-Options: DENY
```

**Options:**
- `DENY` - Never allow framing (our choice)
- `SAMEORIGIN` - Allow framing by same origin
- `ALLOW-FROM uri` - Allow specific URI (deprecated)

**Why it's important:**
- Prevents clickjacking attacks
- Stops malicious sites from embedding your pages
- Protects user interactions

### 3. X-Content-Type-Options

**What it does:** Prevents browsers from MIME-sniffing responses.

**Our configuration:**
```
X-Content-Type-Options: nosniff
```

**Why it's important:**
- Forces browsers to respect declared Content-Type
- Prevents MIME confusion attacks
- Stops browsers from executing unexpected content

### 4. Referrer-Policy

**What it does:** Controls how much referrer information is sent with requests.

**Our configuration:**
```
Referrer-Policy: strict-origin-when-cross-origin
```

**Behavior:**
- Same-origin requests: Send full URL
- Cross-origin HTTPS: Send only origin
- Cross-origin HTTP: Send nothing

**Why it's important:**
- Prevents information leakage in URLs
- Balances privacy and functionality
- Protects sensitive query parameters

### 5. Permissions-Policy

**What it does:** Controls which browser features can be used.

**Our configuration:**
```
Permissions-Policy: geolocation=(), microphone=(), camera=(), payment=(), ...
```

**Disabled features:**
- `geolocation=()` - Location tracking
- `microphone=()` - Microphone access
- `camera=()` - Camera access
- `payment=()` - Payment APIs
- `usb=()` - USB device access

**Allowed features:**
- `fullscreen=(self)` - For video playback
- `picture-in-picture=(self)` - For video controls

**Why it's important:**
- Reduces attack surface
- Prevents abuse of powerful APIs
- Improves privacy

### 6. X-XSS-Protection (Legacy)

**What it does:** Enables XSS filtering in older browsers.

**Our configuration:**
```
X-XSS-Protection: 1; mode=block
```

**Why it's included:**
- Supports older browsers without CSP
- Provides additional layer of defense
- Modern browsers rely on CSP instead

### 7. X-DNS-Prefetch-Control

**What it does:** Controls DNS prefetching.

**Our configuration:**
```
X-DNS-Prefetch-Control: off
```

**Why it's important:**
- Prevents privacy leaks through DNS queries
- Reduces unnecessary network activity

## Content Security Policy (CSP)

CSP is the most powerful security header. It defines which resources can be loaded and executed.

### Environment-Specific Policies

#### Development Environment

**Policy:** Permissive to allow hot module replacement and debugging.

```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com ...;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
img-src 'self' data: https: blob:;
connect-src 'self' http://localhost:* ws://localhost:* ...;
...
```

**Key features:**
- `'unsafe-eval'` - Required for Next.js hot reload
- `'unsafe-inline'` - Allows inline scripts/styles for dev
- `localhost:*` - Allows local development servers
- `ws://localhost:*` - Allows WebSocket connections

#### Production Environment

**Policy:** Strict with nonce-based inline script/style approval.

```
default-src 'none';
script-src 'self' 'nonce-{nonce}' https://js.stripe.com ...;
style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com;
img-src 'self' data: https://api.ainative.studio ...;
upgrade-insecure-requests;
block-all-mixed-content;
report-uri /api/csp-report;
```

**Key features:**
- `default-src 'none'` - Explicit allowlist required
- `'nonce-{nonce}'` - Only scripts/styles with correct nonce execute
- `upgrade-insecure-requests` - Upgrade HTTP to HTTPS
- `block-all-mixed-content` - Block HTTP on HTTPS pages
- `report-uri` - Report violations to endpoint

### CSP Directives Explained

#### default-src

Default policy for resource types not explicitly listed.

**Development:** `'self'` (allow same-origin)
**Production:** `'none'` (deny by default)

#### script-src

Controls which scripts can execute.

**Allowed sources:**
- `'self'` - Same-origin scripts
- `'nonce-{nonce}'` - Inline scripts with nonce (production)
- `https://js.stripe.com` - Stripe payment processing
- `https://www.googletagmanager.com` - Google Tag Manager
- `https://www.google-analytics.com` - Analytics

#### style-src

Controls which stylesheets can be applied.

**Allowed sources:**
- `'self'` - Same-origin styles
- `'nonce-{nonce}'` - Inline styles with nonce (production)
- `https://fonts.googleapis.com` - Google Fonts CSS

#### img-src

Controls image sources.

**Allowed sources:**
- `'self'` - Same-origin images
- `data:` - Data URIs (base64 images)
- `https://api.ainative.studio` - AI Native API images
- `https://storage.ainative.studio` - Object storage

#### font-src

Controls font sources.

**Allowed sources:**
- `'self'` - Same-origin fonts
- `https://fonts.gstatic.com` - Google Fonts

#### connect-src

Controls AJAX, WebSocket, and fetch() destinations.

**Allowed sources:**
- `'self'` - Same-origin requests
- `https://api.ainative.studio` - AI Native API
- `https://api.stripe.com` - Stripe API
- `https://api.beehiiv.com` - BeeHiiv API

#### media-src

Controls audio and video sources.

**Allowed sources:**
- `'self'` - Same-origin media
- `https://*.cloudflarestream.com` - Cloudflare Stream

#### frame-src

Controls iframe sources.

**Allowed sources:**
- `'self'` - Same-origin frames
- `https://js.stripe.com` - Stripe checkout
- `https://*.cloudflarestream.com` - Video player

#### object-src

Controls `<object>`, `<embed>`, and `<applet>` elements.

**Policy:** `'none'` (block all plugins)

#### base-uri

Controls `<base>` tag URLs.

**Policy:** `'self'` (only same-origin)

#### form-action

Controls form submission destinations.

**Policy:** `'self'` (only same-origin)

#### frame-ancestors

Controls who can embed this page.

**Policy:** `'none'` (nobody can embed)

## Configuration

### Environment Variables

Configure security headers via environment variables in `.env`:

```bash
# Enable/disable security headers
SECURITY_HEADERS_ENABLED=true

# CSP reporting mode (report-only for testing)
CSP_REPORT_ONLY=false

# CSP violation report endpoint
CSP_REPORT_URI=/api/csp-report

# HSTS configuration
HSTS_MAX_AGE=31536000          # 1 year in seconds
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=true
```

### Programmatic Configuration

Access configuration in code:

```python
from backend.config import get_settings

settings = get_settings()
config = settings.get_security_headers_config()

print(config)
# {
#     "enabled": True,
#     "csp_report_only": False,
#     "csp_report_uri": "/api/csp-report",
#     "hsts_max_age": 31536000,
#     "hsts_include_subdomains": True,
#     "hsts_preload": True,
# }
```

## Testing Security Headers

### Automated Testing Script

Use the provided testing script:

```bash
# Test local development server
python scripts/test_security_headers.py

# Test specific URL
python scripts/test_security_headers.py --url https://api.wwmaa.com

# Verbose output
python scripts/test_security_headers.py --verbose
```

**Output:**
```
🔒 Testing Security Headers for: http://localhost:8000

================================================================================
Security Headers Test Results - Grade: A+
================================================================================

Checks: 8/8 passed

✅ Strict-Transport-Security
✅ X-Frame-Options
✅ X-Content-Type-Options
✅ Referrer-Policy
✅ Permissions-Policy
✅ Content-Security-Policy
✅ X-XSS-Protection
✅ X-DNS-Prefetch-Control
```

### Manual Testing

#### Using curl

```bash
curl -I http://localhost:8000/health | grep -E "(Strict-Transport|X-Frame|Content-Security)"
```

#### Using Browser DevTools

1. Open your browser's Developer Tools (F12)
2. Go to Network tab
3. Reload the page
4. Click on any request
5. View Response Headers

### External Testing Tools

#### SecurityHeaders.com

Test your deployed site:
```
https://securityheaders.com/?q=https://api.wwmaa.com
```

**Provides:**
- Letter grade (A+ to F)
- Detailed header analysis
- Recommendations

#### Mozilla Observatory

```
https://observatory.mozilla.org/analyze/api.wwmaa.com
```

**Provides:**
- Comprehensive security score
- Multiple security tests
- Implementation guidance

#### Chrome Lighthouse

Run in Chrome DevTools:
1. Open DevTools (F12)
2. Go to Lighthouse tab
3. Select "Best practices"
4. Click "Generate report"

## Debugging CSP Violations

### Viewing Violations in Browser

CSP violations appear in the browser console:

```
Refused to load the script 'https://untrusted.com/script.js' because it
violates the following Content Security Policy directive: "script-src 'self'".
```

### Accessing CSP Reports

#### Development Endpoint

```bash
curl http://localhost:8000/api/security/csp-violations
```

Returns recent violations with details:

```json
{
  "violations": [
    {
      "timestamp": "2025-11-10T10:30:00Z",
      "violation": {
        "document-uri": "http://localhost:3000/dashboard",
        "violated-directive": "script-src-elem",
        "blocked-uri": "https://untrusted.com/script.js",
        "disposition": "enforce"
      }
    }
  ],
  "count": 1
}
```

### Common CSP Violations

#### 1. Inline Script Without Nonce

**Violation:**
```
Refused to execute inline script because it violates CSP directive:
'script-src'. Either the 'unsafe-inline' keyword, a hash, or a nonce is required.
```

**Solution:**
Add nonce to inline scripts:

```python
from backend.middleware.security_headers import get_csp_nonce

@app.get("/page")
async def page(request: Request):
    nonce = get_csp_nonce(request)
    return f'<script nonce="{nonce}">console.log("Safe!");</script>'
```

#### 2. External Script Not Allowlisted

**Violation:**
```
Refused to load script from 'https://new-cdn.com/script.js' because it
violates CSP directive: 'script-src'.
```

**Solution:**
Add the domain to the allowlist in `backend/middleware/security_headers.py`:

```python
"script-src": [
    "'self'",
    f"'nonce-{nonce}'",
    "https://js.stripe.com",
    "https://new-cdn.com",  # Add here
],
```

#### 3. Image from Untrusted Source

**Violation:**
```
Refused to load image from 'https://untrusted.com/image.jpg' because it
violates CSP directive: 'img-src'.
```

**Solution:**
Add the domain to img-src or use a proxy.

### Report-Only Mode

Test CSP changes without breaking functionality:

```bash
# In .env
CSP_REPORT_ONLY=true
```

This sends `Content-Security-Policy-Report-Only` header instead, which:
- Reports violations without blocking
- Allows testing in production
- Helps identify false positives

## Adding Trusted Domains

### Process

1. **Identify the need**
   - CSP violation in console
   - New third-party integration
   - New CDN for assets

2. **Verify trustworthiness**
   - Is this domain trustworthy?
   - Can you use a first-party alternative?
   - Is the domain properly secured (HTTPS)?

3. **Add to appropriate directive**

Edit `/backend/middleware/security_headers.py`:

```python
def _build_production_csp(self, nonce: str) -> str:
    directives = {
        # ... existing directives ...

        "script-src": [
            "'self'",
            f"'nonce-{nonce}'",
            "https://js.stripe.com",
            "https://new-trusted-cdn.com",  # Add here
        ],
    }
```

4. **Test thoroughly**

```bash
# Run tests
pytest backend/tests/test_security_headers.py

# Test manually
python scripts/test_security_headers.py

# Check browser console for violations
```

5. **Deploy and monitor**
   - Deploy to staging first
   - Monitor CSP violations
   - Check Sentry for errors

### Common Third-Party Domains

#### Analytics
```python
"script-src": ["https://www.google-analytics.com"],
"img-src": ["https://www.google-analytics.com"],
"connect-src": ["https://www.google-analytics.com"],
```

#### Fonts
```python
"style-src": ["https://fonts.googleapis.com"],
"font-src": ["https://fonts.gstatic.com"],
```

#### Payment Processing
```python
"script-src": ["https://js.stripe.com"],
"frame-src": ["https://js.stripe.com"],
"connect-src": ["https://api.stripe.com"],
```

#### Video Streaming
```python
"media-src": ["https://*.cloudflarestream.com"],
"frame-src": ["https://*.cloudflarestream.com"],
```

## Best Practices

### 1. Start with Report-Only Mode

Always test CSP changes in report-only mode first:

```bash
CSP_REPORT_ONLY=true
```

### 2. Use Nonces, Not unsafe-inline

**Bad:**
```python
"script-src": ["'self'", "'unsafe-inline'"],  # Weak security
```

**Good:**
```python
"script-src": ["'self'", f"'nonce-{nonce}'"],  # Strong security
```

### 3. Minimize Trusted Domains

Only add domains you trust completely:
- Verify domain ownership
- Check HTTPS support
- Consider SRI (Subresource Integrity) for scripts

### 4. Regular Security Audits

Schedule regular reviews:
- Monthly: Check securityheaders.com grade
- Quarterly: Review trusted domains list
- Annually: Full security audit

### 5. Monitor CSP Violations

Set up alerts for CSP violations:
- Check Sentry regularly
- Review violation logs
- Investigate unusual patterns

### 6. Document Changes

Always document why a domain was added:

```python
"script-src": [
    "'self'",
    "https://new-service.com",  # Added 2025-11-10 for email verification
],
```

### 7. Test Across Browsers

CSP implementation varies by browser:
- Chrome/Edge
- Firefox
- Safari
- Mobile browsers

## Troubleshooting

### Issue: HSTS Warning in Browser

**Symptom:** Browser shows HSTS warning on localhost.

**Cause:** HSTS applies to all ports on a domain, including localhost.

**Solution:**
1. Clear HSTS settings in Chrome: `chrome://net-internals/#hsts`
2. Delete domain: `localhost`
3. Use `127.0.0.1` instead of `localhost`

### Issue: CSP Blocking Legitimate Resources

**Symptom:** Images, scripts, or styles not loading.

**Diagnosis:**
1. Open browser console
2. Look for CSP violation messages
3. Note the blocked URI and directive

**Solution:**
1. Add domain to appropriate directive
2. Test in report-only mode first
3. Deploy and verify

### Issue: Next.js Hot Reload Not Working

**Symptom:** Development server hot reload fails.

**Cause:** CSP blocking WebSocket or eval().

**Solution:**
Ensure development CSP includes:
```python
"script-src": ["'unsafe-eval'"],  # Required for HMR
"connect-src": ["ws://localhost:*"],  # Required for WebSocket
```

### Issue: Stripe Checkout Not Loading

**Symptom:** Stripe payment form doesn't appear.

**Cause:** CSP blocking Stripe domains.

**Solution:**
Verify these domains are allowed:
```python
"script-src": ["https://js.stripe.com"],
"frame-src": ["https://js.stripe.com"],
"connect-src": ["https://api.stripe.com"],
```

### Issue: Google Fonts Not Loading

**Symptom:** Custom fonts not displaying.

**Cause:** CSP blocking Google Fonts.

**Solution:**
```python
"style-src": ["https://fonts.googleapis.com"],
"font-src": ["https://fonts.gstatic.com"],
```

### Issue: High Volume of CSP Violations

**Symptom:** Thousands of CSP violation reports.

**Diagnosis:**
1. Check violation patterns
2. Identify common blocked URIs
3. Look for browser extensions

**Common causes:**
- Browser extensions injecting scripts
- Third-party scripts loading additional resources
- Misconfigured CSP policy

**Solution:**
1. Analyze violation patterns
2. Decide if violations are legitimate
3. Adjust CSP or ignore extension violations

## Related Documentation

- [HSTS Preload Guide](./hsts-preload.md)
- [CSP Specification](https://w3c.github.io/webappsec-csp/)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [MDN Security Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security)

## Support

For questions or issues:
- Check browser console for violation details
- Review CSP violation logs at `/api/security/csp-violations`
- Run test script: `python scripts/test_security_headers.py`
- Check Sentry for reported violations
