# SSL/TLS Configuration Guide for Cloudflare

## Overview

This document provides detailed instructions for configuring SSL/TLS encryption between Cloudflare and the wwmaa.com application, ensuring end-to-end encryption with Full (Strict) mode.

## Table of Contents

1. [SSL/TLS Modes Explained](#ssltls-modes-explained)
2. [Recommended Configuration: Full (Strict)](#recommended-configuration-full-strict)
3. [Origin Certificate Setup](#origin-certificate-setup)
4. [Railway Backend Configuration](#railway-backend-configuration)
5. [Edge Certificates](#edge-certificates)
6. [Security Headers Configuration](#security-headers-configuration)
7. [HSTS Configuration](#hsts-configuration)
8. [TLS Version Settings](#tls-version-settings)
9. [Certificate Monitoring](#certificate-monitoring)
10. [Testing and Validation](#testing-and-validation)
11. [Troubleshooting](#troubleshooting)

## SSL/TLS Modes Explained

Cloudflare offers several SSL/TLS encryption modes:

### Off (Not Recommended)

```
Client ----[HTTP]----> Cloudflare ----[HTTP]----> Origin Server
```
- No encryption at any point
- Vulnerable to eavesdropping
- **Never use for production**

### Flexible (Not Recommended)

```
Client ----[HTTPS]----> Cloudflare ----[HTTP]----> Origin Server
```
- Encrypted between client and Cloudflare only
- Unencrypted between Cloudflare and origin
- Vulnerable to man-in-the-middle attacks between Cloudflare and origin
- **Not secure enough for production**

### Full

```
Client ----[HTTPS]----> Cloudflare ----[HTTPS]----> Origin Server
```
- Encrypted end-to-end
- Origin can use self-signed certificate
- Does not validate origin certificate
- Better than Flexible but not ideal

### Full (Strict) - RECOMMENDED

```
Client ----[HTTPS]----> Cloudflare ----[HTTPS]----> Origin Server
                                      (Valid Certificate)
```
- Encrypted end-to-end
- Origin must have valid certificate (Cloudflare Origin Certificate or trusted CA)
- Certificate validation enforced
- **Best security for production**

### Strict (SSL-Only Origin Pull)

- Similar to Full (Strict)
- Origin must have certificate from trusted CA only
- Cloudflare Origin Certificates not accepted
- Useful for compliance requirements

## Recommended Configuration: Full (Strict)

### Why Full (Strict)?

1. **End-to-end encryption** - Data encrypted from client to origin
2. **Certificate validation** - Prevents man-in-the-middle attacks
3. **Free Cloudflare certificates** - No cost for origin certificates
4. **Best practice** - Industry standard for production applications
5. **Compliance** - Meets security requirements for sensitive data

### Configuration Steps

1. Navigate to **SSL/TLS** in Cloudflare Dashboard
2. Select **Overview** tab
3. Choose **Full (Strict)** mode
4. Wait 30 seconds for changes to propagate
5. Verify configuration (see Testing section)

## Origin Certificate Setup

Cloudflare provides free Origin Certificates that are valid for up to 15 years and specifically designed for Full (Strict) mode.

### Step 1: Generate Origin Certificate

1. Log in to Cloudflare Dashboard
2. Navigate to **SSL/TLS** → **Origin Server**
3. Click **Create Certificate**

### Step 2: Configure Certificate Settings

```
Certificate Options:
- Let Cloudflare generate a private key and a CSR: [Selected]
- Use my private key and CSR: [Not selected]

Hostnames:
- *.wwmaa.com
- wwmaa.com

Certificate Validity: 15 years (default)

Key Type: RSA (2048 bit) [Recommended]
```

**Hostnames Explanation:**
- `wwmaa.com` - Covers the root domain
- `*.wwmaa.com` - Covers all subdomains (www, staging, api, etc.)

### Step 3: Copy Certificate and Private Key

After clicking "Create", you'll see:

```
Origin Certificate:
-----BEGIN CERTIFICATE-----
MIIExDCCA6ygAwIBAgIUXXXXXXXXXXXXXXXXXXXXXXXXXXX...
[Certificate content]
-----END CERTIFICATE-----

Private Key:
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
[Private key content]
-----END PRIVATE KEY-----
```

**IMPORTANT SECURITY NOTES:**
- Copy both certificate and private key immediately
- Save to secure password manager (1Password, LastPass)
- NEVER commit to git repository
- NEVER share via email or insecure channels
- Store in Railway environment variables

### Step 4: Save Certificate Files (for local reference)

Create temporary secure files (DO NOT commit to git):

```bash
# Save certificate
cat > /tmp/wwmaa-origin-cert.pem << 'EOF'
-----BEGIN CERTIFICATE-----
[Paste certificate here]
-----END CERTIFICATE-----
EOF

# Save private key
cat > /tmp/wwmaa-origin-key.pem << 'EOF'
-----BEGIN PRIVATE KEY-----
[Paste private key here]
-----END PRIVATE KEY-----
EOF

# Secure the files
chmod 600 /tmp/wwmaa-origin-cert.pem
chmod 600 /tmp/wwmaa-origin-key.pem
```

## Railway Backend Configuration

### Step 1: Add Certificate to Railway Environment Variables

1. Log in to Railway Dashboard
2. Select your project: wwmaa
3. Select service: backend
4. Navigate to **Variables** tab
5. Add the following variables:

```bash
# Origin Certificate (multi-line)
SSL_CERTIFICATE=-----BEGIN CERTIFICATE-----
MIIExDCCA6ygAwIBAgIUXXXXXXXXXXXXXXXXXXXXXXXXXXX...
-----END CERTIFICATE-----

# Private Key (multi-line)
SSL_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
-----END PRIVATE KEY-----

# Enable SSL in application
USE_SSL=true
SSL_PORT=443
```

**Note:** Railway supports multi-line environment variables. Paste the entire certificate including the `-----BEGIN` and `-----END` lines.

### Step 2: Configure Python/FastAPI Application

Update your FastAPI application to use SSL certificates:

**File: `/backend/main.py`** (or similar)

```python
import os
import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Your routes here...

if __name__ == "__main__":
    use_ssl = os.getenv("USE_SSL", "false").lower() == "true"

    if use_ssl:
        # Write certificates to temporary files
        cert_path = "/tmp/cert.pem"
        key_path = "/tmp/key.pem"

        with open(cert_path, "w") as f:
            f.write(os.getenv("SSL_CERTIFICATE"))

        with open(key_path, "w") as f:
            f.write(os.getenv("SSL_PRIVATE_KEY"))

        # Set proper permissions
        os.chmod(cert_path, 0o600)
        os.chmod(key_path, 0o600)

        # Run with SSL
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("SSL_PORT", 443)),
            ssl_certfile=cert_path,
            ssl_keyfile=key_path
        )
    else:
        # Run without SSL (for local development)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000))
        )
```

### Step 3: Update Railway Configuration

**File: `railway.json`** (if applicable)

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Deploy Changes

```bash
# Commit changes (without certificates)
git add backend/main.py railway.json
git commit -m "feat: Configure SSL/TLS for origin server"
git push

# Railway will auto-deploy
# Monitor deployment logs for SSL initialization
```

## Edge Certificates

Cloudflare automatically provides and manages SSL certificates for your domain (between clients and Cloudflare).

### Universal SSL Certificate

Automatically provisioned for all domains on Cloudflare.

**View Certificate:**
1. Navigate to **SSL/TLS** → **Edge Certificates**
2. See "Universal SSL Status": Active
3. Certificate Authority: Let's Encrypt or Google Trust Services
4. Validity: 90 days (auto-renewed)

**Certificate Details:**
```
Hostnames: wwmaa.com, *.wwmaa.com
Issuer: Let's Encrypt / Google Trust Services
Type: Universal SSL
Validity: 90 days (auto-renewal)
Status: Active
```

### Advanced Certificate Manager (Optional - Paid)

For Business and Enterprise plans:

**Features:**
- Custom certificates
- Longer validity periods
- Specific CA selection
- Multiple certificates per domain

**Not required for most use cases.**

## Security Headers Configuration

Configure security headers to enhance HTTPS security.

### Step 1: Enable Always Use HTTPS

1. Navigate to **SSL/TLS** → **Edge Certificates**
2. Scroll to "Always Use HTTPS"
3. Toggle to **On**

**Effect:** Automatically redirects all HTTP requests to HTTPS.

```
http://wwmaa.com → https://wwmaa.com
```

### Step 2: Enable Automatic HTTPS Rewrites

1. In **SSL/TLS** → **Edge Certificates**
2. Find "Automatic HTTPS Rewrites"
3. Toggle to **On**

**Effect:** Rewrites insecure links in HTML to HTTPS.

```html
<!-- Before -->
<img src="http://wwmaa.com/image.png">

<!-- After (automatically rewritten) -->
<img src="https://wwmaa.com/image.png">
```

### Step 3: Enable Opportunistic Encryption

1. In **SSL/TLS** → **Edge Certificates**
2. Find "Opportunistic Encryption"
3. Toggle to **On**

**Effect:** Allows supporting browsers to automatically upgrade to HTTPS.

## HSTS Configuration

HTTP Strict Transport Security (HSTS) instructs browsers to always use HTTPS.

### Step 1: Enable HSTS in Cloudflare

1. Navigate to **SSL/TLS** → **Edge Certificates**
2. Scroll to "HTTP Strict Transport Security (HSTS)"
3. Click **Enable HSTS**

### Step 2: Configure HSTS Settings

**Recommended Configuration:**

```
Status: Enabled

Max Age Header (max-age): 12 months (31536000 seconds)
- Instructs browsers to remember HTTPS requirement for 1 year

Apply HSTS policy to subdomains (includeSubDomains): Yes
- Applies to www.wwmaa.com, staging.wwmaa.com, etc.

Preload: No (initially)
- Only enable after testing for 30 days

No-Sniff Header: Yes
- Prevents MIME type sniffing
```

**Warning:** HSTS can lock users out if SSL breaks. Test thoroughly before enabling preload.

### Step 3: Verify HSTS Header

After enabling, verify the header is present:

```bash
curl -I https://wwmaa.com | grep -i strict

# Expected output:
strict-transport-security: max-age=31536000; includeSubDomains
```

### Step 4: HSTS Preload (Optional - After 30 Days)

After running HSTS successfully for 30+ days:

1. Enable "Preload" in Cloudflare HSTS settings
2. Submit domain to HSTS Preload List:
   - Visit: https://hstspreload.org/
   - Enter: wwmaa.com
   - Follow submission instructions

**Benefits of Preload:**
- Protection on first visit (before HSTS header seen)
- Included in browser preload lists
- Maximum security

**Requirements:**
- Valid certificate
- Redirect HTTP to HTTPS
- HSTS on base domain and all subdomains
- max-age at least 31536000 seconds (12 months)
- includeSubDomains directive
- preload directive

## TLS Version Settings

Configure minimum TLS version and cipher suites.

### Step 1: Set Minimum TLS Version

1. Navigate to **SSL/TLS** → **Edge Certificates**
2. Find "Minimum TLS Version"
3. Select: **TLS 1.2** (Recommended)

**Options:**
- TLS 1.0 - Legacy (not recommended)
- TLS 1.1 - Legacy (not recommended)
- TLS 1.2 - Recommended (wide compatibility)
- TLS 1.3 - Most secure (may exclude some older clients)

**Recommendation:** Use TLS 1.2 for compatibility, TLS 1.3 for maximum security.

### Step 2: Enable TLS 1.3

1. In **SSL/TLS** → **Edge Certificates**
2. Find "TLS 1.3"
3. Toggle to **On**

**Benefits:**
- Faster handshake (fewer round trips)
- Improved security (better cipher suites)
- Forward secrecy by default
- Zero Round Trip Time (0-RTT) support

### Step 3: Configure Cipher Suites (Advanced)

For Business and Enterprise plans:

1. Navigate to **SSL/TLS** → **Edge Certificates**
2. Click "Cipher Suites"
3. Select modern, secure cipher suites

**Recommended Cipher Suites:**
```
# TLS 1.3 (Automatically used when available)
TLS_AES_128_GCM_SHA256
TLS_AES_256_GCM_SHA384
TLS_CHACHA20_POLY1305_SHA256

# TLS 1.2
ECDHE-ECDSA-AES128-GCM-SHA256
ECDHE-ECDSA-AES256-GCM-SHA384
ECDHE-RSA-AES128-GCM-SHA256
ECDHE-RSA-AES256-GCM-SHA384
```

**Avoid:**
- CBC mode ciphers (vulnerable to padding oracle attacks)
- RC4 (insecure)
- MD5 (insecure)
- DES/3DES (weak)

## Certificate Monitoring

### Step 1: Enable Certificate Expiration Alerts

1. Navigate to **Notifications**
2. Click **Add**
3. Select "SSL Certificate Expiring"
4. Configuration:
   ```
   Alert Name: SSL Certificate Expiration
   Notification: 30 days before expiration
   Delivery: Email + Webhook (Slack)
   Recipients: security@wwmaa.com, ops@wwmaa.com
   ```

### Step 2: Monitor Certificate Status

**Cloudflare Dashboard:**
- **SSL/TLS** → **Edge Certificates** - Check Universal SSL status
- **SSL/TLS** → **Origin Server** - Check Origin Certificate validity

**Automated Monitoring:**

```bash
#!/bin/bash
# check-ssl-expiry.sh
# Run this weekly via cron job

DOMAIN="wwmaa.com"
DAYS_WARNING=30

# Check certificate expiry
EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

echo "Certificate for $DOMAIN expires in $DAYS_LEFT days"

if [ $DAYS_LEFT -lt $DAYS_WARNING ]; then
    echo "WARNING: Certificate expires soon!"
    # Send alert (e.g., to Slack)
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"SSL certificate for $DOMAIN expires in $DAYS_LEFT days!\"}" \
        $SLACK_WEBHOOK_URL
fi
```

### Step 3: Certificate Transparency Monitoring

Monitor Certificate Transparency logs for unauthorized certificates:

1. Use service: https://crt.sh/?q=wwmaa.com
2. Review all certificates issued for your domain
3. Verify all certificates are expected
4. Alert on unexpected certificates

**Automated Monitoring:**
- Set up CT log monitoring with tools like:
  - SSLMate Certspotter
  - Facebook CT Monitor
  - Google Certificate Transparency Search

## Testing and Validation

### Test 1: SSL Labs Test

**Most Comprehensive Test:**

1. Go to: https://www.ssllabs.com/ssltest/
2. Enter: `wwmaa.com`
3. Click "Submit"
4. Wait for analysis (2-5 minutes)

**Target Grade: A+**

**Expected Results:**
```
Overall Rating: A+

Certificate:
- Issuer: Let's Encrypt / Google Trust Services
- Validity: Valid
- Chain: Complete

Protocol Support:
- TLS 1.3: Yes
- TLS 1.2: Yes
- TLS 1.1: No
- TLS 1.0: No

Cipher Suites:
- Strong ciphers only
- Forward Secrecy: Yes
- Weak ciphers: None

Security:
- HSTS: Yes
- HSTS Preload: Yes (if configured)
- Certificate Transparency: Yes
```

### Test 2: Command Line Tests

**Test HTTPS Connection:**
```bash
curl -I https://wwmaa.com

# Expected: HTTP/2 200 OK with security headers
```

**Test TLS Version:**
```bash
openssl s_client -connect wwmaa.com:443 -tls1_3

# Expected: Connection successful with TLS 1.3
```

**Test Certificate Details:**
```bash
echo | openssl s_client -servername wwmaa.com -connect wwmaa.com:443 2>/dev/null | openssl x509 -noout -text

# Expected: Valid certificate details
```

**Test HSTS Header:**
```bash
curl -I https://wwmaa.com | grep -i strict-transport-security

# Expected: strict-transport-security header present
```

**Test HTTP to HTTPS Redirect:**
```bash
curl -I http://wwmaa.com

# Expected: 301/302 redirect to https://wwmaa.com
```

### Test 3: Browser Tests

**Chrome DevTools:**
1. Open https://wwmaa.com
2. Press F12 → Security tab
3. Verify:
   - Connection: Secure
   - Certificate: Valid
   - Protocol: TLS 1.3 or TLS 1.2
   - Cipher: Strong

**Firefox Developer Tools:**
1. Open https://wwmaa.com
2. Press F12 → Security tab
3. Click "View Certificate"
4. Verify certificate details

### Test 4: Origin Certificate Validation

**Test Origin Connection (from Cloudflare):**
1. Temporarily disable Cloudflare proxy (set DNS to "DNS Only")
2. Try accessing: https://[railway-domain].railway.app
3. Verify SSL error (expected - origin cert only valid for wwmaa.com)
4. Re-enable Cloudflare proxy

**Test Origin with Cloudflare:**
1. Ensure proxy is enabled (orange cloud)
2. Access: https://wwmaa.com
3. Should work without SSL errors
4. Confirms Full (Strict) mode working

## Troubleshooting

### Issue: "Too Many Redirects" Error

**Cause:** Origin server is redirecting HTTPS to HTTP, creating loop.

**Solution:**
1. Check origin server configuration
2. Ensure origin serves HTTPS on port 443
3. Verify Cloudflare SSL mode is Full (Strict)
4. Check Railway environment variables

**Fix in FastAPI:**
```python
# Remove any HTTP to HTTPS redirects in your app
# Cloudflare handles this with "Always Use HTTPS"
```

### Issue: "526 Invalid SSL Certificate" Error

**Cause:** Origin certificate is invalid or expired.

**Symptoms:**
- Error 526 on Cloudflare error page
- SSL/TLS verification fails

**Solution:**
1. Verify origin certificate is installed correctly on Railway
2. Check certificate hasn't expired
3. Ensure certificate covers the domain (wwmaa.com)
4. Regenerate origin certificate if needed
5. Verify environment variables in Railway are correct

**Debugging:**
```bash
# Test origin directly (will show certificate error)
curl -k https://[your-railway-url].railway.app

# Check Cloudflare SSL mode
# Ensure it's set to "Full (Strict)"
```

### Issue: Mixed Content Warnings

**Cause:** HTTPS page loading HTTP resources.

**Symptoms:**
- Browser console shows mixed content warnings
- Some resources fail to load
- Broken lock icon in browser

**Solution:**
1. Enable "Automatic HTTPS Rewrites" in Cloudflare
2. Update hardcoded HTTP URLs in code to HTTPS or relative URLs
3. Use Content Security Policy:

```python
# Add to FastAPI middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    return response
```

### Issue: Certificate Not Trusted (Mobile)

**Cause:** Some older mobile devices don't trust Let's Encrypt certificates.

**Solution:**
1. Ensure "Always Use HTTPS" is enabled
2. Cloudflare automatically serves appropriate certificates
3. For very old devices, consider Advanced Certificate Manager (paid)

### Issue: Performance Degradation After Enabling SSL

**Cause:** SSL/TLS handshake overhead.

**Solution:**
1. Enable TLS 1.3 for faster handshakes
2. Enable HTTP/2 (automatic with Cloudflare)
3. Configure session resumption
4. Use Cloudflare's caching

**Verify HTTP/2:**
```bash
curl -I https://wwmaa.com --http2

# Expected: HTTP/2 200
```

### Issue: Origin Certificate Expired

**Cause:** Origin certificate reached end of validity.

**Symptoms:**
- Error 526 suddenly appears
- Was working previously

**Solution:**
1. Generate new origin certificate in Cloudflare
2. Update Railway environment variables
3. Redeploy application
4. Set up expiration monitoring (see Certificate Monitoring section)

## Security Checklist

- [ ] Full (Strict) mode enabled
- [ ] Origin certificate generated and installed
- [ ] Always Use HTTPS enabled
- [ ] Automatic HTTPS Rewrites enabled
- [ ] HSTS enabled with 12-month max-age
- [ ] Minimum TLS version 1.2
- [ ] TLS 1.3 enabled
- [ ] Certificate expiration alerts configured
- [ ] SSL Labs test score: A or A+
- [ ] No mixed content warnings
- [ ] HTTP to HTTPS redirect working
- [ ] Security headers configured
- [ ] Certificate monitoring in place

## Compliance Notes

This SSL/TLS configuration meets requirements for:

- **PCI DSS 3.2.1** - Strong cryptography for cardholder data
- **HIPAA** - Encryption in transit requirements
- **GDPR** - Data protection in transit
- **SOC 2** - Secure transmission controls
- **ISO 27001** - Cryptographic controls

Maintain documentation of:
- Certificate generation dates
- Configuration changes
- Security assessments
- Incident responses

## Additional Resources

- [Cloudflare SSL/TLS Documentation](https://developers.cloudflare.com/ssl/)
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)
- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

## Support

**Internal:**
- Security Team: security@wwmaa.com
- DevOps Team: ops@wwmaa.com

**External:**
- Cloudflare Support: Via dashboard (ticket system)
- Railway Support: https://railway.app/help

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Maintained By:** Security Team
**Review Schedule:** Quarterly
