"""
Unit tests for backend.config module

Tests cover:
- Configuration loading from environment variables
- Validation of required fields
- Validation of field types and constraints
- Default values for optional fields
- Environment-specific configurations
- Helper methods and properties

Target: 80%+ code coverage
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError
from backend.config import Settings, get_settings


class TestSettingsValidation:
    """Test suite for Settings class validation."""

    def test_valid_configuration(self, monkeypatch):
        """Test that valid configuration loads successfully."""
        # Set all required environment variables
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Clear the cache to force reload
        get_settings.cache_clear()

        settings = Settings()
        assert settings.PYTHON_ENV == "development"
        assert settings.ZERODB_API_KEY == "test-api-key-1234567890"
        assert str(settings.ZERODB_API_BASE_URL) == "https://api.ainative.studio/"
        assert settings.JWT_SECRET == "this-is-a-very-secure-secret-key-with-32-plus-characters"

    def test_missing_required_field(self, monkeypatch, tmp_path):
        """Test that missing required fields raise ValidationError."""
        # Create a temporary empty .env file to prevent loading from root .env
        empty_env = tmp_path / ".env"
        empty_env.write_text("")
        monkeypatch.chdir(tmp_path)

        # Clear all environment variables first
        for key in ["ZERODB_API_KEY", "ZERODB_API_BASE_URL", "JWT_SECRET",
                    "REDIS_URL", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
                    "POSTMARK_API_KEY", "BEEHIIV_API_KEY", "CLOUDFLARE_ACCOUNT_ID",
                    "CLOUDFLARE_API_TOKEN", "AINATIVE_API_KEY", "ZERODB_EMAIL",
                    "ZERODB_PASSWORD", "PYTHON_ENV"]:
            monkeypatch.delenv(key, raising=False)

        # Set some but not all required fields
        monkeypatch.setenv("PYTHON_ENV", "development")
        monkeypatch.setenv("ZERODB_API_KEY", "test-key-1234567890")
        # Missing ZERODB_API_BASE_URL

        get_settings.cache_clear()

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error = exc_info.value
        assert len(error.errors()) > 0
        # Check that the error is about missing fields
        error_str = str(error.errors())
        assert "ZERODB_API_BASE_URL" in error_str or "required" in error_str.lower()

    def test_jwt_secret_too_short(self, monkeypatch):
        """Test that JWT_SECRET shorter than 32 characters is rejected."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "short-secret",  # Less than 32 characters
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error = exc_info.value
        assert any("JWT_SECRET" in str(err) or "32 characters" in str(err) for err in error.errors())

    def test_invalid_python_env(self, monkeypatch):
        """Test that invalid PYTHON_ENV value is rejected."""
        env_vars = {
            "PYTHON_ENV": "invalid_environment",  # Invalid value
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error = exc_info.value
        assert any("PYTHON_ENV" in str(err) for err in error.errors())

    def test_api_key_minimum_length(self, monkeypatch):
        """Test that API keys must meet minimum length requirements."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "short",  # Less than 10 characters
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error = exc_info.value
        assert any("ZERODB_API_KEY" in str(err) for err in error.errors())


class TestDefaultValues:
    """Test suite for default configuration values."""

    def test_default_python_env(self, monkeypatch):
        """Test that PYTHON_ENV defaults to 'development'."""
        # Clear PYTHON_ENV to test the default
        monkeypatch.delenv("PYTHON_ENV", raising=False)

        env_vars = {
            # PYTHON_ENV not set - should default to development
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.PYTHON_ENV == "development"

    def test_default_jwt_settings(self, monkeypatch):
        """Test that JWT settings have correct defaults."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_default_backend_url(self, monkeypatch):
        """Test that PYTHON_BACKEND_URL has correct default."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.PYTHON_BACKEND_URL == "http://localhost:8000"

    def test_default_from_email(self, monkeypatch):
        """Test that FROM_EMAIL has correct default."""
        # Delete FROM_EMAIL to ensure default is used
        monkeypatch.delenv("FROM_EMAIL", raising=False)

        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.FROM_EMAIL == "noreply@wwmaa.com"

    def test_default_test_coverage(self, monkeypatch):
        """Test that TEST_COVERAGE_MINIMUM has correct default."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.TEST_COVERAGE_MINIMUM == 80


class TestEnvironmentProperties:
    """Test suite for environment-specific properties."""

    def test_is_development_property(self, monkeypatch):
        """Test is_development property for different environments."""
        base_env = {
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        # Test development
        for key, value in {**base_env, "PYTHON_ENV": "development"}.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_staging is False
        assert settings.is_production is False

    def test_is_staging_property(self, monkeypatch):
        """Test is_staging property for different environments."""
        base_env = {
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        # Test staging
        for key, value in {**base_env, "PYTHON_ENV": "staging"}.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        settings = Settings()
        assert settings.is_development is False
        assert settings.is_staging is True
        assert settings.is_production is False

    def test_is_production_property(self, monkeypatch):
        """Test is_production property for different environments."""
        base_env = {
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        # Test production
        for key, value in {**base_env, "PYTHON_ENV": "production"}.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        settings = Settings()
        assert settings.is_development is False
        assert settings.is_staging is False
        assert settings.is_production is True

    def test_debug_property(self, monkeypatch):
        """Test debug property based on environment."""
        base_env = {
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        # Debug should be True in development
        for key, value in {**base_env, "PYTHON_ENV": "development"}.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        settings = Settings()
        assert settings.debug is True

        # Debug should be False in production
        for key, value in {**base_env, "PYTHON_ENV": "production"}.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()
        settings = Settings()
        assert settings.debug is False


class TestCorsOrigins:
    """Test suite for CORS origins based on environment."""

    def test_cors_origins_development(self, monkeypatch):
        """Test CORS origins in development environment."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        cors_origins = settings.cors_origins

        assert "http://localhost:3000" in cors_origins
        assert "http://localhost:8000" in cors_origins
        assert "http://127.0.0.1:3000" in cors_origins
        assert "http://127.0.0.1:8000" in cors_origins

    def test_cors_origins_staging(self, monkeypatch):
        """Test CORS origins in staging environment."""
        env_vars = {
            "PYTHON_ENV": "staging",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        cors_origins = settings.cors_origins

        assert "https://staging.wwmaa.com" in cors_origins
        assert "https://staging-api.wwmaa.com" in cors_origins

    def test_cors_origins_production(self, monkeypatch):
        """Test CORS origins in production environment."""
        env_vars = {
            "PYTHON_ENV": "production",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        cors_origins = settings.cors_origins

        assert "https://wwmaa.com" in cors_origins
        assert "https://www.wwmaa.com" in cors_origins
        assert "https://api.wwmaa.com" in cors_origins


class TestLogLevel:
    """Test suite for log level based on environment."""

    def test_log_level_development(self, monkeypatch):
        """Test log level in development environment."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.log_level == "DEBUG"

    def test_log_level_staging(self, monkeypatch):
        """Test log level in staging environment."""
        env_vars = {
            "PYTHON_ENV": "staging",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.log_level == "INFO"

    def test_log_level_production(self, monkeypatch):
        """Test log level in production environment."""
        env_vars = {
            "PYTHON_ENV": "production",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        assert settings.log_level == "WARNING"


class TestHelperMethods:
    """Test suite for helper methods."""

    def test_get_database_config(self, monkeypatch):
        """Test get_database_config method."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "ZERODB_EMAIL": "test@example.com",
            "ZERODB_PASSWORD": "test-password",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        db_config = settings.get_database_config()

        assert db_config["api_key"] == "test-api-key-1234567890"
        assert db_config["base_url"] == "https://api.ainative.studio/"
        assert db_config["email"] == "test@example.com"
        assert db_config["password"] == "test-password"

    def test_get_stripe_config(self, monkeypatch):
        """Test get_stripe_config method."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "STRIPE_PUBLISHABLE_KEY": "pk_test_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        stripe_config = settings.get_stripe_config()

        assert stripe_config["secret_key"] == "sk_test_1234567890"
        assert stripe_config["webhook_secret"] == "whsec_1234567890"
        assert stripe_config["publishable_key"] == "pk_test_1234567890"

    def test_get_email_config(self, monkeypatch):
        """Test get_email_config method."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "FROM_EMAIL": "custom@example.com",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = Settings()
        email_config = settings.get_email_config()

        assert email_config["api_key"] == "test-postmark-key"
        assert email_config["from_email"] == "custom@example.com"


class TestGetSettingsFunction:
    """Test suite for get_settings function."""

    def test_get_settings_returns_settings_instance(self, monkeypatch):
        """Test that get_settings returns a Settings instance."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caches_instance(self, monkeypatch):
        """Test that get_settings caches the Settings instance."""
        env_vars = {
            "PYTHON_ENV": "development",
            "ZERODB_API_KEY": "test-api-key-1234567890",
            "ZERODB_API_BASE_URL": "https://api.ainative.studio",
            "JWT_SECRET": "this-is-a-very-secure-secret-key-with-32-plus-characters",
            "REDIS_URL": "redis://localhost:6379",
            "STRIPE_SECRET_KEY": "sk_test_1234567890",
            "STRIPE_WEBHOOK_SECRET": "whsec_1234567890",
            "POSTMARK_API_KEY": "test-postmark-key",
            "BEEHIIV_API_KEY": "test-beehiiv-key",
            "CLOUDFLARE_ACCOUNT_ID": "test-cloudflare-account",
            "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
            "AINATIVE_API_KEY": "test-ainative-key"
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        get_settings.cache_clear()

        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()

        # They should be the same instance due to caching
        assert settings1 is settings2
