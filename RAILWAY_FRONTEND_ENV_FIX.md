# Railway Frontend Environment Variable Fix

## Problem
Next.js is still trying to download SWC binary despite swcMinify: false.
The download keeps getting corrupted on Railway infrastructure.

## Solution
Add environment variable to completely skip SWC binary installation.

## Action Required

Go to Railway Dashboard → **WWMAA-FRONTEND** → **Variables** and add:

### Variable Name:
```
NEXT_SKIP_NATIVE_POSTINSTALL
```

### Variable Value:
```
1
```

This tells Next.js to skip the postinstall script that downloads native binaries.

## Expected Result
- No "Downloading swc package" message in logs
- Build uses Babel instead
- Build completes successfully

## Alternative: Use Custom Dockerfile

If the environment variable doesn't work, we can switch to using the custom Dockerfile.frontend which has more control over the build process.
