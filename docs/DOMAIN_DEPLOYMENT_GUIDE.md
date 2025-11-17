# Domain Deployment Guide - wwmaa.com

## Executive Summary

This guide provides a complete walkthrough for deploying the custom domain `wwmaa.com` to your Railway-hosted WWMAA application. The process involves DNS configuration, SSL certificate provisioning, and application configuration updates.

**Estimated Time:** 1-2 hours (including DNS propagation)

**Prerequisites:**
- Access to domain registrar (Cloudflare, GoDaddy, Namecheap, etc.)
- Access to Railway dashboard
- Domain ownership verification completed

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Railway Configuration](#railway-configuration)
3. [DNS Configuration](#dns-configuration)
4. [SSL Certificate Validation](#ssl-certificate-validation)
5. [Application Configuration](#application-configuration)
6. [Testing and Verification](#testing-and-verification)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

## Pre-Deployment Checklist

Before starting, verify you have:

- [ ] Domain `wwmaa.com` registered and active
- [ ] Access to domain registrar dashboard
- [ ] Railway dashboard access
- [ ] Current Railway deployment URLs documented:
  - Frontend: `https://wwmaa.ainative.studio`
  - Backend: `https://athletic-curiosity-production.up.railway.app`
- [ ] Understanding that backend remains on Railway subdomain
- [ ] Backup of current environment variables
- [ ] Team notification sent (if applicable)

## Railway Configuration

### Step 1: Add Custom Domain to Frontend Service

1. Login to Railway dashboard: https://railway.app/
2. Navigate to your WWMAA project
3. Click on **WWMAA-FRONTEND** service
4. Click **Settings** tab
5. Scroll to **Domains** section
6. Click **"+ Custom Domain"**
7. Enter `wwmaa.com` and click **Add Domain**
8. Click **"+ Custom Domain"** again
9. Enter `www.wwmaa.com` and click **Add Domain**

### Step 2: Record DNS Values

Railway will display the required DNS records. Document these values:

**For apex domain (wwmaa.com):**
```
Type: [A or CNAME - Railway will specify]
Name: @ (or root)
Value: [Record this value from Railway]
TTL: 300
```

**For www subdomain:**
```
Type: CNAME
Name: www
Value: [Record this value from Railway]
TTL: 300
```

Screenshot these values or copy them to a note for the next step.

## DNS Configuration

### Option A: Cloudflare DNS

**Recommended if using Cloudflare**

1. Login to Cloudflare dashboard
2. Select **wwmaa.com** domain
3. Go to **DNS** → **Records**
4. Click **Add record**

**Add apex domain record:**
- Type: `CNAME` (Cloudflare supports CNAME flattening)
- Name: `@`
- Target: [Value from Railway]
- Proxy status: **Proxied** (orange cloud) - Recommended
- TTL: Auto
- Click **Save**

**Add www subdomain record:**
- Type: `CNAME`
- Name: `www`
- Target: [Value from Railway]
- Proxy status: **Proxied** (orange cloud) - Recommended
- TTL: Auto
- Click **Save**

**Configure SSL/TLS:**
1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode to: **Full (strict)**
3. Go to **SSL/TLS** → **Edge Certificates**
4. Enable **Always Use HTTPS**: On
5. Enable **Automatic HTTPS Rewrites**: On

### Option B: GoDaddy DNS

1. Login to GoDaddy account
2. Go to **My Products** → **Domain Portfolio**
3. Click **DNS** next to wwmaa.com
4. Click **Add New Record**

**Add apex domain record:**
- Type: `A`
- Name: `@`
- Value: [IP address from Railway]
- TTL: 600 seconds
- Click **Save**

**Add www subdomain record:**
- Type: `CNAME`
- Name: `www`
- Value: [CNAME value from Railway]
- TTL: 600 seconds
- Click **Save**

### Option C: Namecheap DNS

1. Login to Namecheap account
2. Select **Domain List** → Click **Manage** next to wwmaa.com
3. Go to **Advanced DNS** tab
4. Click **Add New Record**

**Add apex domain record:**
- Type: `A Record`
- Host: `@`
- Value: [IP address from Railway]
- TTL: Automatic
- Click **Save All Changes**

**Add www subdomain record:**
- Type: `CNAME Record`
- Host: `www`
- Value: [CNAME value from Railway]
- TTL: Automatic
- Click **Save All Changes**

### Option D: AWS Route53

1. Login to AWS Console
2. Go to **Route53** → **Hosted zones**
3. Click on **wwmaa.com** hosted zone
4. Click **Create record**

**Add apex domain record:**
- Record name: (leave blank for root)
- Record type: `A` or `ALIAS` (ALIAS recommended)
- Value: [IP address or alias target from Railway]
- TTL: 300
- Routing policy: Simple
- Click **Create records**

**Add www subdomain record:**
- Record name: `www`
- Record type: `CNAME`
- Value: [CNAME value from Railway]
- TTL: 300
- Routing policy: Simple
- Click **Create records**

## DNS Propagation Verification

### Step 1: Wait for Initial Propagation (5-10 minutes)

DNS changes propagate globally. Initial propagation typically takes 5-10 minutes but can take up to 48 hours in rare cases.

### Step 2: Check DNS Resolution Locally

```bash
# Check apex domain
dig wwmaa.com

# Expected output:
# ;; ANSWER SECTION:
# wwmaa.com.  300  IN  A  104.238.123.45

# Check www subdomain
dig www.wwmaa.com

# Expected output:
# ;; ANSWER SECTION:
# www.wwmaa.com.  300  IN  CNAME  unique-id.up.railway.app
```

### Step 3: Check Global Propagation

Visit https://dnschecker.org and enter:
- `wwmaa.com`
- `www.wwmaa.com`

Look for green checkmarks indicating successful propagation globally.

### Step 4: Verify with nslookup

```bash
# Check apex domain
nslookup wwmaa.com

# Expected output:
# Server:  [DNS server]
# Address:  [DNS server IP]
#
# Name:    wwmaa.com
# Address:  [Railway IP]

# Check www subdomain
nslookup www.wwmaa.com

# Expected output shows CNAME to Railway
```

## SSL Certificate Validation

Railway automatically provisions SSL certificates via Let's Encrypt once DNS propagates.

### Step 1: Monitor SSL Certificate Status

1. Go to Railway dashboard
2. Click on **WWMAA-FRONTEND** service
3. Go to **Settings** → **Domains**
4. Check certificate status for both domains:
   - Initially shows: "SSL Certificate: Pending"
   - After 5-15 minutes: "SSL Certificate: Active"

### Step 2: Verify SSL Certificate

Once status shows "Active", verify the certificate:

```bash
# Test apex domain
curl -I https://wwmaa.com

# Expected: HTTP/2 200 OK with valid SSL

# Test www subdomain
curl -I https://www.wwmaa.com

# Expected: HTTP/2 200 OK with valid SSL
```

### Step 3: Check Certificate Details

```bash
# View certificate details
openssl s_client -connect wwmaa.com:443 -servername wwmaa.com | openssl x509 -noout -text

# Verify:
# - Issuer: Let's Encrypt
# - Subject: CN=wwmaa.com
# - Valid dates are correct
# - Subject Alternative Names include www.wwmaa.com
```

## Application Configuration

### Backend Configuration (Already Complete)

Good news! The backend CORS configuration already includes the custom domains:

**File:** `/Users/aideveloper/Desktop/wwmaa/backend/config.py`

The `cors_origins` property (lines 512-543) automatically includes:
- `https://wwmaa.com`
- `https://www.wwmaa.com`
- `https://wwmaa.ainative.studio` (fallback)

**When `PYTHON_ENV=production` is set**, these origins are active.

**Action Required:** Verify environment variable:
```bash
# Check Railway backend environment
railway vars --service wwmaa-backend

# Ensure PYTHON_ENV=production
```

If not set to production:
```bash
railway vars set PYTHON_ENV=production --service wwmaa-backend
```

### Frontend Configuration

Update environment variables in Railway:

1. Go to Railway dashboard
2. Click on **WWMAA-FRONTEND** service
3. Go to **Variables** tab
4. Update or add:

```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.com
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
PYTHON_ENV=production
```

5. Click **Save**
6. This will automatically trigger a redeploy

### Redeploy Backend (If PYTHON_ENV Changed)

If you had to set `PYTHON_ENV=production`:

1. Go to Railway dashboard
2. Click on **WWMAA-BACKEND** service
3. Go to **Deployments** tab
4. Click **Redeploy** on the latest deployment

## Testing and Verification

### Automated Testing

Run these commands to verify everything works:

```bash
# Test homepage loads
curl -I https://wwmaa.com
# Expected: HTTP/2 200

# Test www subdomain
curl -I https://www.wwmaa.com
# Expected: HTTP/2 200

# Test CORS from new domain
curl -H "Origin: https://wwmaa.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://athletic-curiosity-production.up.railway.app/api/health

# Expected response headers:
# Access-Control-Allow-Origin: https://wwmaa.com
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
# Access-Control-Allow-Headers: Content-Type, X-CSRF-Token, Authorization, ...

# Test backend health
curl https://athletic-curiosity-production.up.railway.app/health
# Expected: {"status":"healthy","environment":"production","debug":false}
```

### Manual Testing Checklist

- [ ] Visit https://wwmaa.com - homepage loads
- [ ] Visit https://www.wwmaa.com - homepage loads
- [ ] Green padlock (SSL) appears in browser
- [ ] Click on padlock → Certificate is valid
- [ ] No security warnings in browser
- [ ] Open browser console - no errors
- [ ] Test navigation - all pages load
- [ ] Test login functionality:
  - [ ] Navigate to login page
  - [ ] Enter credentials
  - [ ] Login succeeds
  - [ ] No CORS errors in console
- [ ] Test API calls:
  - [ ] Open DevTools → Network tab
  - [ ] Perform actions that call API
  - [ ] Verify API calls succeed (status 200)
  - [ ] Check Response headers include CORS headers
- [ ] Test logout functionality
- [ ] Test registration (if applicable)
- [ ] Test protected routes (dashboard, profile, etc.)

### Browser Compatibility Testing

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

## Troubleshooting

### Issue 1: DNS Not Resolving

**Symptoms:**
- `dig wwmaa.com` returns NXDOMAIN
- Website doesn't load
- "DNS_PROBE_FINISHED_NXDOMAIN" error

**Solutions:**
1. Wait longer (DNS can take up to 48 hours, typically 5-60 minutes)
2. Clear local DNS cache:
   ```bash
   # macOS
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder

   # Linux
   sudo systemd-resolve --flush-caches

   # Windows
   ipconfig /flushdns
   ```
3. Verify DNS records in registrar dashboard
4. Check Railway provided the correct values
5. Use https://dnschecker.org to monitor propagation

### Issue 2: SSL Certificate Pending

**Symptoms:**
- Railway shows "SSL Certificate: Pending"
- HTTPS doesn't work
- Browser shows "Not Secure"

**Solutions:**
1. Verify DNS resolves to Railway (see Issue 1)
2. Wait 15-30 minutes after DNS propagates
3. Check Railway logs for SSL errors:
   ```bash
   railway logs --service wwmaa-frontend
   ```
4. Ensure Railway subdomain still works (validates Railway is healthy)
5. Try removing and re-adding custom domain in Railway
6. Contact Railway support if issue persists

### Issue 3: CORS Errors

**Symptoms:**
- Browser console shows CORS errors
- API calls fail with CORS policy errors
- Login/registration doesn't work

**Solutions:**
1. Verify `PYTHON_ENV=production` in backend:
   ```bash
   railway vars --service wwmaa-backend | grep PYTHON_ENV
   ```
2. Redeploy backend service
3. Check backend logs:
   ```bash
   railway logs --service wwmaa-backend | grep -i cors
   ```
4. Verify CORS origins logged on startup:
   ```
   INFO: CORS origins: ['https://wwmaa.com', 'https://www.wwmaa.com', ...]
   ```
5. Test CORS explicitly:
   ```bash
   curl -H "Origin: https://wwmaa.com" -I https://athletic-curiosity-production.up.railway.app/health
   ```
6. Clear browser cache and cookies
7. Try incognito/private browsing mode

### Issue 4: Mixed Content Warnings

**Symptoms:**
- Some resources don't load
- Browser console shows mixed content warnings
- Images/videos don't display

**Solutions:**
1. Verify all API calls use HTTPS
2. Check `NEXT_PUBLIC_API_URL` uses `https://`
3. Search codebase for hardcoded HTTP URLs:
   ```bash
   grep -r "http://" frontend/src --include="*.ts" --include="*.tsx"
   ```
4. Update any HTTP URLs to HTTPS or relative URLs
5. Redeploy frontend

### Issue 5: Login Redirects to Old Domain

**Symptoms:**
- After login, redirected to `wwmaa.ainative.studio`
- Callbacks use old domain

**Solutions:**
1. Verify `NEXT_PUBLIC_SITE_URL=https://wwmaa.com` in frontend
2. Check OAuth redirect URLs (if using OAuth):
   - Update in provider dashboard (Google, GitHub, etc.)
   - Add new domain to allowed redirect URIs
3. Update Stripe redirect URLs (if applicable)
4. Clear browser cookies for old domain
5. Redeploy frontend after env changes

### Issue 6: 404 on Direct Page Load

**Symptoms:**
- Homepage works
- Navigation works
- Direct page load (refresh) shows 404

**Solutions:**
1. This is likely a Railway routing issue
2. Verify Railway is serving the Next.js app correctly
3. Check build output:
   ```bash
   railway logs --service wwmaa-frontend | grep -i "build\|error"
   ```
4. Ensure `.output` directory exists (Nuxt) or `.next` (Next.js)
5. Redeploy with verbose logging

## Rollback Procedures

If you need to rollback to the Railway subdomain:

### Quick Rollback (Frontend Only)

1. Go to Railway dashboard
2. Click **WWMAA-FRONTEND** service
3. Go to **Variables** tab
4. Update:
   ```env
   NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
   ```
5. Save and redeploy

Railway subdomain continues to work immediately.

### Full Rollback (Remove Custom Domain)

1. Go to Railway dashboard
2. Click **WWMAA-FRONTEND** service
3. Go to **Settings** → **Domains**
4. Click **Remove** next to custom domains
5. Update frontend environment variables back to Railway subdomain
6. Optionally remove DNS records from registrar

### Partial Rollback (Keep DNS, Use Subdomain)

Keep DNS configured but temporarily use Railway subdomain:

1. Update frontend environment variable only:
   ```env
   NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
   ```
2. Users can access via both domains
3. Investigate and fix issue
4. Switch back when ready

## Post-Deployment Checklist

After successful deployment:

- [ ] Update documentation with new domain
- [ ] Update README.md
- [ ] Update Google Search Console:
  - [ ] Add new property for wwmaa.com
  - [ ] Submit sitemap
- [ ] Update Google Analytics:
  - [ ] Add new property or update existing
  - [ ] Verify tracking works
- [ ] Update OAuth providers (if applicable):
  - [ ] Google OAuth redirect URIs
  - [ ] GitHub OAuth callback URLs
  - [ ] Facebook App domains
- [ ] Update Stripe webhooks (if applicable):
  - [ ] Success/cancel URLs
  - [ ] Webhook endpoints
- [ ] Update email templates:
  - [ ] Verify links use new domain
  - [ ] Test welcome emails
  - [ ] Test password reset emails
- [ ] Update social media links:
  - [ ] Twitter/X profile
  - [ ] Facebook page
  - [ ] LinkedIn
  - [ ] Instagram bio
- [ ] Set up monitoring:
  - [ ] UptimeRobot or similar
  - [ ] SSL certificate expiration alerts
  - [ ] DNS monitoring
- [ ] Notify team/users of new domain
- [ ] Update business cards/marketing materials

## Timeline Summary

| Phase | Duration | Details |
|-------|----------|---------|
| **Railway Setup** | 5 minutes | Add custom domains |
| **DNS Configuration** | 10 minutes | Add records at registrar |
| **DNS Propagation** | 5-60 minutes | Wait for global propagation |
| **SSL Provisioning** | 5-15 minutes | Let's Encrypt validation |
| **App Configuration** | 10 minutes | Update environment variables |
| **Deployment** | 5-10 minutes | Redeploy services |
| **Testing** | 15-30 minutes | Comprehensive testing |
| **Documentation** | 15-30 minutes | Update docs and external services |
| **Total** | **70-170 minutes** | **1-3 hours** |

## Support and Resources

- **Railway Documentation:** https://docs.railway.app/deploy/custom-domains
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **DNS Checker:** https://dnschecker.org
- **SSL Labs Test:** https://www.ssllabs.com/ssltest/
- **CORS Testing:** https://www.test-cors.org/
- **Railway Support:** https://help.railway.app/

## Success Criteria

Deployment is successful when:

1. **DNS Resolution:** Both wwmaa.com and www.wwmaa.com resolve to Railway
2. **SSL Certificate:** Valid SSL certificate from Let's Encrypt
3. **Homepage:** Loads successfully at https://wwmaa.com
4. **CORS:** API calls succeed without CORS errors
5. **Authentication:** Login/logout functionality works
6. **Navigation:** All pages load correctly
7. **Security:** No browser security warnings
8. **Performance:** Page load times are acceptable
9. **Mobile:** Works on mobile devices
10. **Cross-browser:** Works in all major browsers

Congratulations! Your custom domain is now live.
