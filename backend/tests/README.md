# WWMAA Backend - Testing Documentation

## Overview

This directory contains the comprehensive test suite for the WWMAA Python backend. The test infrastructure is built using `pytest` and follows industry best practices for test organization, coverage reporting, and continuous integration.

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Test Fixtures](#test-fixtures)
- [Mocking External Services](#mocking-external-services)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

Install test dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=backend --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Approval workflow tests
pytest -m approval

# Permission tests
pytest -m permissions
```

---

## Test Structure

The test suite is organized into the following directories:

```
backend/tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── README.md                   # This file
│
├── test_unit/                  # Fast, isolated unit tests
│   ├── __init__.py
│   ├── test_approval_workflow.py
│   └── test_permissions.py
│
├── test_integration/           # Integration tests (API, workflows)
│   └── __init__.py
│
├── test_services/              # Service layer tests
│   ├── __init__.py
│   └── test_zerodb_service.py
│
├── test_utils/                 # Utility function tests
│   ├── __init__.py
│   ├── test_validators.py
│   └── test_string_utils.py
│
└── fixtures/                   # Shared test data and factories
    └── __init__.py
```

### Directory Purposes

- **test_unit/**: Fast, isolated tests for individual functions and classes
- **test_integration/**: Tests that verify interactions between components
- **test_services/**: Tests for service layer and business logic
- **test_utils/**: Tests for utility functions and helpers
- **fixtures/**: Factory functions and shared test data

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run tests in parallel (faster)
pytest -n auto

# Run specific test file
pytest tests/test_unit/test_approval_workflow.py

# Run specific test function
pytest tests/test_unit/test_approval_workflow.py::test_create_approval_workflow

# Run specific test class
pytest tests/test_unit/test_approval_workflow.py::TestApprovalWorkflow
```

### Using Test Markers

Tests are tagged with markers for easy filtering:

```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run approval workflow tests
pytest -m approval

# Run permission tests
pytest -m permissions

# Run validation tests
pytest -m validation

# Exclude slow tests
pytest -m "not slow"
```

### Available Markers

- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (slower, may require services)
- `slow`: Slow tests (database, API calls)
- `auth`: Authentication and authorization tests
- `payment`: Payment processing tests
- `email`: Email sending tests
- `database`: Database-dependent tests
- `mock`: Tests that use mocking extensively
- `approval`: Approval workflow tests
- `permissions`: Role-based permission tests
- `validation`: Data validation tests
- `utils`: Utility function tests
- `search`: Search functionality tests

---

## Test Coverage

### Coverage Requirements

- **Minimum Coverage**: 80% (enforced by CI/CD)
- **Target Coverage**: 90%+

### Running Coverage Reports

```bash
# Generate terminal coverage report
pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# Open HTML report in browser
open htmlcov/index.html

# Generate XML coverage report (for CI)
pytest --cov=backend --cov-report=xml

# Fail if coverage is below 80%
pytest --cov=backend --cov-fail-under=80
```

### Coverage Configuration

Coverage settings are configured in:
- `pytest.ini` - Main pytest configuration
- `.coveragerc` - Additional coverage settings

### Understanding Coverage Reports

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
backend/services/user.py        45      5    89%    23-27
backend/utils/validators.py    30      0   100%
-----------------------------------------------------------
TOTAL                          250     15    94%
```

- **Stmts**: Total number of statements
- **Miss**: Number of statements not executed
- **Cover**: Percentage of code covered
- **Missing**: Line numbers not covered

---

## Writing Tests

### Test File Naming

- Test files must start with `test_` or end with `_test.py`
- Test functions must start with `test_`
- Test classes must start with `Test`

Example:
```python
# test_approval_workflow.py

class TestApprovalWorkflow:
    def test_create_approval_workflow(self):
        pass
```

### Test Structure (AAA Pattern)

Use the **Arrange-Act-Assert** pattern:

```python
def test_add_approval(self):
    # Arrange: Set up test data and conditions
    workflow = ApprovalWorkflow("promo_123", "promotion")
    approver_id = "admin_001"

    # Act: Execute the code being tested
    approval = workflow.add_approval(approver_id, "state_admin")

    # Assert: Verify the results
    assert len(workflow.approvals) == 1
    assert approval["approver_id"] == approver_id
```

### Async Tests

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("num_approvals,expected_status", [
    (0, "pending"),
    (1, "pending"),
    (2, "approved"),
    (3, "approved"),
])
def test_approval_status(num_approvals, expected_status):
    workflow = ApprovalWorkflow("promo_123", "promotion")
    for i in range(num_approvals):
        workflow.add_approval(f"admin_{i}", "admin")
    assert workflow.status == expected_status
```

### Testing Exceptions

```python
def test_duplicate_approval_raises_error():
    workflow = ApprovalWorkflow("promo_123", "promotion")
    workflow.add_approval("admin_001", "admin")

    with pytest.raises(ValueError, match="already approved"):
        workflow.add_approval("admin_001", "admin")
```

---

## Test Fixtures

### What are Fixtures?

Fixtures provide reusable setup and teardown logic for tests. They are defined in `conftest.py` and automatically available to all tests.

### Using Fixtures

```python
def test_user_creation(sample_user_data):
    # sample_user_data is automatically provided by the fixture
    assert "email" in sample_user_data
    assert "first_name" in sample_user_data
```

### Available Fixtures

#### Data Fixtures

- `faker_instance`: Faker instance for generating test data
- `sample_user_data`: Sample user data dictionary
- `sample_admin_data`: Sample admin user data
- `sample_promotion_data`: Sample promotion data
- `sample_approval_workflow_data`: Sample approval workflow data

#### Mock Service Fixtures

- `mock_zerodb_client`: Mocked ZeroDB client
- `mock_async_zerodb_client`: Async mocked ZeroDB client
- `mock_stripe_client`: Mocked Stripe client
- `mock_redis_client`: Mocked Redis client
- `mock_email_service`: Mocked email service

#### Environment Fixtures

- `test_env_vars`: Test environment variables
- `setup_test_env`: Auto-sets test environment variables

#### HTTP Client Fixtures

- `async_client`: Async HTTP client for API testing

### Creating Custom Fixtures

Add fixtures to `conftest.py`:

```python
@pytest.fixture
def custom_fixture():
    # Setup
    data = {"key": "value"}

    yield data  # Provide to test

    # Teardown (optional)
    # Clean up resources
```

---

## Mocking External Services

### Why Mock?

- **Speed**: Avoid slow network calls
- **Reliability**: Tests don't depend on external services
- **Control**: Simulate error conditions and edge cases
- **Cost**: Avoid charges for API calls during testing

### Mocking ZeroDB

```python
def test_with_zerodb_mock(mock_async_zerodb_client):
    # Configure mock behavior
    mock_async_zerodb_client.get_user.return_value = {
        "id": "123",
        "email": "test@example.com"
    }

    # Use the mock
    user = await service.get_user("123")

    # Verify mock was called
    mock_async_zerodb_client.get_user.assert_called_once_with("123")
```

### Mocking Stripe

```python
def test_payment(mock_stripe_client):
    mock_stripe_client.PaymentIntent.create.return_value = {
        "id": "pi_123",
        "status": "succeeded"
    }

    result = process_payment(1000, mock_stripe_client)
    assert result["status"] == "succeeded"
```

### Mocking Redis

```python
def test_cache(mock_redis_client):
    mock_redis_client.get.return_value = b'{"cached": "data"}'

    result = get_from_cache("key", mock_redis_client)
    assert result == {"cached": "data"}
```

### Advanced Mocking

```python
from unittest.mock import patch, MagicMock

@patch('backend.services.external_api.make_request')
def test_with_patch(mock_request):
    mock_request.return_value = {"success": True}

    result = call_external_api()
    assert result["success"] is True
    mock_request.assert_called_once()
```

---

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on other tests:

```python
# Good: Independent test
def test_create_user():
    user = create_user("test@example.com")
    assert user is not None

# Bad: Depends on previous test
def test_update_user():
    # Assumes user from previous test exists
    user = update_user("test@example.com")
```

### 2. Use Descriptive Names

```python
# Good: Clear what is being tested
def test_user_cannot_approve_own_submission():
    pass

# Bad: Unclear test purpose
def test_approval():
    pass
```

### 3. Test One Thing

```python
# Good: Tests one specific behavior
def test_quorum_met_with_two_approvals():
    workflow = ApprovalWorkflow("promo_123", "promotion")
    workflow.add_approval("admin_001", "admin")
    workflow.add_approval("admin_002", "admin")
    assert workflow.is_quorum_met() is True

# Bad: Tests multiple behaviors
def test_workflow():
    workflow = ApprovalWorkflow("promo_123", "promotion")
    workflow.add_approval("admin_001", "admin")
    assert len(workflow.approvals) == 1
    workflow.add_approval("admin_002", "admin")
    assert workflow.is_quorum_met() is True
    workflow.reject("admin_003", "reason")
    assert workflow.status == "rejected"
```

### 4. Test Edge Cases

Always test:
- Empty inputs
- Null/None values
- Boundary conditions
- Error cases
- Invalid data

### 5. Keep Tests Fast

- Mock external services
- Avoid real database calls in unit tests
- Use in-memory databases for integration tests
- Run slow tests separately

### 6. Don't Test Implementation Details

```python
# Good: Tests behavior
def test_user_email_is_validated():
    with pytest.raises(ValidationError):
        User(email="invalid")

# Bad: Tests internal implementation
def test_validator_uses_regex():
    assert hasattr(EmailValidator, '_regex_pattern')
```

### 7. Use Fixtures for Common Setup

```python
# Good: Reusable fixture
@pytest.fixture
def workflow():
    return ApprovalWorkflow("promo_123", "promotion")

def test_add_approval(workflow):
    workflow.add_approval("admin_001", "admin")
    assert len(workflow.approvals) == 1

# Bad: Duplicated setup
def test_add_approval():
    workflow = ApprovalWorkflow("promo_123", "promotion")
    workflow.add_approval("admin_001", "admin")
    assert len(workflow.approvals) == 1
```

---

## CI/CD Integration

### GitHub Actions Example

Tests will run automatically on every PR:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=backend --cov-report=xml --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend
pytest --cov=backend --cov-fail-under=80
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'backend'`

**Solution**: Ensure you're running pytest from the correct directory:
```bash
cd backend
pytest
```

#### 2. Coverage Below 80%

**Problem**: `FAILED: coverage: total coverage is 75%, required is 80%`

**Solution**:
- Identify uncovered lines: `pytest --cov=backend --cov-report=term-missing`
- Add tests for missing coverage
- Or update `.coveragerc` to exclude non-critical files

#### 3. Async Tests Not Running

**Problem**: `SyntaxError: 'await' outside async function`

**Solution**: Add `@pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
```

#### 4. Fixture Not Found

**Problem**: `fixture 'sample_user_data' not found`

**Solution**: Ensure `conftest.py` is in the tests directory and the fixture is defined there.

#### 5. Tests Pass Locally but Fail in CI

**Problem**: Environment-specific issues

**Solution**:
- Check environment variables are set in CI
- Ensure all dependencies are in `requirements.txt`
- Check Python version matches

---

## Additional Resources

### Pytest Documentation
- [Pytest Official Docs](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/example/markers.html)

### Coverage Documentation
- [Coverage.py](https://coverage.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### Testing Best Practices
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)

---

## Questions?

For questions about testing, please:
1. Check this README
2. Review existing test files for examples
3. Consult pytest documentation
4. Ask in the team Slack channel

---

**Last Updated**: November 9, 2025
**Maintained By**: WWMAA Development Team
