# Environment Variable Debugging Guide

## The Problem

Even though environment variables are set in Railway, the frontend is still connecting to `localhost:8000`. This happens because:

**Next.js bakes `NEXT_PUBLIC_*` variables into the JavaScript at BUILD time, not runtime.**

If variables are added AFTER a build, or if the build doesn't pick them up, the code will still have the fallback values hardcoded.

## What I Just Did

I pushed changes that will:
1. **Trigger a new Railway build** (automatic on git push)
2. **Log environment variables during build** so we can see what Railway sees
3. **Validate required variables** and warn if they're missing

## What to Check in Railway Build Logs

### Step 1: Watch the Build

1. Go to Railway Dashboard
2. Open **WWMAA-FRONTEND** service
3. Click **Deployments** tab
4. Click on the newest deployment (should be building now)
5. Click **Build Logs** tab

### Step 2: Look for Environment Variable Logs

You should see output like this during the build:

**✅ GOOD - Variables are set:**
```
🔧 Build-time environment:
   NEXT_PUBLIC_API_URL: https://athletic-curiosity-production.up.railway.app
   NEXT_PUBLIC_API_MODE: live
   NEXT_PUBLIC_SITE_URL: https://wwmaa.ainative.studio
```

**❌ BAD - Variables are missing:**
```
⚠️  WARNING: Missing required environment variables:
   - NEXT_PUBLIC_API_URL
   - NEXT_PUBLIC_API_MODE

   The application will default to localhost:8000
   Set these variables in Railway to connect to production backend.

🔧 Build-time environment:
   NEXT_PUBLIC_API_URL: NOT SET (will use localhost:8000)
   NEXT_PUBLIC_API_MODE: NOT SET (will use mock)
   NEXT_PUBLIC_SITE_URL: NOT SET
```

## If Variables Are Missing in Build Logs

The variables might be set in Railway but not being passed to the build. Here's how to fix it:

### Option 1: Verify Variable Names (Case Sensitive!)

In Railway Variables tab, make sure you have EXACTLY:
```
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_API_MODE
NEXT_PUBLIC_SITE_URL
```

NOT:
- `Next_Public_Api_Url` (wrong case)
- `NEXT_PUBLIC_API_URL ` (trailing space)
- `api_url` (missing prefix)

### Option 2: Check Variable Scope

In Railway, make sure variables are set for the **WWMAA-FRONTEND** service, not globally or for a different service.

### Option 3: Use Raw Editor

1. Go to **WWMAA-FRONTEND** > **Variables**
2. Click **RAW Editor** button
3. Copy-paste this EXACTLY:
```
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
NODE_ENV=production
```
4. Click **Update Variables**
5. Wait for automatic redeploy

### Option 4: Manual Redeploy

If variables are set but build didn't pick them up:
1. Go to **WWMAA-FRONTEND** > **Deployments**
2. Find the latest successful deployment
3. Click the **three dots menu** (⋮)
4. Click **Redeploy**

## After Build Completes Successfully

### Verify the Fix

1. Go to: https://wwmaa.ainative.studio/login
2. Open browser DevTools (F12)
3. Go to **Console** tab
4. Try to login with: `admin@wwmaa.com` / `AdminPass123!`

**You should see:**
```
Fetch: https://athletic-curiosity-production.up.railway.app/api/security/csrf-token
Fetch: https://athletic-curiosity-production.up.railway.app/api/auth/login
```

**NOT:**
```
Fetch: localhost:8000/api/security/csrf-token (ERR_CONNECTION_REFUSED)
```

## Troubleshooting

### Build logs show variables are set, but login still fails

- Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- Try in incognito/private browsing mode
- Check that the deployment actually completed (green checkmark)

### Build logs don't show the environment variable output

- The `next.config.js` change might not have been picked up
- Check the build logs for `console.log` output
- Verify the commit was pushed successfully

### Variables disappear after setting them

- Railway might have an issue
- Try setting them again
- Contact Railway support if it persists

## Expected Timeline

1. **Now:** Pushed code changes
2. **~30 seconds:** Railway detects git push
3. **~3-5 minutes:** Build completes
4. **~1 minute:** Deployment goes live
5. **Total:** ~5-7 minutes from push to working login

---

*Last Updated: November 13, 2025*
*Next: Check Railway build logs for environment variable output*
