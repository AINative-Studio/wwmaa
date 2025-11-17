# Custom Domain Setup Summary - wwmaa.com

## Overview

This document summarizes the current state of custom domain configuration and what actions are needed to complete the setup.

## Current State Analysis

### Backend Configuration (COMPLETE ✓)

The backend is **already configured** to support the custom domain `wwmaa.com`:

**File:** `/Users/aideveloper/Desktop/wwmaa/backend/config.py`

**Configuration Details:**
- **Lines 512-543:** `cors_origins` property dynamically returns allowed origins based on environment
- **Production CORS origins include:**
  - `https://wwmaa.com`
  - `https://www.wwmaa.com`
  - `https://api.wwmaa.com`
  - `https://wwmaa.ainative.studio` (Railway subdomain fallback)
  - `https://athletic-curiosity-production.up.railway.app` (backend URL)

**How it works:**
```python
@property
def cors_origins(self) -> list[str]:
    """Return CORS origins based on environment."""
    origins = []

    if self.is_production:
        origins = [
            "https://wwmaa.com",
            "https://www.wwmaa.com",
            "https://api.wwmaa.com",
            "https://wwmaa.ainative.studio",
            "https://athletic-curiosity-production.up.railway.app"
        ]
    # ... rest of configuration
```

**File:** `/Users/aideveloper/Desktop/wwmaa/backend/app.py`

**Line 98:** CORS middleware configured to use `settings.cors_origins`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization", "Accept", "Origin", "User-Agent"],
    expose_headers=["*"],
    max_age=600,
)
```

**Action Required:** Verify `PYTHON_ENV=production` is set in Railway backend service.

### Frontend Configuration (NEEDS UPDATE)

The frontend needs environment variables updated after DNS is configured.

**Current configuration (Railway subdomain):**
```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
```

**Required configuration (Custom domain):**
```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.com
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
PYTHON_ENV=production
```

**Action Required:** Update after DNS and SSL are configured.

### DNS Configuration (NOT STARTED)

DNS records need to be added at your domain registrar.

**Status:** Not configured
**Action Required:** Follow steps in `DOMAIN_DEPLOYMENT_GUIDE.md`

### SSL Certificate (PENDING DNS)

Railway automatically provisions SSL certificates via Let's Encrypt.

**Status:** Pending (will auto-provision after DNS)
**Action Required:** None (automatic after DNS propagates)

## What's Already Done

1. **Backend CORS Configuration** - Fully configured for custom domain
2. **Documentation** - Comprehensive guides created:
   - `DOMAIN_SETUP.md` - Complete setup guide with troubleshooting
   - `DOMAIN_DEPLOYMENT_GUIDE.md` - Detailed step-by-step deployment guide
   - `DNS_CHECKLIST.md` - Checklist for DNS configuration
   - `ENV_UPDATES_FOR_DOMAIN.md` - Environment variable instructions
   - `DOMAIN_QUICK_REFERENCE.md` - One-page quick reference
   - `DOMAIN_SETUP_SUMMARY.md` - This file

## What Needs To Be Done

### Step 1: Railway Configuration (USER ACTION REQUIRED)

You need to add custom domains in Railway dashboard:

1. Login to Railway: https://railway.app/
2. Navigate to WWMAA project
3. Click WWMAA-FRONTEND service
4. Settings → Domains → + Custom Domain
5. Add `wwmaa.com`
6. Add `www.wwmaa.com`
7. **Note the DNS records Railway provides**

**Time Required:** 5 minutes

**Documentation:** See `DOMAIN_DEPLOYMENT_GUIDE.md` - "Railway Configuration" section

### Step 2: DNS Configuration (USER ACTION REQUIRED)

You need to add DNS records at your domain registrar:

1. Identify your registrar (Cloudflare, GoDaddy, Namecheap, etc.)
2. Login to registrar dashboard
3. Add DNS records as specified by Railway
4. Save changes

**Time Required:** 10 minutes
**Propagation Time:** 5-60 minutes

**Documentation:** See `DOMAIN_DEPLOYMENT_GUIDE.md` - "DNS Configuration" section

### Step 3: Wait for DNS Propagation (AUTOMATIC)

DNS changes propagate globally:

1. Wait 5-10 minutes initially
2. Check propagation with `dig wwmaa.com`
3. Monitor at https://dnschecker.org
4. Proceed when DNS resolves to Railway

**Time Required:** 5-60 minutes (passive waiting)

**Documentation:** See `DOMAIN_DEPLOYMENT_GUIDE.md` - "DNS Propagation Verification" section

### Step 4: Wait for SSL Certificate (AUTOMATIC)

Railway automatically provisions SSL:

1. After DNS propagates, Railway detects it
2. Railway requests certificate from Let's Encrypt
3. Certificate provisioned (5-15 minutes)
4. Check Railway dashboard for "SSL Certificate: Active"

**Time Required:** 5-15 minutes after DNS (automatic)

**Documentation:** See `DOMAIN_DEPLOYMENT_GUIDE.md` - "SSL Certificate Validation" section

### Step 5: Verify Backend Environment (USER ACTION)

Ensure backend is in production mode:

```bash
# Check current value
railway vars --service wwmaa-backend | grep PYTHON_ENV

# If not set to production, set it:
railway vars set PYTHON_ENV=production --service wwmaa-backend

# Redeploy backend (if changed)
# Railway will auto-redeploy when vars change
```

**Time Required:** 2 minutes

**Why:** Backend CORS uses `PYTHON_ENV` to determine which origins to allow

### Step 6: Update Frontend Environment Variables (USER ACTION)

Update frontend to use custom domain:

1. Railway dashboard → WWMAA-FRONTEND → Variables
2. Update:
   ```env
   NEXT_PUBLIC_SITE_URL=https://wwmaa.com
   NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
   PYTHON_ENV=production
   ```
3. Save (auto-redeploys)

**Time Required:** 5 minutes (including redeploy)

**Documentation:** See `ENV_UPDATES_FOR_DOMAIN.md`

### Step 7: Testing (USER ACTION)

Verify everything works:

1. **Automated tests:**
   ```bash
   curl -I https://wwmaa.com
   curl -I https://www.wwmaa.com
   # See DOMAIN_QUICK_REFERENCE.md for full test commands
   ```

2. **Manual testing:**
   - Visit https://wwmaa.com
   - Check SSL certificate (green padlock)
   - Test login/logout
   - Verify no CORS errors in console
   - Test all major functionality

**Time Required:** 15-30 minutes

**Documentation:** See `DOMAIN_DEPLOYMENT_GUIDE.md` - "Testing and Verification" section

### Step 8: Post-Deployment Updates (USER ACTION)

Update external services and documentation:

- [ ] Update README.md
- [ ] Google Search Console
- [ ] Google Analytics
- [ ] OAuth providers (if applicable)
- [ ] Stripe webhooks (if applicable)
- [ ] Email templates
- [ ] Social media links
- [ ] Set up monitoring

**Time Required:** 30-60 minutes

**Documentation:** See `DOMAIN_DEPLOYMENT_GUIDE.md` - "Post-Deployment Checklist" section

## Complete Timeline

| Phase | Duration | Type | Status |
|-------|----------|------|--------|
| Backend CORS config | N/A | Code | COMPLETE ✓ |
| Documentation | N/A | Code | COMPLETE ✓ |
| Railway setup | 5 min | User action | TODO |
| DNS configuration | 10 min | User action | TODO |
| DNS propagation | 5-60 min | Automatic | TODO |
| SSL provisioning | 5-15 min | Automatic | TODO |
| Backend env check | 2 min | User action | TODO |
| Frontend env update | 5 min | User action | TODO |
| Testing | 15-30 min | User action | TODO |
| Post-deployment | 30-60 min | User action | TODO |
| **Total User Time** | **72-122 min** | | |
| **Total Elapsed Time** | **77-182 min** | | |

## Key Points

### No Code Changes Required

All code is already configured for the custom domain. You only need to:
1. Configure DNS
2. Update environment variables
3. Redeploy

### Backend URL Stays the Same

The backend remains at:
```
https://athletic-curiosity-production.up.railway.app
```

Only the frontend moves to the custom domain.

### Railway Subdomain Always Works

The Railway subdomain will always work as a fallback:
```
https://wwmaa.ainative.studio
```

This allows safe rollback if needed.

### Environment Variable is Critical

The backend MUST have `PYTHON_ENV=production` set for CORS to work with custom domains.

**Verify with:**
```bash
railway vars --service wwmaa-backend | grep PYTHON_ENV
```

**Expected output:**
```
PYTHON_ENV=production
```

## Documentation Files

All documentation is located in `/Users/aideveloper/Desktop/wwmaa/docs/`:

1. **DOMAIN_DEPLOYMENT_GUIDE.md** (8KB)
   - Complete step-by-step deployment guide
   - Troubleshooting section
   - Rollback procedures
   - Post-deployment checklist

2. **DOMAIN_SETUP.md** (5KB)
   - High-level setup overview
   - DNS configuration for different registrars
   - Testing procedures

3. **DNS_CHECKLIST.md** (6KB)
   - Step-by-step DNS configuration checklist
   - Registrar-specific instructions
   - Verification steps

4. **ENV_UPDATES_FOR_DOMAIN.md** (3KB)
   - Environment variable instructions
   - Verification commands
   - Troubleshooting

5. **DOMAIN_QUICK_REFERENCE.md** (4KB)
   - One-page quick reference
   - Common commands
   - Quick fixes

6. **DOMAIN_SETUP_SUMMARY.md** (This file)
   - Overview of current state
   - What's done vs. what's needed
   - Complete timeline

## Next Steps

To proceed with domain setup:

1. **Start with:** `DOMAIN_QUICK_REFERENCE.md` for quick overview
2. **Follow:** `DOMAIN_DEPLOYMENT_GUIDE.md` for complete step-by-step
3. **Reference:** `DNS_CHECKLIST.md` while configuring DNS
4. **Use:** `DOMAIN_QUICK_REFERENCE.md` for commands during testing

## Questions & Support

If you encounter issues:

1. **Check:** `DOMAIN_DEPLOYMENT_GUIDE.md` - "Troubleshooting" section
2. **Review:** Backend logs: `railway logs --service wwmaa-backend`
3. **Review:** Frontend logs: `railway logs --service wwmaa-frontend`
4. **Test:** Use commands in `DOMAIN_QUICK_REFERENCE.md`
5. **Contact:** Railway support if infrastructure issues

## Success Criteria

Deployment is successful when:

1. DNS resolves: `dig wwmaa.com` returns Railway IP
2. SSL active: Railway dashboard shows "SSL Certificate: Active"
3. Site loads: https://wwmaa.com loads successfully
4. CORS works: No CORS errors in browser console
5. Auth works: Login/logout functionality works
6. All pages work: Navigation and all features work

## Rollback Plan

If something goes wrong:

**Quick rollback:**
```bash
# Update frontend environment variable
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
```

Railway subdomain continues working immediately. No data loss.

See `DOMAIN_DEPLOYMENT_GUIDE.md` - "Rollback Procedures" for details.

## Conclusion

The custom domain setup is well-prepared:

- **Backend:** Already configured for custom domain (no changes needed)
- **Frontend:** Ready for environment variable update
- **Documentation:** Comprehensive guides covering all scenarios
- **Rollback:** Safe rollback available at any time

Total estimated time: **1.5-3 hours** including DNS propagation and testing.

You're ready to proceed when you have:
- Access to domain registrar
- Access to Railway dashboard
- 1-3 hours to complete the process (including wait times)
