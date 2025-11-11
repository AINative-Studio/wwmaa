# Railway Missing Environment Variables

## Status: 7 Required Variables Missing

The app is failing because Pydantic requires these 7 additional environment variables that are not yet in Railway.

## Variables to Add in Railway Dashboard

Go to: **Railway → wwmaa → Variables tab** and add these:

```env
# Redis (Required for rate limiting and caching)
REDIS_URL=redis://redis.railway.internal:6379

# Stripe (Required for payment processing)
STRIPE_SECRET_KEY=sk_test_placeholder_replace_with_real_key
STRIPE_WEBHOOK_SECRET=whsec_placeholder_replace_with_real_secret

# Postmark (Required for transactional emails)
POSTMARK_API_KEY=placeholder-postmark-key-replace-later

# Cloudflare (Required for video streaming)
CLOUDFLARE_ACCOUNT_ID=a6c7673a76151a92805b7159cc5aa136
CLOUDFLARE_API_TOKEN=yeN9JMDBlIS9G8NZ2b5dZsm-awUaIPPMonfM8AHV

# AI Registry (Required for LLM orchestration)
AI_REGISTRY_API_KEY=placeholder-ai-registry-key-replace-later
```

## Quick Copy-Paste (for Railway Variables)

If Railway has a bulk import feature, use this format:

```
REDIS_URL=redis://redis.railway.internal:6379
STRIPE_SECRET_KEY=sk_test_placeholder_replace_with_real_key
STRIPE_WEBHOOK_SECRET=whsec_placeholder_replace_with_real_secret
POSTMARK_API_KEY=placeholder-postmark-key-replace-later
CLOUDFLARE_ACCOUNT_ID=a6c7673a76151a92805b7159cc5aa136
CLOUDFLARE_API_TOKEN=yeN9JMDBlIS9G8NZ2b5dZsm-awUaIPPMonfM8AHV
AI_REGISTRY_API_KEY=placeholder-ai-registry-key-replace-later
```

## Notes

- **REDIS_URL**: Use Railway's internal Redis service if you have one, otherwise this placeholder will work
- **STRIPE_***: Use test keys for now (sk_test_...), replace with live keys when ready
- **POSTMARK_API_KEY**: Placeholder until you have a Postmark account
- **CLOUDFLARE_***: Use the values from your .env file (already present there)
- **AI_REGISTRY_API_KEY**: Placeholder for now

## After Adding Variables

1. Save the variables in Railway
2. Railway will automatically redeploy
3. The app should start successfully
4. Check Deploy Logs - you should see "✅ All required environment variables present" followed by "🎯 Starting Uvicorn Server..."
5. Healthcheck should pass and deployment succeeds

## Priority

These are **placeholders** - the app will start, but services won't work until you replace with real keys:

- **Critical for basic functionality**: REDIS_URL
- **Needed for payments**: STRIPE_* (use test keys for now)
- **Needed for emails**: POSTMARK_API_KEY
- **Needed for video**: CLOUDFLARE_* (use real keys from .env)
- **Needed for AI features**: AI_REGISTRY_API_KEY

## Alternative: Make Services Optional (Future Improvement)

For a future sprint, we should make these services optional in config.py so the app can start without them and gracefully disable features when keys are missing. But for now, adding placeholders is the fastest path to deployment.
