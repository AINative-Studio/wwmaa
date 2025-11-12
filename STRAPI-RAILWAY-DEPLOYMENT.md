# Strapi CMS Railway Deployment Guide

**Project**: WWMAA (Women Who Make an Artisan Alchemists)
**Date**: November 11, 2025
**Status**: Ready for Deployment

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Railway Setup](#railway-setup)
5. [Environment Variables](#environment-variables)
6. [Deployment Steps](#deployment-steps)
7. [Post-Deployment Configuration](#post-deployment-configuration)
8. [Backend Integration](#backend-integration)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## Overview

This guide provides step-by-step instructions for deploying Strapi CMS as a third service on Railway alongside your existing backend and frontend services.

### What is Strapi?

Strapi is an open-source headless CMS that provides:
- Content management API
- Admin dashboard for content editors
- Role-based access control
- Media library
- RESTful and GraphQL APIs

### Why Strapi for WWMAA?

- Manage blog posts, events, and educational content
- Non-technical team members can update content
- Structured content with custom types
- Built-in media management
- API-first architecture integrates with existing backend

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Railway Project                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │   Frontend   │      │   Backend    │      │  Strapi  │  │
│  │  (Next.js)   │─────▶│  (FastAPI)   │◀────▶│   CMS    │  │
│  │              │      │              │      │          │  │
│  └──────────────┘      └──────────────┘      └─────┬────┘  │
│                                                     │        │
│                                                     │        │
│                        ┌────────────────────────────┘        │
│                        │                                     │
│                        ▼                                     │
│                  ┌──────────┐                                │
│                  │PostgreSQL│                                │
│                  │ Database │                                │
│                  └──────────┘                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Service Communication

- **Frontend** → **Backend**: API calls for user data, authentication
- **Backend** → **Strapi**: Content API calls for blog posts, events
- **Strapi** → **PostgreSQL**: Database for content storage
- **Frontend** → **Strapi**: Optional direct content API calls (cached)

---

## Prerequisites

### Required

- ✅ Railway account with active project
- ✅ Existing backend and frontend services deployed
- ✅ GitHub repository access
- ✅ Basic knowledge of Strapi and Docker

### Tools

- Git (for pushing code)
- OpenSSL (for generating secrets)
- Railway CLI (optional, for debugging)

### Repository Structure

```
wwmaa/
├── backend/                 # Existing FastAPI backend
├── strapi/                 # NEW: Strapi CMS application
│   ├── config/            # Strapi configuration
│   ├── src/               # Custom content types, controllers
│   ├── database/          # Database configuration
│   ├── public/            # Public assets
│   └── package.json       # Node.js dependencies
├── Dockerfile.backend      # Existing backend Dockerfile
├── Dockerfile.strapi       # NEW: Strapi Dockerfile
├── railway.strapi.json     # NEW: Railway configuration for Strapi
├── railway-strapi-start.sh # NEW: Strapi startup script
└── strapi-env-generator.sh # NEW: Generate environment variables
```

---

## Railway Setup

### Step 1: Add PostgreSQL Database (If Not Already Added)

1. Go to Railway Dashboard > Your Project
2. Click **New** → **Database** → **PostgreSQL**
3. Wait for provisioning to complete
4. PostgreSQL will automatically provide these environment variables:
   - `DATABASE_URL`
   - `DATABASE_HOST`
   - `DATABASE_PORT`
   - `DATABASE_NAME` (typically `railway`)
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`

### Step 2: Create New Strapi Service

1. In Railway Dashboard, click **New** → **GitHub Repo**
2. Select your `wwmaa` repository
3. Name the service: **strapi-cms**
4. Click **Deploy**

### Step 3: Configure Strapi Service Settings

1. Go to **strapi-cms** service → **Settings** tab
2. **Build Configuration**:
   - Build Command: (leave empty - Dockerfile handles this)
   - Dockerfile Path: `Dockerfile.strapi`
   - Root Directory: `/`
3. **Deploy Configuration**:
   - Start Command: `/bin/bash /opt/app/railway-strapi-start.sh`
   - Watch Paths: `strapi/**`
4. **Health Check**:
   - Path: `/_health`
   - Timeout: 180 seconds
5. **Region**: Same as your backend (e.g., `us-west1`)

### Step 4: Connect PostgreSQL to Strapi

1. Go to **strapi-cms** service → **Variables** tab
2. Click **Reference** → Select **PostgreSQL** service
3. Add these references:
   - `DATABASE_URL` → Reference PostgreSQL's `DATABASE_URL`

Alternatively, you can manually add individual variables:
   - `DATABASE_HOST` → Reference `PGHOST`
   - `DATABASE_PORT` → Reference `PGPORT`
   - `DATABASE_NAME` → Reference `PGDATABASE`
   - `DATABASE_USERNAME` → Reference `PGUSER`
   - `DATABASE_PASSWORD` → Reference `PGPASSWORD`

---

## Environment Variables

### Generate Secure Secrets

Run the provided script to generate all required secrets:

```bash
cd /Users/aideveloper/Desktop/wwmaa
./strapi-env-generator.sh
```

This will output all environment variables you need to copy to Railway.

### Required Variables for Railway

Add these to **strapi-cms** service → **Variables** tab:

#### Strapi Secrets (Generated by Script)

```env
ADMIN_JWT_SECRET=<generated-secret>
API_TOKEN_SALT=<generated-secret>
JWT_SECRET=<generated-secret>
TRANSFER_TOKEN_SALT=<generated-secret>
APP_KEYS=<key1>,<key2>,<key3>,<key4>
```

#### Database Configuration

```env
DATABASE_CLIENT=postgres
DATABASE_SSL=false
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
```

If using Railway's PostgreSQL reference variables, the startup script will automatically parse `DATABASE_URL`. Otherwise, add these manually:

```env
DATABASE_HOST=${{Postgres.PGHOST}}
DATABASE_PORT=${{Postgres.PGPORT}}
DATABASE_NAME=${{Postgres.PGDATABASE}}
DATABASE_USERNAME=${{Postgres.PGUSER}}
DATABASE_PASSWORD=${{Postgres.PGPASSWORD}}
```

#### Application Configuration

```env
NODE_ENV=production
HOST=0.0.0.0
```

**Note**: `PORT` is automatically set by Railway, do not override.

#### Frontend Integration

```env
STRAPI_ADMIN_CLIENT_URL=https://your-frontend.railway.app
STRAPI_ADMIN_CLIENT_PREVIEW_SECRET=<generated-secret>
```

#### Admin Panel Configuration

```env
ADMIN_URL=/admin
PUBLIC_URL=https://your-strapi-service.railway.app
```

#### CORS Configuration

```env
CORS_ORIGIN=https://your-frontend.railway.app,https://yourdomain.com
```

#### File Upload Configuration

For local storage (default):
```env
UPLOAD_PROVIDER=local
```

For Cloudflare R2 (recommended for production):
```env
UPLOAD_PROVIDER=cloudflare-r2
CF_R2_ACCOUNT_ID=your-account-id
CF_R2_ACCESS_KEY_ID=your-access-key
CF_R2_SECRET_ACCESS_KEY=your-secret-key
CF_R2_BUCKET=strapi-uploads
CF_R2_REGION=auto
```

---

## Deployment Steps

### Step 1: Create Strapi Application Locally

If you haven't already created the Strapi application:

```bash
cd /Users/aideveloper/Desktop/wwmaa
npx create-strapi-app@latest strapi --quickstart --no-run
```

This creates the `strapi/` directory with all necessary files.

### Step 2: Configure Strapi for Production

Edit `/Users/aideveloper/Desktop/wwmaa/strapi/config/database.js`:

```javascript
module.exports = ({ env }) => ({
  connection: {
    client: env('DATABASE_CLIENT', 'postgres'),
    connection: {
      host: env('DATABASE_HOST', '127.0.0.1'),
      port: env.int('DATABASE_PORT', 5432),
      database: env('DATABASE_NAME', 'strapi'),
      user: env('DATABASE_USERNAME', 'strapi'),
      password: env('DATABASE_PASSWORD', 'strapi'),
      ssl: env.bool('DATABASE_SSL', false) && {
        rejectUnauthorized: env.bool('DATABASE_SSL_SELF', false),
      },
    },
    pool: {
      min: env.int('DATABASE_POOL_MIN', 2),
      max: env.int('DATABASE_POOL_MAX', 10),
    },
  },
});
```

Edit `/Users/aideveloper/Desktop/wwmaa/strapi/config/server.js`:

```javascript
module.exports = ({ env }) => ({
  host: env('HOST', '0.0.0.0'),
  port: env.int('PORT', 1337),
  app: {
    keys: env.array('APP_KEYS'),
  },
  webhooks: {
    populateRelations: env.bool('WEBHOOKS_POPULATE_RELATIONS', false),
  },
  url: env('PUBLIC_URL', 'http://localhost:1337'),
});
```

Edit `/Users/aideveloper/Desktop/wwmaa/strapi/config/admin.js`:

```javascript
module.exports = ({ env }) => ({
  auth: {
    secret: env('ADMIN_JWT_SECRET'),
  },
  apiToken: {
    salt: env('API_TOKEN_SALT'),
  },
  transfer: {
    token: {
      salt: env('TRANSFER_TOKEN_SALT'),
    },
  },
  url: env('ADMIN_URL', '/admin'),
});
```

### Step 3: Add Health Check Endpoint

Create `/Users/aideveloper/Desktop/wwmaa/strapi/src/api/health/routes/health.js`:

```javascript
module.exports = {
  routes: [
    {
      method: 'GET',
      path: '/_health',
      handler: 'health.check',
      config: {
        auth: false,
      },
    },
  ],
};
```

Create `/Users/aideveloper/Desktop/wwmaa/strapi/src/api/health/controllers/health.js`:

```javascript
module.exports = {
  async check(ctx) {
    ctx.body = {
      status: 'ok',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    };
  },
};
```

### Step 4: Commit and Push to GitHub

```bash
cd /Users/aideveloper/Desktop/wwmaa
git add .
git commit -m "Add Strapi CMS configuration for Railway deployment"
git push origin main
```

### Step 5: Configure Railway Variables

1. Go to Railway Dashboard → **strapi-cms** service → **Variables** tab
2. Add all environment variables from the [Environment Variables](#environment-variables) section
3. Save changes

### Step 6: Deploy

1. Railway will automatically detect the push and start deployment
2. Monitor deployment in **Deploy Logs** tab
3. Wait for build to complete (~3-5 minutes)
4. Wait for health check to pass (~2-3 minutes)

### Step 7: Verify Deployment

Check health endpoint:

```bash
curl https://your-strapi-service.railway.app/_health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-11-11T23:45:00.000Z",
  "uptime": 123.456
}
```

---

## Post-Deployment Configuration

### Step 1: Access Strapi Admin Panel

1. Navigate to: `https://your-strapi-service.railway.app/admin`
2. Create your first admin user
3. Log in to the admin panel

### Step 2: Generate API Token for Backend

1. In Strapi admin panel, go to **Settings** → **API Tokens**
2. Click **Create new API Token**
3. Name: `WWMAA Backend`
4. Token type: `Full access` (or customize permissions)
5. Copy the generated token

### Step 3: Add Strapi Token to Backend

1. Go to Railway Dashboard → **backend** service → **Variables** tab
2. Add new variable:
   ```
   STRAPI_API_TOKEN=<your-generated-token>
   STRAPI_API_URL=https://your-strapi-service.railway.app
   ```
3. Redeploy backend service

### Step 4: Create Content Types

In Strapi admin panel, create your content types:

#### Blog Post Content Type

1. Go to **Content-Type Builder**
2. Click **Create new collection type**
3. Display name: `Blog Post`
4. Add fields:
   - Title (Text, required)
   - Slug (UID, based on title)
   - Content (Rich text, required)
   - Excerpt (Text, long)
   - Featured Image (Media, single)
   - Author (Relation to User)
   - Published At (DateTime)
   - SEO (Component: Title, Description, Keywords)
5. Save and publish

#### Event Content Type

1. Create new collection type: `Event`
2. Add fields:
   - Title (Text, required)
   - Description (Rich text)
   - Start Date (DateTime, required)
   - End Date (DateTime)
   - Location (Text)
   - RSVP Link (Text, URL)
   - Featured Image (Media)
   - Category (Enumeration: Workshop, Networking, Conference)
3. Save and publish

### Step 5: Configure Permissions

1. Go to **Settings** → **Roles** → **Public**
2. Enable read access for:
   - Blog Posts: `find`, `findOne`
   - Events: `find`, `findOne`
3. Save

---

## Backend Integration

### Update Backend to Fetch Content from Strapi

Create `/Users/aideveloper/Desktop/wwmaa/backend/services/strapi_service.py`:

```python
import httpx
from typing import List, Optional
from backend.config import settings

class StrapiService:
    def __init__(self):
        self.base_url = settings.STRAPI_API_URL
        self.api_token = settings.STRAPI_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def get_blog_posts(
        self,
        page: int = 1,
        page_size: int = 10,
        sort: str = "publishedAt:desc"
    ) -> dict:
        """Fetch blog posts from Strapi"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/blog-posts",
                headers=self.headers,
                params={
                    "pagination[page]": page,
                    "pagination[pageSize]": page_size,
                    "sort": sort,
                    "populate": "*"
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_blog_post(self, slug: str) -> Optional[dict]:
        """Fetch single blog post by slug"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/blog-posts",
                headers=self.headers,
                params={
                    "filters[slug][$eq]": slug,
                    "populate": "*"
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0] if data["data"] else None

    async def get_events(
        self,
        upcoming_only: bool = True,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """Fetch events from Strapi"""
        params = {
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "sort": "startDate:asc",
            "populate": "*"
        }

        if upcoming_only:
            from datetime import datetime
            params["filters[startDate][$gte]"] = datetime.utcnow().isoformat()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/events",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

# Singleton instance
strapi_service = StrapiService()
```

### Update Backend Configuration

Edit `/Users/aideveloper/Desktop/wwmaa/backend/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    # Strapi CMS Configuration
    STRAPI_API_URL: str = "http://localhost:1337"
    STRAPI_API_TOKEN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Create API Endpoints

Create `/Users/aideveloper/Desktop/wwmaa/backend/routes/content.py`:

```python
from fastapi import APIRouter, HTTPException
from backend.services.strapi_service import strapi_service

router = APIRouter(prefix="/api/content", tags=["content"])

@router.get("/blog-posts")
async def get_blog_posts(page: int = 1, page_size: int = 10):
    """Get all blog posts from Strapi"""
    try:
        return await strapi_service.get_blog_posts(page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog-posts/{slug}")
async def get_blog_post(slug: str):
    """Get single blog post by slug"""
    try:
        post = await strapi_service.get_blog_post(slug)
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        return post
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def get_events(upcoming_only: bool = True, page: int = 1, page_size: int = 10):
    """Get events from Strapi"""
    try:
        return await strapi_service.get_events(upcoming_only, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Register the router in `/Users/aideveloper/Desktop/wwmaa/backend/app.py`:

```python
from backend.routes import content

# ... existing code ...

app.include_router(content.router)
```

---

## Troubleshooting

### Issue: Deployment Fails - "service unavailable"

**Cause**: Health check endpoint not responding within timeout.

**Solution**:
1. Increase health check timeout to 180 seconds in Railway settings
2. Check Deploy Logs for startup errors
3. Verify all environment variables are set correctly
4. Ensure PostgreSQL is connected

### Issue: Database Connection Error

**Cause**: Strapi cannot connect to PostgreSQL.

**Solution**:
1. Verify PostgreSQL service is running in Railway
2. Check `DATABASE_URL` reference is set correctly
3. Ensure `DATABASE_SSL=false` for Railway's internal PostgreSQL
4. Check startup logs for connection errors

### Issue: Admin Panel Shows 404

**Cause**: Strapi admin panel not built or wrong URL.

**Solution**:
1. Verify `ADMIN_URL=/admin` is set
2. Check build logs for admin panel build errors
3. Rebuild with `npm run build` in Dockerfile
4. Access via full URL: `https://your-service.railway.app/admin`

### Issue: CORS Errors When Accessing from Frontend

**Cause**: CORS not configured for frontend domain.

**Solution**:
1. Add frontend domain to `CORS_ORIGIN` environment variable
2. Format: `https://frontend.railway.app,https://yourdomain.com`
3. Redeploy Strapi service

### Issue: Build Takes Too Long (Over 10 Minutes)

**Cause**: Installing all dependencies in single stage.

**Solution**:
1. Dockerfile already uses multi-stage build
2. Verify build command is not running `npm install` twice
3. Use `npm ci --only=production` for faster installs
4. Clear build cache in Railway settings

### Issue: Environment Variables Not Loading

**Cause**: Variable names don't match Strapi expectations.

**Solution**:
1. Verify exact variable names (case-sensitive)
2. Use Railway's reference syntax for PostgreSQL: `${{Postgres.PGHOST}}`
3. Check startup script logs for parsed values
4. Ensure no typos in variable names

---

## Security Best Practices

### 1. Use Strong Secrets

- Generate all secrets with `openssl rand -base64 32`
- Never commit secrets to Git
- Rotate secrets every 90 days

### 2. Database Security

- Use Railway's internal PostgreSQL (automatic encryption)
- Enable SSL for external connections
- Use connection pooling (already configured)
- Regular database backups

### 3. API Token Management

- Create separate tokens for each service
- Use least-privilege permissions
- Rotate tokens regularly
- Store tokens in Railway environment variables only

### 4. CORS Configuration

- Only allow specific origins (no wildcards in production)
- Update `CORS_ORIGIN` to include only trusted domains
- Regularly audit allowed origins

### 5. Admin Panel Security

- Use strong password for admin user
- Enable 2FA for admin accounts (Strapi plugin)
- Restrict admin panel access to specific IPs (if possible)
- Regularly update Strapi version

### 6. File Upload Security

- Use Cloudflare R2 for production (not local storage)
- Set maximum file size limits
- Validate file types
- Scan uploaded files for malware

### 7. Monitoring & Logging

- Enable Railway metrics
- Monitor API request rates
- Set up alerts for failed health checks
- Log all admin panel access

---

## Next Steps

1. ✅ Deploy Strapi to Railway
2. ✅ Configure PostgreSQL connection
3. ✅ Set up environment variables
4. ✅ Create admin user
5. ✅ Define content types
6. ✅ Generate API token
7. ✅ Integrate with backend
8. ⏳ Test content API endpoints
9. ⏳ Set up file upload (Cloudflare R2)
10. ⏳ Configure webhooks for cache invalidation
11. ⏳ Add frontend components to display content
12. ⏳ Train content editors on Strapi admin panel

---

## Additional Resources

- **Strapi Documentation**: https://docs.strapi.io
- **Railway Documentation**: https://docs.railway.app
- **PostgreSQL Best Practices**: https://www.postgresql.org/docs/current/
- **Strapi API Reference**: https://docs.strapi.io/dev-docs/api/rest
- **Railway Health Checks**: https://docs.railway.app/deploy/healthchecks

---

**Last Updated**: November 11, 2025
**Maintained By**: WWMAA Development Team
