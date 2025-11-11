# API Keys and Integration Setup Guide

Complete reference guide for configuring all third-party integrations required to run the WWMAA application with real data (not mocks).

## Table of Contents

- [Overview](#overview)
- [Required Integrations](#required-integrations)
  - [1. ZeroDB (Database & Storage)](#1-zerodb-database--storage)
  - [2. OpenAI (Embeddings)](#2-openai-embeddings)
  - [3. AINative AI Registry (LLM Orchestration)](#3-ainative-ai-registry-llm-orchestration)
  - [4. Stripe (Payment Processing)](#4-stripe-payment-processing)
  - [5. Postmark (Email Notifications)](#5-postmark-email-notifications)
  - [6. BeeHiiv (Newsletter)](#6-beehiiv-newsletter)
  - [7. Cloudflare (Video & CDN)](#7-cloudflare-video--cdn)
  - [8. Redis (Caching & Rate Limiting)](#8-redis-caching--rate-limiting)
  - [9. Railway (Deployment Platform)](#9-railway-deployment-platform)
- [Environment File Template](#environment-file-template)
- [Development vs Production Configuration](#development-vs-production-configuration)
- [Security Best Practices](#security-best-practices)
- [Testing Each Integration](#testing-each-integration)
- [Troubleshooting](#troubleshooting)
- [Cost Estimates](#cost-estimates)

---

## Overview

The WWMAA application integrates with 9 external services. Each service requires API keys or credentials that must be configured in your environment variables before the application can function properly.

**Prerequisites:**
- Python 3.11+
- Git
- A credit card for services that require payment (Stripe, Cloudflare, OpenAI)

**Setup Time:** 1-2 hours (depending on account creation and verification)

---

## Required Integrations

### 1. ZeroDB (Database & Storage)

**Purpose:** Primary database for all application data, vector search for semantic content search, and object storage for files/images.

**Required Environment Variables:**
```bash
ZERODB_API_KEY=your-zerodb-api-key-here
ZERODB_API_BASE_URL=https://api.ainative.studio
ZERODB_EMAIL=your-email@example.com        # Optional
ZERODB_PASSWORD=your-password              # Optional
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://api.ainative.studio/dashboard
   - Sign up for a new account
   - Verify your email address

2. **Get API Key:**
   - Log in to your dashboard
   - Navigate to **API Keys** section
   - Click **"Create New API Key"**
   - Copy the API key (it will only be shown once)
   - Store it securely

3. **Configuration:**
   - The API key must be at least 10 characters
   - Base URL should always be `https://api.ainative.studio`
   - Email/Password are optional for most operations

**Test Endpoints:**

```bash
# Test connection
curl -X GET https://api.ainative.studio/health \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test document creation
curl -X POST https://api.ainative.studio/collections/test/documents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"test": "value"}}'
```

**Python Test:**
```python
from backend.services.zerodb_service import ZeroDBClient

client = ZeroDBClient()
# Test connection
result = client.create_document("test_collection", {"test": "data"})
print(f"✓ ZeroDB connected: {result}")
```

**Features Used:**
- CRUD operations on collections (users, applications, events, etc.)
- Vector similarity search (1536-dimension embeddings)
- Object storage (file uploads)
- Batch operations

**Cost:** Free tier available, paid plans start at $29/month for production use

---

### 2. OpenAI (Embeddings)

**Purpose:** Generate vector embeddings for semantic search and content indexing.

**Required Environment Variables:**
```bash
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Optional, defaults to text-embedding-3-small
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://platform.openai.com/signup
   - Sign up with email or Google account
   - Verify phone number (required)

2. **Add Payment Method:**
   - Go to **Billing** → **Payment methods**
   - Add a credit card
   - Set usage limits (recommended: $10-20/month for development)

3. **Generate API Key:**
   - Navigate to **API keys** section
   - Click **"Create new secret key"**
   - Name it (e.g., "WWMAA Development")
   - Copy the key (starts with `sk-`)
   - Store it securely (cannot be viewed again)

**Test Endpoints:**

```bash
# Test embeddings API
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Test embedding generation",
    "model": "text-embedding-3-small"
  }'
```

**Python Test:**
```python
from backend.services.embedding_service import EmbeddingService

service = EmbeddingService()
embedding = service.generate_embedding("test query")
print(f"✓ OpenAI embeddings working: {len(embedding)} dimensions")
```

**Models Used:**
- `text-embedding-3-small` (1536 dimensions) - Default, cost-effective
- `text-embedding-3-large` (3072 dimensions) - Higher quality, more expensive
- `text-embedding-ada-002` (1536 dimensions) - Legacy model

**Cost Estimates:**
- text-embedding-3-small: $0.02 per 1M tokens (~$0.00002 per query)
- Development/Testing: ~$1-5/month
- Production: ~$10-50/month depending on usage

**Rate Limits:**
- Tier 1 (new accounts): 3,500 RPM, 1M TPM
- Tier 2 ($50+ spent): 3,500 RPM, 5M TPM

---

### 3. AINative AI Registry (LLM Orchestration)

**Purpose:** LLM-powered question answering, content generation, and RAG (Retrieval Augmented Generation) for intelligent search.

**Required Environment Variables:**
```bash
AINATIVE_API_KEY=your-ainative-api-key
AI_REGISTRY_API_KEY=your-ai-registry-api-key
AI_REGISTRY_BASE_URL=https://api.ainative.studio
AI_REGISTRY_MODEL=gpt-4o-mini              # Primary model
AI_REGISTRY_FALLBACK_MODEL=gpt-3.5-turbo  # Fallback model
AI_REGISTRY_MAX_TOKENS=2000                # Max response length
AI_REGISTRY_TEMPERATURE=0.7                # 0.0-2.0, controls randomness
AI_REGISTRY_TIMEOUT=60                     # Request timeout in seconds
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://ainative.studio/registry
   - Sign up or use existing AINative account
   - Verify email

2. **Get API Key:**
   - Navigate to **Registry → API Keys**
   - Create new API key
   - Copy and store securely

3. **Configure Models:**
   - Choose primary model (gpt-4o-mini recommended for cost/performance)
   - Set fallback model for when primary fails
   - Configure temperature (0.7 = balanced, 0.0 = deterministic, 1.5+ = creative)

**Available Models:**
- `gpt-4o-mini` - Fast, cost-effective, good quality (recommended)
- `gpt-4` - Highest quality, slower, expensive
- `gpt-4-turbo` - Fast, high quality, moderate cost
- `gpt-3.5-turbo` - Fast, cheapest, lower quality (good fallback)
- `claude-3-sonnet` - Anthropic's balanced model
- `claude-3-haiku` - Anthropic's fast model

**Test Endpoints:**

```bash
# Test chat completion
curl https://api.ainative.studio/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is martial arts?"}],
    "max_tokens": 200
  }'
```

**Python Test:**
```python
from backend.services.ai_registry_service import AIRegistryService

service = AIRegistryService()
result = service.generate_answer(
    query="What is karate?",
    context=[],
    model="gpt-4o-mini"
)
print(f"✓ AI Registry working: {result['answer'][:100]}...")
```

**Cost Estimates (per 1M tokens):**
- gpt-4o-mini: $0.15 input, $0.60 output
- gpt-4: $30 input, $60 output
- gpt-3.5-turbo: $0.50 input, $1.50 output
- claude-3-haiku: $0.25 input, $1.25 output

**Typical Usage:**
- Development: $2-10/month
- Production: $20-100/month depending on query volume

---

### 4. Stripe (Payment Processing)

**Purpose:** Process membership payments, event registrations, and subscriptions.

**Required Environment Variables:**
```bash
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key     # Test mode
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
STRIPE_PUBLISHABLE_KEY=pk_test_your-publishable-key  # Optional, for frontend
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://dashboard.stripe.com/register
   - Sign up with email
   - Complete business verification (required for live mode)

2. **Get Test API Keys:**
   - Go to **Developers → API keys**
   - Toggle to **"Test mode"** (top right)
   - Copy **Secret key** (starts with `sk_test_`)
   - Copy **Publishable key** (starts with `pk_test_`)

3. **Setup Webhook:**
   - Go to **Developers → Webhooks**
   - Click **"Add endpoint"**
   - Endpoint URL: `https://your-backend-url.com/api/webhooks/stripe`
   - Select events to listen for:
     - `checkout.session.completed`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
   - Copy the **Webhook signing secret** (starts with `whsec_`)

4. **Setup Products (Optional for Testing):**
   ```bash
   python backend/scripts/setup_stripe_products.py
   ```

**Test Endpoints:**

```bash
# Test API connection
curl https://api.stripe.com/v1/customers \
  -u YOUR_SECRET_KEY: \
  -d "description=Test customer"

# Test webhook signing
stripe trigger checkout.session.completed
```

**Python Test:**
```python
from backend.services.stripe_service import StripeService

service = StripeService()

# Test checkout session creation
session = service.create_checkout_session(
    user_id="test_user",
    application_id="test_app",
    tier_id="basic",
    customer_email="test@example.com"
)
print(f"✓ Stripe working: {session['url']}")
```

**Test Cards:**
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Auth required: `4000 0025 0000 3155`
- Expiry: Any future date (e.g., 12/34)
- CVC: Any 3 digits (e.g., 123)

**Membership Pricing:**
- Basic: $29.00/year
- Premium: $79.00/year
- Lifetime: $149.00 one-time

**Cost:**
- 2.9% + $0.30 per successful transaction
- No monthly fees
- Free test mode

**Going Live:**
- Complete business verification
- Switch to **Live mode**
- Update keys to `sk_live_` and `pk_live_`
- Update webhook URL to production endpoint

---

### 5. Postmark (Email Notifications)

**Purpose:** Send transactional emails (verification, password reset, application updates, event confirmations).

**Required Environment Variables:**
```bash
POSTMARK_API_KEY=your-postmark-server-token
FROM_EMAIL=noreply@wwmaa.com              # Must be verified domain
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://account.postmarkapp.com/sign_up
   - Sign up with email
   - Verify email address

2. **Create Server:**
   - Click **"Servers"** → **"Create Server"**
   - Name it (e.g., "WWMAA Production")
   - Select **"Transactional"** stream type

3. **Get API Token:**
   - Go to your server
   - Click **"API Tokens"** tab
   - Copy the **Server API token**

4. **Verify Sender Domain:**
   - Go to **"Sender Signatures"**
   - Click **"Add Domain"**
   - Enter your domain (e.g., `wwmaa.com`)
   - Add DNS records to your domain:
     - DKIM record (for authentication)
     - Return-Path record (for bounces)
   - Wait for verification (usually 1-24 hours)

5. **Alternative - Verify Individual Email:**
   - If you don't have a domain, verify individual email
   - Go to **"Sender Signatures"** → **"Add Email Address"**
   - Enter email and verify via confirmation link

**Test Endpoints:**

```bash
# Test email sending
curl "https://api.postmarkapp.com/email" \
  -X POST \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Postmark-Server-Token: YOUR_API_KEY" \
  -d '{
    "From": "noreply@your-verified-domain.com",
    "To": "test@example.com",
    "Subject": "Test Email",
    "TextBody": "This is a test email from WWMAA"
  }'
```

**Python Test:**
```python
from backend.services.email_service import EmailService

service = EmailService()

# Test verification email
result = service.send_verification_email(
    email="your-test-email@example.com",
    token="test_token_123",
    user_name="Test User"
)
print(f"✓ Postmark working: {result}")
```

**Email Templates Used:**
- Email verification
- Welcome email
- Password reset
- Application approval/rejection
- Payment confirmations
- Event RSVP confirmations
- Waitlist notifications

**Cost:**
- Free tier: 100 emails/month
- Starter: $15/month for 10,000 emails
- Production: Custom pricing for high volume

**Deliverability Tips:**
- Always use verified domain/email
- Monitor bounce rates
- Keep suppression list clean
- Use proper email headers

---

### 6. BeeHiiv (Newsletter)

**Purpose:** Newsletter subscription management and email campaigns.

**Required Environment Variables:**
```bash
BEEHIIV_API_KEY=your-beehiiv-api-key
BEEHIIV_PUBLICATION_ID=your-publication-id  # Optional
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://www.beehiiv.com/
   - Sign up for account
   - Create a publication

2. **Get API Key:**
   - Go to **Settings → Integrations**
   - Find **API** section
   - Click **"Generate API Key"**
   - Copy and store securely

3. **Get Publication ID:**
   - In your publication settings
   - Copy the **Publication ID** (if needed for API calls)

**Test Endpoints:**

```bash
# Test subscriber creation
curl https://api.beehiiv.com/v2/publications/YOUR_PUB_ID/subscriptions \
  -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "reactivate_existing": false
  }'
```

**Python Test:**
```python
import requests

# Test newsletter subscription
response = requests.post(
    "https://api.beehiiv.com/v2/publications/YOUR_PUB_ID/subscriptions",
    headers={
        "Authorization": f"Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={"email": "test@example.com"}
)
print(f"✓ BeeHiiv working: {response.status_code == 201}")
```

**Cost:**
- Free: Up to 2,500 subscribers
- Growth: $42/month for unlimited subscribers
- Scale: Custom pricing

**Note:** BeeHiiv integration is for newsletter subscriptions. Transactional emails still go through Postmark.

---

### 7. Cloudflare (Video & CDN)

**Purpose:** Video hosting for training content via Cloudflare Stream, and optionally Cloudflare Calls for video conferencing.

**Required Environment Variables:**
```bash
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_CALLS_APP_ID=your-calls-app-id  # Optional
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://dash.cloudflare.com/sign-up
   - Sign up with email
   - Add payment method (required for Stream)

2. **Get Account ID:**
   - Log in to Cloudflare dashboard
   - Click on your profile icon → **Account Home**
   - Copy **Account ID** from the sidebar

3. **Create API Token:**
   - Go to **My Profile → API Tokens**
   - Click **"Create Token"**
   - Use **"Create Custom Token"** template
   - Set permissions:
     - **Stream: Edit** (for video uploads)
     - **Calls: Edit** (if using Calls)
   - Set IP filtering (optional but recommended)
   - Create token and copy it

4. **Enable Cloudflare Stream:**
   - Go to **Stream** from main dashboard
   - Enable Stream service
   - Note pricing: $1 per 1,000 minutes stored + $1 per 1,000 minutes delivered

5. **Setup Calls (Optional):**
   - Go to **Calls** from main dashboard
   - Create a new application
   - Copy the **App ID**

**Test Endpoints:**

```bash
# Test Stream API
curl -X GET https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/stream \
  -H "Authorization: Bearer YOUR_API_TOKEN"

# Upload test video to Stream
curl -X POST \
  https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/stream \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@/path/to/video.mp4"
```

**Python Test:**
```python
import requests

# Test Cloudflare Stream access
response = requests.get(
    f"https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/stream",
    headers={"Authorization": f"Bearer YOUR_API_TOKEN"}
)
print(f"✓ Cloudflare working: {response.status_code == 200}")
```

**Video Formats Supported:**
- MP4, MOV, WebM, MKV, AVI
- Max size: 30GB per video
- Automatic transcoding to multiple qualities

**Cost Estimates:**
- Storage: $1 per 1,000 minutes stored per month
- Delivery: $1 per 1,000 minutes delivered
- Typical usage: $5-20/month for small libraries

**Cloudflare Calls Cost:**
- $0.05 per participant minute
- WebRTC-based video conferencing

---

### 8. Redis (Caching & Rate Limiting)

**Purpose:** Session caching, rate limiting, and temporary data storage.

**Required Environment Variables:**
```bash
REDIS_URL=redis://localhost:6379              # Local development
# OR
REDIS_URL=redis://default:password@host:6379  # Production/Railway
```

**Setup Instructions (Local Development):**

1. **Install Redis:**

   **macOS (Homebrew):**
   ```bash
   brew install redis
   brew services start redis
   ```

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   ```

   **Windows:**
   - Download from: https://github.com/microsoftarchive/redis/releases
   - Or use Docker: `docker run -d -p 6379:6379 redis`

2. **Verify Installation:**
   ```bash
   redis-cli ping
   # Should respond: PONG
   ```

3. **Configure (Optional):**
   - Edit `/usr/local/etc/redis.conf` (macOS)
   - Or `/etc/redis/redis.conf` (Linux)
   - Set password: `requirepass your_password`
   - Restart Redis

**Setup Instructions (Production - Railway):**

1. **Add Redis Service:**
   - In Railway project, click **"New"** → **"Database"** → **"Redis"**
   - Railway will provision Redis automatically
   - Copy connection URL from service variables

2. **Use Connection String:**
   ```bash
   REDIS_URL=redis://default:PASSWORD@redis.railway.internal:6379
   ```

**Test Endpoints:**

```bash
# Test Redis connection
redis-cli ping

# Set a test key
redis-cli SET test_key "test_value"

# Get the key
redis-cli GET test_key

# Test with password
redis-cli -a your_password ping
```

**Python Test:**
```python
import redis

# Test Redis connection
client = redis.from_url("redis://localhost:6379")
client.ping()
print("✓ Redis connected")

# Test set/get
client.set("test", "value")
value = client.get("test")
print(f"✓ Redis working: {value}")
```

**Uses in Application:**
- Rate limiting (per-IP and per-user)
- Embedding cache (reduces OpenAI costs)
- Session storage
- Temporary locks

**Cost:**
- Local: Free
- Railway Redis: $5-10/month (included in many plans)
- Redis Cloud: Free tier available, paid plans start at $5/month

**Performance:**
- Typical latency: <1ms
- Throughput: 100,000+ ops/sec

---

### 9. Railway (Deployment Platform)

**Purpose:** Host backend application, database, and Redis in production.

**Required Environment Variables:**
```bash
# Railway automatically provides these:
RAILWAY_ENVIRONMENT=production
RAILWAY_PROJECT_ID=auto-generated
PORT=auto-assigned
```

**Setup Instructions:**

1. **Create Account:**
   - Visit: https://railway.app/
   - Sign up with GitHub account (recommended)

2. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   # OR
   brew install railway
   ```

3. **Login:**
   ```bash
   railway login
   ```

4. **Create Project:**
   ```bash
   cd /path/to/wwmaa
   railway init
   ```

5. **Link Services:**
   ```bash
   # Add Python backend
   railway service create backend

   # Add Redis
   railway service create redis
   ```

6. **Configure Environment Variables:**
   ```bash
   # Upload all environment variables
   railway vars set ZERODB_API_KEY=your-key
   railway vars set OPENAI_API_KEY=your-key
   # ... (repeat for all variables)
   ```

7. **Deploy:**
   ```bash
   railway up
   ```

**MCP Tools Available:**

The Railway integration includes MCP tools for managing deployments:

```python
# Check Railway status
railway_status = check_railway_status()

# Deploy
railway_deploy(workspace_path="/path/to/wwmaa")

# Generate domain
domain = generate_domain(workspace_path="/path/to/wwmaa")

# List services
services = list_services(workspace_path="/path/to/wwmaa")

# Get logs
logs = get_logs(
    workspace_path="/path/to/wwmaa",
    log_type="deploy",
    lines=100
)
```

**Cost:**
- Free tier: $5 credit/month
- Hobby plan: $5/month + usage
- Production: $20/month + usage
- Typical usage: $10-30/month

**Deployment Options:**
1. Git-based (automatic on push)
2. CLI deployment (`railway up`)
3. GitHub Actions (CI/CD)

---

## Environment File Template

Complete `.env` file template with all required variables:

```bash
# ==========================================
# WWMAA Backend Environment Configuration
# ==========================================
# Copy this file to .env and fill in the values
# DO NOT commit .env file to version control

# ==========================================
# Environment
# ==========================================
PYTHON_ENV=development  # Options: development, staging, production

# ==========================================
# ZeroDB Configuration (REQUIRED)
# ==========================================
ZERODB_API_KEY=your-zerodb-api-key-here
ZERODB_API_BASE_URL=https://api.ainative.studio
ZERODB_EMAIL=admin@ainative.studio
ZERODB_PASSWORD=your-password-here

# ==========================================
# JWT Configuration (REQUIRED)
# ==========================================
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=change-this-to-a-secure-random-string-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ==========================================
# Redis Configuration (REQUIRED)
# ==========================================
REDIS_URL=redis://localhost:6379
# Production Railway: redis://default:password@redis.railway.internal:6379

# ==========================================
# Stripe Configuration (REQUIRED)
# ==========================================
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-stripe-webhook-secret
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key

# ==========================================
# Email Configuration (REQUIRED)
# ==========================================
POSTMARK_API_KEY=your-postmark-api-key
FROM_EMAIL=noreply@wwmaa.com

# ==========================================
# BeeHiiv Newsletter (REQUIRED)
# ==========================================
BEEHIIV_API_KEY=your-beehiiv-api-key
BEEHIIV_PUBLICATION_ID=your-publication-id

# ==========================================
# Cloudflare Configuration (REQUIRED)
# ==========================================
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_CALLS_APP_ID=your-calls-app-id

# ==========================================
# AINative AI Registry (REQUIRED)
# ==========================================
AINATIVE_API_KEY=your-ainative-api-key
AI_REGISTRY_API_KEY=your-ai-registry-api-key
AI_REGISTRY_BASE_URL=https://api.ainative.studio
AI_REGISTRY_MODEL=gpt-4o-mini
AI_REGISTRY_FALLBACK_MODEL=gpt-3.5-turbo
AI_REGISTRY_MAX_TOKENS=2000
AI_REGISTRY_TEMPERATURE=0.7
AI_REGISTRY_TIMEOUT=60

# ==========================================
# OpenAI Configuration (REQUIRED)
# ==========================================
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ==========================================
# Content Indexing Configuration
# ==========================================
INDEXING_SCHEDULE_INTERVAL_HOURS=6
INDEXING_CHUNK_SIZE=500
INDEXING_CHUNK_OVERLAP=50
INDEXING_BATCH_SIZE=100

# ==========================================
# Backend Configuration
# ==========================================
PYTHON_BACKEND_URL=http://localhost:8000

# ==========================================
# Testing Configuration
# ==========================================
TEST_COVERAGE_MINIMUM=80
```

---

## Development vs Production Configuration

### Development Configuration

**Use test/development credentials where available:**

```bash
# Stripe - Use test mode
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Postmark - Use sandbox token (optional)
POSTMARK_API_KEY=POSTMARK_API_TEST

# Redis - Local instance
REDIS_URL=redis://localhost:6379

# AI Registry - Use cheaper models
AI_REGISTRY_MODEL=gpt-4o-mini
AI_REGISTRY_FALLBACK_MODEL=gpt-3.5-turbo

# OpenAI - Use small embedding model
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Environment
PYTHON_ENV=development
PYTHON_BACKEND_URL=http://localhost:8000
```

### Production Configuration

**Use production credentials:**

```bash
# Stripe - Use live mode
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Postmark - Use production server token
POSTMARK_API_KEY=your-production-token

# Redis - Railway or Redis Cloud
REDIS_URL=redis://default:password@production-host:6379

# Environment
PYTHON_ENV=production
PYTHON_BACKEND_URL=https://api.wwmaa.com

# Same AI models (already cost-optimized)
AI_REGISTRY_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Staging Configuration

**Use production-like setup with test data:**

```bash
PYTHON_ENV=staging
STRIPE_SECRET_KEY=sk_test_...  # Still use test mode
PYTHON_BACKEND_URL=https://staging-api.wwmaa.com
```

---

## Security Best Practices

### 1. Environment Variables

- ✓ **NEVER** commit `.env` files to version control
- ✓ Add `.env` to `.gitignore`
- ✓ Use `.env.example` as a template (without real values)
- ✓ Rotate API keys regularly (every 90 days)
- ✓ Use different keys for dev/staging/production
- ✓ Store production keys in secure vault (1Password, AWS Secrets Manager)

### 2. API Key Management

```bash
# Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Check if .env is in .gitignore
grep -q ".env" .gitignore && echo "✓ Protected" || echo "✗ Add .env to .gitignore"

# Audit environment variables
python -c "from backend.config import settings; print('✓ All required env vars loaded')"
```

### 3. Rate Limiting

Redis-based rate limiting is configured for:
- Login attempts: 5 per 15 minutes per IP
- Password reset: 3 per hour per email
- API endpoints: 100 per minute per user
- Payment endpoints: 10 per hour per user

### 4. Webhook Security

**Stripe Webhooks:**
```python
# Always verify webhook signatures
import stripe

def verify_stripe_webhook(payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError:
        # Invalid payload
        raise
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise
```

### 5. Database Security

- ✓ Use ZeroDB API keys, not credentials
- ✓ Enable IP whitelisting in ZeroDB dashboard
- ✓ Use read-only keys for analytics/reporting
- ✓ Regular backups (automated daily)

---

## Testing Each Integration

### Automated Test Suite

Run all integration tests:

```bash
# Set up test environment
cp .env.example .env
# Fill in test API keys

# Run integration tests
pytest backend/tests/test_integration/ -v

# Test specific service
pytest backend/tests/test_integration/test_zerodb.py -v
pytest backend/tests/test_integration/test_stripe.py -v
```

### Manual Testing Checklist

**ZeroDB:**
```bash
python -c "
from backend.services.zerodb_service import ZeroDBClient
client = ZeroDBClient()
result = client.create_document('test', {'hello': 'world'})
print('✓ ZeroDB:', result)
"
```

**OpenAI:**
```bash
python -c "
from backend.services.embedding_service import EmbeddingService
service = EmbeddingService()
emb = service.generate_embedding('test')
print(f'✓ OpenAI: {len(emb)} dimensions')
"
```

**AI Registry:**
```bash
python -c "
from backend.services.ai_registry_service import AIRegistryService
service = AIRegistryService()
result = service.generate_answer('What is karate?', [])
print('✓ AI Registry:', result['answer'][:100])
"
```

**Stripe:**
```bash
python -c "
from backend.services.stripe_service import StripeService
service = StripeService()
pricing = service.get_tier_pricing('basic')
print('✓ Stripe:', pricing)
"
```

**Postmark:**
```bash
python -c "
from backend.services.email_service import EmailService
service = EmailService()
print('✓ Postmark: Service initialized')
# Note: Don't send test email in automated check
"
```

**Redis:**
```bash
redis-cli ping || echo "✗ Redis not running"
```

**Test Full Stack:**
```bash
# Start backend
cd backend
uvicorn app:app --reload

# In another terminal, test API
curl http://localhost:8000/health
curl http://localhost:8000/api/config
```

---

## Troubleshooting

### Common Issues

#### ZeroDB Connection Errors

**Error:** `ZeroDBAuthenticationError: Authentication failed`

**Solutions:**
1. Verify API key is correct
2. Check API key hasn't expired
3. Ensure ZERODB_API_BASE_URL is correct
4. Test with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" https://api.ainative.studio/health
   ```

#### OpenAI Rate Limits

**Error:** `RateLimitError: Rate limit exceeded`

**Solutions:**
1. Check usage: https://platform.openai.com/usage
2. Implement exponential backoff
3. Use embedding cache (Redis)
4. Upgrade tier (requires $50+ spent)
5. Batch requests when possible

#### Stripe Webhook Failures

**Error:** `Invalid signature`

**Solutions:**
1. Verify webhook secret matches
2. Check endpoint URL is correct
3. Test with Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:8000/api/webhooks/stripe
   stripe trigger checkout.session.completed
   ```

#### Redis Connection Refused

**Error:** `ConnectionError: Error connecting to Redis`

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Start Redis: `redis-server` or `brew services start redis`
3. Verify REDIS_URL is correct
4. Check firewall settings
5. For Railway: Ensure Redis service is running

#### Postmark Domain Not Verified

**Error:** `422 Unprocessable Entity: Sender signature not found`

**Solutions:**
1. Verify domain in Postmark dashboard
2. Add DNS records (DKIM, Return-Path)
3. Wait for verification (up to 24 hours)
4. Use verified email address as temporary solution

#### Cloudflare 403 Forbidden

**Error:** `403 Forbidden: Invalid API token`

**Solutions:**
1. Verify token has correct permissions
2. Check token hasn't expired
3. Create new token with Stream:Edit permission
4. Verify Account ID is correct

---

## Cost Estimates

### Monthly Cost Breakdown

**Development/Testing:**
- ZeroDB: Free tier
- OpenAI: $1-5
- AI Registry: $2-10
- Stripe: Free (test mode)
- Postmark: Free tier (100 emails)
- BeeHiiv: Free tier (up to 2,500 subscribers)
- Cloudflare: $5-10
- Redis: Free (local)
- Railway: Free tier ($5 credit)

**Total Development: $8-30/month**

**Production (Small - 100 users):**
- ZeroDB: $29/month
- OpenAI: $10-20
- AI Registry: $20-50
- Stripe: 2.9% + $0.30 per transaction (variable)
- Postmark: $15/month (10,000 emails)
- BeeHiiv: Free tier (up to 2,500 subscribers)
- Cloudflare: $10-30
- Redis: $5-10 (Railway)
- Railway: $20-40

**Total Production (Small): $109-214/month** + transaction fees

**Production (Medium - 1,000 users):**
- ZeroDB: $99/month
- OpenAI: $50-100
- AI Registry: $100-200
- Stripe: Transaction-based
- Postmark: $45/month (50,000 emails)
- BeeHiiv: $42/month
- Cloudflare: $50-100
- Redis: $10-20
- Railway: $50-100

**Total Production (Medium): $446-761/month** + transaction fees

### Cost Optimization Tips

1. **Use caching aggressively** - Redis cache for embeddings saves 90%+ on OpenAI costs
2. **Batch operations** - Batch embed generation instead of single calls
3. **Choose right models** - gpt-4o-mini vs gpt-4 saves 95% on AI costs
4. **Monitor usage** - Set up billing alerts on all platforms
5. **Free tiers** - Max out free tiers before upgrading (BeeHiiv, Postmark)
6. **Annual billing** - Many services offer discounts for annual plans

---

## Quick Start Script

Automated setup script for development environment:

```bash
#!/bin/bash
# setup-integrations.sh

echo "WWMAA Integration Setup"
echo "======================="
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo "⚠️  Please edit .env and add your API keys"
    exit 1
fi

# Test Redis
echo "Testing Redis..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Redis connected"
else
    echo "✗ Redis not running - start with: redis-server"
    exit 1
fi

# Test Python dependencies
echo "Checking Python dependencies..."
python -c "import redis, stripe, openai, requests" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Python dependencies installed"
else
    echo "✗ Installing dependencies..."
    pip install -r requirements.txt
fi

# Test integrations
echo ""
echo "Testing integrations..."
python -c "
from backend.config import get_settings
try:
    settings = get_settings()
    print('✓ Configuration loaded successfully')
    print(f'  Environment: {settings.PYTHON_ENV}')
    print(f'  ZeroDB URL: {settings.ZERODB_API_BASE_URL}')
    print(f'  Redis URL: {settings.REDIS_URL}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    exit(1)
"

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your real API keys"
echo "2. Run: python -m pytest backend/tests/test_integration/"
echo "3. Start backend: uvicorn backend.app:app --reload"
```

Run with:
```bash
chmod +x setup-integrations.sh
./setup-integrations.sh
```

---

## Additional Resources

**Official Documentation:**
- ZeroDB: https://api.ainative.studio/docs
- OpenAI: https://platform.openai.com/docs
- Stripe: https://stripe.com/docs
- Postmark: https://postmarkapp.com/developer
- BeeHiiv: https://developers.beehiiv.com/
- Cloudflare: https://developers.cloudflare.com/
- Redis: https://redis.io/documentation
- Railway: https://docs.railway.app/

**Support Channels:**
- ZeroDB: support@ainative.studio
- OpenAI: https://help.openai.com/
- Stripe: https://support.stripe.com/
- Postmark: https://postmarkapp.com/support
- Cloudflare: https://support.cloudflare.com/

**Community:**
- WWMAA GitHub Issues: https://github.com/your-org/wwmaa/issues
- WWMAA Discussions: https://github.com/your-org/wwmaa/discussions

---

**Last Updated:** 2025-01-10

**Maintained By:** WWMAA Development Team

**Version:** 1.0
