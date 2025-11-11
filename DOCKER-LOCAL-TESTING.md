# 🐳 Docker Local Testing Guide

This guide helps you run WWMAA locally using Docker on high ports.

## Quick Start

### Option 1: Using the Helper Script (Recommended)

```bash
# Navigate to project root
cd /Users/aideveloper/Desktop/wwmaa

# Run the interactive script
./docker-local-test.sh
```

Then select option **6** (Build and start) for first-time setup.

### Option 2: Manual Docker Commands

```bash
# 1. Build the backend image
docker-compose build backend

# 2. Start all services (backend + redis)
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f backend

# 5. Test health endpoint
curl http://localhost:8080/api/health
```

## Service URLs

Once running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Backend API** | http://localhost:8080 | FastAPI backend |
| **Health Check** | http://localhost:8080/api/health | Service health status |
| **API Documentation** | http://localhost:8080/docs | Swagger UI |
| **Redis** | localhost:6380 | Redis cache |

## Port Configuration

The following high ports are used to avoid conflicts:

- **Backend:** 8080 (external) → 8000 (container)
- **Redis:** 6380 (external) → 6379 (container)
- **Frontend:** 3001 (if using Docker, currently disabled)

## Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Rebuild After Code Changes
```bash
# Rebuild and restart
docker-compose up -d --build
```

### Clean Everything (Reset)
```bash
# Remove containers, networks, and volumes
docker-compose down -v

# Remove images too
docker-compose down -v --rmi all
```

## Testing the Deployment

### 1. Health Check
```bash
curl http://localhost:8080/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2025-11-10T..."
}
```

### 2. Detailed Health Check
```bash
curl http://localhost:8080/api/health/detailed
```

### 3. Test API Endpoints
```bash
# Get API documentation
open http://localhost:8080/docs

# Test CSRF token endpoint
curl http://localhost:8080/api/security/csrf-token
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check if port is already in use
lsof -i :8080
```

### Environment Variables Not Loading

```bash
# Verify .env file exists
ls -la .env

# Check what environment variables the container sees
docker-compose exec backend env | grep -E "PYTHON_ENV|DATABASE_URL|REDIS_URL"
```

### Permission Errors

```bash
# The Dockerfile runs as non-root user 'appuser'
# If you see permission errors, check file ownership:
docker-compose exec backend ls -la /app/backend
```

### Redis Connection Issues

```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check if backend can reach Redis
docker-compose exec backend curl -f http://redis:6379
```

### Build Failures

```bash
# Clean build (no cache)
docker-compose build --no-cache backend

# Check Docker disk space
docker system df

# Clean up old images/containers
docker system prune -a
```

## Frontend (Next.js) - Not in Docker

The frontend is currently configured to run outside Docker using npm:

```bash
# In a separate terminal
npm install
npm run dev
```

Frontend will run on: http://localhost:3000 (or next available port)

Set this environment variable for frontend to connect to Docker backend:
```bash
export NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Comparing to Railway Deployment

### Local (Docker):
- Backend: http://localhost:8080
- Environment: development
- Logs: `docker-compose logs`
- Restart: `docker-compose restart`

### Railway (Staging):
- Backend: https://your-app-staging.railway.app
- Environment: staging
- Logs: `railway logs --environment staging`
- Restart: Auto-restart on deploy

## Debugging Railway Deployment Issues

If you're seeing errors on Railway, test locally first:

1. **Build the image locally** to verify Dockerfile works
2. **Run with staging environment variables** to replicate Railway
3. **Check health endpoint** responds correctly
4. **Review logs** for any startup errors

To test with staging-like environment:

```bash
# Edit docker-compose.yml, change:
# PYTHON_ENV=development
# to:
# PYTHON_ENV=staging

# Then rebuild and restart
docker-compose up -d --build
```

## Next Steps

After confirming local Docker deployment works:

1. ✅ Test all health endpoints
2. ✅ Test key API endpoints
3. ✅ Check Redis connectivity
4. ✅ Review logs for errors
5. 🚀 Deploy to Railway with confidence

## Need Help?

- Check logs: `docker-compose logs -f backend`
- Inspect container: `docker-compose exec backend bash`
- Test health: `curl http://localhost:8080/api/health`
- Reset everything: `docker-compose down -v && docker-compose up -d --build`
