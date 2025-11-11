# WWMAA Staging Environment Setup Guide

## Overview

This guide walks through the complete setup of the WWMAA staging environment on Railway.app. The staging environment provides a production-like environment for testing before deploying to production.

**Staging Environment Architecture:**
- **Platform**: Railway.app
- **Backend**: Python FastAPI (api-staging.wwmaa.com)
- **Frontend**: Next.js 13+ (staging.wwmaa.com)
- **Redis**: Railway-managed Redis instance
- **Database**: ZeroDB (staging collections with `staging_` prefix)
- **Monitoring**: Sentry (staging environment), Prometheus metrics

## Prerequisites

Before starting, ensure you have:

1. **Railway Account**: Sign up at https://railway.app
2. **Railway CLI**: Install with `npm i -g @railway/cli`
3. **Domain Access**: Ability to configure DNS for wwmaa.com
4. **ZeroDB Account**: Access to create staging collections
5. **API Keys**: Staging/test keys for all integrations (Stripe, Postmark, etc.)
6. **GitHub Repository**: WWMAA repository with latest code

## Step 1: Railway Project Setup

### 1.1 Install Railway CLI

```bash
# Install Railway CLI globally
npm install -g @railway/cli

# Verify installation
railway --version

# Login to Railway
railway login
```

### 1.2 Create Railway Project

**Option A: Using CLI (Automated)**
```bash
# Navigate to project root
cd /path/to/wwmaa

# Run setup script
./scripts/railway/setup-staging.sh
```

**Option B: Using Railway Dashboard (Manual)**
1. Go to https://railway.app/new
2. Click "Empty Project"
3. Name the project: `wwmaa-staging`
4. Click "Create Project"

### 1.3 Create Staging Environment

```bash
# Create staging environment
railway environment create staging

# Set as default for this directory
railway environment use staging
```

## Step 2: Add Required Services

### 2.1 Add Redis Service

**Via Railway Dashboard:**
1. Open your `wwmaa-staging` project
2. Click "New Service"
3. Select "Database" → "Redis"
4. Click "Add Redis"
5. Railway will automatically provision Redis and set `REDIS_URL` environment variable

**Via CLI:**
```bash
# Add Redis from template
railway service create --template redis
```

### 2.2 Add Python Backend Service

1. Click "New Service" in Railway dashboard
2. Select "GitHub Repo"
3. Connect your WWMAA repository
4. Configure service:
   - **Root Directory**: Leave empty (uses root)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Healthcheck Path**: `/api/health`

### 2.3 Add Next.js Frontend Service

1. Click "New Service" in Railway dashboard
2. Select "GitHub Repo" (same repository)
3. Configure service:
   - **Root Directory**: Leave empty
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Healthcheck Path**: `/`

**Note**: You may want to create separate deployments for backend and frontend using different Railway projects or services.

## Step 3: Configure Environment Variables

### 3.1 Backend Environment Variables

Copy all variables from `/.env.staging.example` to Railway dashboard:

1. Open Backend Service in Railway dashboard
2. Go to "Variables" tab
3. Add the following **required** variables:

**Core Configuration:**
```bash
PYTHON_ENV=staging
PYTHON_BACKEND_URL=https://api-staging.wwmaa.com
NEXT_PUBLIC_APP_URL=https://staging.wwmaa.com
```

**ZeroDB Configuration:**
```bash
ZERODB_API_KEY=<your-staging-zerodb-api-key>
ZERODB_EMAIL=staging@ainative.studio
ZERODB_PASSWORD=<your-staging-password>
ZERODB_API_BASE_URL=https://api.ainative.studio
```

**JWT Configuration:**
```bash
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET=<generate-random-64-char-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Redis Configuration:**
```bash
# Railway automatically provides this when Redis service is linked
REDIS_URL=${REDIS_URL}
```

**Stripe Configuration (Test Mode):**
```bash
STRIPE_SECRET_KEY=sk_test_<your-stripe-test-secret-key>
STRIPE_WEBHOOK_SECRET=whsec_test_<your-stripe-test-webhook-secret>
STRIPE_PUBLISHABLE_KEY=pk_test_<your-stripe-test-publishable-key>
```

**Email Configuration:**
```bash
POSTMARK_API_KEY=<your-staging-postmark-api-key>
FROM_EMAIL=staging@wwmaa.com
```

**AI Services:**
```bash
OPENAI_API_KEY=sk-<your-staging-openai-api-key>
AI_REGISTRY_API_KEY=<your-staging-ai-registry-api-key>
AINATIVE_API_KEY=<your-staging-ainative-api-key>
```

**Monitoring:**
```bash
SENTRY_DSN=<your-staging-sentry-dsn>
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=1.0
```

See `/.env.staging.example` for complete list of environment variables.

### 3.2 Frontend Environment Variables

Add to Next.js service:
```bash
NEXT_PUBLIC_BACKEND_API_URL=https://api-staging.wwmaa.com
NEXT_PUBLIC_APP_URL=https://staging.wwmaa.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_<your-key>
NEXT_PUBLIC_ENVIRONMENT=staging
```

## Step 4: Configure Custom Domains

### 4.1 Add Custom Domains to Railway

**Backend Domain (api-staging.wwmaa.com):**
1. Open Backend Service in Railway
2. Go to "Settings" → "Domains"
3. Click "Add Custom Domain"
4. Enter: `api-staging.wwmaa.com`
5. Note the CNAME target provided by Railway

**Frontend Domain (staging.wwmaa.com):**
1. Open Frontend Service in Railway
2. Go to "Settings" → "Domains"
3. Click "Add Custom Domain"
4. Enter: `staging.wwmaa.com`
5. Note the CNAME target provided by Railway

### 4.2 Configure DNS Records

Add CNAME records to your DNS provider (e.g., Cloudflare, Route53):

```
Type: CNAME
Name: api-staging
Value: <railway-provided-backend-target>
TTL: Auto

Type: CNAME
Name: staging
Value: <railway-provided-frontend-target>
TTL: Auto
```

### 4.3 Verify SSL Certificates

Railway automatically provisions SSL certificates via Let's Encrypt. Wait 5-10 minutes for DNS propagation and certificate issuance.

Verify:
```bash
curl -I https://api-staging.wwmaa.com/api/health
curl -I https://staging.wwmaa.com
```

## Step 5: ZeroDB Staging Collections Setup

### 5.1 Create Staging Collections

Log in to ZeroDB dashboard at https://api.ainative.studio/dashboard and create the following collections with `staging_` prefix:

**Required Collections:**
- `staging_profiles` - User profiles
- `staging_applications` - Membership applications
- `staging_subscriptions` - Subscription records
- `staging_payments` - Payment history
- `staging_events` - Event listings
- `staging_rsvps` - Event RSVPs
- `staging_attendees` - Event attendees
- `staging_blog_posts` - Blog content
- `staging_search_queries` - Search analytics
- `staging_indexed_content` - Search indexes

### 5.2 Configure Collection Schemas

For each collection, configure appropriate schemas based on production collections. See `/docs/STORAGE-ARCHITECTURE.md` for schema definitions.

### 5.3 Set Collection Permissions

Configure read/write permissions for staging collections:
- **Public Read**: Only for `staging_blog_posts`, `staging_events` (public events)
- **Authenticated Read**: For user-specific data
- **Admin Write**: For all collections

## Step 6: Deploy to Staging

### 6.1 Deploy via CLI

```bash
# Navigate to project root
cd /path/to/wwmaa

# Deploy to staging
./scripts/railway/deploy-staging.sh
```

### 6.2 Deploy via GitHub (Auto-deploy)

1. Configure auto-deploy in Railway dashboard:
   - Go to Service Settings → "Deploys"
   - Enable "Automatic Deploys"
   - Set branch: `develop` or `staging`

2. Push code to trigger deployment:
```bash
git push origin develop
```

### 6.3 Monitor Deployment

```bash
# Watch deployment logs
railway logs --environment staging --tail

# Check deployment status
railway status --environment staging
```

## Step 7: Load Seed Data

### 7.1 Prepare Seed Data Script

The seed data script is located at `/scripts/seed-staging-data.py` and will populate:
- 50 test users (various tiers)
- 20 test events (past and upcoming)
- 100 test blog posts
- 30 test applications
- 40 test subscriptions

### 7.2 Run Seed Data Script

**Option A: Run Locally (Recommended)**
```bash
# Set staging environment variables locally
export PYTHON_ENV=staging
export ZERODB_API_KEY=<your-staging-api-key>
# ... other required env vars

# Run seed script
python scripts/seed-staging-data.py
```

**Option B: Run on Railway**
```bash
# Execute on Railway instance
railway run --environment staging python scripts/seed-staging-data.py
```

### 7.3 Verify Seed Data

1. Check ZeroDB dashboard for populated collections
2. Test API endpoints:
```bash
# Get profiles
curl https://api-staging.wwmaa.com/api/profiles

# Get events
curl https://api-staging.wwmaa.com/api/events

# Get blog posts
curl https://api-staging.wwmaa.com/api/blog/posts
```

## Step 8: Configure Webhooks

### 8.1 Stripe Webhooks

1. Go to Stripe Dashboard → Developers → Webhooks (Test Mode)
2. Click "Add endpoint"
3. Enter URL: `https://api-staging.wwmaa.com/api/webhooks/stripe`
4. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET` in Railway

### 8.2 BeeHiiv Webhooks (if applicable)

Configure BeeHiiv webhooks to point to:
```
https://api-staging.wwmaa.com/api/webhooks/beehiiv
```

## Step 9: Verification & Testing

### 9.1 Run Verification Script

```bash
# Run comprehensive verification
./scripts/railway/verify-staging.sh
```

This script checks:
- Health endpoints (backend & frontend)
- SSL certificates
- CORS configuration
- Security headers
- Authentication endpoints
- Metrics endpoints
- DNS resolution

### 9.2 Manual Testing Checklist

**Backend Health:**
- [ ] Health check responds: `curl https://api-staging.wwmaa.com/api/health`
- [ ] Metrics accessible: `curl https://api-staging.wwmaa.com/metrics`
- [ ] SSL certificate valid
- [ ] CORS headers present

**Authentication:**
- [ ] User registration works
- [ ] User login works
- [ ] JWT tokens generated correctly
- [ ] Token refresh works

**Database Operations:**
- [ ] ZeroDB collections accessible
- [ ] CRUD operations work
- [ ] Seed data visible

**Event Management:**
- [ ] Events list loads
- [ ] RSVP functionality works
- [ ] Attendee tracking works

**Search:**
- [ ] Semantic search returns results
- [ ] Search analytics tracked
- [ ] Indexed content queryable

**Payments:**
- [ ] Stripe checkout (test mode) works
- [ ] Subscription creation works
- [ ] Webhook events processed

**Monitoring:**
- [ ] Sentry errors captured
- [ ] Prometheus metrics collected
- [ ] Railway logs accessible

### 9.3 End-to-End User Flow

Test complete user journey:

1. **Registration**: Create new account
2. **Login**: Authenticate user
3. **Browse Events**: View event listings
4. **RSVP**: Register for event
5. **Search**: Use semantic search for blog posts
6. **Subscribe**: Create subscription (Stripe test mode)
7. **Billing**: View subscription status

## Step 10: Post-Deployment Configuration

### 10.1 Set Up Monitoring Alerts

Configure Sentry alerts for staging:
1. Go to Sentry project settings
2. Create alert rules for:
   - Error rate > 10/min
   - 500 errors
   - Performance degradation

### 10.2 Configure Logging

Ensure Railway logging is enabled:
```bash
# View logs
railway logs --environment staging --tail

# Filter logs
railway logs --environment staging --filter "ERROR"
```

### 10.3 Set Up Auto-Scaling (Optional)

For staging, typically 1 instance is sufficient. For production-like testing:

1. Go to Service Settings → "Scaling"
2. Enable autoscaling
3. Set min: 1, max: 2
4. Configure scale-up threshold

## Troubleshooting

### Issue: Health Check Fails

**Symptoms**: `/api/health` returns 404 or 500

**Solutions**:
```bash
# Check backend logs
railway logs --environment staging --service backend

# Verify environment variables
railway run --environment staging env | grep PYTHON_ENV

# Check Railway service status
railway status --environment staging
```

### Issue: Redis Connection Failed

**Symptoms**: Errors about Redis connection in logs

**Solutions**:
```bash
# Verify Redis service is running
railway service list

# Check REDIS_URL is set
railway run --environment staging env | grep REDIS_URL

# Restart Redis service
railway service restart redis
```

### Issue: ZeroDB Authentication Failed

**Symptoms**: 401 errors when accessing ZeroDB collections

**Solutions**:
- Verify `ZERODB_API_KEY` is correct in Railway dashboard
- Check API key is for staging environment
- Ensure collections exist with `staging_` prefix
- Verify API key has read/write permissions

### Issue: Custom Domain Not Resolving

**Symptoms**: Domain doesn't point to Railway service

**Solutions**:
1. Check DNS propagation: `dig api-staging.wwmaa.com`
2. Verify CNAME record is correct
3. Wait for DNS propagation (up to 24 hours)
4. Clear DNS cache locally: `sudo dscacheutil -flushcache` (macOS)

### Issue: SSL Certificate Not Provisioning

**Symptoms**: HTTPS connection fails or shows invalid certificate

**Solutions**:
1. Ensure DNS is properly configured
2. Wait 10-15 minutes for Let's Encrypt provisioning
3. Verify domain ownership in Railway
4. Check Railway status page for issues

## Maintenance & Updates

### Updating Staging Environment

```bash
# Deploy latest changes
git push origin develop

# Or deploy specific branch
railway up --environment staging --branch feature/new-feature
```

### Refreshing Seed Data

```bash
# Clear existing data (optional - use with caution)
# Manually delete documents in ZeroDB dashboard

# Re-run seed script
python scripts/seed-staging-data.py
```

### Monitoring Costs

Railway offers free tier with limited usage. Monitor:
1. Railway dashboard → Usage tab
2. Check monthly usage and costs
3. Optimize if approaching limits

## Security Considerations

**Staging Environment Security:**
- ✅ Use test API keys (Stripe, etc.)
- ✅ HTTPS enforced
- ✅ Separate ZeroDB collections (staging_ prefix)
- ✅ CSP headers enabled
- ✅ Rate limiting enabled (moderate)
- ⚠️ Debug mode enabled (for testing)
- ⚠️ More permissive CORS (for testing)

**Never in Staging:**
- ❌ Production API keys
- ❌ Real user data
- ❌ Live payment processing
- ❌ Production database access

## Next Steps

After successful staging setup:

1. **Test Thoroughly**: Run all test scenarios
2. **Document Issues**: Track bugs in GitHub Issues
3. **Performance Test**: Load test with realistic data
4. **Security Scan**: Run security audit tools
5. **Production Deployment**: Once staging is stable, deploy to production

## Resources

- **Railway Documentation**: https://docs.railway.app
- **ZeroDB Dashboard**: https://api.ainative.studio/dashboard
- **Sentry Staging**: https://sentry.io/organizations/wwmaa/projects/staging
- **Environment Variables**: `/.env.staging.example`
- **Deployment Scripts**: `/scripts/railway/`
- **Architecture Docs**: `/docs/ARCHITECTURE-CLARIFICATION.md`

## Support

For issues or questions:
- **Railway Support**: support@railway.app
- **Internal Team**: #staging-environment Slack channel
- **GitHub Issues**: https://github.com/wwmaa/wwmaa/issues

---

**Last Updated**: 2025-01-10
**Version**: 1.0.0
**Maintained By**: DevOps Team
