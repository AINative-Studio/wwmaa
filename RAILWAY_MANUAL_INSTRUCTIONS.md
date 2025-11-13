# Railway Manual Instructions - Add ZeroDB Credentials

## Issue
Backend is returning: `Authentication failed: Could not validate credentials`

## Root Cause
Railway backend service is missing ZeroDB authentication credentials.

---

## Option 1: Using Railway CLI (Recommended)

### Prerequisites
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`

### Run the Script
```bash
cd /Users/aideveloper/Desktop/wwmaa
chmod +x RAILWAY_ADD_ZERODB_CREDENTIALS.sh
./RAILWAY_ADD_ZERODB_CREDENTIALS.sh
```

The script will automatically add all 5 required variables.

---

## Option 2: Using Railway Dashboard (Manual)

### Steps

1. **Go to Railway Dashboard**
   - Navigate to: https://railway.app
   - Login to your account
   - Select your **WWMAA** project

2. **Open Backend Service**
   - Click on **WWMAA-BACKEND** service
   - Click on **Variables** tab

3. **Add These Variables**

Click **+ New Variable** for each of these:

#### Variable 1: ZERODB_EMAIL
```
Name: ZERODB_EMAIL
Value: admin@ainative.studio
```

#### Variable 2: ZERODB_PASSWORD
```
Name: ZERODB_PASSWORD
Value: Admin2025!Secure
```

#### Variable 3: ZERODB_API_KEY
```
Name: ZERODB_API_KEY
Value: kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
```

#### Variable 4: ZERODB_API_BASE_URL
```
Name: ZERODB_API_BASE_URL
Value: https://api.ainative.studio
```

#### Variable 5: ZERODB_PROJECT_ID (Already added, verify)
```
Name: ZERODB_PROJECT_ID
Value: e4f3d95f-593f-4ae6-9017-24bff5f72c5e
```

4. **Save and Deploy**
   - Click **Save** after adding each variable
   - Railway will automatically redeploy the backend
   - Wait 2-3 minutes for deployment to complete

---

## Verification

After adding the variables and waiting for deployment:

### Test the Backend
```bash
curl https://athletic-curiosity-production.up.railway.app/api/events/public
```

### Expected Result
```json
[]  // Empty array (no events match filter criteria yet)
```

OR if events exist:
```json
[
  {
    "id": "...",
    "title": "...",
    "description": "...",
    ...
  }
]
```

### What NOT to see
```json
{
  "detail": "Failed to list events: Authentication failed: Could not validate credentials"
}
```

---

## Common Issues

### Issue: "Service not found"
**Solution:** Make sure you're in the WWMAA-BACKEND service, not WWMAA-FRONTEND

### Issue: "Variables not taking effect"
**Solution:**
1. Check deployment status in Railway dashboard
2. Wait for "Deployed" status (green checkmark)
3. Check logs for startup errors

### Issue: "Still getting authentication error"
**Solution:**
1. Double-check all variable values (no typos)
2. Make sure there are no extra spaces
3. Verify ZERODB_PASSWORD is exactly: `Admin2025!Secure`

---

## Next Steps After Fix

1. ✅ Backend authentication working
2. ⏭️ Test all backend endpoints
3. ⏭️ Fix frontend build cache issue
4. ⏭️ Deploy frontend
5. ⏭️ Test full stack integration

---

## Support

If issues persist:
- Check Railway logs: Dashboard → WWMAA-BACKEND → Logs
- Check ZeroDB status: https://api.ainative.studio/health
- Contact Railway support: https://railway.app/help
