# Contributing to WWMAA

Thank you for your interest in contributing to the WWMAA (Worldwide Minority Advertising Agencies) project! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Commit Message Guidelines](#commit-message-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Documentation](#documentation)
10. [Getting Help](#getting-help)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, identity, or experience level.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept responsibility for mistakes
- Prioritize what's best for the community

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling, insulting/derogatory comments, or personal attacks
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** installed
- **Git** installed and configured
- **Redis** (for integration tests)
- A **GitHub account**
- Code editor (VS Code, PyCharm, etc.)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/wwmaa.git
   cd wwmaa
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/wwmaa.git
   ```

### Set Up Development Environment

#### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Install development dependencies
pip install black flake8 mypy isort pytest pytest-cov
```

#### Frontend Setup

```bash
# Install dependencies
npm install

# Install development dependencies (already included)
npm install --save-dev @testing-library/react @testing-library/jest-dom jest
```

#### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=sqlite:///./wwmaa.db

# Authentication
SECRET_KEY=your-secret-key-here

# ZeroDB
ZERODB_API_KEY=your-zerodb-api-key
ZERODB_EMAIL=your-email@example.com
ZERODB_PASSWORD=your-password

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI (optional)
OPENAI_API_KEY=your-openai-api-key
```

### Verify Setup

```bash
# Backend tests
pytest backend/tests/ -v

# Frontend tests
npm test

# Linting
flake8 backend/
black --check backend/
npm run lint
```

---

## Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming Conventions**:
- `feature/` - New features (e.g., `feature/user-authentication`)
- `fix/` - Bug fixes (e.g., `fix/login-error`)
- `docs/` - Documentation changes (e.g., `docs/api-guide`)
- `refactor/` - Code refactoring (e.g., `refactor/payment-service`)
- `test/` - Test improvements (e.g., `test/integration-coverage`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

### 2. Make Your Changes

1. **Write code** following our coding standards
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run linters** to check code quality
5. **Run tests** to ensure nothing breaks

### 3. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add user authentication endpoint"
```

See [Commit Message Guidelines](#commit-message-guidelines) for format.

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create a Pull Request

1. Go to your fork on GitHub
2. Click "Compare & pull request"
3. Fill out the PR template
4. Wait for CI checks to pass
5. Request review from maintainers

---

## Coding Standards

### Python (Backend)

#### Style Guide

Follow [PEP 8](https://pep8.org/) with these modifications:
- **Line length**: 120 characters (not 79)
- **String quotes**: Double quotes preferred
- **Imports**: Use isort for consistent ordering

#### Code Formatting

Use **Black** for automatic formatting:

```bash
# Format all Python files
black backend/

# Check formatting without changes
black --check backend/
```

#### Import Sorting

Use **isort** for import organization:

```bash
# Sort imports
isort backend/

# Check import order
isort --check-only backend/
```

#### Linting

Use **flake8** for style enforcement:

```bash
# Run flake8
flake8 backend/

# With detailed output
flake8 backend/ --count --statistics --show-source
```

#### Type Hints

Use **mypy** for type checking:

```bash
# Run type checking
mypy backend/

# Ignore missing imports (configured in mypy.ini)
mypy backend/ --ignore-missing-imports
```

#### Example: Well-Formatted Python Code

```python
"""
User authentication service module.

This module provides functions for user authentication, token generation,
and password management.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import settings
from backend.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Raises:
        ValueError: If token data is invalid
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    return encoded_jwt
```

### TypeScript/JavaScript (Frontend)

#### Style Guide

Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) with TypeScript extensions.

#### Code Formatting

Use **ESLint** for linting:

```bash
# Run ESLint
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

#### Type Checking

Use **TypeScript compiler**:

```bash
# Run type checking
npm run typecheck
```

#### Example: Well-Formatted TypeScript Code

```typescript
/**
 * User authentication hook for managing login state.
 */

import { useState, useCallback } from 'react';
import { useRouter } from 'next/router';

interface User {
  id: string;
  email: string;
  name: string;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface UseAuthReturn {
  user: User | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

/**
 * Custom hook for user authentication.
 *
 * @returns Authentication state and methods
 */
export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const userData = await response.json();
      setUser(userData);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  const logout = useCallback(async () => {
    setUser(null);
    router.push('/login');
  }, [router]);

  return { user, login, logout, isLoading, error };
};
```

---

## Testing Requirements

All contributions must include appropriate tests. We maintain a **minimum of 80% code coverage**.

### Backend Testing

#### Unit Tests

Write unit tests for business logic, utilities, and services:

```python
"""Tests for authentication service."""

import pytest
from unittest.mock import Mock, patch

from backend.services.auth_service import verify_password, create_access_token


def test_verify_password_success():
    """Test password verification with correct password."""
    hashed = "$2b$12$abc123..."  # Mock hashed password

    with patch('backend.services.auth_service.pwd_context.verify') as mock_verify:
        mock_verify.return_value = True
        result = verify_password("password123", hashed)

    assert result is True
    mock_verify.assert_called_once_with("password123", hashed)


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "user@example.com"}
    token = create_access_token(data)

    assert token is not None
    assert isinstance(token, str)
```

#### Integration Tests

Write integration tests for API endpoints and service interactions:

```python
"""Integration tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_login_endpoint_success(client):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

#### Running Backend Tests

```bash
# All tests
pytest backend/tests/ -v

# Unit tests only
pytest backend/tests/ -v --ignore=backend/tests/test_integration/

# Integration tests only
pytest backend/tests/test_integration/ -v

# With coverage
pytest backend/tests/ -v --cov=backend --cov-report=html

# Specific test
pytest backend/tests/test_auth_service.py::test_verify_password_success -v
```

### Frontend Testing

#### Component Tests

Write tests for React components using React Testing Library:

```typescript
/**
 * Tests for LoginForm component.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('renders login form fields', () => {
    render(<LoginForm onSubmit={jest.fn()} />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('submits form with valid credentials', async () => {
    const mockSubmit = jest.fn();
    render(<LoginForm onSubmit={mockSubmit} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');

    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });

  it('displays error for invalid email', async () => {
    render(<LoginForm onSubmit={jest.fn()} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'invalid-email');
    fireEvent.blur(screen.getByLabelText(/email/i));

    await waitFor(() => {
      expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
    });
  });
});
```

#### Running Frontend Tests

```bash
# All tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage

# Specific test
npm test -- LoginForm.test.tsx
```

### Test Organization

Use pytest markers to organize tests:

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
@pytest.mark.requires_redis
def test_integration_with_redis():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

Run specific test groups:

```bash
# Run only unit tests
pytest -m unit

# Run tests except slow ones
pytest -m "not slow"

# Run integration tests that require Redis
pytest -m "integration and requires_redis"
```

---

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies

### Scope (Optional)

The scope indicates which part of the codebase is affected:

- `auth`: Authentication
- `events`: Event management
- `payments`: Payment processing
- `search`: Search functionality
- `api`: API changes
- `ui`: User interface
- `config`: Configuration changes

### Examples

```bash
# Feature
git commit -m "feat(auth): add OAuth2 authentication support"

# Bug fix
git commit -m "fix(events): correct timezone handling in event creation"

# Documentation
git commit -m "docs(api): update API endpoint documentation"

# Test
git commit -m "test(payments): add integration tests for Stripe webhooks"

# Breaking change
git commit -m "feat(api)!: change user authentication endpoint

BREAKING CHANGE: /api/login is now /api/auth/login"
```

### Commit Message Best Practices

1. **Use imperative mood**: "add feature" not "added feature"
2. **Keep subject under 72 characters**
3. **Capitalize subject line**
4. **No period at end of subject**
5. **Separate subject from body with blank line**
6. **Wrap body at 72 characters**
7. **Explain what and why, not how**

---

## Pull Request Process

### Before Creating a PR

1. **Update your branch** with latest main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Run all checks locally**:
   ```bash
   # Backend
   black backend/
   isort backend/
   flake8 backend/
   pytest backend/tests/ -v --cov=backend

   # Frontend
   npm run lint -- --fix
   npm run typecheck
   npm test
   ```

3. **Ensure tests pass** and coverage is maintained

4. **Update documentation** if needed

### Creating the PR

1. **Push your branch**:
   ```bash
   git push origin your-branch
   ```

2. **Open PR on GitHub**:
   - Go to your fork
   - Click "Compare & pull request"
   - Select base: `main` and compare: `your-branch`

3. **Fill out PR template**:

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

Add screenshots for UI changes.

## Related Issues

Closes #123
```

### PR Review Process

1. **Automated checks** run (CI pipeline)
2. **Reviewers assigned** by maintainers
3. **Address feedback**:
   ```bash
   # Make changes
   git add .
   git commit -m "fix: address review feedback"
   git push origin your-branch
   ```
4. **Approval required** (minimum 1)
5. **Merge** by maintainer

### After Merge

1. **Delete your branch**:
   ```bash
   git checkout main
   git pull upstream main
   git branch -d your-branch
   git push origin --delete your-branch
   ```

2. **Update your fork**:
   ```bash
   git push origin main
   ```

---

## CI/CD Pipeline

All pull requests trigger our CI/CD pipeline. The pipeline must pass before merging.

### Pipeline Stages

1. **Backend Linting** (5-10 min)
   - flake8
   - black
   - isort
   - mypy

2. **Backend Tests** (10-20 min)
   - Unit tests
   - Integration tests
   - Coverage reporting (80% minimum)

3. **Frontend Linting** (5-10 min)
   - ESLint
   - TypeScript checking

4. **Frontend Build & Test** (10-20 min)
   - Production build
   - Jest tests
   - Coverage reporting

5. **Security Scanning** (5-10 min)
   - pip-audit
   - npm audit

### CI Status Checks

Your PR must pass these checks:
- ✅ `backend-lint`
- ✅ `backend-unit-tests`
- ✅ `backend-integration-tests`
- ✅ `frontend-lint`
- ✅ `frontend-build-test`
- ✅ `ci-status`

### Viewing CI Results

1. Go to your PR on GitHub
2. Scroll to "Checks" section
3. Click on failed check for details
4. Review logs and fix issues
5. Push new commit to re-run checks

### Common CI Failures

See [CI/CD Documentation](./CI_CD.md#troubleshooting) for troubleshooting guide.

---

## Documentation

### When to Update Documentation

Update documentation when you:
- Add new features
- Change existing functionality
- Add new API endpoints
- Modify configuration
- Change development setup

### Documentation Locations

- **API Documentation**: `docs/api/`
- **Development Guides**: `docs/development/`
- **User Guides**: `docs/user-guides/`
- **Code Comments**: In-line with code

### Documentation Style

- Use **Markdown** format
- Include **code examples**
- Add **screenshots** for UI
- Keep **up-to-date** with code
- Use **clear, concise** language

---

## Getting Help

### Resources

- **Documentation**: `/docs`
- **CI/CD Guide**: `/docs/development/CI_CD.md`
- **API Documentation**: `/docs/api`
- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions

### Contact

- **Email**: dev@wwmaa.org (if applicable)
- **Slack**: #development channel (if applicable)
- **GitHub**: Open an issue or discussion

---

## License

By contributing to WWMAA, you agree that your contributions will be licensed under the same license as the project.

---

## Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes
- Project documentation (for significant contributions)

---

**Thank you for contributing to WWMAA!**

We appreciate your time and effort in making this project better. Every contribution, no matter how small, makes a difference.

---

**Last Updated**: 2025-11-10
**Version**: 1.0.0
**Maintained By**: WWMAA Development Team
