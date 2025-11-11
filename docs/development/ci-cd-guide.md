# CI/CD Pipeline Guide

## Overview

This guide provides comprehensive information about the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the WWMAA project.

## Table of Contents

1. [Pipeline Architecture](#pipeline-architecture)
2. [GitHub Actions Workflows](#github-actions-workflows)
3. [Running Checks Locally](#running-checks-locally)
4. [Debugging Failed Checks](#debugging-failed-checks)
5. [Code Coverage Requirements](#code-coverage-requirements)
6. [Updating Dependencies](#updating-dependencies)
7. [Best Practices](#best-practices)

---

## Pipeline Architecture

### Overview

The WWMAA CI/CD pipeline is built using GitHub Actions and consists of multiple workflows:

- **Main CI Pipeline** (`.github/workflows/ci.yml`)
- **Frontend CI Pipeline** (`.github/workflows/frontend-ci.yml`)
- **Accessibility Tests** (`.github/workflows/accessibility-tests.yml`)

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│                     CI Pipeline Flow                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Trigger: Push to main or PR creation                    │
│                                                              │
│  2. Parallel Execution:                                      │
│     ├── Backend Lint (flake8, black, isort, mypy)          │
│     └── Frontend Lint (ESLint, TypeScript)                  │
│                                                              │
│  3. Parallel Testing (if lint passes):                      │
│     ├── Backend Unit Tests + Coverage                       │
│     ├── Backend Integration Tests + Coverage                │
│     └── Frontend Build + Tests + Coverage                   │
│                                                              │
│  4. Security Scanning:                                       │
│     ├── Python Dependencies (pip-audit)                     │
│     └── Node Dependencies (npm audit)                       │
│                                                              │
│  5. Status Check:                                            │
│     └── Aggregate results and post PR comment               │
│                                                              │
│  6. Notifications (on failure):                              │
│     └── Slack notification (if configured)                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions Workflows

### Main CI Pipeline

**File:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch

**Jobs:**

1. **backend-lint**
   - Runs flake8, black, isort, and mypy
   - Fails fast on linting errors
   - Timeout: 10 minutes

2. **backend-unit-tests**
   - Runs pytest with coverage
   - Matrix: Python 3.11
   - Parallel execution with pytest-xdist
   - Timeout: 20 minutes
   - Coverage target: 80%

3. **backend-integration-tests**
   - Runs integration tests with Redis service
   - Tests external API integrations
   - Timeout: 20 minutes

4. **frontend-lint**
   - Runs ESLint and TypeScript type checking
   - Timeout: 10 minutes

5. **frontend-build-test**
   - Builds Next.js application
   - Runs Jest tests with coverage
   - Timeout: 20 minutes
   - Coverage target: 75%

6. **security-scan**
   - Scans Python and Node dependencies
   - Reports vulnerabilities
   - Non-blocking (continues on error)

7. **ci-status**
   - Aggregates all check results
   - Posts summary comment on PR
   - Fails if any required check fails

8. **notify-failure**
   - Sends Slack notification on failure
   - Only runs on main branch failures

### Frontend CI Pipeline

**File:** `.github/workflows/frontend-ci.yml`

**Triggers:**
- Changes to frontend files only (`app/`, `components/`, `lib/`, `hooks/`, etc.)

**Jobs:**
1. Lint & Format Check
2. TypeScript Type Check
3. Unit Tests
4. Build Verification
5. Bundle Size Analysis

### Accessibility Tests

**File:** `.github/workflows/accessibility-tests.yml`

**Triggers:**
- Push to main or PR
- Changes to frontend files

**Tests:**
- Jest-axe integration
- WCAG 2.1 Level AA compliance
- Aria attribute validation

---

## Running Checks Locally

### Prerequisites

```bash
# Python environment
python --version  # Should be 3.11+
pip install -r backend/requirements.txt

# Node environment
node --version  # Should be 18+ or 20
npm install

# Optional: Pre-commit hooks
pip install pre-commit
pre-commit install
```

### Backend Checks

#### 1. Linting

```bash
# Run all linters
cd backend

# Flake8
flake8 . --config=../.flake8

# Black (check only)
black --check . --config=../pyproject.toml

# Black (fix)
black . --config=../pyproject.toml

# isort (check only)
isort --check-only . --settings-path=../pyproject.toml

# isort (fix)
isort . --settings-path=../pyproject.toml

# MyPy
mypy . --config-file=../mypy.ini
```

#### 2. Unit Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# Run specific test file
pytest backend/tests/test_auth.py -v

# Run specific test
pytest backend/tests/test_auth.py::test_login -v

# Run tests in parallel
pytest backend/tests/ -n auto

# Run only unit tests (exclude integration)
pytest backend/tests/ -v -m "not integration"
```

#### 3. Integration Tests

```bash
# Ensure Redis is running
redis-cli ping  # Should return "PONG"

# Run integration tests
pytest backend/tests/test_integration/ -v

# Run with coverage
pytest backend/tests/test_integration/ -v --cov=backend --cov-report=term-missing
```

### Frontend Checks

#### 1. Linting

```bash
# ESLint
npm run lint

# ESLint with auto-fix
npm run lint -- --fix

# TypeScript type check
npm run typecheck
```

#### 2. Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- __tests__/components/footer.test.tsx

# Run accessibility tests only
npm run test:a11y
```

#### 3. Build

```bash
# Build for production
npm run build

# Start production server
npm start

# Run development server
npm run dev
```

### Pre-commit Hooks

Pre-commit hooks automatically run checks before each commit:

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks for a commit (not recommended)
git commit -m "message" --no-verify

# Update hook versions
pre-commit autoupdate
```

---

## Debugging Failed Checks

### Common Issues and Solutions

#### 1. Linting Failures

**Problem:** Flake8 or ESLint errors

**Solution:**
```bash
# Backend
black backend/  # Auto-fix formatting
isort backend/  # Auto-fix import order

# Frontend
npm run lint -- --fix  # Auto-fix ESLint issues
```

#### 2. Type Checking Failures

**Problem:** MyPy or TypeScript errors

**Solution:**
```bash
# Backend - Review type hints
mypy backend/ --config-file=mypy.ini

# Frontend - Review TypeScript types
npm run typecheck
```

#### 3. Test Failures

**Problem:** Failing tests

**Solution:**
```bash
# Run failing test in isolation
pytest backend/tests/test_file.py::test_function -v

# Enable verbose output
pytest backend/tests/ -vv

# Show local variables
pytest backend/tests/ --showlocals

# Debug with pdb
pytest backend/tests/ --pdb
```

#### 4. Coverage Failures

**Problem:** Coverage below 80%

**Solution:**
```bash
# Generate HTML coverage report
pytest backend/tests/ --cov=backend --cov-report=html

# Open htmlcov/index.html to see uncovered lines
open htmlcov/index.html

# Add tests for uncovered code
```

#### 5. Build Failures

**Problem:** Next.js build fails

**Solution:**
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check environment variables
cp .env.example .env.local

# Build again
npm run build
```

### Viewing GitHub Actions Logs

1. Go to the **Actions** tab in the GitHub repository
2. Click on the failed workflow run
3. Click on the failed job
4. Expand the failed step to view logs
5. Download logs for offline analysis (optional)

### Local Environment Matching CI

To match the CI environment exactly:

```bash
# Backend
docker run -it python:3.11-slim bash
pip install -r requirements.txt
pytest backend/tests/

# Frontend
docker run -it node:20-alpine sh
npm ci
npm run build
npm test
```

---

## Code Coverage Requirements

### Coverage Targets

| Component | Minimum Coverage | Target Coverage |
|-----------|------------------|-----------------|
| Backend   | 80%              | 85%+            |
| Frontend  | 75%              | 80%+            |
| New Code  | 70%              | 80%+            |

### Codecov Integration

**Configuration:** `.codecov.yml`

**Features:**
- Automatic PR comments with coverage changes
- Project coverage status checks
- Patch coverage (new code only)
- Flag-based coverage (backend, frontend, tests)

**Coverage Reports:**
- Uploaded automatically in CI
- View on [codecov.io](https://codecov.io)
- Check PR comments for coverage changes

### Improving Coverage

1. **Identify uncovered code:**
   ```bash
   pytest backend/tests/ --cov=backend --cov-report=term-missing
   ```

2. **Write tests for uncovered lines:**
   - Focus on critical paths first
   - Test error handling
   - Test edge cases

3. **Mark code as no-cover (only when justified):**
   ```python
   def debug_function():  # pragma: no cover
       # Only used in development
       pass
   ```

---

## Updating Dependencies

### Backend Dependencies

#### Regular Updates

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements.txt
pip freeze > backend/requirements.txt
```

#### Security Updates

```bash
# Run pip-audit
pip-audit -r backend/requirements.txt

# Fix vulnerabilities
pip install --upgrade vulnerable-package

# Update requirements.txt
pip freeze > backend/requirements.txt
```

### Frontend Dependencies

#### Regular Updates

```bash
# Check for outdated packages
npm outdated

# Update specific package
npm update package-name

# Update all packages (minor and patch)
npm update

# Update all packages (including major)
npx npm-check-updates -u
npm install
```

#### Security Updates

```bash
# Check for vulnerabilities
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Fix vulnerabilities (with breaking changes)
npm audit fix --force
```

### Automated Dependency Updates

**Dependabot Configuration:**

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

---

## Best Practices

### 1. Commit Frequently

- Make small, focused commits
- Run tests before committing
- Use pre-commit hooks

### 2. Write Tests First (TDD)

- Write failing test
- Implement feature
- Ensure test passes
- Refactor

### 3. Keep CI Fast

- Use caching for dependencies
- Run tests in parallel
- Split long-running tests

### 4. Monitor CI Performance

- Track build times
- Identify slow tests
- Optimize as needed

### 5. Fix Broken Main Branch Immediately

- Revert breaking commits
- Fix forward quickly
- Communicate with team

### 6. Review CI Logs

- Don't ignore warnings
- Fix deprecation warnings
- Update deprecated dependencies

### 7. Keep Configuration in Sync

- Update `.flake8`, `pyproject.toml`, etc.
- Match local and CI configurations
- Document configuration changes

### 8. Use Feature Flags

- Deploy incomplete features behind flags
- Enable features gradually
- Roll back without code changes

### 9. Maintain Documentation

- Update docs with code changes
- Document CI/CD changes
- Keep runbooks current

### 10. Security First

- Never commit secrets
- Use GitHub Secrets for sensitive data
- Rotate secrets regularly
- Run security scans

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [ESLint Documentation](https://eslint.org/)
- [Pre-commit Documentation](https://pre-commit.com/)

---

## Support

For issues or questions about the CI/CD pipeline:

1. Check this documentation first
2. Review GitHub Actions logs
3. Ask in team Slack channel
4. Create GitHub issue for persistent problems

---

**Last Updated:** November 10, 2025
**Maintainer:** WWMAA Development Team
