# Railway Frontend Environment Variables

## Required Variables for WWMAA-FRONTE Service

Go to: **Railway → WWMAA-FRONTE → Variables tab**

Add these environment variables:

```env
# Backend API URL (for client-side fetches)
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app

# Frontend site URL (for SEO and social sharing)
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio

# Server-side backend URL (used in API routes)
BACKEND_URL=https://athletic-curiosity-production.up.railway.app

# API mode - set to "live" to use real backend (not mock data)
NEXT_PUBLIC_API_MODE=live

# Node environment
NODE_ENV=production
```

## Quick Copy-Paste Format

```
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
BACKEND_URL=https://athletic-curiosity-production.up.railway.app
NEXT_PUBLIC_API_MODE=live
NODE_ENV=production
```

## Variable Explanations

### NEXT_PUBLIC_API_URL
- **Purpose**: Backend API endpoint for client-side API calls
- **Default**: http://localhost:8000
- **Production**: Your Railway backend URL
- **Used by**: Frontend components making API requests

### NEXT_PUBLIC_SITE_URL
- **Purpose**: Your frontend's public URL
- **Default**: https://wwmaa.ainative.studio
- **Production**: Your Railway frontend domain
- **Used by**: SEO metadata, Open Graph tags, JSON-LD structured data

### BACKEND_URL
- **Purpose**: Backend API endpoint for server-side API routes
- **Default**: http://localhost:8000
- **Production**: Your Railway backend URL
- **Used by**: Next.js API routes (server-side only)

### NEXT_PUBLIC_API_MODE
- **Purpose**: Toggle between mock data and real backend
- **Options**: "mock" or "live"
- **Development**: "mock" (uses mock data from lib/mock/db.ts)
- **Production**: "live" (uses real backend API)

### NODE_ENV
- **Purpose**: Node.js environment
- **Options**: "development", "production"
- **Railway**: Always set to "production"

## After Adding Variables

1. Save the variables in Railway
2. Railway will automatically redeploy the frontend
3. Wait 2-3 minutes for the build to complete
4. Visit https://wwmaa.ainative.studio to test

## Verification

Once deployed, the frontend should:
- ✅ Load successfully at https://wwmaa.ainative.studio
- ✅ Make API calls to https://athletic-curiosity-production.up.railway.app
- ✅ Use live backend data (not mock data)
- ✅ Display proper SEO metadata with correct URLs

## Troubleshooting

If frontend still shows mock data:
- Verify `NEXT_PUBLIC_API_MODE=live` (not "mock")
- Check browser console for API errors
- Verify backend is accessible from frontend

If API calls fail with CORS errors:
- Backend CORS is already configured with both domains
- Check Network tab in browser DevTools
- Verify `NEXT_PUBLIC_API_URL` matches backend domain exactly
