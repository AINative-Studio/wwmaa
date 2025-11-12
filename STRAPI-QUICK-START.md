# Strapi Railway Quick Start Guide

**5-Minute Deployment Checklist**

---

## Prerequisites

- Railway account with WWMAA project
- GitHub repository access
- PostgreSQL database service in Railway

---

## Step 1: Generate Secrets (2 minutes)

```bash
cd /Users/aideveloper/Desktop/wwmaa
./strapi-env-generator.sh > strapi-secrets.txt
```

Save the output - you'll need it for Railway variables.

---

## Step 2: Create Strapi Service in Railway (1 minute)

1. Railway Dashboard → Your Project → **New** → **GitHub Repo**
2. Select `wwmaa` repository
3. Service name: `strapi-cms`
4. Click **Deploy**

---

## Step 3: Configure Railway Service (2 minutes)

### Build Settings

Go to `strapi-cms` → **Settings** → **Build**:

- Dockerfile Path: `Dockerfile.strapi`
- Root Directory: `/`

### Deploy Settings

Go to `strapi-cms` → **Settings** → **Deploy**:

- Start Command: `/bin/bash /opt/app/railway-strapi-start.sh`
- Health Check Path: `/_health`
- Health Check Timeout: `180`

---

## Step 4: Add Environment Variables (5 minutes)

Go to `strapi-cms` → **Variables** tab and add these:

### Copy from Generated Secrets

```env
ADMIN_JWT_SECRET=<from-generator>
API_TOKEN_SALT=<from-generator>
JWT_SECRET=<from-generator>
TRANSFER_TOKEN_SALT=<from-generator>
APP_KEYS=<from-generator>
STRAPI_ADMIN_CLIENT_PREVIEW_SECRET=<from-generator>
```

### Database Configuration

```env
DATABASE_CLIENT=postgres
DATABASE_SSL=false
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
```

### Database Connection (Option A: Reference Variables)

Click **Reference** and select PostgreSQL service:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Database Connection (Option B: Manual)

```env
DATABASE_HOST=${{Postgres.PGHOST}}
DATABASE_PORT=${{Postgres.PGPORT}}
DATABASE_NAME=${{Postgres.PGDATABASE}}
DATABASE_USERNAME=${{Postgres.PGUSER}}
DATABASE_PASSWORD=${{Postgres.PGPASSWORD}}
```

### Application Settings

```env
NODE_ENV=production
HOST=0.0.0.0
```

### Frontend Integration

```env
STRAPI_ADMIN_CLIENT_URL=https://your-frontend.railway.app
ADMIN_URL=/admin
PUBLIC_URL=https://<your-strapi-service>.railway.app
CORS_ORIGIN=https://your-frontend.railway.app
```

Replace `<your-strapi-service>` and `your-frontend` with actual Railway URLs.

---

## Step 5: Deploy (5 minutes)

1. Click **Redeploy** in Railway dashboard
2. Watch **Deploy Logs** for any errors
3. Wait for health check to pass
4. Service should show **Active** status

---

## Step 6: Access Strapi Admin (2 minutes)

1. Get your Strapi service URL from Railway (e.g., `https://strapi-production.up.railway.app`)
2. Navigate to: `https://<your-url>/admin`
3. Create your first admin user:
   - Email: `admin@yourdomain.com`
   - Password: Use strong password
   - First name & Last name
4. Click **Create Admin**

---

## Step 7: Generate API Token for Backend (3 minutes)

1. In Strapi admin panel: **Settings** → **API Tokens** → **Create new API Token**
2. Name: `WWMAA Backend`
3. Token type: `Full access` (or customize)
4. Token duration: `Unlimited`
5. Click **Save** and **COPY THE TOKEN** (shown only once!)

### Add to Backend Service

Go to Railway → `backend` service → **Variables**:

```env
STRAPI_API_URL=https://<your-strapi-service>.railway.app
STRAPI_API_TOKEN=<token-from-step-above>
STRAPI_CACHE_TTL=300
STRAPI_TIMEOUT=10
```

Redeploy backend service.

---

## Step 8: Create Content Types (10 minutes)

### Blog Post

1. **Content-Type Builder** → **Create new collection type**
2. Display name: `Blog Post`
3. Add fields:
   - `title` (Text, required, short text)
   - `slug` (UID, attached to title)
   - `content` (Rich text, required)
   - `excerpt` (Text, long text)
   - `featuredImage` (Media, single image)
   - `publishedAt` (DateTime)
   - `author` (Relation → User, Many-to-One)
4. **Save** and **Publish**

### Event

1. **Create new collection type**: `Event`
2. Add fields:
   - `title` (Text, required)
   - `description` (Rich text)
   - `startDate` (DateTime, required)
   - `endDate` (DateTime)
   - `location` (Text)
   - `rsvpLink` (Text)
   - `featuredImage` (Media, single image)
   - `category` (Enumeration: Workshop, Networking, Conference)
3. **Save** and **Publish**

---

## Step 9: Configure Permissions (2 minutes)

1. **Settings** → **Roles** → **Public**
2. Enable for **Blog Post**:
   - ✅ `find`
   - ✅ `findOne`
3. Enable for **Event**:
   - ✅ `find`
   - ✅ `findOne`
4. **Save**

---

## Step 10: Test API (2 minutes)

### Test Health Endpoint

```bash
curl https://<your-strapi-url>/_health
```

Expected:
```json
{"status":"ok","timestamp":"2025-11-11T...","uptime":123.45}
```

### Test Blog Posts API

```bash
curl https://<your-strapi-url>/api/blog-posts
```

Expected:
```json
{"data":[],"meta":{"pagination":{"page":1,"pageSize":25,"pageCount":0,"total":0}}}
```

### Test from Backend

```bash
curl https://<your-backend-url>/api/content/blog-posts
```

Should return same format (cached).

---

## Troubleshooting

### Deployment Fails

**Check**: Deploy Logs for errors

Common issues:
- Missing environment variables → Add all required vars
- Database connection failed → Verify PostgreSQL reference
- Build timeout → Increase build timeout in settings

### Health Check Fails

**Check**: Health check endpoint is `/_health` (not `/api/health`)

**Solution**: Update Railway settings → Health Check Path → `/_health`

### Admin Panel Shows 404

**Check**: Build logs for admin panel build errors

**Solution**: Verify Dockerfile runs `npm run build` successfully

### CORS Errors from Frontend

**Check**: `CORS_ORIGIN` includes your frontend URL

**Solution**: Add frontend domain to `CORS_ORIGIN` variable

### Backend Cannot Connect to Strapi

**Check**:
1. `STRAPI_API_URL` is correct
2. `STRAPI_API_TOKEN` is set
3. Strapi API token has correct permissions

---

## Files Created

This deployment created the following files in your repository:

```
/Users/aideveloper/Desktop/wwmaa/
├── Dockerfile.strapi                    # Multi-stage Docker build
├── railway.strapi.json                  # Railway configuration
├── railway-strapi-start.sh              # Startup script with health checks
├── strapi-env-generator.sh              # Environment variable generator
├── STRAPI-RAILWAY-DEPLOYMENT.md         # Comprehensive guide
├── STRAPI-BACKEND-INTEGRATION.md        # Backend integration details
└── STRAPI-QUICK-START.md               # This file
```

---

## Next Steps

- [ ] Create first blog post in Strapi admin
- [ ] Test content API from backend
- [ ] Update frontend to display Strapi content
- [ ] Set up Cloudflare R2 for file uploads
- [ ] Configure webhooks for cache invalidation
- [ ] Train team on Strapi admin panel

---

## Support

- **Strapi Docs**: https://docs.strapi.io
- **Railway Docs**: https://docs.railway.app
- **WWMAA Full Guide**: See `STRAPI-RAILWAY-DEPLOYMENT.md`

---

**Total Setup Time**: ~30 minutes
**Last Updated**: November 11, 2025
