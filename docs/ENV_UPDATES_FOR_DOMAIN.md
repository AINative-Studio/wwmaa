# Environment Variable Updates for Custom Domain

## Frontend (WWMAA-FRONTEND)

Update these variables in Railway:
```env
NEXT_PUBLIC_SITE_URL=https://wwmaa.com
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
```

After updating, redeploy the frontend service.

## Backend (WWMAA-BACKEND)

The CORS configuration is in code (`backend/config.py`), so just redeploy after updating the CORS origins.

## Verification

After updates:
```bash
# Check environment variables are loaded
curl https://wwmaa.com/_next/data/[build-id]/index.json | jq

# Check CORS headers
curl -H "Origin: https://wwmaa.com" -I https://athletic-curiosity-production.up.railway.app/health
```

## Step-by-Step Instructions

### Update Frontend Environment Variables in Railway

1. Login to Railway dashboard
2. Navigate to your project
3. Click on WWMAA-FRONTEND service
4. Go to "Variables" tab
5. Update or add these variables:

```
NEXT_PUBLIC_SITE_URL=https://wwmaa.com
NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app
```

6. Click "Save" - this will automatically trigger a redeploy

### Alternative: Using Railway CLI

If you prefer using the CLI:

```bash
# Navigate to frontend directory
cd /Users/aideveloper/Desktop/wwmaa/frontend

# Set environment variables
railway variables set NEXT_PUBLIC_SITE_URL=https://wwmaa.com
railway variables set NEXT_PUBLIC_API_URL=https://athletic-curiosity-production.up.railway.app

# Trigger redeploy
railway up
```

### Verify Changes

Once the redeploy completes (usually 2-5 minutes):

1. Check the new domain loads:
```bash
curl -I https://wwmaa.com
```

2. Verify environment variables are in the build:
```bash
# Check the HTML source includes the correct values
curl https://wwmaa.com | grep "NEXT_PUBLIC"
```

3. Test in browser:
   - Open browser console
   - Navigate to https://wwmaa.com
   - Run: `console.log(process.env.NEXT_PUBLIC_SITE_URL)`
   - Should show: `https://wwmaa.com`

4. Check API connectivity:
```bash
# Test CORS from new domain
curl -H "Origin: https://wwmaa.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://athletic-curiosity-production.up.railway.app/api/health
```

Expected response headers:
```
Access-Control-Allow-Origin: https://wwmaa.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## Backend CORS Configuration

No environment variable changes needed for backend. The CORS configuration is handled in code via `backend/config.py` which automatically includes:
- `https://wwmaa.com`
- `https://www.wwmaa.com`
- `https://wwmaa.ainative.studio` (fallback)

Simply redeploy the backend service after the code update is deployed.

## Rollback Plan

If something goes wrong:

1. Revert environment variables in Railway dashboard:
```
NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
```

2. Or via CLI:
```bash
railway variables set NEXT_PUBLIC_SITE_URL=https://wwmaa.ainative.studio
railway up
```

3. The old domain will continue to work immediately

## Common Issues

### Issue: Environment variables not taking effect
**Solution:**
- Ensure you saved the changes in Railway dashboard
- Verify redeploy was triggered (check deployment logs)
- Clear browser cache and hard reload (Cmd+Shift+R)

### Issue: CORS errors persist
**Solution:**
- Verify backend was redeployed after CORS config change
- Check backend logs: `railway logs -s wwmaa-backend`
- Ensure origin header matches exactly (with/without www)

### Issue: Mixed content warnings
**Solution:**
- All API calls must use HTTPS
- Check for any hardcoded HTTP URLs in code
- Verify NEXT_PUBLIC_API_URL uses https://

## Timeline

- Update variables: 2 minutes
- Redeploy frontend: 3-5 minutes
- DNS propagation (if needed): 5-60 minutes
- Verification: 5 minutes
- **Total: 15-72 minutes**
