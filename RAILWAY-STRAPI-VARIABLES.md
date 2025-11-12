# Railway Strapi Service - Environment Variables Reference

**Quick Reference Card for Railway Dashboard**

---

## How to Add Variables in Railway

1. Go to Railway Dashboard
2. Select your project
3. Click on **strapi-cms** service
4. Go to **Variables** tab
5. Click **Add Variable** or **Raw Editor**
6. Copy/paste the variables below

---

## Option 1: Use Raw Editor (Fastest)

Click **Raw Editor** and paste this template:

```env
# Strapi Secrets (Replace with output from ./strapi-env-generator.sh)
ADMIN_JWT_SECRET=REPLACE_WITH_GENERATED_SECRET
API_TOKEN_SALT=REPLACE_WITH_GENERATED_SECRET
JWT_SECRET=REPLACE_WITH_GENERATED_SECRET
TRANSFER_TOKEN_SALT=REPLACE_WITH_GENERATED_SECRET
APP_KEYS=REPLACE_WITH_GENERATED_KEYS
STRAPI_ADMIN_CLIENT_PREVIEW_SECRET=REPLACE_WITH_GENERATED_SECRET

# Database Configuration
DATABASE_CLIENT=postgres
DATABASE_SSL=false
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Application Settings
NODE_ENV=production
HOST=0.0.0.0

# URLs (Replace with your actual Railway URLs)
PUBLIC_URL=https://strapi-production-xxxx.up.railway.app
STRAPI_ADMIN_CLIENT_URL=https://frontend-production-yyyy.up.railway.app
ADMIN_URL=/admin

# CORS (Replace with your domains)
CORS_ORIGIN=https://frontend-production-yyyy.up.railway.app,https://yourdomain.com

# File Upload (Optional)
UPLOAD_PROVIDER=local
```

---

## Option 2: Use Railway References for Database

This is the recommended approach for database connection:

### Step 1: Click "Reference" for DATABASE_URL

1. Click **Add Variable**
2. Variable name: `DATABASE_URL`
3. Click **Reference**
4. Select: **Postgres** service
5. Select: `DATABASE_URL`
6. Click **Add**

### Step 2: Add All Other Variables

```env
ADMIN_JWT_SECRET=<from-generator>
API_TOKEN_SALT=<from-generator>
JWT_SECRET=<from-generator>
TRANSFER_TOKEN_SALT=<from-generator>
APP_KEYS=<from-generator>
STRAPI_ADMIN_CLIENT_PREVIEW_SECRET=<from-generator>
DATABASE_CLIENT=postgres
DATABASE_SSL=false
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
NODE_ENV=production
HOST=0.0.0.0
PUBLIC_URL=https://your-strapi-url.railway.app
STRAPI_ADMIN_CLIENT_URL=https://your-frontend-url.railway.app
ADMIN_URL=/admin
CORS_ORIGIN=https://your-frontend-url.railway.app
UPLOAD_PROVIDER=local
```

The startup script will automatically parse `DATABASE_URL` into individual connection variables.

---

## Variable Descriptions

### Critical Variables (Required)

| Variable | Purpose | Example |
|----------|---------|---------|
| `ADMIN_JWT_SECRET` | Admin panel JWT signing | 64-char random string |
| `API_TOKEN_SALT` | API token encryption salt | 64-char random string |
| `JWT_SECRET` | General JWT signing | 64-char random string |
| `TRANSFER_TOKEN_SALT` | Transfer token encryption | 64-char random string |
| `APP_KEYS` | App-level encryption keys | 4 comma-separated hex strings |
| `DATABASE_CLIENT` | Database type | `postgres` |
| `DATABASE_URL` | Full database connection | Reference from Postgres |
| `NODE_ENV` | Application environment | `production` |
| `HOST` | Bind host address | `0.0.0.0` |

### Important Variables (Recommended)

| Variable | Purpose | Example |
|----------|---------|---------|
| `PUBLIC_URL` | Public-facing Strapi URL | `https://strapi.railway.app` |
| `ADMIN_URL` | Admin panel path | `/admin` |
| `STRAPI_ADMIN_CLIENT_URL` | Frontend URL for CORS | `https://frontend.railway.app` |
| `CORS_ORIGIN` | Allowed CORS origins | Comma-separated URLs |
| `DATABASE_SSL` | Database SSL mode | `false` (Railway internal) |
| `DATABASE_POOL_MIN` | Min DB connections | `2` |
| `DATABASE_POOL_MAX` | Max DB connections | `10` |

### Optional Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | Server port | Railway sets automatically |
| `UPLOAD_PROVIDER` | File storage provider | `local` |
| `STRAPI_ADMIN_CLIENT_PREVIEW_SECRET` | Preview mode secret | Generated string |
| `STRAPI_WEBHOOK_SECRET` | Webhook verification | Generated string |
| `SENTRY_DSN` | Error tracking | Sentry project DSN |

---

## Generate Secrets Command

Before adding variables to Railway, generate all secrets:

```bash
cd /Users/aideveloper/Desktop/wwmaa
./strapi-env-generator.sh
```

Copy the output and replace the placeholder values in Railway.

---

## Database Connection Options

### Option A: DATABASE_URL Reference (Recommended)

**Pros**:
- Automatic updates if database credentials change
- Single variable to manage
- Railway best practice

**Setup**:
1. Add reference to Postgres `DATABASE_URL`
2. Startup script parses it automatically
3. No manual host/port/password management

### Option B: Individual Variables

**Pros**:
- More explicit
- Easier to debug connection issues

**Setup**:
Add these Railway references:
- `DATABASE_HOST` → `${{Postgres.PGHOST}}`
- `DATABASE_PORT` → `${{Postgres.PGPORT}}`
- `DATABASE_NAME` → `${{Postgres.PGDATABASE}}`
- `DATABASE_USERNAME` → `${{Postgres.PGUSER}}`
- `DATABASE_PASSWORD` → `${{Postgres.PGPASSWORD}}`

---

## CORS Configuration Examples

### Single Frontend Domain

```env
CORS_ORIGIN=https://wwmaa-frontend.railway.app
```

### Multiple Domains

```env
CORS_ORIGIN=https://wwmaa-frontend.railway.app,https://www.wwmaa.com,https://wwmaa.com
```

### Development + Production

```env
CORS_ORIGIN=http://localhost:3000,https://wwmaa-frontend.railway.app,https://www.wwmaa.com
```

Important: NO SPACES after commas!

---

## File Upload Providers

### Local Storage (Default)

```env
UPLOAD_PROVIDER=local
```

**Pros**: Simple, no extra setup
**Cons**: Files lost on redeploy, not scalable

### Cloudflare R2 (Recommended)

```env
UPLOAD_PROVIDER=cloudflare-r2
CF_R2_ACCOUNT_ID=your-account-id
CF_R2_ACCESS_KEY_ID=your-access-key-id
CF_R2_SECRET_ACCESS_KEY=your-secret-access-key
CF_R2_BUCKET=strapi-uploads
CF_R2_REGION=auto
```

**Pros**: Cheap, fast, S3-compatible
**Cons**: Requires Cloudflare account

### AWS S3

```env
UPLOAD_PROVIDER=aws-s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_BUCKET=strapi-uploads
```

**Pros**: Industry standard, reliable
**Cons**: More expensive than R2

---

## Verification Checklist

After adding variables to Railway:

- [ ] All required variables present (9 minimum)
- [ ] No typos in variable names
- [ ] Secrets are random and unique (not placeholder values)
- [ ] URLs match actual Railway service URLs
- [ ] CORS_ORIGIN includes frontend domain
- [ ] DATABASE_URL reference set correctly
- [ ] No trailing spaces in values
- [ ] NODE_ENV set to `production`

---

## Common Mistakes

### 1. Using Placeholder Values

Wrong:
```env
ADMIN_JWT_SECRET=REPLACE_WITH_GENERATED_SECRET
```

Right:
```env
ADMIN_JWT_SECRET=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOMabcd123...
```

### 2. Wrong CORS Format

Wrong:
```env
CORS_ORIGIN=https://frontend.railway.app, https://wwmaa.com
```

Right (no spaces):
```env
CORS_ORIGIN=https://frontend.railway.app,https://wwmaa.com
```

### 3. Hardcoding PORT

Wrong:
```env
PORT=1337
```

Right (let Railway set it):
```env
# Don't set PORT - Railway provides it automatically
```

### 4. Wrong Database SSL Setting

Wrong for Railway internal Postgres:
```env
DATABASE_SSL=true
```

Right for Railway:
```env
DATABASE_SSL=false
```

Railway encrypts internal traffic automatically.

### 5. Missing APP_KEYS Commas

Wrong:
```env
APP_KEYS=key1 key2 key3 key4
```

Right:
```env
APP_KEYS=key1,key2,key3,key4
```

---

## Testing Variables

After adding variables and deploying, check the deployment logs for:

```
========================================
Strapi CMS Starting on Railway
========================================
Date: 2025-11-11...
Region: us-west1
Port: 3456
Environment: production
========================================

Checking Environment Variables...
========================================
Found: ADMIN_JWT_SECRET
Found: API_TOKEN_SALT
Found: APP_KEYS
Found: JWT_SECRET
Found: DATABASE_CLIENT
Found: DATABASE_URL (Railway PostgreSQL plugin detected)
Parsed DATABASE_HOST: ...
Parsed DATABASE_PORT: 5432
Parsed DATABASE_NAME: railway
Found: PORT=3456
========================================
All required environment variables present
========================================
```

If you see "MISSING: ..." errors, that variable needs to be added.

---

## Getting Railway Service URLs

### Strapi Service URL

1. Railway Dashboard → Strapi service
2. Click **Settings** → **Domains**
3. Copy the generated Railway domain (e.g., `strapi-production-xxxx.up.railway.app`)
4. Use in `PUBLIC_URL` variable

### Frontend Service URL

1. Railway Dashboard → Frontend service
2. Click **Settings** → **Domains**
3. Copy the Railway domain or custom domain
4. Use in `STRAPI_ADMIN_CLIENT_URL` and `CORS_ORIGIN`

---

## Environment-Specific Variables

### Development

Not recommended for Railway, but for local development:

```env
NODE_ENV=development
HOST=localhost
PORT=1337
DATABASE_SSL=false
```

### Staging

```env
NODE_ENV=production
PUBLIC_URL=https://strapi-staging.railway.app
STRAPI_ADMIN_CLIENT_URL=https://frontend-staging.railway.app
```

### Production

```env
NODE_ENV=production
PUBLIC_URL=https://strapi.yourdomain.com
STRAPI_ADMIN_CLIENT_URL=https://www.yourdomain.com
```

---

## Quick Copy Templates

### Minimal Required Variables (Raw Editor)

```env
ADMIN_JWT_SECRET=
API_TOKEN_SALT=
JWT_SECRET=
TRANSFER_TOKEN_SALT=
APP_KEYS=
DATABASE_CLIENT=postgres
NODE_ENV=production
HOST=0.0.0.0
DATABASE_SSL=false
```

Then add DATABASE_URL as a reference to Postgres.

### Recommended Variables (Raw Editor)

```env
ADMIN_JWT_SECRET=
API_TOKEN_SALT=
JWT_SECRET=
TRANSFER_TOKEN_SALT=
APP_KEYS=
STRAPI_ADMIN_CLIENT_PREVIEW_SECRET=
DATABASE_CLIENT=postgres
DATABASE_SSL=false
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
NODE_ENV=production
HOST=0.0.0.0
PUBLIC_URL=
STRAPI_ADMIN_CLIENT_URL=
ADMIN_URL=/admin
CORS_ORIGIN=
UPLOAD_PROVIDER=local
```

Fill in the blank values and add DATABASE_URL reference.

---

## Support

If you encounter issues with environment variables:

1. Check Railway Deploy Logs for validation errors
2. Verify variable names are spelled correctly (case-sensitive)
3. Ensure no trailing spaces in values
4. Try deploying with minimal variables first, then add more

---

**Last Updated**: November 11, 2025
**For**: WWMAA Strapi Railway Deployment
