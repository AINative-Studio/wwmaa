# Railway Frontend Environment Variables - REQUIRED

**Issue:** Frontend is connecting to `localhost:8000` instead of production backend
**Error:** `net::ERR_CONNECTION_REFUSED` when trying to login

## Root Cause

The `NEXT_PUBLIC_API_URL` environment variable is **not set** in Railway, so the frontend defaults to:
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

## Solution: Add Environment Variables in Railway

### Go to Railway Dashboard

1. Open: https://railway.app
2. Navigate to **AINative Studio - Production** project
3. Click on **WWMAA-FRONTEND** service
4. Click **Variables** tab

### Add These Variables

Click **New Variable** for each (or use Raw Editor):

```bash
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
NODE_ENV=production
```

### Very Important: Variable Naming

⚠️ **These MUST start with `NEXT_PUBLIC_`** for Next.js to expose them to the browser!

Without this prefix, the variables won't be available in client-side code.

### After Adding Variables

1. Click **Save** (or they auto-save)
2. Railway will **automatically redeploy** (~3-5 minutes)
3. Once deployed, try logging in again

## Verification

After deployment, check browser console:
- **Before:** `localhost:8000/api/security/csrf-token` (fails)
- **After:** `https://athletic-curiosity-production.up.railway.app/api/security/csrf-token` (succeeds)

## All Required Variables for WWMAA-FRONTEND

Here's the complete list for copy-paste:

```bash
# API Configuration (REQUIRED)
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio

# Environment
NODE_ENV=production

# Build Configuration (Optional but Recommended)
NEXT_TELEMETRY_DISABLED=1
NEXT_SWC_SKIP_DOWNLOAD=1
NEXT_USE_SWC_WASM=true
NEXT_SKIP_NATIVE_POSTINSTALL=1
```

## How to Add in Railway UI

### Method 1: One by One
1. Click **+ New Variable**
2. Enter variable name (e.g., `NEXT_PUBLIC_API_URL`)
3. Enter value (e.g., `https://athletic-curiosity-production.up.railway.app`)
4. Repeat for each variable

### Method 2: Raw Editor (Faster)
1. Click **RAW Editor** button (top right of Variables section)
2. Paste all variables:
   ```
   NEXT_PUBLIC_API_MODE=live
   NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
   NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
   NODE_ENV=production
   NEXT_TELEMETRY_DISABLED=1
   NEXT_SWC_SKIP_DOWNLOAD=1
   NEXT_USE_SWC_WASM=true
   NEXT_SKIP_NATIVE_POSTINSTALL=1
   ```
3. Click **Update Variables**

## After Variables are Set

Wait for Railway to redeploy (~3-5 minutes), then test login:

```
URL: https://wwmaa.ainative.studio/login
Email: admin@wwmaa.com
Password: AdminPass123!
```

### Expected Behavior

1. Click "Sign In"
2. Browser console shows:
   - Request to `https://athletic-curiosity-production.up.railway.app/api/security/csrf-token`
   - Request to `https://athletic-curiosity-production.up.railway.app/api/auth/login`
3. Successful login → redirect to dashboard
4. You see your name in top right
5. No errors in console

---

*Last Updated: November 13, 2025*
*Priority: CRITICAL - Login cannot work without these variables*
