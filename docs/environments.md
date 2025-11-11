# WWMAA Environment Configuration

## Overview

WWMAA supports three distinct environments, each with specific configurations and purposes:

1. **Development** - Local development environment
2. **Staging** - Pre-production testing environment (Railway)
3. **Production** - Live production environment (Railway)

## Environment Comparison

| Feature | Development | Staging | Production |
|---------|-------------|---------|------------|
| **Platform** | Local | Railway | Railway |
| **Database** | ZeroDB (dev collections) | ZeroDB (staging_ prefix) | ZeroDB (prod collections) |
| **Redis** | Local/Docker | Railway Redis | Railway Redis |
| **Domain** | localhost:8000 | api-staging.wwmaa.com | api.wwmaa.com |
| **SSL** | No | Yes (Railway) | Yes (Railway) |
| **Stripe** | Test mode | Test mode | Live mode |
| **Email** | Test/Console | Postmark (staging) | Postmark (production) |
| **Monitoring** | Minimal | Full (Sentry staging) | Full (Sentry production) |
| **Auto-scaling** | No | No (1 instance) | Yes (2-4 instances) |
| **Seed Data** | Optional | Yes | No |

## Environment Variables

### Development (.env)

```bash
PYTHON_ENV=development
PYTHON_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# ZeroDB (development collections)
ZERODB_API_KEY=your-dev-api-key
ZERODB_EMAIL=dev@ainative.studio
ZERODB_PASSWORD=your-dev-password

# Local Redis
REDIS_URL=redis://localhost:6379

# Stripe test keys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...

# Other development configurations...
```

See `/backend/.env.example` for complete development configuration.

### Staging (.env.staging.example)

```bash
PYTHON_ENV=staging
PYTHON_BACKEND_URL=https://api-staging.wwmaa.com
NEXT_PUBLIC_APP_URL=https://staging.wwmaa.com

# ZeroDB (staging_ prefixed collections)
ZERODB_API_KEY=your-staging-api-key
ZERODB_EMAIL=staging@ainative.studio

# Railway-managed Redis
REDIS_URL=${REDIS_URL}

# Stripe test mode
STRIPE_SECRET_KEY=sk_test_...

# Sentry staging environment
SENTRY_DSN=your-staging-dsn
SENTRY_ENVIRONMENT=staging

# Other staging configurations...
```

See `/.env.staging.example` for complete staging configuration.

### Production

Production environment variables are configured directly in Railway dashboard and are **not** committed to version control.

**Critical Production Settings:**
- `PYTHON_ENV=production`
- Live Stripe keys (`sk_live_`, `pk_live_`)
- Production ZeroDB collections (no prefix)
- Production Sentry DSN
- Higher rate limits and security settings
- Auto-scaling enabled (2-4 instances)

## ZeroDB Collections by Environment

### Development Collections
- `dev_profiles` or `profiles`
- `dev_applications` or `applications`
- `dev_subscriptions` or `subscriptions`
- etc.

### Staging Collections (Required Prefix: `staging_`)
- `staging_profiles`
- `staging_applications`
- `staging_subscriptions`
- `staging_payments`
- `staging_events`
- `staging_rsvps`
- `staging_attendees`
- `staging_blog_posts`
- `staging_search_queries`
- `staging_indexed_content`

### Production Collections
- `profiles`
- `applications`
- `subscriptions`
- `payments`
- `events`
- `rsvps`
- `attendees`
- `blog_posts`
- `search_queries`
- `indexed_content`

## Environment-Specific Features

### Development
- **Debug Mode**: Enabled
- **Verbose Logging**: Enabled
- **Hot Reload**: Enabled
- **CORS**: Permissive (localhost)
- **Rate Limiting**: Disabled or very high limits
- **Seed Data Endpoint**: Available at `/api/admin/seed-data`

### Staging
- **Debug Mode**: Enabled (for testing)
- **Verbose Logging**: Enabled
- **CORS**: Configured for staging.wwmaa.com
- **Rate Limiting**: Moderate (100/min)
- **Seed Data**: Pre-loaded via script
- **Health Checks**: Enabled
- **Monitoring**: Full Sentry + Prometheus
- **SSL**: Auto-managed by Railway

### Production
- **Debug Mode**: Disabled
- **Verbose Logging**: Disabled (INFO level only)
- **CORS**: Strict (wwmaa.com only)
- **Rate Limiting**: Strict (30/min default)
- **Seed Data**: Not available
- **Health Checks**: Enabled
- **Monitoring**: Full Sentry + Prometheus + alerts
- **SSL**: Auto-managed by Railway
- **Auto-scaling**: 2-4 instances based on load

## Switching Between Environments

### Local Development
```bash
# Set environment variable
export PYTHON_ENV=development

# Or in .env file
echo "PYTHON_ENV=development" > .env

# Start backend
cd backend
uvicorn app:app --reload
```

### Deploy to Staging
```bash
# Using Railway CLI
railway up --environment staging

# Or using deployment script
./scripts/railway/deploy-staging.sh
```

### Deploy to Production
```bash
# Using Railway CLI
railway up --environment production

# Or via Railway dashboard (recommended)
# Merge to main branch → Auto-deploy
```

## Environment Health Checks

All environments expose a health check endpoint:

```bash
# Development
curl http://localhost:8000/api/health

# Staging
curl https://api-staging.wwmaa.com/api/health

# Production
curl https://api.wwmaa.com/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "environment": "staging",
  "version": "1.0.0",
  "timestamp": "2025-01-10T12:00:00Z",
  "services": {
    "zerodb": "connected",
    "redis": "connected"
  }
}
```

## Environment Security

### Development
- Local only, no public access
- Test credentials acceptable
- Debug tools enabled

### Staging
- HTTPS required
- Test API keys (Stripe, etc.)
- Staging-specific credentials
- Security headers enabled
- CSP reporting enabled

### Production
- HTTPS enforced
- Live API keys (secure vault)
- Strict CORS and CSP
- Rate limiting enforced
- Full audit logging
- Secrets rotation policy

## Troubleshooting

### Environment Not Detected
```bash
# Check environment variable
echo $PYTHON_ENV

# Verify in application
python -c "from backend.config import get_settings; print(get_settings().python_env)"
```

### Wrong Collections Accessed
```bash
# Check ZeroDB configuration
python -c "from backend.config import get_settings; s = get_settings(); print(f'Email: {s.zerodb_email}')"

# Verify collection names in ZeroDB dashboard
# Staging should use staging_ prefix
```

### Redis Connection Issues
```bash
# Development: Check Redis is running
redis-cli ping

# Staging/Production: Check Railway Redis service
railway run env | grep REDIS_URL
```

## Best Practices

1. **Never mix environments** - Don't use production keys in staging
2. **Always use environment detection** - Let `config.py` handle environment logic
3. **Test in staging first** - All changes must pass staging before production
4. **Monitor environment-specific metrics** - Use tags/labels to separate metrics
5. **Document environment differences** - Keep this file updated
6. **Automate environment setup** - Use provided scripts for consistency
7. **Secure production secrets** - Use Railway secrets, never commit to git

## See Also

- [Staging Setup Guide](./deployment/STAGING_SETUP.md)
- [Backend Configuration](../backend/.env.example)
- [Railway Configuration](../railway.json)
- [Deployment Scripts](../scripts/railway/)
