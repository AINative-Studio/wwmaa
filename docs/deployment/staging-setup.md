# Railway Staging Environment Setup Guide

Complete guide for setting up the WWMAA staging environment on Railway.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Railway Account Setup](#railway-account-setup)
3. [Project Creation](#project-creation)
4. [Service Configuration](#service-configuration)
5. [Environment Variables](#environment-variables)
6. [Database Setup](#database-setup)
7. [Deployment](#deployment)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- Railway account (sign up at https://railway.app)
- Railway CLI installed: `npm install -g @railway/cli`
- Access to required third-party services:
  - ZeroDB account with API key
  - Stripe account (test mode)
  - Cloudflare account for video/calls
  - BeeHiiv account for newsletters
  - Postmark account for emails
  - OpenAI API key
- Git repository access
- Node.js 18+ and Python 3.9+

## Railway Account Setup

### 1. Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub (recommended) or email
3. Verify your email address
4. Add payment method (Railway offers $5 free credit monthly)

### 2. Install Railway CLI

```bash
# Install globally via npm
npm install -g @railway/cli

# Verify installation
railway --version

# Login to Railway
railway login
```

The CLI will open a browser window for authentication.

### 3. Verify Authentication

```bash
# Check login status
railway whoami
```

---

## Project Creation

### Option 1: Automated Setup (Recommended)

Use the provided setup script:

```bash
cd /path/to/wwmaa
./scripts/railway/setup-staging.sh
```

This script will:
- Create Railway project
- Create staging environment
- Link project to local directory
- Guide you through service and domain configuration

### Option 2: Manual Setup

#### Step 1: Create New Project

```bash
# Initialize new Railway project
railway init --name wwmaa-staging
```

Or create via Railway Dashboard:
1. Go to https://railway.app/new
2. Click "Empty Project"
3. Name it "wwmaa-staging"

#### Step 2: Link Project Locally

```bash
# Link to the project you just created
railway link

# Select "wwmaa-staging" from the list
```

#### Step 3: Create Staging Environment

```bash
# Create staging environment
railway environment create staging

# Switch to staging environment
railway environment staging
```

---

## Service Configuration

### Backend Service (Python FastAPI)

#### 1. Create Backend Service

Via Railway Dashboard:
1. Click "New Service" in your project
2. Select "GitHub Repo"
3. Choose your WWMAA repository
4. Name it "backend"

#### 2. Configure Build Settings

Railway will auto-detect Python and use Nixpacks. Configuration is in `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.app:app --host 0.0.0.0 --port $PORT --workers 2",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 100
  }
}
```

#### 3. Configure Service Settings

1. Go to backend service settings
2. Set root directory: `/` (default)
3. Set environment: `staging`
4. Enable health checks: `/api/health`

### Frontend Service (Next.js)

#### 1. Create Frontend Service (Optional)

If deploying frontend to Railway:

1. Click "New Service"
2. Select "GitHub Repo"
3. Choose repository
4. Name it "frontend"

#### 2. Configure Build Settings

Railway auto-detects Next.js:

```bash
# Build command (automatic)
npm install && npm run build

# Start command (automatic)
npm start
```

### Redis Service

#### 1. Add Redis from Template

1. In Railway project dashboard, click "New"
2. Select "Database" → "Add Redis"
3. Railway will provision Redis automatically
4. Redis URL will be available as `REDIS_URL` environment variable

#### 2. Verify Redis Connection

```bash
# Check Redis service logs
railway logs --service redis --environment staging
```

---

## Environment Variables

### Backend Environment Variables

Set these in Railway Dashboard under backend service → Variables:

#### Core Configuration
```bash
PYTHON_ENV=staging
PYTHONUNBUFFERED=1
DEBUG=false
LOG_LEVEL=INFO
```

#### Database & Cache
```bash
ZERODB_API_KEY=<your-zerodb-api-key>
ZERODB_API_BASE_URL=https://api.zerodb.io/v1
REDIS_URL=${{Redis.REDIS_URL}}  # Railway internal reference
```

#### Authentication & Security
```bash
JWT_SECRET=<generate-secure-random-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CSRF_PROTECTION_ENABLED=true
```

#### Stripe (Test Mode)
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_BASIC_PRICE_ID=price_test_...
STRIPE_STANDARD_PRICE_ID=price_test_...
STRIPE_PREMIUM_PRICE_ID=price_test_...
```

#### Cloudflare
```bash
CLOUDFLARE_ACCOUNT_ID=<your-account-id>
CLOUDFLARE_API_TOKEN=<your-api-token>
CF_STREAM_ACCOUNT_ID=<your-stream-account>
CF_CALLS_APP_ID=<your-calls-app-id>
```

#### Email & Newsletter
```bash
POSTMARK_API_KEY=<staging-api-key>
FROM_EMAIL=staging@wwmaa.com
BEEHIIV_API_KEY=<test-api-key>
BEEHIIV_PUBLICATION_ID=<test-publication-id>
```

#### AI Services
```bash
OPENAI_API_KEY=<your-openai-key>
AI_REGISTRY_API_KEY=<your-ai-registry-key>
```

#### Observability
```bash
SENTRY_DSN=<staging-sentry-dsn>
SENTRY_ENVIRONMENT=staging
OTEL_EXPORTER_OTLP_ENDPOINT=<staging-otel-endpoint>
OTEL_SERVICE_NAME=wwmaa-backend-staging
```

#### CORS
```bash
CORS_ORIGINS=["https://staging.wwmaa.com","https://frontend-staging.railway.app"]
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://api-staging.wwmaa.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_CF_CALLS_APP_ID=<your-calls-app-id>
NEXT_PUBLIC_ENV=staging
NODE_ENV=production
```

### Using Railway CLI to Set Variables

```bash
# Set individual variable
railway variables set PYTHON_ENV=staging --environment staging

# Set multiple variables from file
railway variables set -f .env.staging --environment staging
```

---

## Database Setup

### 1. Set Up ZeroDB Collections

Run the staging database setup script:

```bash
# Ensure environment variables are set
export PYTHON_ENV=staging
export ZERODB_API_KEY=<your-api-key>

# Run setup script
python scripts/setup-staging-db.py
```

This creates collections:
- `staging_profiles` - User profiles
- `staging_events` - Events and workshops
- `staging_rsvps` - Event RSVPs
- `staging_applications` - Membership applications
- `staging_subscriptions` - Stripe subscriptions
- `staging_blog_posts` - Blog content
- `staging_newsletter_subscribers` - Newsletter subscriptions
- `staging_training_sessions` - Training sessions

### 2. Seed Test Data

Load realistic test data:

```bash
# Run seed data script
python scripts/seed-staging-data.py
```

This creates:
- 50 test user accounts
- 20 test events (past and upcoming)
- 100 blog posts for search testing
- 30 membership applications
- 40 subscription records

---

## Deployment

### Deploy Backend

#### Option 1: Automated Deployment

```bash
./scripts/railway/deploy-staging.sh
```

#### Option 2: Manual Deployment

```bash
# Deploy to staging environment
railway up --environment staging

# Watch deployment logs
railway logs --environment staging
```

#### Option 3: CI/CD with GitHub Actions

Railway automatically deploys on push to main branch if configured.

### Generate Domain

Generate Railway-provided domain or configure custom domain:

```bash
# Generate Railway domain
railway domain --environment staging
```

Or in Railway Dashboard:
1. Go to backend service → Settings → Domains
2. Click "Generate Domain"
3. Note the URL (e.g., `backend-staging-production.up.railway.app`)

### Configure Custom Domain (Optional)

For custom domain (e.g., `api-staging.wwmaa.com`):

1. In Railway Dashboard:
   - Go to service → Settings → Domains
   - Click "Custom Domain"
   - Enter: `api-staging.wwmaa.com`

2. In your DNS provider:
   - Add CNAME record: `api-staging` → `backend-staging-production.up.railway.app`
   - Wait for DNS propagation (5-30 minutes)

3. Railway will automatically provision SSL certificate

---

## Verification

### Automated Verification

Run the verification script:

```bash
# Set URLs if using custom domains
export BACKEND_URL=https://api-staging.wwmaa.com
export FRONTEND_URL=https://staging.wwmaa.com

# Run verification
./scripts/railway/verify-staging.sh
```

### Manual Verification

#### 1. Check Health Endpoint

```bash
# Basic health check
curl https://api-staging.wwmaa.com/api/health

# Expected response:
{
  "status": "healthy",
  "environment": "staging",
  "timestamp": "2024-01-10T12:00:00Z"
}

# Detailed health check
curl https://api-staging.wwmaa.com/api/health/detailed
```

#### 2. Check Metrics

```bash
# Prometheus metrics
curl https://api-staging.wwmaa.com/metrics
```

#### 3. Test Authentication

```bash
# Test login endpoint (expect 401 for invalid credentials)
curl -X POST https://api-staging.wwmaa.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"invalid"}'
```

#### 4. Check Railway Status

```bash
# View deployment status
railway status --environment staging

# View logs
railway logs --environment staging --tail 100
```

#### 5. Verify Redis Connection

Check application logs for Redis connection confirmation.

#### 6. Test End-to-End Flows

- User registration and login
- Event creation and RSVP
- Membership application
- Semantic search
- Stripe checkout (test mode)

---

## Troubleshooting

### Common Issues

#### 1. Health Check Failing

**Symptoms:** Railway shows service as unhealthy

**Solutions:**
```bash
# Check application logs
railway logs --environment staging

# Verify health endpoint locally
curl https://your-app.railway.app/api/health

# Check if port is correct ($PORT environment variable)
# Railway assigns port dynamically
```

#### 2. Environment Variables Not Set

**Symptoms:** Application errors about missing configuration

**Solutions:**
```bash
# List all variables
railway variables --environment staging

# Set missing variables
railway variables set VARIABLE_NAME=value --environment staging

# Restart service after setting variables
railway restart --environment staging
```

#### 3. Build Failures

**Symptoms:** Deployment fails during build

**Solutions:**
```bash
# Check build logs
railway logs --environment staging

# Common fixes:
# - Verify requirements.txt includes all dependencies
# - Check Python version compatibility
# - Ensure railway.json configuration is correct

# Try local build
docker build -f Dockerfile -t test-build .
```

#### 4. Redis Connection Errors

**Symptoms:** Application can't connect to Redis

**Solutions:**
```bash
# Verify Redis service is running
railway status --service redis --environment staging

# Check REDIS_URL variable is set correctly
railway variables --environment staging | grep REDIS

# Use Railway internal reference:
REDIS_URL=${{Redis.REDIS_URL}}
```

#### 5. ZeroDB Connection Issues

**Symptoms:** Database operations failing

**Solutions:**
- Verify `ZERODB_API_KEY` is correct
- Check ZeroDB dashboard for service status
- Ensure collections were created: `python scripts/setup-staging-db.py`
- Test connection: `curl -H "Authorization: Bearer $ZERODB_API_KEY" https://api.zerodb.io/v1/collections`

#### 6. CORS Errors

**Symptoms:** Frontend can't communicate with backend

**Solutions:**
```bash
# Update CORS_ORIGINS to include your frontend domain
railway variables set CORS_ORIGINS='["https://staging.wwmaa.com"]' --environment staging

# Restart backend
railway restart --environment staging
```

#### 7. SSL Certificate Issues

**Symptoms:** HTTPS not working on custom domain

**Solutions:**
- Wait 5-10 minutes after adding custom domain
- Verify DNS CNAME is correct
- Check Railway dashboard for certificate status
- Ensure domain points to Railway's provided URL

### Getting Help

#### Railway Logs

```bash
# View recent logs
railway logs --environment staging --tail 100

# Stream logs in real-time
railway logs --environment staging --follow

# Filter logs
railway logs --environment staging | grep ERROR
```

#### Railway Status

```bash
# Check service status
railway status --environment staging

# Check specific service
railway status --service backend --environment staging
```

#### Railway Dashboard

Visit https://railway.app/project/[your-project-id] for:
- Real-time logs
- Metrics and monitoring
- Deployment history
- Service health

#### Support Channels

- Railway Discord: https://discord.gg/railway
- Railway Documentation: https://docs.railway.app
- WWMAA Project Issues: [GitHub Issues]

---

## Next Steps

After successful staging deployment:

1. **Run Seed Data:** `python scripts/seed-staging-data.py`
2. **Test User Flows:** Register, login, create events, RSVP
3. **Test Integrations:** Stripe payments, email sending, search
4. **Configure Monitoring:** Set up alerts in Railway dashboard
5. **Document URLs:** Update team documentation with staging URLs
6. **CI/CD Setup:** Configure GitHub Actions for automatic deployments
7. **Production Planning:** Use staging as template for production environment

---

## Maintenance

### Regular Tasks

- **Monitor Logs:** Check Railway dashboard daily
- **Update Dependencies:** Run `pip install -U -r requirements.txt` weekly
- **Refresh Seed Data:** Re-run seed script monthly
- **Test Backups:** Verify ZeroDB backups are working
- **Security Updates:** Apply security patches promptly

### Staging Environment Lifecycle

- **Purpose:** Pre-production testing and QA
- **Data Retention:** Refresh test data monthly
- **Uptime Target:** 95% (not production-critical)
- **Cost Management:** Monitor Railway usage to stay within free tier

---

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Environment Configuration Guide](../environments.md)
- [ZeroDB Setup Script](../../scripts/setup-staging-db.py)
- [Seed Data Script](../../scripts/seed-staging-data.py)
- [Verification Script](../../scripts/railway/verify-staging.sh)
