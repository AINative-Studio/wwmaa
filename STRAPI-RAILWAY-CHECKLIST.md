# Strapi CMS Railway Deployment Checklist

**Project**: WWMAA
**Date**: November 11, 2025

---

## Pre-Deployment Checklist

### Files Verification

- [x] `Dockerfile.strapi` - Multi-stage Docker build
- [x] `railway.strapi.json` - Railway configuration
- [x] `railway-strapi-start.sh` - Startup script (executable)
- [x] `strapi-env-generator.sh` - Secret generator (executable)
- [x] `STRAPI-RAILWAY-DEPLOYMENT.md` - Main documentation
- [x] `STRAPI-BACKEND-INTEGRATION.md` - Integration guide
- [x] `STRAPI-QUICK-START.md` - Quick reference
- [x] `STRAPI-DEPLOYMENT-SUMMARY.md` - Overview
- [x] `.env.strapi.example` - Environment template

### Repository

- [ ] All files committed to Git
- [ ] Pushed to GitHub main branch
- [ ] No secrets in repository
- [ ] `.gitignore` includes `.env` files

---

## Railway Infrastructure Setup

### PostgreSQL Database

- [ ] PostgreSQL service exists in Railway project
- [ ] Database is running and healthy
- [ ] Can connect to database from Railway internal network

### Strapi Service Creation

- [ ] New service created: `strapi-cms`
- [ ] Linked to GitHub repository
- [ ] Correct branch selected (usually `main`)
- [ ] Service region selected (same as backend)

---

## Railway Build Configuration

### Build Settings

Go to `strapi-cms` → **Settings** → **Build**:

- [ ] Builder: `DOCKERFILE`
- [ ] Dockerfile Path: `Dockerfile.strapi`
- [ ] Root Directory: `/`
- [ ] Watch Paths: `strapi/**` (optional, for auto-rebuild)

### Deploy Settings

Go to `strapi-cms` → **Settings** → **Deploy**:

- [ ] Start Command: `/bin/bash /opt/app/railway-strapi-start.sh`
- [ ] Restart Policy: `ON_FAILURE`
- [ ] Restart Policy Max Retries: `3`

### Health Check Settings

Go to `strapi-cms` → **Settings** → **Health Check**:

- [ ] Health Check Enabled: `Yes`
- [ ] Health Check Path: `/_health`
- [ ] Health Check Timeout: `180` seconds
- [ ] Health Check Interval: `30` seconds (default)

---

## Environment Variables Setup

### Step 1: Generate Secrets

```bash
cd /Users/aideveloper/Desktop/wwmaa
./strapi-env-generator.sh > strapi-secrets.txt
```

- [ ] Script executed successfully
- [ ] Secrets saved securely
- [ ] File permissions set (chmod 600 strapi-secrets.txt)

### Step 2: Add Variables to Railway

Go to `strapi-cms` → **Variables** tab:

#### Strapi Secrets (Copy from generated output)

- [ ] `ADMIN_JWT_SECRET`
- [ ] `API_TOKEN_SALT`
- [ ] `JWT_SECRET`
- [ ] `TRANSFER_TOKEN_SALT`
- [ ] `APP_KEYS` (4 comma-separated keys)
- [ ] `STRAPI_ADMIN_CLIENT_PREVIEW_SECRET`

#### Database Configuration

- [ ] `DATABASE_CLIENT=postgres`
- [ ] `DATABASE_SSL=false`
- [ ] `DATABASE_POOL_MIN=2`
- [ ] `DATABASE_POOL_MAX=10`

#### Database Connection (Choose One)

Option A (Recommended):
- [ ] `DATABASE_URL` → Reference: `${{Postgres.DATABASE_URL}}`

Option B (Manual):
- [ ] `DATABASE_HOST` → Reference: `${{Postgres.PGHOST}}`
- [ ] `DATABASE_PORT` → Reference: `${{Postgres.PGPORT}}`
- [ ] `DATABASE_NAME` → Reference: `${{Postgres.PGDATABASE}}`
- [ ] `DATABASE_USERNAME` → Reference: `${{Postgres.PGUSER}}`
- [ ] `DATABASE_PASSWORD` → Reference: `${{Postgres.PGPASSWORD}}`

#### Application Settings

- [ ] `NODE_ENV=production`
- [ ] `HOST=0.0.0.0`
- [ ] `PORT` - (Leave empty, Railway sets automatically)

#### URLs (Replace with actual Railway URLs)

- [ ] `PUBLIC_URL=https://<your-strapi-service>.railway.app`
- [ ] `STRAPI_ADMIN_CLIENT_URL=https://<your-frontend>.railway.app`
- [ ] `ADMIN_URL=/admin`

#### CORS

- [ ] `CORS_ORIGIN=https://<frontend>.railway.app,https://yourdomain.com`

#### Optional Variables

- [ ] `UPLOAD_PROVIDER=local` (or cloudflare-r2, aws-s3)
- [ ] `STRAPI_WEBHOOK_SECRET` (for cache invalidation)
- [ ] `SENTRY_DSN` (for error tracking)

---

## Initial Deployment

### Trigger Deployment

- [ ] Click **Deploy** or push to GitHub to trigger build
- [ ] Build logs show no errors
- [ ] Build completes in < 10 minutes
- [ ] Image size reasonable (< 500MB)

### Monitor Deployment

Watch **Deploy Logs** tab:

- [ ] Environment variables validated
- [ ] PostgreSQL connection successful
- [ ] Database migrations run (if any)
- [ ] Strapi starts successfully
- [ ] Health check passes
- [ ] Service status: **Active**

### Verify Deployment

Test health endpoint:
```bash
curl https://<your-strapi-url>/_health
```

- [ ] Returns 200 OK
- [ ] Response JSON: `{"status":"ok","timestamp":"...","uptime":...}`

---

## Strapi Configuration

### Access Admin Panel

- [ ] Navigate to: `https://<strapi-url>/admin`
- [ ] Admin registration page loads
- [ ] No CORS errors in browser console

### Create Admin User

- [ ] First name entered
- [ ] Last name entered
- [ ] Email address entered (valid format)
- [ ] Strong password set (min 8 chars, mixed case, numbers, symbols)
- [ ] Admin user created successfully
- [ ] Can log in to admin panel

---

## Content Types Setup

### Blog Post Content Type

- [ ] Content-Type Builder opened
- [ ] New collection type created: `Blog Post`
- [ ] API ID: `blog-post` (auto-generated)

Fields added:
- [ ] `title` (Text, required, short text)
- [ ] `slug` (UID, attached to title, required)
- [ ] `content` (Rich text, required)
- [ ] `excerpt` (Text, long text)
- [ ] `featuredImage` (Media, single image)
- [ ] `publishedAt` (DateTime)
- [ ] `author` (Relation → User, Many-to-One)

- [ ] Content type saved
- [ ] Server restarted automatically

### Event Content Type

- [ ] New collection type created: `Event`
- [ ] API ID: `event` (auto-generated)

Fields added:
- [ ] `title` (Text, required)
- [ ] `description` (Rich text)
- [ ] `startDate` (DateTime, required)
- [ ] `endDate` (DateTime)
- [ ] `location` (Text)
- [ ] `rsvpLink` (Text)
- [ ] `featuredImage` (Media, single image)
- [ ] `category` (Enumeration: Workshop, Networking, Conference)

- [ ] Content type saved
- [ ] Server restarted automatically

---

## Permissions Configuration

### Public Role Permissions

Go to **Settings** → **Roles** → **Public**:

#### Blog Post Permissions
- [ ] `find` - Enabled
- [ ] `findOne` - Enabled
- [ ] `create` - Disabled
- [ ] `update` - Disabled
- [ ] `delete` - Disabled

#### Event Permissions
- [ ] `find` - Enabled
- [ ] `findOne` - Enabled
- [ ] `create` - Disabled
- [ ] `update` - Disabled
- [ ] `delete` - Disabled

- [ ] Permissions saved

### Authenticated Role (Optional)

If allowing authenticated users to create content:
- [ ] Configure authenticated role permissions
- [ ] Set field-level permissions
- [ ] Test with authenticated requests

---

## API Token Generation

### Create Backend API Token

Go to **Settings** → **API Tokens**:

- [ ] Click **Create new API Token**
- [ ] Name: `WWMAA Backend`
- [ ] Token type: `Full access` (or custom)
- [ ] Token duration: `Unlimited`
- [ ] Token created
- [ ] **Token copied to secure location** (shown only once!)

---

## Backend Integration

### Update Backend Environment Variables

Go to Railway → `backend` service → **Variables**:

- [ ] `STRAPI_API_URL=https://<strapi-service>.railway.app`
- [ ] `STRAPI_API_TOKEN=<token-from-strapi>`
- [ ] `STRAPI_CACHE_TTL=300`
- [ ] `STRAPI_TIMEOUT=10`
- [ ] `STRAPI_WEBHOOK_SECRET=<generated>` (optional)

### Deploy Backend Integration Code

Files to create in backend:

- [ ] `/backend/services/strapi_service.py`
- [ ] `/backend/routes/content.py`
- [ ] `/backend/routes/webhooks.py` (optional)
- [ ] Update `/backend/config.py`
- [ ] Update `/backend/app.py` to include content router

### Commit and Deploy

- [ ] All backend files committed
- [ ] Pushed to GitHub
- [ ] Backend service redeployed
- [ ] Backend deploy logs show no errors

---

## Testing

### Strapi API Tests

Test blog posts endpoint:
```bash
curl https://<strapi-url>/api/blog-posts
```
- [ ] Returns 200 OK
- [ ] Returns empty array: `{"data":[],"meta":{...}}`

Test events endpoint:
```bash
curl https://<strapi-url>/api/events
```
- [ ] Returns 200 OK
- [ ] Returns empty array: `{"data":[],"meta":{...}}`

### Backend Content API Tests

Test blog posts via backend:
```bash
curl https://<backend-url>/api/content/blog-posts
```
- [ ] Returns 200 OK
- [ ] Data matches Strapi response
- [ ] Response time < 500ms

Test events via backend:
```bash
curl https://<backend-url>/api/content/events
```
- [ ] Returns 200 OK
- [ ] Data matches Strapi response
- [ ] Response time < 500ms

### Cache Testing

Create a blog post in Strapi, then:

1. First request to backend:
   - [ ] Cache MISS (slower, ~200-500ms)
   - [ ] Data retrieved from Strapi
   - [ ] Cached in Redis

2. Second request to backend:
   - [ ] Cache HIT (faster, < 50ms)
   - [ ] Data from Redis cache

3. Invalidate cache:
   ```bash
   curl -X POST https://<backend-url>/api/content/cache/invalidate?content_type=blog
   ```
   - [ ] Returns success message
   - [ ] Cache cleared in Redis

4. Next request:
   - [ ] Cache MISS again
   - [ ] Fresh data from Strapi

---

## Create Sample Content

### First Blog Post

In Strapi admin panel:

- [ ] Go to **Content Manager** → **Blog Posts**
- [ ] Click **Create new entry**
- [ ] Title: "Welcome to WWMAA"
- [ ] Content: Sample markdown content
- [ ] Featured Image: Upload test image
- [ ] Published At: Current date/time
- [ ] Click **Save** and **Publish**

### Test Blog Post API

```bash
curl https://<strapi-url>/api/blog-posts
```
- [ ] Returns 1 blog post
- [ ] Title matches: "Welcome to WWMAA"
- [ ] All fields populated correctly

### First Event

- [ ] Go to **Content Manager** → **Events**
- [ ] Click **Create new entry**
- [ ] Title: "Test Workshop"
- [ ] Description: Sample event details
- [ ] Start Date: Future date
- [ ] Category: Workshop
- [ ] Click **Save** and **Publish**

### Test Event API

```bash
curl https://<strapi-url>/api/events?upcoming_only=true
```
- [ ] Returns 1 event
- [ ] Title matches: "Test Workshop"
- [ ] All fields populated correctly

---

## Optional: File Upload Configuration

### Cloudflare R2 Setup (Recommended)

If using Cloudflare R2 for file storage:

1. Create R2 bucket:
   - [ ] Bucket name: `strapi-uploads`
   - [ ] Bucket created in Cloudflare
   - [ ] API token generated with read/write permissions

2. Add R2 credentials to Railway:
   - [ ] `UPLOAD_PROVIDER=cloudflare-r2`
   - [ ] `CF_R2_ACCOUNT_ID=<account-id>`
   - [ ] `CF_R2_ACCESS_KEY_ID=<access-key>`
   - [ ] `CF_R2_SECRET_ACCESS_KEY=<secret-key>`
   - [ ] `CF_R2_BUCKET=strapi-uploads`
   - [ ] `CF_R2_REGION=auto`

3. Test file upload:
   - [ ] Upload image in Strapi Media Library
   - [ ] Image appears in R2 bucket
   - [ ] Image accessible via R2 URL

---

## Optional: Webhook Configuration

### Set Up Content Update Webhook

In Strapi admin panel, **Settings** → **Webhooks**:

- [ ] Click **Create new webhook**
- [ ] Name: `Backend Cache Invalidation`
- [ ] URL: `https://<backend-url>/api/webhooks/strapi/content-updated`
- [ ] Events selected:
  - [ ] `entry.create`
  - [ ] `entry.update`
  - [ ] `entry.delete`
- [ ] Headers: `x-strapi-signature: <webhook-secret>`
- [ ] Webhook saved

### Test Webhook

1. Update a blog post in Strapi:
   - [ ] Webhook fires
   - [ ] Backend receives webhook
   - [ ] Cache invalidated automatically
   - [ ] Backend logs show webhook received

---

## Performance Validation

### Response Time Benchmarks

- [ ] Strapi health check: < 100ms
- [ ] Backend content API (cache hit): < 50ms
- [ ] Backend content API (cache miss): < 500ms
- [ ] Strapi admin panel load: < 2s

### Load Testing

Using Apache Bench or similar:
```bash
ab -n 1000 -c 10 https://<backend-url>/api/content/blog-posts
```

- [ ] All requests succeed (0 failed)
- [ ] Mean response time < 200ms
- [ ] No memory leaks
- [ ] Database connections stable

---

## Security Validation

### Secrets Management

- [ ] All secrets generated with strong randomness
- [ ] No secrets committed to Git
- [ ] Secrets stored only in Railway environment variables
- [ ] File permissions on local secrets file: 600

### API Security

- [ ] Public API endpoints only return published content
- [ ] Admin endpoints require authentication
- [ ] CORS configured for specific origins (no wildcards)
- [ ] Rate limiting enabled (if configured)

### Database Security

- [ ] PostgreSQL uses Railway internal network
- [ ] Database credentials not exposed
- [ ] SSL disabled for internal connections (Railway encrypts internally)
- [ ] Connection pooling configured

---

## Monitoring Setup

### Railway Metrics

- [ ] Service metrics dashboard accessible
- [ ] CPU usage normal (< 80%)
- [ ] Memory usage normal (< 80%)
- [ ] Deployment history visible

### Application Logging

- [ ] Deployment logs retained
- [ ] Application logs show startup sequence
- [ ] No error logs on startup
- [ ] Request logs visible

### Alerts (Optional)

If using Sentry or similar:
- [ ] Error tracking configured
- [ ] Alerts sent to team channel
- [ ] Error rate threshold set

---

## Documentation

### Team Documentation

- [ ] Deployment guide shared with team
- [ ] Environment variables documented
- [ ] API endpoints documented
- [ ] Content creation guide written

### Runbooks Created

- [ ] How to deploy updates
- [ ] How to rollback deployment
- [ ] How to add content types
- [ ] How to invalidate cache
- [ ] How to troubleshoot common issues

---

## Post-Deployment Tasks

### Immediate (Day 1)

- [ ] Monitor deployment for 24 hours
- [ ] Check error logs
- [ ] Verify all features work
- [ ] Test from different networks

### Week 1

- [ ] Create remaining content types
- [ ] Add initial content (10+ blog posts, 5+ events)
- [ ] Train content editors
- [ ] Set up editorial workflow

### Month 1

- [ ] Review performance metrics
- [ ] Optimize slow queries
- [ ] Implement full-text search (if needed)
- [ ] Add analytics tracking

---

## Rollback Plan

If issues occur, follow this rollback procedure:

### Immediate Rollback

1. Railway Dashboard → Strapi service:
   - [ ] Click **Deployments** tab
   - [ ] Find last working deployment
   - [ ] Click **Redeploy**

2. Verify rollback:
   - [ ] Health check passes
   - [ ] Admin panel accessible
   - [ ] API endpoints work

### Data Rollback (if needed)

1. Railway Dashboard → PostgreSQL service:
   - [ ] Click **Backups** tab
   - [ ] Select backup before issue
   - [ ] Click **Restore**
   - [ ] Wait for restore to complete

### Communication

- [ ] Notify team of rollback
- [ ] Document issue in incident log
- [ ] Create post-mortem after resolution

---

## Sign-Off

### Technical Verification

- [ ] All services deployed successfully
- [ ] All tests passing
- [ ] Performance meets requirements
- [ ] Security requirements met

### Stakeholder Approval

- [ ] Product Owner reviewed: _______________
- [ ] Tech Lead approved: _______________
- [ ] DevOps verified: _______________

### Go-Live

- [ ] Production deployment complete
- [ ] All users can access
- [ ] Monitoring active
- [ ] Team trained

---

## Support Contacts

**Railway Issues**:
- Discord: https://discord.gg/railway
- Docs: https://docs.railway.app

**Strapi Issues**:
- Discord: https://discord.strapi.io
- Docs: https://docs.strapi.io

**WWMAA Team**:
- DevOps Lead: [Contact]
- Backend Lead: [Contact]
- Frontend Lead: [Contact]

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Sign-Off Date**: _______________

---

**Last Updated**: November 11, 2025
