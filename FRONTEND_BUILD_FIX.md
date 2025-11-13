# Frontend Build Fix - Action Required

**Issue:** Frontend build failing with SWC binary corruption
**Error:** `unhandledRejection ZlibError: zlib: unexpected end of file`

## Root Cause

The environment variables in `nixpacks.toml` are not available during the build phase. Railway needs these variables set in the service configuration.

## Solution: Add Build-Time Environment Variables in Railway

### Go to Railway Dashboard

1. Open https://railway.app
2. Navigate to **AINative Studio - Production** project
3. Click on **WWMAA-FRONTEND** service
4. Go to **Variables** tab

### Add These Variables

Click **New Variable** for each and set to **Raw Editor**:

```
NEXT_TELEMETRY_DISABLED=1
NEXT_SKIP_NATIVE_POSTINSTALL=1
NEXT_SWC_SKIP_DOWNLOAD=1
NEXT_USE_SWC_WASM=true
```

### Verify Existing Variables

Make sure these are also present:
```
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
NODE_ENV=production
```

### Trigger Rebuild

After adding the variables:
1. Click **Save** (if needed)
2. Railway will automatically redeploy
3. Watch the build logs - it should say "Creating an optimized production build" without "Downloading swc package"

## Alternative: Switch to Dockerfile Build

If the above doesn't work, switch to using the Dockerfile:

1. Go to **WWMAA-FRONTEND** > **Settings**
2. Scroll to **Build** section
3. Change **Builder** from "Nixpacks" to "Dockerfile"
4. Set **Dockerfile Path** to: `Dockerfile.frontend`
5. Click **Save**

The Dockerfile uses Alpine Linux which handles the SWC compilation better.

---

## What These Variables Do

| Variable | Purpose |
|----------|---------|
| `NEXT_TELEMETRY_DISABLED=1` | Disables Next.js telemetry collection |
| `NEXT_SKIP_NATIVE_POSTINSTALL=1` | Skips native module post-install scripts |
| `NEXT_SWC_SKIP_DOWNLOAD=1` | Prevents downloading SWC native binary |
| `NEXT_USE_SWC_WASM=true` | Forces Next.js to use WASM version of SWC |

The WASM version is already in `node_modules` as `@next/swc-wasm-nodejs`, so no download is needed.

---

*Last Updated: November 13, 2025*
*Status: Awaiting Railway variable configuration*
