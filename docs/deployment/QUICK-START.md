# Railway Staging Quick Start Guide

Quick reference for deploying and managing the WWMAA staging environment on Railway.

## Prerequisites

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login
```

## Initial Setup (First Time Only)

```bash
# 1. Run automated setup
./scripts/railway/setup-staging.sh

# 2. Set environment variables in Railway dashboard
# Copy from .env.staging.example
# https://railway.app/project/[your-project-id]/settings

# 3. Set up ZeroDB collections
export PYTHON_ENV=staging
export ZERODB_API_KEY=your-key
python scripts/setup-staging-db.py

# 4. Deploy
./scripts/railway/deploy-staging.sh

# 5. Seed test data
python scripts/seed-staging-data.py

# 6. Verify
./scripts/railway/verify-staging.sh
```

## Daily Commands

### Deploy Changes
```bash
# Quick deploy
railway up --environment staging

# Or use script (includes validation)
./scripts/railway/deploy-staging.sh
```

### Check Status
```bash
# Service status
railway status --environment staging

# View logs
railway logs --environment staging --tail 100

# Stream logs in real-time
railway logs --environment staging --follow
```

### Health Checks
```bash
# Basic health
curl https://api-staging.wwmaa.com/api/health

# Detailed health with dependencies
curl https://api-staging.wwmaa.com/api/health/detailed

# Full verification
./scripts/railway/verify-staging.sh
```

### Environment Variables
```bash
# List all variables
railway variables --environment staging

# Set variable
railway variables set VARIABLE_NAME=value --environment staging

# Set multiple from file
railway variables set -f .env.staging --environment staging
```

### Restart Service
```bash
# Restart backend
railway restart --environment staging

# Restart specific service
railway restart --service backend --environment staging
```

## Troubleshooting

### Health Check Failing
```bash
# Check logs
railway logs --environment staging

# Check Redis
railway status --service redis --environment staging

# Test health endpoint
curl -v https://api-staging.wwmaa.com/api/health
```

### Environment Variables Missing
```bash
# List current variables
railway variables --environment staging

# Set missing variable
railway variables set ZERODB_API_KEY=your-key --environment staging

# Restart after changes
railway restart --environment staging
```

### Build Failing
```bash
# View build logs
railway logs --environment staging

# Test build locally
docker build -f Dockerfile .

# Check requirements.txt
cat backend/requirements.txt
```

### Redis Connection Issues
```bash
# Check Redis service
railway status --service redis

# Verify REDIS_URL variable
railway variables --environment staging | grep REDIS

# Use Railway internal reference
REDIS_URL=${{Redis.REDIS_URL}}
```

## Key URLs

- **Railway Dashboard:** https://railway.app/dashboard
- **Staging Backend:** https://api-staging.wwmaa.com
- **Staging Frontend:** https://staging.wwmaa.com
- **Health Check:** https://api-staging.wwmaa.com/api/health
- **Metrics:** https://api-staging.wwmaa.com/metrics

## Quick Links

- [Complete Setup Guide](staging-setup.md)
- [Environment Configuration](../environments.md)
- [Implementation Summary](US-081-IMPLEMENTATION-SUMMARY.md)
- [Railway Documentation](https://docs.railway.app)

## Common Tasks

### Refresh Test Data
```bash
python scripts/seed-staging-data.py
```

### View Metrics
```bash
curl https://api-staging.wwmaa.com/metrics
```

### Check Service Info
```bash
curl https://api-staging.wwmaa.com/api/health/status
```

### Generate New Domain
```bash
railway domain --environment staging
```

## Emergency Procedures

### Rollback Deployment
```bash
# View deployment history
railway list --environment staging

# Rollback to previous
railway rollback --environment staging
```

### Force Restart
```bash
railway restart --environment staging
```

### Clear Cache (Redis)
```bash
# Connect to Redis
railway run redis-cli --environment staging

# Flush cache
FLUSHDB
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/railway/setup-staging.sh` | Initial environment setup |
| `scripts/railway/deploy-staging.sh` | Deploy to staging |
| `scripts/railway/verify-staging.sh` | Verify deployment health |
| `scripts/setup-staging-db.py` | Create ZeroDB collections |
| `scripts/seed-staging-data.py` | Load test data |

## Support

For detailed documentation, see:
- [Staging Setup Guide](staging-setup.md)
- [Troubleshooting Section](staging-setup.md#troubleshooting)

For Railway-specific issues:
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
