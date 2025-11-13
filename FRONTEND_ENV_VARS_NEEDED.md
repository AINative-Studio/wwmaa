# Frontend Environment Variables Needed

**Date:** November 12, 2025
**Status:** ⚠️ **ACTION REQUIRED**

---

## Issue

The frontend is showing: `Application error: a server-side exception has occurred`

This is because the frontend doesn't know how to connect to the backend API.

---

## Root Cause

The frontend needs 2 environment variables to connect to the backend:
1. `NEXT_PUBLIC_API_MODE` - tells it to use "live" mode instead of "mock" data
2. `NEXT_PUBLIC_API_URL` - the backend API URL

Without these, the frontend tries to connect to `http://localhost:8000` (default) which doesn't exist in production.

---

## Solution

### Add 2 Environment Variables to Railway Frontend

Go to Railway Dashboard → **WWMAA-FRONTEND** → **Variables** and add:

#### Variable 1: NEXT_PUBLIC_API_MODE
```
NEXT_PUBLIC_API_MODE=live
```

#### Variable 2: NEXT_PUBLIC_API_URL
```
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
```

---

## Steps

1. Open Railway Dashboard: https://railway.app
2. Click on **WWMAA-FRONTEND** service
3. Click on **Variables** tab
4. Click **+ New Variable** and add:
   - Name: `NEXT_PUBLIC_API_MODE`
   - Value: `live`
5. Click **+ New Variable** again and add:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://athletic-curiosity-production.up.railway.app`
6. Click **Save**
7. Wait for Railway to redeploy (2-3 minutes)

---

## What These Variables Do

### NEXT_PUBLIC_API_MODE
- Controls whether the app uses mock data or real API
- Values: `"mock"` (default) or `"live"`
- When `"live"`, all API calls go to the backend

### NEXT_PUBLIC_API_URL
- The base URL for the backend API
- Default: `http://localhost:8000` (development)
- Production: `https://athletic-curiosity-production.up.railway.app`

---

## How the Frontend Uses Them

From `lib/api.ts`:
```typescript
const MODE = process.env.NEXT_PUBLIC_API_MODE ?? "mock";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = {
  async getTiers(): Promise<MembershipTier[]> {
    if (MODE === "mock") return tiers;
    const r = await fetch(`${API_URL}/api/subscriptions`);
    return r.json();
  },
  // ... other API methods
};
```

---

## Additional Fix Applied

I've also added error handling to the homepage to prevent crashes if the API is temporarily unavailable:

```typescript
export default async function HomePage() {
  let tiers;
  try {
    tiers = await api.getTiers();
  } catch (error) {
    console.error('Failed to fetch tiers:', error);
    // Fallback to mock data if API fails
    const { tiers: mockTiers } = await import("@/lib/mock/db");
    tiers = mockTiers;
  }
  // ... rest of page
}
```

This ensures the page still renders even if the backend is down.

---

## After Adding Variables

Once you've added the variables and Railway has redeployed:

1. The frontend will connect to the backend
2. API calls will work
3. The error should be gone
4. The page will load correctly

---

## Testing

After deployment, test these:

```bash
# 1. Open the frontend URL
open https://your-frontend-url.up.railway.app

# 2. Check browser console (should see no errors)
# 3. Check page loads correctly
# 4. Check membership tiers are displayed
```

---

## Summary

**What to add:** 2 environment variables to WWMAA-FRONTEND
**Where:** Railway Dashboard → WWMAA-FRONTEND → Variables
**Values:**
- `NEXT_PUBLIC_API_MODE=live`
- `NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app`
**Time:** 2 minutes to add + 2-3 minutes for redeploy = ~5 minutes total

---

*Last Updated: November 12, 2025*
*Document: FRONTEND_ENV_VARS_NEEDED.md*
