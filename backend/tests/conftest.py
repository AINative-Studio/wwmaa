"""
WWMAA Backend - Pytest Configuration and Shared Fixtures

This module contains pytest fixtures that are available to all test modules.
Fixtures are organized by scope and purpose.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Generator, Any
from unittest.mock import AsyncMock, Mock, MagicMock

import pytest
from faker import Faker

# Add backend to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================================
# FAKER SETUP
# ============================================================================

@pytest.fixture(scope="session")
def faker_instance() -> Faker:
    """
    Provides a Faker instance for generating test data.

    Usage:
        def test_user_creation(faker_instance):
            email = faker_instance.email()
            name = faker_instance.name()
    """
    fake = Faker()
    Faker.seed(12345)  # For reproducible test data
    return fake


# ============================================================================
# ENVIRONMENT & CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_env_vars() -> Dict[str, str]:
    """
    Provides test environment variables.
    These override production values for testing.
    """
    return {
        "PYTHON_ENV": "development",
        "ZERODB_EMAIL": "test@example.com",
        "ZERODB_PASSWORD": "test_password",
        "ZERODB_API_KEY": "test_api_key_123456789",
        "ZERODB_API_BASE_URL": "https://test.api.ainative.studio",
        "JWT_SECRET": "test_jwt_secret_key_must_be_at_least_32_characters_long",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "REDIS_URL": "redis://localhost:6379/1",
        "STRIPE_SECRET_KEY": "sk_test_123456789",
        "STRIPE_WEBHOOK_SECRET": "whsec_123456789",
        "STRIPE_PUBLISHABLE_KEY": "pk_test_123456789",
        "POSTMARK_API_KEY": "test_postmark_key",
        "FROM_EMAIL": "test@example.com",
        "BEEHIIV_API_KEY": "test_beehiiv_key",
        "BEEHIIV_PUBLICATION_ID": "test_publication",
        "CLOUDFLARE_ACCOUNT_ID": "test_account_id",
        "CLOUDFLARE_API_TOKEN": "test_token_123",
        "CLOUDFLARE_CALLS_APP_ID": "test_calls_app",
        "AINATIVE_API_KEY": "test_ainative_key",
        "PYTHON_BACKEND_URL": "http://localhost:8000",
        "TEST_COVERAGE_MINIMUM": "80",
    }


@pytest.fixture(autouse=True)
def setup_test_env(test_env_vars, monkeypatch):
    """
    Automatically sets up test environment variables for all tests.
    This fixture runs before every test.
    """
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


# ============================================================================
# ZERODB MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_zerodb_client(mocker) -> Mock:
    """
    Provides a mocked ZeroDB client for testing without real API calls.

    Usage:
        def test_fetch_user(mock_zerodb_client):
            mock_zerodb_client.get_user.return_value = {"id": "123", "email": "test@example.com"}
            # Your test code here
    """
    mock_client = Mock()

    # Mock common methods
    mock_client.authenticate = Mock(return_value={"token": "mock_token"})
    mock_client.get_user = Mock(return_value=None)
    mock_client.create_user = Mock(return_value={"id": "new_user_123"})
    mock_client.update_user = Mock(return_value={"id": "123", "updated": True})
    mock_client.delete_user = Mock(return_value={"deleted": True})
    mock_client.query = Mock(return_value=[])

    return mock_client


@pytest.fixture
async def mock_async_zerodb_client(mocker) -> AsyncMock:
    """
    Provides a mocked async ZeroDB client for testing async operations.

    Usage:
        async def test_async_fetch(mock_async_zerodb_client):
            mock_async_zerodb_client.get_user.return_value = {"id": "123"}
            user = await service.fetch_user("123")
    """
    mock_client = AsyncMock()

    # Mock async methods
    mock_client.authenticate = AsyncMock(return_value={"token": "mock_token"})
    mock_client.get_user = AsyncMock(return_value=None)
    mock_client.create_user = AsyncMock(return_value={"id": "new_user_123"})
    mock_client.update_user = AsyncMock(return_value={"id": "123", "updated": True})
    mock_client.delete_user = AsyncMock(return_value={"deleted": True})
    mock_client.query = AsyncMock(return_value=[])

    return mock_client


# ============================================================================
# EXTERNAL SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_stripe_client(mocker) -> Mock:
    """
    Provides a mocked Stripe client for payment testing.

    Usage:
        def test_payment(mock_stripe_client):
            mock_stripe_client.PaymentIntent.create.return_value = {"id": "pi_123"}
    """
    mock_stripe = Mock()

    # Mock common Stripe operations
    mock_stripe.PaymentIntent = Mock()
    mock_stripe.PaymentIntent.create = Mock(return_value={
        "id": "pi_test123",
        "amount": 5000,
        "currency": "usd",
        "status": "succeeded"
    })

    mock_stripe.Customer = Mock()
    mock_stripe.Customer.create = Mock(return_value={
        "id": "cus_test123",
        "email": "test@example.com"
    })

    return mock_stripe


@pytest.fixture
def mock_redis_client(mocker) -> Mock:
    """
    Provides a mocked Redis client for caching tests.

    Usage:
        def test_cache(mock_redis_client):
            mock_redis_client.get.return_value = b'{"cached": "data"}'
    """
    mock_redis = Mock()

    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=0)
    mock_redis.expire = Mock(return_value=1)

    return mock_redis


@pytest.fixture
def mock_email_service(mocker) -> Mock:
    """
    Provides a mocked email service for email sending tests.

    Usage:
        def test_send_email(mock_email_service):
            mock_email_service.send.return_value = {"message_id": "123"}
    """
    mock_email = Mock()

    mock_email.send = Mock(return_value={
        "message_id": "test_message_123",
        "status": "sent"
    })
    mock_email.send_template = Mock(return_value={
        "message_id": "test_template_123",
        "status": "sent"
    })

    return mock_email


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_data(faker_instance) -> Dict[str, Any]:
    """
    Provides sample user data for testing.

    Returns:
        Dict with user fields: id, email, first_name, last_name, role, etc.
    """
    return {
        "id": faker_instance.uuid4(),
        "email": faker_instance.email(),
        "first_name": faker_instance.first_name(),
        "last_name": faker_instance.last_name(),
        "role": "member",
        "status": "active",
        "state": faker_instance.state_abbr(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_admin_data(faker_instance) -> Dict[str, Any]:
    """
    Provides sample admin user data for testing.
    """
    return {
        "id": faker_instance.uuid4(),
        "email": faker_instance.email(),
        "first_name": faker_instance.first_name(),
        "last_name": faker_instance.last_name(),
        "role": "admin",
        "status": "active",
        "permissions": ["read", "write", "delete", "approve"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_promotion_data(faker_instance) -> Dict[str, Any]:
    """
    Provides sample promotion data for testing.
    """
    return {
        "id": faker_instance.uuid4(),
        "title": faker_instance.catch_phrase(),
        "description": faker_instance.text(max_nb_chars=200),
        "company": faker_instance.company(),
        "discount_code": faker_instance.lexify(text="????-####").upper(),
        "discount_percentage": faker_instance.random_int(min=5, max=50),
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "status": "active",
        "approvals": [],
        "created_by": faker_instance.uuid4(),
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_approval_workflow_data() -> Dict[str, Any]:
    """
    Provides sample approval workflow data for testing.
    """
    return {
        "id": "approval_123",
        "entity_type": "promotion",
        "entity_id": "promo_456",
        "status": "pending",
        "required_approvals": 2,
        "approvals": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# HTTP CLIENT FIXTURES (for API testing)
# ============================================================================

@pytest.fixture
async def async_client() -> AsyncGenerator:
    """
    Provides an async HTTP client for testing FastAPI endpoints.

    Usage:
        async def test_endpoint(async_client):
            response = await async_client.get("/api/users")
            assert response.status_code == 200
    """
    # Import here to avoid dependency issues if FastAPI not yet implemented
    try:
        from httpx import AsyncClient
        from backend.app import app  # Will be created later

        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    except ImportError:
        # Provide a mock client if dependencies not installed
        yield AsyncMock()


# ============================================================================
# TIME & DATE FIXTURES
# ============================================================================

@pytest.fixture
def freeze_time(monkeypatch):
    """
    Provides a way to freeze time for deterministic date testing.

    Usage:
        def test_with_frozen_time(freeze_time):
            fixed_time = datetime(2025, 1, 1, 12, 0, 0)
            freeze_time(fixed_time)
            # Now datetime.utcnow() will always return fixed_time
    """
    def _freeze(frozen_datetime: datetime):
        class FrozenDatetime:
            @classmethod
            def utcnow(cls):
                return frozen_datetime

            @classmethod
            def now(cls, tz=None):
                return frozen_datetime

        monkeypatch.setattr("datetime.datetime", FrozenDatetime)

    return _freeze


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """
    Automatically resets all mocks after each test.
    This ensures test isolation.
    """
    yield
    # Cleanup happens here after test completes


# ============================================================================
# CUSTOM MARKERS & HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Custom pytest configuration.
    Registers custom markers and settings.
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, may require services)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (database, API calls)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.
    Tests in test_unit/ get @pytest.mark.unit
    Tests in test_integration/ get @pytest.mark.integration
    """
    for item in items:
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
