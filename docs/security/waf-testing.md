# WAF Testing Procedures

## Overview

This document provides comprehensive testing procedures to validate Cloudflare WAF configuration, ensure proper protection against attacks, and verify that legitimate traffic is not blocked.

## Table of Contents

1. [Testing Prerequisites](#testing-prerequisites)
2. [SSL/TLS Testing](#ssltls-testing)
3. [WAF Rule Testing](#waf-rule-testing)
4. [Rate Limiting Testing](#rate-limiting-testing)
5. [Bot Protection Testing](#bot-protection-testing)
6. [Custom Rule Testing](#custom-rule-testing)
7. [Penetration Testing](#penetration-testing)
8. [Performance Testing](#performance-testing)
9. [Monitoring and Logging Verification](#monitoring-and-logging-verification)
10. [Automated Testing](#automated-testing)
11. [Test Results Documentation](#test-results-documentation)

## Testing Prerequisites

### Required Tools

**Command Line Tools:**
```bash
# Install required tools
brew install curl openssl jq

# For penetration testing
brew install --cask burp-suite
# Or install OWASP ZAP: https://www.zaproxy.org/download/
```

**Online Tools:**
- SSL Labs: https://www.ssllabs.com/ssltest/
- Security Headers: https://securityheaders.com/
- HTTP/2 Test: https://tools.keycdn.com/http2-test
- WebPageTest: https://www.webpagetest.org/

**Python Testing Script:**
```bash
pip install requests pytest python-dotenv
```

### Testing Environments

**Staging Environment:**
- URL: https://staging.wwmaa.com
- Purpose: Initial testing with Log mode
- Impact: No production users affected

**Production Environment:**
- URL: https://wwmaa.com
- Purpose: Final validation
- Timing: After staging tests pass
- Caution: Test during low-traffic periods

### Access Requirements

- Cloudflare Dashboard access (view analytics)
- Test user accounts (various permission levels)
- VPN or proxy for geo-blocking tests
- API keys for automated testing

## SSL/TLS Testing

### Test 1: SSL Labs Assessment

**Objective:** Verify SSL/TLS configuration achieves A+ rating.

**Procedure:**
1. Navigate to: https://www.ssllabs.com/ssltest/
2. Enter domain: `wwmaa.com`
3. Check "Do not show the results on the boards" (for production)
4. Click "Submit"
5. Wait for analysis (2-5 minutes)

**Expected Results:**
```
Overall Rating: A+

Certificate:
- Trust: Trusted
- Validity: Valid (not expired)
- Chain: Complete

Protocol Support:
- TLS 1.3: Yes
- TLS 1.2: Yes
- TLS 1.1: No
- TLS 1.0: No
- SSL 3: No
- SSL 2: No

Cipher Suites:
- Forward Secrecy: Yes
- Weak Ciphers: No
- RC4: No

Features:
- HSTS: Yes
- HSTS Max Age: 31536000 (12 months)
- HSTS includeSubDomains: Yes
- Certificate Transparency: Yes
```

**Pass Criteria:** Overall rating A or A+

**Failure Actions:**
- Rating B: Review cipher suites and protocol versions
- Rating C or below: Critical - review SSL/TLS configuration immediately

### Test 2: Certificate Validation

**Objective:** Verify certificate is valid and trusted.

**Command Line Test:**
```bash
# Test certificate validity
echo | openssl s_client -servername wwmaa.com -connect wwmaa.com:443 2>/dev/null | openssl x509 -noout -dates

# Expected output:
# notBefore=Jan  1 00:00:00 2025 GMT
# notAfter=Apr  1 23:59:59 2025 GMT (example dates)

# Test certificate chain
echo | openssl s_client -servername wwmaa.com -connect wwmaa.com:443 2>/dev/null | openssl x509 -noout -issuer -subject

# Expected output:
# issuer=C = US, O = Let's Encrypt, CN = R3
# subject=CN = wwmaa.com
```

**Pass Criteria:** Certificate valid and not expired, chain complete.

### Test 3: TLS Version Verification

**Objective:** Verify only secure TLS versions are supported.

**Test TLS 1.3 (Should Succeed):**
```bash
openssl s_client -connect wwmaa.com:443 -tls1_3 < /dev/null

# Expected: Successful connection with TLS 1.3
```

**Test TLS 1.2 (Should Succeed):**
```bash
openssl s_client -connect wwmaa.com:443 -tls1_2 < /dev/null

# Expected: Successful connection with TLS 1.2
```

**Test TLS 1.1 (Should Fail):**
```bash
openssl s_client -connect wwmaa.com:443 -tls1_1 < /dev/null 2>&1 | grep -i "handshake failure"

# Expected: Connection failure (TLS 1.1 disabled)
```

**Test TLS 1.0 (Should Fail):**
```bash
openssl s_client -connect wwmaa.com:443 -tls1 < /dev/null 2>&1 | grep -i "handshake failure"

# Expected: Connection failure (TLS 1.0 disabled)
```

**Pass Criteria:** TLS 1.2 and 1.3 work, older versions fail.

### Test 4: HSTS Header Verification

**Objective:** Verify HSTS header is present and configured correctly.

**Test Command:**
```bash
curl -I https://wwmaa.com | grep -i strict-transport-security

# Expected output:
# strict-transport-security: max-age=31536000; includeSubDomains
```

**Pass Criteria:** Header present with max-age >= 31536000 seconds.

### Test 5: HTTP to HTTPS Redirect

**Objective:** Verify all HTTP requests redirect to HTTPS.

**Test Command:**
```bash
curl -I http://wwmaa.com

# Expected output:
# HTTP/1.1 301 Moved Permanently
# Location: https://wwmaa.com/
```

**Test with www:**
```bash
curl -I http://www.wwmaa.com

# Expected output:
# HTTP/1.1 301 Moved Permanently
# Location: https://www.wwmaa.com/
```

**Pass Criteria:** All HTTP requests return 301/302 redirect to HTTPS.

## WAF Rule Testing

### Test 1: SQL Injection Protection

**Objective:** Verify OWASP rules block SQL injection attempts.

**Test 1.1: Basic SQL Injection in Query Parameter**
```bash
curl -v "https://staging.wwmaa.com/api/search?q=1' OR '1'='1"

# Expected: 403 Forbidden (blocked by WAF)
```

**Test 1.2: UNION-based SQL Injection**
```bash
curl -v "https://staging.wwmaa.com/api/users?id=1 UNION SELECT * FROM users"

# Expected: 403 Forbidden
```

**Test 1.3: SQL Injection in POST Body**
```bash
curl -X POST https://staging.wwmaa.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "1' OR '1'='1"}'

# Expected: 403 Forbidden
```

**Test 1.4: Time-based SQL Injection**
```bash
curl -v "https://staging.wwmaa.com/api/users?id=1' AND SLEEP(5)--"

# Expected: 403 Forbidden
```

**Pass Criteria:** All SQL injection attempts blocked with 403 status.

### Test 2: Cross-Site Scripting (XSS) Protection

**Objective:** Verify XSS attempts are blocked.

**Test 2.1: Basic XSS in Query Parameter**
```bash
curl -v "https://staging.wwmaa.com/api/search?q=<script>alert('XSS')</script>"

# Expected: 403 Forbidden
```

**Test 2.2: XSS with Event Handlers**
```bash
curl -v "https://staging.wwmaa.com/api/search?q=<img src=x onerror=alert('XSS')>"

# Expected: 403 Forbidden
```

**Test 2.3: XSS in POST Data**
```bash
curl -X POST https://staging.wwmaa.com/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert(document.cookie)</script>"}'

# Expected: 403 Forbidden
```

**Pass Criteria:** All XSS attempts blocked with 403 status.

### Test 3: Path Traversal Protection

**Objective:** Verify directory traversal attempts are blocked.

**Test 3.1: Basic Path Traversal**
```bash
curl -v "https://staging.wwmaa.com/api/files?path=../../etc/passwd"

# Expected: 403 Forbidden
```

**Test 3.2: Encoded Path Traversal**
```bash
curl -v "https://staging.wwmaa.com/api/files?path=..%2F..%2Fetc%2Fpasswd"

# Expected: 403 Forbidden
```

**Pass Criteria:** Path traversal attempts blocked.

### Test 4: Remote Code Execution (RCE) Protection

**Objective:** Verify RCE attempts are blocked.

**Test 4.1: Command Injection**
```bash
curl -v "https://staging.wwmaa.com/api/search?q=test; ls -la"

# Expected: 403 Forbidden
```

**Test 4.2: PHP Code Injection**
```bash
curl -v "https://staging.wwmaa.com/api/upload?filename=shell.php&content=<?php system(\$_GET['cmd']); ?>"

# Expected: 403 Forbidden
```

**Pass Criteria:** RCE attempts blocked.

### Test 5: Local File Inclusion (LFI) Protection

**Objective:** Verify LFI attempts are blocked.

**Test 5.1: Basic LFI**
```bash
curl -v "https://staging.wwmaa.com/api/page?file=/etc/passwd"

# Expected: 403 Forbidden
```

**Test 5.2: PHP Wrapper LFI**
```bash
curl -v "https://staging.wwmaa.com/api/page?file=php://filter/convert.base64-encode/resource=index.php"

# Expected: 403 Forbidden
```

**Pass Criteria:** LFI attempts blocked.

### Test 6: Legitimate Traffic (False Positive Check)

**Objective:** Verify legitimate requests are NOT blocked.

**Test 6.1: Normal Search Query**
```bash
curl -v "https://staging.wwmaa.com/api/search?q=membership%20application"

# Expected: 200 OK with search results
```

**Test 6.2: Normal Login**
```bash
curl -X POST https://staging.wwmaa.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "ValidPassword123!"}'

# Expected: 200 OK or 401 Unauthorized (not 403)
```

**Test 6.3: Normal API Request**
```bash
curl -v https://staging.wwmaa.com/api/users \
  -H "Authorization: Bearer [valid-token]"

# Expected: 200 OK with user data
```

**Pass Criteria:** All legitimate requests succeed (no 403 errors).

## Rate Limiting Testing

### Test 1: API Rate Limit (100 req/min)

**Objective:** Verify API rate limit blocks excessive requests.

**Test Script:**
```bash
#!/bin/bash
# test-api-rate-limit.sh

API_URL="https://staging.wwmaa.com/api/health"
LIMIT=100
BLOCKED=0

echo "Testing API rate limit: $LIMIT requests/minute"

for i in $(seq 1 120); do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

    if [ "$RESPONSE" == "429" ]; then
        BLOCKED=$((BLOCKED + 1))
        echo "Request $i: BLOCKED (429)"
    else
        echo "Request $i: OK ($RESPONSE)"
    fi

    # Small delay to stay within minute window
    sleep 0.5
done

echo ""
echo "Summary:"
echo "- Total requests: 120"
echo "- Blocked requests: $BLOCKED"
echo "- Expected blocks: ~20"

if [ $BLOCKED -ge 15 ]; then
    echo "PASS: Rate limiting working"
else
    echo "FAIL: Rate limiting not working properly"
fi
```

**Run Test:**
```bash
chmod +x test-api-rate-limit.sh
./test-api-rate-limit.sh
```

**Expected Results:**
- Requests 1-100: 200 OK
- Requests 101+: 429 Too Many Requests
- Rate limit duration: 1 hour block

**Pass Criteria:** Requests blocked after threshold exceeded.

### Test 2: Login Rate Limit (5 req/min)

**Objective:** Verify login endpoint has strict rate limiting.

**Test Script:**
```bash
#!/bin/bash
# test-login-rate-limit.sh

LOGIN_URL="https://staging.wwmaa.com/api/auth/login"

echo "Testing login rate limit: 5 requests/minute"

for i in $(seq 1 10); do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST $LOGIN_URL \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"test123"}')

    echo "Login attempt $i: $RESPONSE"
    sleep 1
done
```

**Expected Results:**
- Attempts 1-5: 401 Unauthorized (login failed) or 200 OK (login success)
- Attempts 6+: 429 Too Many Requests

**Pass Criteria:** Login blocked after 5 attempts.

### Test 3: Registration Rate Limit (3 req/min)

**Objective:** Verify registration endpoint prevents automated account creation.

**Test Script:**
```bash
#!/bin/bash
# test-registration-rate-limit.sh

REGISTER_URL="https://staging.wwmaa.com/api/auth/register"

echo "Testing registration rate limit: 3 requests/minute"

for i in $(seq 1 6); do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST $REGISTER_URL \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"test$i@example.com\",\"password\":\"Test123!\",\"name\":\"Test User\"}")

    echo "Registration attempt $i: $RESPONSE"
    sleep 1
done
```

**Expected Results:**
- Attempts 1-3: 201 Created or 400 Bad Request (validation error)
- Attempts 4+: 429 Too Many Requests

**Pass Criteria:** Registration blocked after 3 attempts.

### Test 4: Search Rate Limit (10 req/min)

**Objective:** Verify search endpoint prevents scraping.

**Test Script:**
```bash
#!/bin/bash
# test-search-rate-limit.sh

SEARCH_URL="https://staging.wwmaa.com/api/search"

echo "Testing search rate limit: 10 requests/minute"

for i in $(seq 1 15); do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$SEARCH_URL?q=test$i")
    echo "Search request $i: $RESPONSE"
    sleep 1
done
```

**Expected Results:**
- Requests 1-10: 200 OK
- Requests 11+: 429 Too Many Requests (or JS Challenge)

**Pass Criteria:** Search blocked or challenged after 10 requests.

### Test 5: Rate Limit Recovery

**Objective:** Verify rate limit resets after timeout period.

**Test Procedure:**
1. Trigger rate limit (e.g., 101 API requests)
2. Wait for timeout period (60 seconds for API limit)
3. Attempt request again
4. Verify request succeeds

**Test Script:**
```bash
#!/bin/bash
# test-rate-limit-recovery.sh

API_URL="https://staging.wwmaa.com/api/health"

echo "Step 1: Trigger rate limit"
for i in $(seq 1 101); do
    curl -s -o /dev/null $API_URL
done

echo ""
echo "Step 2: Verify rate limit active"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
echo "Response: $RESPONSE (expected: 429)"

echo ""
echo "Step 3: Wait 65 seconds for rate limit reset..."
sleep 65

echo ""
echo "Step 4: Test if rate limit reset"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
echo "Response: $RESPONSE (expected: 200)"

if [ "$RESPONSE" == "200" ]; then
    echo "PASS: Rate limit reset successfully"
else
    echo "FAIL: Rate limit did not reset"
fi
```

**Pass Criteria:** Rate limit resets and requests succeed after timeout.

## Bot Protection Testing

### Test 1: Normal Browser Access

**Objective:** Verify legitimate browser access is not blocked.

**Test Procedure:**
1. Open browser (Chrome/Firefox/Safari)
2. Navigate to https://staging.wwmaa.com
3. Browse site normally (click links, submit forms)
4. Verify no CAPTCHA challenges appear

**Pass Criteria:** No challenges or blocks for normal browsing.

### Test 2: Headless Browser Detection

**Objective:** Verify automated browsers are challenged.

**Test with Puppeteer:**
```javascript
// test-bot-protection.js
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  try {
    const response = await page.goto('https://staging.wwmaa.com');
    console.log('Status:', response.status());
    console.log('Final URL:', page.url());

    // Check if challenge page appeared
    const content = await page.content();
    if (content.includes('challenge') || content.includes('Checking your browser')) {
      console.log('PASS: Bot challenge detected');
    } else {
      console.log('FAIL: No bot challenge (may need to enable stricter settings)');
    }
  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
})();
```

**Run Test:**
```bash
npm install puppeteer
node test-bot-protection.js
```

**Expected Result:** Challenge page or blocked access.

### Test 3: cURL User-Agent

**Objective:** Verify non-browser user agents are challenged or blocked.

**Test with Default cURL:**
```bash
curl -v https://staging.wwmaa.com

# May show challenge page or block
```

**Test with Browser User-Agent:**
```bash
curl -v https://staging.wwmaa.com \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Should succeed (browser user-agent)
```

**Test without User-Agent:**
```bash
curl -v https://staging.wwmaa.com -H "User-Agent:"

# Should be blocked (no user-agent)
```

**Pass Criteria:** Suspicious user agents challenged, browser user agents allowed.

### Test 4: Verified Bot Allowlist

**Objective:** Verify legitimate crawlers are allowed.

**Test Googlebot:**
```bash
curl -v https://staging.wwmaa.com \
  -H "User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

# Expected: 200 OK (Googlebot allowed)
```

**Test Bingbot:**
```bash
curl -v https://staging.wwmaa.com \
  -H "User-Agent: Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"

# Expected: 200 OK (Bingbot allowed)
```

**Pass Criteria:** Verified bots (Google, Bing) are not blocked.

### Test 5: Rapid Automated Requests

**Objective:** Verify rapid automated requests trigger bot protection.

**Test Script:**
```bash
#!/bin/bash
# test-bot-rapid-requests.sh

URL="https://staging.wwmaa.com"

echo "Sending 50 rapid requests..."

for i in $(seq 1 50); do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)
    echo "Request $i: $RESPONSE"
done
```

**Expected Results:**
- Initial requests: 200 OK
- Later requests: 403 Forbidden or Challenge page

**Pass Criteria:** Bot protection activates after suspicious pattern.

## Custom Rule Testing

### Test 1: Malicious IP Block

**Objective:** Verify IPs on blocklist are blocked.

**Test Procedure:**
1. Add test IP to malicious_ips_list in Cloudflare
2. Make request from that IP (or simulate with X-Forwarded-For header in staging)
3. Verify request is blocked

**Test with VPN:**
```bash
# Connect to VPN with IP on blocklist
curl -v https://staging.wwmaa.com

# Expected: 403 Forbidden
```

**Pass Criteria:** Blocklisted IPs cannot access site.

### Test 2: Sensitive Endpoint Challenge

**Objective:** Verify admin/payment endpoints show challenge.

**Test Admin Endpoint:**
```bash
curl -v https://staging.wwmaa.com/api/admin/users

# Expected: Challenge page or Managed Challenge
```

**Test Payment Endpoint:**
```bash
curl -v https://staging.wwmaa.com/api/payment/process

# Expected: Challenge page or Managed Challenge
```

**Test in Browser:**
1. Navigate to https://staging.wwmaa.com/api/admin
2. Verify challenge appears (may be transparent Managed Challenge)
3. Complete challenge
4. Verify access granted after challenge

**Pass Criteria:** Sensitive endpoints show challenge, can be completed.

### Test 3: Geo-Blocking (If Enabled)

**Objective:** Verify geo-blocking rules work correctly.

**Test with VPN:**
1. Connect to VPN in blocked country (e.g., CN, RU if configured)
2. Attempt to access site
3. Verify access is blocked

**Test Command (if VPN configured):**
```bash
curl -v https://staging.wwmaa.com

# Expected: 403 Forbidden (from blocked country)
```

**Test from Allowed Country:**
```bash
# Disconnect VPN or use VPN in allowed country
curl -v https://staging.wwmaa.com

# Expected: 200 OK
```

**Pass Criteria:** Blocked countries cannot access, allowed countries can.

### Test 4: Scanner Tool Detection

**Objective:** Verify security scanner tools are blocked.

**Test with sqlmap User-Agent:**
```bash
curl -v https://staging.wwmaa.com \
  -H "User-Agent: sqlmap/1.0-dev"

# Expected: 403 Forbidden
```

**Test with nikto User-Agent:**
```bash
curl -v https://staging.wwmaa.com \
  -H "User-Agent: Nikto/2.1.6"

# Expected: 403 Forbidden
```

**Pass Criteria:** Known scanner tools are blocked.

## Penetration Testing

### Tool 1: OWASP ZAP

**Objective:** Comprehensive security scan with automated tool.

**Setup:**
1. Download OWASP ZAP: https://www.zaproxy.org/download/
2. Install and launch ZAP
3. Configure proxy in browser

**Test Procedure:**

**Passive Scan:**
1. In ZAP, set target: https://staging.wwmaa.com
2. Spider the site: Right-click target → Attack → Spider
3. Wait for spider to complete
4. Review results in "Alerts" tab

**Active Scan:**
1. After spider completes, right-click target
2. Select "Attack" → "Active Scan"
3. Configure scan policy (use OWASP Top 10)
4. Start scan
5. Wait for completion (may take 30-60 minutes)

**Expected Results:**
- Low/Info alerts: Acceptable
- Medium alerts: Review and fix if necessary
- High alerts: Should be minimal (WAF blocks most attacks)
- Critical alerts: None (WAF blocks all critical attacks)

**Documentation:**
```bash
# Export ZAP report
File → Generate Report → HTML
Save as: waf-penetration-test-report-$(date +%Y%m%d).html
```

**Pass Criteria:**
- No critical vulnerabilities
- High severity alerts blocked by WAF
- Report documents WAF effectiveness

### Tool 2: Burp Suite

**Objective:** Manual penetration testing with professional tool.

**Test Procedure:**
1. Launch Burp Suite
2. Configure browser proxy (127.0.0.1:8080)
3. Browse staging.wwmaa.com through proxy
4. In Burp, go to "Scanner" tab
5. Right-click target → "Scan"
6. Review findings

**Manual Tests:**
- Intercept requests and modify payloads
- Test for SQL injection with custom payloads
- Test for XSS with various encoding techniques
- Test authentication bypass attempts
- Test authorization issues

**Pass Criteria:** All attack attempts blocked by WAF.

### Tool 3: Nikto Web Scanner

**Objective:** Test for known vulnerabilities.

**Test Command:**
```bash
# Install nikto
brew install nikto

# Run scan (should be blocked by WAF)
nikto -h https://staging.wwmaa.com

# Expected: Connection blocked or severely limited
```

**Pass Criteria:** Scanner detected and blocked by WAF.

### Tool 4: SQLMap

**Objective:** Test SQL injection protection.

**Test Command:**
```bash
# Install sqlmap
brew install sqlmap

# Attempt SQL injection scan
sqlmap -u "https://staging.wwmaa.com/api/users?id=1" --batch

# Expected: WAF blocks all injection attempts
```

**Expected Output:**
```
[WARNING] WAF/IPS detected
[ERROR] all tested parameters do not appear to be injectable
```

**Pass Criteria:** sqlmap unable to exploit any injection vulnerabilities.

## Performance Testing

### Test 1: Page Load Time

**Objective:** Verify WAF doesn't significantly impact performance.

**Test with cURL:**
```bash
curl -w "@curl-format.txt" -o /dev/null -s https://staging.wwmaa.com

# curl-format.txt contents:
# time_namelookup:  %{time_namelookup}\n
# time_connect:  %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n
# time_pretransfer:  %{time_pretransfer}\n
# time_redirect:  %{time_redirect}\n
# time_starttransfer:  %{time_starttransfer}\n
# ----------\n
# time_total:  %{time_total}\n
```

**Create curl-format.txt:**
```bash
cat > curl-format.txt << 'EOF'
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
----------\n
time_total:  %{time_total}\n
EOF
```

**Expected Results:**
- Total time: < 500ms (for simple page)
- App connect (TLS): < 200ms
- Star transfer: < 300ms

**Pass Criteria:** Performance acceptable, no significant degradation.

### Test 2: Concurrent Requests

**Objective:** Verify WAF handles high concurrency.

**Test with Apache Bench:**
```bash
# Install apache bench
brew install httpd

# Test 1000 requests, 100 concurrent
ab -n 1000 -c 100 https://staging.wwmaa.com/

# Review results:
# - Requests per second
# - Time per request
# - Failed requests
```

**Expected Results:**
- Failed requests: 0 (unless rate limiting triggered)
- Requests per second: > 500
- Average time per request: < 200ms

**Pass Criteria:** No errors, acceptable performance under load.

## Monitoring and Logging Verification

### Test 1: WAF Events in Dashboard

**Objective:** Verify WAF events are logged.

**Test Procedure:**
1. Perform SQL injection test: `curl "https://staging.wwmaa.com/api/search?q=1' OR '1'='1"`
2. Wait 1-2 minutes
3. Log in to Cloudflare Dashboard
4. Navigate to **Security** → **Events**
5. Find the blocked request

**Expected Details:**
```
Action: Block
Rule: Cloudflare OWASP Core Ruleset
Details: SQL Injection attempt
IP: [Your test IP]
Country: [Your country]
User-Agent: curl/7.x
Path: /api/search
Query: q=1' OR '1'='1
```

**Pass Criteria:** Event logged with complete details.

### Test 2: Rate Limiting Events

**Objective:** Verify rate limiting events are logged.

**Test Procedure:**
1. Trigger rate limit (send 101 API requests)
2. Check **Security** → **Events** for rate limiting events
3. Verify event details

**Expected Details:**
```
Action: Block
Rule: API Rate Limit
IP: [Your test IP]
Rate: 101 requests in 60 seconds
Threshold: 100 requests per 60 seconds
Block Duration: 3600 seconds
```

**Pass Criteria:** Rate limiting events logged correctly.

### Test 3: Bot Detection Logging

**Objective:** Verify bot detection events are logged.

**Test Procedure:**
1. Send request with bot user-agent: `curl -H "User-Agent: sqlmap/1.0" https://staging.wwmaa.com`
2. Check **Security** → **Bots** for event
3. Verify bot score and action

**Expected Details:**
```
Action: Block/Challenge
Bot Score: < 30 (lower = more likely bot)
Source: Bot Fight Mode / Super Bot Fight Mode
User-Agent: sqlmap/1.0
```

**Pass Criteria:** Bot detection logged with correct score.

### Test 4: Alert Notifications

**Objective:** Verify alerts are sent when thresholds exceeded.

**Test Procedure:**
1. Trigger alert condition (e.g., 1000+ blocks in 5 minutes)
2. Check email for alert notification
3. Check Slack channel (if configured)
4. Check PagerDuty (if configured)

**Pass Criteria:** Alerts received via all configured channels.

## Automated Testing

### Complete Test Suite

**File: `tests/security/test_waf.py`**

```python
#!/usr/bin/env python3
"""
Automated WAF testing suite for wwmaa.com
Run: pytest tests/security/test_waf.py -v
"""

import requests
import time
import pytest
from typing import List, Dict

BASE_URL = "https://staging.wwmaa.com"
API_URL = f"{BASE_URL}/api"

class TestWAFProtection:
    """Test WAF protection mechanisms"""

    def test_sql_injection_blocked(self):
        """Test SQL injection attempts are blocked"""
        payloads = [
            "1' OR '1'='1",
            "1 UNION SELECT * FROM users",
            "1'; DROP TABLE users--",
            "1' AND SLEEP(5)--"
        ]

        for payload in payloads:
            response = requests.get(f"{API_URL}/search", params={"q": payload})
            assert response.status_code == 403, f"SQL injection not blocked: {payload}"

    def test_xss_blocked(self):
        """Test XSS attempts are blocked"""
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]

        for payload in payloads:
            response = requests.get(f"{API_URL}/search", params={"q": payload})
            assert response.status_code == 403, f"XSS not blocked: {payload}"

    def test_path_traversal_blocked(self):
        """Test path traversal attempts are blocked"""
        payloads = [
            "../../etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "....//....//etc/passwd"
        ]

        for payload in payloads:
            response = requests.get(f"{API_URL}/files", params={"path": payload})
            assert response.status_code == 403, f"Path traversal not blocked: {payload}"

    def test_legitimate_requests_allowed(self):
        """Test legitimate requests are not blocked"""
        # Normal search
        response = requests.get(f"{API_URL}/search", params={"q": "membership"})
        assert response.status_code in [200, 401], "Legitimate search blocked"

        # Normal API request
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200, "Legitimate API request blocked"

class TestRateLimiting:
    """Test rate limiting rules"""

    def test_api_rate_limit(self):
        """Test API rate limit (100 req/min)"""
        url = f"{API_URL}/health"
        blocked_count = 0

        # Send 105 requests
        for i in range(105):
            response = requests.get(url)
            if response.status_code == 429:
                blocked_count += 1

        assert blocked_count > 0, "Rate limit not enforced"
        assert blocked_count >= 5, "Rate limit too lenient"

    def test_login_rate_limit(self):
        """Test login rate limit (5 req/min)"""
        url = f"{API_URL}/auth/login"
        blocked_count = 0

        # Send 8 login attempts
        for i in range(8):
            response = requests.post(url, json={
                "email": "test@example.com",
                "password": "test123"
            })
            if response.status_code == 429:
                blocked_count += 1
            time.sleep(1)

        assert blocked_count > 0, "Login rate limit not enforced"

class TestBotProtection:
    """Test bot protection mechanisms"""

    def test_scanner_user_agent_blocked(self):
        """Test security scanner user-agents are blocked"""
        headers_list = [
            {"User-Agent": "sqlmap/1.0"},
            {"User-Agent": "Nikto/2.1.6"},
            {"User-Agent": "nmap scripting engine"}
        ]

        for headers in headers_list:
            response = requests.get(BASE_URL, headers=headers)
            assert response.status_code == 403, f"Scanner not blocked: {headers['User-Agent']}"

    def test_browser_user_agent_allowed(self):
        """Test normal browser user-agents are allowed"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(BASE_URL, headers=headers)
        assert response.status_code == 200, "Browser user-agent blocked"

class TestSSLTLS:
    """Test SSL/TLS configuration"""

    def test_https_works(self):
        """Test HTTPS connection works"""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert response.url.startswith("https://")

    def test_hsts_header_present(self):
        """Test HSTS header is present"""
        response = requests.get(BASE_URL)
        assert "strict-transport-security" in response.headers
        hsts = response.headers["strict-transport-security"]
        assert "max-age" in hsts
        assert "includeSubDomains" in hsts

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Run Automated Tests:**
```bash
# Install dependencies
pip install pytest requests

# Run all tests
pytest tests/security/test_waf.py -v

# Run specific test class
pytest tests/security/test_waf.py::TestWAFProtection -v

# Run with coverage
pytest tests/security/test_waf.py --cov=. --cov-report=html
```

## Test Results Documentation

### Test Report Template

**File: `test-results/waf-test-report-YYYYMMDD.md`**

```markdown
# WAF Testing Report

**Date:** 2025-01-10
**Tester:** [Your Name]
**Environment:** Staging
**Cloudflare Plan:** Free / Pro

## Test Summary

- Total Tests: 50
- Passed: 48
- Failed: 2
- Skipped: 0

## SSL/TLS Testing

| Test | Result | Notes |
|------|--------|-------|
| SSL Labs Rating | A+ | Meets security standards |
| Certificate Validity | PASS | Valid until 2025-04-01 |
| TLS 1.3 Support | PASS | |
| TLS 1.2 Support | PASS | |
| TLS 1.1 Blocked | PASS | |
| HSTS Header | PASS | max-age=31536000 |
| HTTP Redirect | PASS | |

## WAF Rule Testing

| Attack Type | Test Result | Notes |
|-------------|-------------|-------|
| SQL Injection | PASS | All 10 payloads blocked |
| XSS | PASS | All 8 payloads blocked |
| Path Traversal | PASS | All 5 payloads blocked |
| RCE | PASS | All 4 payloads blocked |
| LFI | PASS | All 3 payloads blocked |
| Legitimate Traffic | PASS | No false positives |

## Rate Limiting Testing

| Endpoint | Limit | Test Result | Notes |
|----------|-------|-------------|-------|
| API | 100/min | PASS | Blocked at 101st request |
| Login | 5/min | PASS | Blocked at 6th request |
| Registration | 3/min | PASS | Blocked at 4th request |
| Search | 10/min | PASS | Challenged at 11th request |

## Bot Protection Testing

| Test | Result | Notes |
|------|--------|-------|
| Normal Browser | PASS | No challenges |
| Headless Browser | PASS | Challenge shown |
| sqlmap User-Agent | PASS | Blocked |
| Nikto User-Agent | PASS | Blocked |
| Googlebot | PASS | Allowed |

## Issues Found

### Issue 1: Rate Limit Recovery Slow
- **Severity:** Low
- **Description:** Rate limit takes 62 seconds to reset (expected 60)
- **Action:** Monitor, may be acceptable variance

### Issue 2: Admin Endpoint Challenge Not Showing
- **Severity:** Medium
- **Description:** Admin endpoints not showing challenge in browser tests
- **Action:** Verify custom rule configuration

## Recommendations

1. Enable HSTS preload after 30-day observation
2. Consider increasing login rate limit to 10/min (too strict)
3. Add more geo-specific rules if abuse detected
4. Enable Super Bot Fight Mode (requires Pro plan)

## Sign-off

**Tester:** [Name]
**Date:** 2025-01-10
**Approved:** [Security Lead]
```

## Continuous Testing

### Weekly Automated Tests

**File: `.github/workflows/waf-tests.yml`**

```yaml
name: WAF Security Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight
  workflow_dispatch:  # Manual trigger

jobs:
  waf-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest requests

      - name: Run WAF tests
        run: |
          pytest tests/security/test_waf.py -v --junitxml=test-results.xml

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: waf-test-results
          path: test-results.xml

      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'WAF tests failed! Check GitHub Actions for details.'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Maintained By:** Security Team
**Review Schedule:** After each major WAF configuration change
