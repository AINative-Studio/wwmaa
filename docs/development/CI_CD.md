# CI/CD Pipeline Documentation

## Overview

The WWMAA project uses GitHub Actions for continuous integration and continuous deployment. This document outlines our CI/CD pipeline, including workflows, testing strategies, and best practices.

## Table of Contents

1. [CI Pipeline Overview](#ci-pipeline-overview)
2. [Workflow Files](#workflow-files)
3. [Pipeline Stages](#pipeline-stages)
4. [Configuration Files](#configuration-files)
5. [Branch Protection Rules](#branch-protection-rules)
6. [Environment Variables and Secrets](#environment-variables-and-secrets)
7. [Local Development](#local-development)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## CI Pipeline Overview

Our CI pipeline is designed to ensure code quality, security, and reliability on every commit. The pipeline automatically runs on:

- **Push to `main` branch**: Full CI pipeline validation
- **Pull requests to `main`**: Full CI pipeline validation with PR comments
- **Documentation changes**: Skipped to save resources

### Pipeline Architecture

```
┌─────────────────┐
│  Code Commit    │
└────────┬────────┘
         │
    ┌────▼────────────────────────────────────────┐
    │                                             │
    │  Parallel Execution (Fail Fast)             │
    │                                             │
    ├──────────────┬──────────────┬──────────────┤
    │              │              │              │
┌───▼───┐    ┌────▼────┐   ┌────▼────┐   ┌─────▼─────┐
│Backend│    │Backend  │   │Frontend │   │ Frontend  │
│Lint   │    │Tests    │   │Lint     │   │Build/Test │
└───┬───┘    └────┬────┘   └────┬────┘   └─────┬─────┘
    │             │             │              │
    │             │             │              │
    └─────────────┴─────────────┴──────────────┘
                  │
            ┌─────▼──────┐
            │ CI Status  │
            │   Check    │
            └─────┬──────┘
                  │
          ┌───────▼────────┐
          │  PR Comment /  │
          │ Slack Notify   │
          └────────────────┘
```

---

## Workflow Files

### Main CI Workflow

**File**: `.github/workflows/ci.yml`

This is the primary CI pipeline that runs all quality checks, tests, and builds.

**Triggers**:
- Push to `main` branch
- Pull requests targeting `main`
- Ignores: `*.md`, `docs/**`, `LICENSE`, `.gitignore`

**Jobs**:
1. `backend-lint`: Python linting (flake8, black, isort, mypy)
2. `backend-unit-tests`: Unit test execution with coverage
3. `backend-integration-tests`: Integration tests with Redis
4. `frontend-lint`: ESLint and TypeScript checking
5. `frontend-build-test`: Next.js build and Jest tests
6. `security-scan`: Security vulnerability scanning
7. `ci-status`: Final status aggregation
8. `notify-failure`: Slack notifications on failure

### Accessibility Tests Workflow

**File**: `.github/workflows/accessibility-tests.yml`

Runs accessibility tests and Lighthouse audits.

---

## Pipeline Stages

### Stage 1: Backend Linting (Parallel)

**Duration**: ~5-10 minutes

Runs Python code quality checks to ensure adherence to coding standards.

**Checks**:
- **flake8**: PEP 8 style guide enforcement
- **black**: Code formatting verification (120 char line length)
- **isort**: Import statement sorting
- **mypy**: Static type checking (advisory only)

**Configuration Files**:
- `.flake8`
- `pyproject.toml` (black, isort)
- `mypy.ini`

**Commands**:
```bash
flake8 backend/ --max-line-length=120 --count --statistics
black --check backend/ --line-length=120
isort --check-only backend/ --line-length=120 --profile=black
mypy backend/ --ignore-missing-imports
```

**Failure Impact**: Blocks merge if flake8, black, or isort fail. mypy is advisory only.

---

### Stage 2: Backend Unit Tests (After Linting)

**Duration**: ~10-20 minutes

Runs all unit tests with code coverage reporting.

**Features**:
- Parallel test execution (`pytest-xdist`)
- Code coverage tracking (target: 80%)
- JUnit XML report generation
- HTML coverage reports
- Codecov integration

**Configuration**:
- `pytest.ini`
- `pyproject.toml` (coverage settings)

**Commands**:
```bash
pytest backend/tests/ \
  -v \
  --cov=backend \
  --cov-report=xml \
  --cov-report=html \
  --cov-report=term-missing \
  --junitxml=backend/test-results/junit.xml \
  --maxfail=5 \
  -n auto \
  --ignore=backend/tests/test_integration/
```

**Environment Variables Required**:
- `TESTING=true`
- `DATABASE_URL=sqlite:///./test.db`
- `SECRET_KEY=test-secret-key-for-ci`
- `ZERODB_API_KEY` (secret)
- `ZERODB_EMAIL` (secret)
- `ZERODB_PASSWORD` (secret)

**Artifacts**:
- Test results (JUnit XML)
- Coverage reports (XML, HTML)
- Retention: 30 days

**Failure Impact**: Blocks merge if tests fail or coverage < 80%

---

### Stage 3: Backend Integration Tests (After Linting)

**Duration**: ~10-20 minutes

Runs integration tests that require external services.

**Services**:
- **Redis**: In-memory cache (Docker service)

**Features**:
- Real service dependencies
- Database integration testing
- API integration testing
- Coverage appending to unit test coverage

**Commands**:
```bash
pytest backend/tests/test_integration/ \
  -v \
  --cov=backend \
  --cov-report=xml \
  --cov-append \
  --junitxml=backend/test-results/integration-junit.xml
```

**Environment Variables Required**:
- All unit test variables
- `REDIS_URL=redis://localhost:6379`
- `OPENAI_API_KEY` (secret, optional)

**Failure Impact**: Blocks merge if integration tests fail

---

### Stage 4: Frontend Linting (Parallel)

**Duration**: ~5-10 minutes

Validates TypeScript/JavaScript code quality.

**Checks**:
- **ESLint**: JavaScript/TypeScript linting
- **TypeScript**: Type checking (`tsc --noEmit`)

**Commands**:
```bash
npm run lint
npm run typecheck
```

**Failure Impact**: Blocks merge if linting or type checking fails

---

### Stage 5: Frontend Build & Test (After Linting)

**Duration**: ~10-20 minutes

Builds the Next.js application and runs frontend tests.

**Features**:
- Production build validation
- Next.js cache optimization
- Jest test execution
- Coverage reporting to Codecov

**Commands**:
```bash
npm run build
npm test -- --coverage --maxWorkers=2
```

**Environment Variables**:
- `NODE_ENV=production`
- `NEXT_TELEMETRY_DISABLED=1`
- `CI=true`

**Artifacts**:
- Build output (`.next/`, `out/`)
- Test coverage reports
- Retention: 7-30 days

**Failure Impact**: Blocks merge if build fails or tests fail

---

### Stage 6: Security Scanning (Parallel)

**Duration**: ~5-10 minutes

Scans dependencies for known security vulnerabilities.

**Scanners**:
- **pip-audit**: Python dependency vulnerability scanning
- **npm audit**: Node.js dependency vulnerability scanning

**Commands**:
```bash
pip-audit -r backend/requirements.txt --format json
npm audit --json
```

**Failure Impact**: Advisory only (continues on error)

**Artifacts**:
- Security scan results (JSON)
- Retention: 30 days

---

### Stage 7: CI Status Check

**Duration**: ~1 minute

Aggregates all job results and posts status to PR.

**Functions**:
1. Checks all job results
2. Posts summary comment to PR
3. Fails if any required job failed

**PR Comment Format**:
```
## ✅ CI Pipeline Status

All CI checks passed!

- Backend Linting: success
- Backend Unit Tests: success
- Backend Integration Tests: success
- Frontend Linting: success
- Frontend Build & Test: success
```

---

### Stage 8: Failure Notifications (On Failure)

**Duration**: ~1 minute

Sends notifications when CI fails on main branch.

**Notification Channels**:
- Slack (if `SLACK_WEBHOOK_URL` configured)

**Slack Message Includes**:
- Repository name
- Branch name
- Commit message and author
- Link to GitHub Actions run

---

## Configuration Files

### Pytest Configuration

**Files**: `pytest.ini`, `pyproject.toml`

Key settings:
- Test discovery patterns
- Coverage targets (80%)
- Markers for test organization
- Asyncio mode
- Parallel execution

**Test Markers**:
```python
@pytest.mark.slow          # Slow-running tests
@pytest.mark.integration   # Integration tests
@pytest.mark.unit          # Unit tests
@pytest.mark.requires_api  # Requires external API
@pytest.mark.requires_redis # Requires Redis
@pytest.mark.security      # Security-related tests
```

### Flake8 Configuration

**File**: `.flake8`

Key settings:
- Max line length: 120
- Max complexity: 15
- Ignores: E203, E501, W503 (black compatibility)
- Per-file ignores for `__init__.py` and test files

### Black Configuration

**File**: `pyproject.toml`

Key settings:
- Line length: 120
- Target version: Python 3.11
- Excludes: venv, cache directories, migrations

### isort Configuration

**File**: `pyproject.toml`

Key settings:
- Profile: black (compatibility)
- Line length: 120
- Known first party: `backend`
- Section ordering: FUTURE, STDLIB, THIRDPARTY, FIRSTPARTY, LOCALFOLDER

### MyPy Configuration

**File**: `mypy.ini`

Key settings:
- Python version: 3.11
- Ignore missing imports: True
- Strict mode: Partially enabled
- Per-module ignores for test files

---

## Branch Protection Rules

Configure these in GitHub repository settings under **Settings → Branches → Branch protection rules**.

### Required for `main` Branch

1. **Require status checks to pass before merging**
   - Required checks:
     - `backend-lint`
     - `backend-unit-tests`
     - `backend-integration-tests`
     - `frontend-lint`
     - `frontend-build-test`
     - `ci-status`

2. **Require branches to be up to date before merging**
   - Ensures PR has latest main branch changes

3. **Require pull request reviews before merging**
   - Minimum: 1 approval
   - Dismiss stale reviews when new commits are pushed

4. **Require linear history** (optional)
   - Prevents merge commits
   - Enforces rebase or squash merging

5. **Do not allow bypassing the above settings**
   - Admins must follow the same rules

6. **Restrict pushes**
   - Only allow through pull requests

### How to Configure

1. Go to GitHub repository
2. Settings → Branches
3. Add rule for `main` branch
4. Enable all required checks listed above
5. Save changes

---

## Environment Variables and Secrets

### GitHub Secrets Configuration

Configure in **Settings → Secrets and variables → Actions**.

#### Required Secrets

| Secret Name | Purpose | Source |
|------------|---------|--------|
| `ZERODB_API_KEY` | ZeroDB API authentication | ZeroDB dashboard |
| `ZERODB_EMAIL` | ZeroDB account email | ZeroDB account |
| `ZERODB_PASSWORD` | ZeroDB account password | ZeroDB account |
| `CODECOV_TOKEN` | Code coverage reporting | Codecov.io |
| `OPENAI_API_KEY` | OpenAI API (optional) | OpenAI dashboard |
| `SLACK_WEBHOOK_URL` | Slack notifications (optional) | Slack app settings |

#### How to Add Secrets

1. Go to repository Settings
2. Secrets and variables → Actions
3. Click "New repository secret"
4. Add secret name and value
5. Click "Add secret"

### Environment Variables

Set in workflow files or job steps:

```yaml
env:
  TESTING: true
  DATABASE_URL: sqlite:///./test.db
  SECRET_KEY: test-secret-key-for-ci
  REDIS_URL: redis://localhost:6379
  NODE_ENV: production
  NEXT_TELEMETRY_DISABLED: 1
  CI: true
```

---

## Local Development

### Running Tests Locally

#### Backend Tests

```bash
# All tests
pytest backend/tests/ -v

# Unit tests only
pytest backend/tests/ -v --ignore=backend/tests/test_integration/

# Integration tests only
pytest backend/tests/test_integration/ -v

# With coverage
pytest backend/tests/ -v --cov=backend --cov-report=html

# Parallel execution
pytest backend/tests/ -v -n auto

# Specific test file
pytest backend/tests/test_auth_routes.py -v

# Specific test function
pytest backend/tests/test_auth_routes.py::test_login -v
```

#### Frontend Tests

```bash
# All tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage

# Specific test file
npm test -- EventCard.test.tsx
```

### Running Linters Locally

#### Backend Linting

```bash
# Run all linters
flake8 backend/
black --check backend/
isort --check-only backend/
mypy backend/

# Auto-fix formatting
black backend/
isort backend/
```

#### Frontend Linting

```bash
# Run ESLint
npm run lint

# Auto-fix ESLint issues
npm run lint -- --fix

# TypeScript type checking
npm run typecheck
```

### Building Locally

#### Backend

```bash
# No build step required for Python
# Just run the application
uvicorn backend.main:app --reload
```

#### Frontend

```bash
# Development build
npm run dev

# Production build
npm run build
npm start
```

---

## Troubleshooting

### Common Issues

#### 1. Linting Failures

**Problem**: flake8 or black reports formatting errors

**Solution**:
```bash
# Auto-fix with black
black backend/

# Auto-fix imports with isort
isort backend/

# Check what black would change
black --check backend/ --diff
```

#### 2. Test Failures

**Problem**: Tests pass locally but fail in CI

**Possible causes**:
- Missing environment variables
- Different Python/Node versions
- Timing issues in async tests
- Database state issues

**Solution**:
```bash
# Check Python version
python --version  # Should be 3.11+

# Check Node version
node --version  # Should be 18+

# Run tests in same environment as CI
TESTING=true pytest backend/tests/ -v

# Clean test artifacts
rm -rf .pytest_cache __pycache__ .mypy_cache
```

#### 3. Import Errors

**Problem**: `ModuleNotFoundError` in tests

**Solution**:
```bash
# Ensure backend is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest.ini pythonpath setting (already configured)
pytest backend/tests/ -v
```

#### 4. Coverage Below Threshold

**Problem**: Coverage drops below 80%

**Solution**:
```bash
# Generate coverage report
pytest backend/tests/ --cov=backend --cov-report=html

# Open htmlcov/index.html in browser to see uncovered lines

# Add tests for uncovered code
# Exclude unavoidable uncovered code with:
#   # pragma: no cover
```

#### 5. Dependency Installation Failures

**Problem**: pip or npm install fails

**Solution**:
```bash
# Backend: Update pip
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# Frontend: Clear cache
rm -rf node_modules package-lock.json
npm install

# Check for conflicting dependencies
pip check  # Backend
npm audit  # Frontend
```

#### 6. Redis Connection Errors (Integration Tests)

**Problem**: Integration tests fail with Redis connection errors

**Solution**:
```bash
# Start Redis locally
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine

# Check Redis is running
redis-cli ping  # Should return PONG
```

### Debugging CI Failures

1. **Check job logs**:
   - Go to Actions tab in GitHub
   - Click on failed workflow run
   - Click on failed job
   - Expand failed step

2. **Download artifacts**:
   - Scroll to bottom of workflow run
   - Download test results or coverage reports
   - Review locally

3. **Re-run jobs**:
   - Click "Re-run failed jobs" or "Re-run all jobs"
   - Useful for transient failures

4. **Enable debug logging**:
   ```yaml
   - name: Debug step
     run: |
       echo "Debug info"
       env
     if: failure()
   ```

---

## Best Practices

### For Developers

1. **Run linters before committing**:
   ```bash
   black backend/
   isort backend/
   flake8 backend/
   npm run lint -- --fix
   ```

2. **Run tests locally before pushing**:
   ```bash
   pytest backend/tests/ -v
   npm test
   ```

3. **Keep tests fast**:
   - Use mocks for external services
   - Mark slow tests with `@pytest.mark.slow`
   - Use `pytest-xdist` for parallel execution

4. **Write meaningful test names**:
   ```python
   def test_user_login_with_valid_credentials():
       # Good: descriptive name
       pass

   def test_login():
       # Bad: vague name
       pass
   ```

5. **Keep PRs small and focused**:
   - Easier to review
   - Faster CI execution
   - Easier to debug failures

6. **Add tests for new features**:
   - Unit tests for business logic
   - Integration tests for API endpoints
   - Maintain or improve coverage

### For CI Configuration

1. **Use caching aggressively**:
   - pip cache
   - npm cache
   - Next.js cache
   - Reduces CI time by 50-70%

2. **Fail fast**:
   - Run linting before tests
   - Use `--maxfail` in pytest
   - Set job timeouts

3. **Parallelize independent jobs**:
   - Backend and frontend linting run in parallel
   - Unit and integration tests run in parallel

4. **Use workflow concurrency**:
   - Cancel outdated runs when new commits pushed
   - Saves CI minutes

5. **Monitor CI metrics**:
   - Job duration trends
   - Failure rates
   - Flaky tests

6. **Keep workflows DRY**:
   - Use reusable workflows
   - Use composite actions
   - Use environment variables

### For Testing

1. **Organize tests with markers**:
   ```python
   @pytest.mark.unit
   @pytest.mark.requires_redis
   def test_redis_cache():
       pass
   ```

2. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def auth_client():
       return TestClient(app)
   ```

3. **Mock external dependencies**:
   ```python
   @patch('backend.services.stripe_service.stripe.Charge.create')
   def test_payment(mock_charge):
       mock_charge.return_value = {"id": "ch_123"}
       # Test code
   ```

4. **Test edge cases**:
   - Null/empty inputs
   - Boundary values
   - Error conditions
   - Race conditions

5. **Keep tests isolated**:
   - No dependencies between tests
   - Clean up after tests
   - Use unique test data

---

## Performance Optimization

### Current CI Performance

| Stage | Duration | Optimization |
|-------|----------|-------------|
| Backend Linting | ~5 min | Cached pip packages |
| Backend Unit Tests | ~10 min | Parallel execution, cached deps |
| Backend Integration Tests | ~10 min | Redis service, cached deps |
| Frontend Linting | ~5 min | Cached npm packages |
| Frontend Build & Test | ~10 min | Next.js cache, cached deps |
| **Total** | **~15-20 min** | Parallel execution |

### Optimization Strategies

1. **Caching**:
   - pip: `~/.cache/pip`
   - npm: `~/.npm`
   - Next.js: `.next/cache`

2. **Parallel execution**:
   - pytest: `-n auto` (uses all CPU cores)
   - Jest: `--maxWorkers=2`
   - Parallel jobs: linting and testing

3. **Incremental builds**:
   - Next.js cache
   - MyPy incremental mode

4. **Skip unnecessary runs**:
   - `paths-ignore` for docs-only changes
   - `cancel-in-progress` for outdated runs

---

## Monitoring and Alerts

### Monitoring

1. **GitHub Actions insights**:
   - Actions tab → Workflow → View insights
   - Track success rate, duration, failures

2. **Codecov dashboards**:
   - codecov.io → Project dashboard
   - Track coverage trends

3. **Slack notifications**:
   - Immediate alerts on main branch failures
   - Includes commit info and run link

### Metrics to Track

- CI success rate (target: >95%)
- Average CI duration (target: <20 minutes)
- Test coverage (target: >80%)
- Flaky test rate (target: <5%)
- Security vulnerabilities (target: 0 critical)

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Next.js Testing](https://nextjs.org/docs/testing)
- [Codecov Documentation](https://docs.codecov.com/)

---

## Support

For CI/CD issues or questions:

1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Contact the development team
4. Open an issue in the repository

---

**Last Updated**: 2025-11-10
**Version**: 1.0.0
**Maintained By**: WWMAA Development Team
