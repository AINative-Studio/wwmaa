# WWMAA - Women's Martial Arts Association of America

Full-stack application for WWMAA membership management, event coordination, and community engagement.

## Overview

WWMAA is a comprehensive platform built with:
- **Backend:** Python FastAPI with ZeroDB
- **Frontend:** Next.js 14 with TypeScript
- **Infrastructure:** Railway (staging/production), Docker
- **Key Features:** Membership management, event RSVP, live training, semantic search, payment processing

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Deployment](#deployment)
- [Architecture](#architecture)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Redis
- Git

### Local Development

```bash
# Clone repository
git clone https://github.com/your-org/wwmaa.git
cd wwmaa

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Configure .env with your credentials

# Start backend
uvicorn app:app --reload --port 8000

# Frontend setup (in new terminal)
cd frontend
npm install
cp .env.local.example .env.local
# Configure .env.local

# Start frontend
npm run dev
```

Visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Development Setup

### Backend

#### Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
PYTHON_ENV=development
ZERODB_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
```

See [Environment Configuration](docs/environments.md) for complete details.

#### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_auth.py
```

#### Start Development Server

```bash
# With hot reload
uvicorn backend.app:app --reload --port 8000

# With specific host
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

#### Run Development Server

```bash
npm run dev
```

#### Run Tests

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:coverage
```

---

## Deployment

### Staging Environment (Railway)

WWMAA uses Railway for staging and production deployments.

#### Quick Deploy to Staging

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy to staging
./scripts/railway/deploy-staging.sh
```

#### Detailed Staging Setup

For complete staging environment setup, see [Staging Setup Guide](docs/deployment/staging-setup.md).

**Key Steps:**

1. **Create Railway Project**
   ```bash
   railway init --name wwmaa-staging
   railway environment create staging
   railway link
   ```

2. **Add Services**
   - Backend (Python FastAPI)
   - Redis (from Railway template)

3. **Configure Environment Variables**
   ```bash
   railway variables set PYTHON_ENV=staging --environment staging
   railway variables set ZERODB_API_KEY=your-key --environment staging
   # ... (see docs/deployment/staging-setup.md for complete list)
   ```

4. **Set Up Database**
   ```bash
   export PYTHON_ENV=staging
   export ZERODB_API_KEY=your-key
   python scripts/setup-staging-db.py
   ```

5. **Deploy**
   ```bash
   railway up --environment staging
   ```

6. **Seed Test Data**
   ```bash
   python scripts/seed-staging-data.py
   ```

7. **Verify Deployment**
   ```bash
   ./scripts/railway/verify-staging.sh
   ```

#### Staging URLs

After deployment:
- Backend: `https://api-staging.wwmaa.com` (or Railway-provided URL)
- Frontend: `https://staging.wwmaa.com` (if configured)
- Health Check: `https://api-staging.wwmaa.com/api/health`
- Metrics: `https://api-staging.wwmaa.com/metrics`

### Production Deployment

Production deployment follows the same process as staging but with:
- `production` environment
- Live API keys (Stripe, etc.)
- Production ZeroDB collections
- Auto-scaling enabled (2-4 instances)

```bash
# Deploy to production
railway up --environment production
```

See [Deployment Documentation](docs/deployment/staging-setup.md) for production-specific configuration.

### Docker Deployment

#### Build Image

```bash
# Build backend
docker build -f Dockerfile -t wwmaa-backend:latest .

# Build with specific environment
docker build -f Dockerfile --build-arg PYTHON_ENV=staging -t wwmaa-backend:staging .
```

#### Run Container

```bash
# Run backend
docker run -p 8000:8000 \
  -e PYTHON_ENV=production \
  -e ZERODB_API_KEY=your-key \
  -e REDIS_URL=redis://redis:6379 \
  wwmaa-backend:latest
```

#### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Architecture

### Tech Stack

**Backend:**
- FastAPI (Python 3.9+)
- ZeroDB (NoSQL database)
- Redis (caching & sessions)
- Pydantic (validation)
- JWT authentication
- Stripe (payments)
- OpenAI (AI features)

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn/ui components
- React Query (data fetching)
- Zustand (state management)

**Infrastructure:**
- Railway (hosting)
- Docker (containerization)
- GitHub Actions (CI/CD)
- Cloudflare (CDN, video, calls)

**Monitoring:**
- Sentry (error tracking)
- Prometheus (metrics)
- OpenTelemetry (tracing)

### Project Structure

```
wwmaa/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── config.py           # Configuration management
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic
│   ├── middleware/         # Custom middleware
│   ├── observability/      # Monitoring & tracing
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js application (if included)
├── docs/
│   ├── deployment/         # Deployment guides
│   ├── environments.md     # Environment configuration
│   └── privacy/            # Privacy & GDPR docs
├── scripts/
│   ├── railway/            # Railway deployment scripts
│   ├── setup-staging-db.py # ZeroDB setup
│   └── seed-staging-data.py # Test data seeding
├── Dockerfile              # Backend Docker image
├── railway.json            # Railway configuration
├── railway.toml            # Railway build config
└── README.md               # This file
```

### API Endpoints

Key backend endpoints:

- **Authentication:** `/api/auth/login`, `/api/auth/register`, `/api/auth/refresh`
- **Events:** `/api/events`, `/api/events/{id}`, `/api/events/{id}/rsvp`
- **Applications:** `/api/applications`, `/api/applications/{id}`
- **Payments:** `/api/payments/checkout`, `/api/payments/subscriptions`
- **Search:** `/api/search/semantic`, `/api/search/events`
- **Training:** `/api/training/sessions`, `/api/training/chat`
- **Health:** `/api/health`, `/api/health/detailed`
- **Metrics:** `/metrics` (Prometheus format)

See API documentation at `/docs` (development only).

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test category
pytest backend/tests/test_auth.py
pytest backend/tests/test_events.py

# Run integration tests
pytest backend/tests/ -m integration

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm test

# E2E tests
npm run test:e2e

# Coverage report
npm run test:coverage

# Watch mode
npm test -- --watch
```

### Load Testing

```bash
# Run load tests (if configured)
cd load-tests
locust -f locustfile.py
```

### Test Coverage Goals

- Backend: 80% minimum coverage
- Frontend: 70% minimum coverage
- Integration tests for all critical paths

---

## Documentation

### Development Guides

- [Environment Configuration](docs/environments.md) - Development, staging, production environments
- [Staging Setup](docs/deployment/staging-setup.md) - Complete staging deployment guide
- [Privacy & GDPR](docs/privacy/) - Data protection and compliance
- [Security](docs/security/) - Security features and best practices

### API Documentation

- **Development:** http://localhost:8000/docs (Swagger UI)
- **Development:** http://localhost:8000/redoc (ReDoc)
- **Note:** API docs disabled in production for security

### Scripts Documentation

#### Railway Scripts

Located in `scripts/railway/`:

- **setup-staging.sh** - Initial staging environment setup
- **deploy-staging.sh** - Deploy backend to staging
- **verify-staging.sh** - Verify staging deployment health

#### Database Scripts

- **setup-staging-db.py** - Create ZeroDB staging collections
- **seed-staging-data.py** - Load test data into staging

Usage:
```bash
# Setup database
export PYTHON_ENV=staging
export ZERODB_API_KEY=your-key
python scripts/setup-staging-db.py

# Seed test data
python scripts/seed-staging-data.py
```

---

## Environment Variables

### Required Variables

**Backend:**
```bash
PYTHON_ENV=development|staging|production
ZERODB_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
STRIPE_SECRET_KEY=sk_test_or_live_...
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

See [Environment Configuration](docs/environments.md) for complete variable reference.

---

## Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run tests: `pytest` (backend) and `npm test` (frontend)
4. Commit changes: `git commit -m "feat: your feature"`
5. Push branch: `git push origin feature/your-feature`
6. Create pull request

### Code Style

**Backend:**
- Follow PEP 8
- Use type hints
- Format with `black`
- Lint with `flake8`

**Frontend:**
- Use TypeScript
- Follow Next.js conventions
- Format with Prettier
- Lint with ESLint

### Commit Conventions

Follow conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

---

## Troubleshooting

### Common Issues

#### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.9+

# Verify virtual environment
which python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Redis connection errors

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Start Redis (if needed)
redis-server

# Check Redis URL in .env
echo $REDIS_URL
```

#### ZeroDB connection errors

```bash
# Verify API key
echo $ZERODB_API_KEY

# Test connection
python -c "from backend.services.zerodb_service import ZeroDBService; z = ZeroDBService(); print('Connected')"
```

#### Staging deployment issues

See [Troubleshooting section](docs/deployment/staging-setup.md#troubleshooting) in Staging Setup Guide.

### Getting Help

- Check [Documentation](docs/)
- Review [GitHub Issues](https://github.com/your-org/wwmaa/issues)
- Contact development team

---

## License

[Your License Here]

---

## Contact

- **Website:** https://wwmaa.com
- **Email:** info@wwmaa.com
- **GitHub:** https://github.com/your-org/wwmaa

---

## Acknowledgments

Built with FastAPI, Next.js, Railway, and modern DevOps practices.

---

**Last Updated:** 2025-01-10
