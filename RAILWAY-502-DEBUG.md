# Railway 502 Bad Gateway - Debug Guide

## Current Status

- **Deploy Status**: SUCCESS ✅
- **Application Status**: Started successfully on port 5432
- **Issue**: URL returns 502 Bad Gateway error
- **CORS**: Fixed and configured correctly

## Deploy Logs Analysis

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5432
CORS origins: ['https://wwmaa.com', 'https://www.wwmaa.com', 'https://api.wwmaa.com', 'https://athletic-curiosity-production.up.railway.app']
```

Application started successfully, CORS is configured, but URL is not accessible.

## Possible Causes

### 1. Railway Healthcheck Failure
Railway may be running healthchecks on a path that doesn't exist or is failing. Without railway.json, Railway uses default healthcheck behavior.

### 2. Container Crashed After Startup
The container may have started but crashed immediately after the logs we see.

### 3. Port Configuration Issue
Railway may not be routing to port 5432 correctly.

## Debugging Steps

### Step 1: Check Railway Dashboard - Deployments Tab

Go to: **Railway → WWMAA-BACKEND → Deployments**

Check if the deployment shows:
- ✅ **Active** (green checkmark)
- ⚠️  **Building** (yellow)
- ❌ **Crashed** (red X)
- ⏸️  **Sleeping** (paused)

### Step 2: Check HTTP Logs Tab

Go to: **Railway → WWMAA-BACKEND → HTTP Logs** (not Deploy Logs)

Look for:
- Any incoming HTTP requests to `/` or `/health`
- What status codes are being returned (502, 503, 504, etc.)
- Any error messages from Railway's proxy

### Step 3: Check Settings Tab - Healthcheck

Go to: **Railway → WWMAA-BACKEND → Settings → Healthcheck**

Check if there's a healthcheck path configured:
- If it's set to `/health` or `/api/health` → Good
- If it's empty or set to a non-existent path → This could cause 502

### Step 4: Check Settings Tab - Networking

Go to: **Railway → WWMAA-BACKEND → Settings → Networking**

Verify:
- Public domain is: `athletic-curiosity-production.up.railway.app`
- Port should be automatically detected (Railway uses $PORT variable)

## Quick Fixes to Try

### Fix #1: Add Healthcheck Configuration

In Railway Dashboard → WWMAA-BACKEND → Settings → Healthcheck:
```
Healthcheck Path: /api/health
Healthcheck Timeout: 60 seconds
```

### Fix #2: Check if Redis Is Causing Issues

The Redis connection error might be causing requests to fail. We can either:

**Option A**: Remove REDIS_URL from Railway Variables
- Go to Railway → WWMAA-BACKEND → Variables
- Delete `REDIS_URL` variable
- Redeploy (Railway auto-redeploys on variable changes)
- App will run without Redis (rate limiting disabled, but app functional)

**Option B**: Use a Free Redis Service
- Sign up for Upstash Redis (free tier): https://upstash.com
- Get Redis URL with credentials (format: `redis://default:password@host:port`)
- Update Railway `REDIS_URL` variable
- Redeploy

### Fix #3: Add PYTHON_ENV Variable

Ensure `PYTHON_ENV=production` is set in Railway Variables. This ensures proper configuration loading.

## Expected Behavior After Fix

Once fixed, visiting `https://athletic-curiosity-production.up.railway.app` should return:

```json
{
  "name": "WWMAA Backend API",
  "version": "1.0.0",
  "environment": "production",
  "status": "running"
}
```

And `/api/health` should return:

```json
{
  "status": "healthy",
  "service": "wwmaa-backend",
  "environment": "production",
  "timestamp": "2025-11-12T02:30:19.786203",
  "version": "1.0.0"
}
```

## Next Steps

1. Check Railway Dashboard as described above
2. Check HTTP Logs to see actual error messages
3. Try Fix #1 (add healthcheck configuration)
4. If that doesn't work, try Fix #2 Option A (remove Redis temporarily)
5. Report back with findings from HTTP Logs tab

## Additional Information

The application code is correct and working (confirmed by successful local Docker deployment). This is purely a Railway configuration/networking issue.
