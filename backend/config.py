"""
Environment Configuration Management for WWMAA Backend

This module provides environment-specific configuration management using pydantic-settings.
All environment variables are validated at startup to ensure required fields are present
and have valid values.

Usage:
    from backend.config import get_settings

    settings = get_settings()
    api_key = settings.ZERODB_API_KEY
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment-specific configurations.

    Validates all environment variables at startup and provides typed access
    to configuration values. Automatically loads from .env file.
    """

    # ==========================================
    # Environment Configuration
    # ==========================================
    PYTHON_ENV: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )

    # ==========================================
    # ZeroDB Configuration (REQUIRED)
    # ==========================================
    ZERODB_API_KEY: str = Field(
        ...,
        min_length=10,
        description="ZeroDB authentication API key"
    )

    ZERODB_API_BASE_URL: HttpUrl = Field(
        ...,
        description="ZeroDB API endpoint (e.g., https://api.ainative.studio)"
    )

    ZERODB_EMAIL: str = Field(
        default="",
        description="ZeroDB account email (optional, for some operations)"
    )

    ZERODB_PASSWORD: str = Field(
        default="",
        description="ZeroDB account password (optional, for some operations)"
    )

    ZERODB_PROJECT_ID: str = Field(
        ...,
        min_length=10,
        description="ZeroDB project ID for project-based API access"
    )

    # ==========================================
    # JWT Configuration (REQUIRED)
    # ==========================================
    JWT_SECRET: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT token signing (min 32 characters)"
    )

    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration time in minutes (1-1440)"
    )

    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Refresh token expiration time in days (1-90)"
    )

    # ==========================================
    # Redis Configuration (REQUIRED)
    # ==========================================
    REDIS_URL: str = Field(
        ...,
        description="Redis connection URL (e.g., redis://localhost:6379)"
    )

    # ==========================================
    # Stripe Configuration (REQUIRED)
    # ==========================================
    STRIPE_SECRET_KEY: str = Field(
        ...,
        min_length=10,
        description="Stripe secret key for payment processing"
    )

    STRIPE_WEBHOOK_SECRET: str = Field(
        ...,
        min_length=10,
        description="Stripe webhook secret for webhook validation"
    )

    STRIPE_PUBLISHABLE_KEY: str = Field(
        default="",
        description="Stripe publishable key (optional, mainly for frontend)"
    )

    # ==========================================
    # Strapi CMS Integration Configuration
    # ==========================================
    STRAPI_URL: str = Field(
        default="http://localhost:1337",
        description="Strapi CMS base URL (http://localhost:1337 for local, http://strapi:1337 for Docker)"
    )

    STRAPI_API_TOKEN: str = Field(
        default="",
        description="Strapi API token for authentication (optional for public content)"
    )

    # ==========================================
    # BeeHiiv Blog Integration Configuration (Legacy)
    # ==========================================
    BEEHIIV_API_KEY: str = Field(
        default="",
        description="BeeHiiv API key for blog post synchronization"
    )

    BEEHIIV_PUBLICATION_ID: str = Field(
        default="",
        description="BeeHiiv publication ID"
    )

    BEEHIIV_WEBHOOK_SECRET: str = Field(
        default="",
        description="BeeHiiv webhook secret for signature verification"
    )

    # ==========================================
    # Email Configuration (REQUIRED)
    # ==========================================
    POSTMARK_API_KEY: str = Field(
        ...,
        min_length=10,
        description="Postmark API key for transactional emails"
    )

    FROM_EMAIL: str = Field(
        default="noreply@wwmaa.com",
        description="Default sender email address"
    )

    # ==========================================
    # BeeHiiv Newsletter (REQUIRED)
    # ==========================================
    BEEHIIV_API_KEY: str = Field(
        ...,
        min_length=10,
        description="BeeHiiv API key for newsletter integration"
    )

    BEEHIIV_PUBLICATION_ID: str = Field(
        default="",
        description="BeeHiiv publication ID (optional)"
    )

    # ==========================================
    # Cloudflare Configuration (REQUIRED)
    # ==========================================
    CLOUDFLARE_ACCOUNT_ID: str = Field(
        ...,
        min_length=10,
        description="Cloudflare account ID for video services"
    )

    CLOUDFLARE_API_TOKEN: str = Field(
        ...,
        min_length=10,
        description="Cloudflare API token for authentication"
    )

    CLOUDFLARE_CALLS_APP_ID: str = Field(
        default="",
        description="Cloudflare Calls application ID (optional)"
    )

    CLOUDFLARE_WEBHOOK_SECRET: str = Field(
        default="",
        description="Cloudflare webhook secret for signature verification (optional)"
    )

    CLOUDFLARE_CALLS_API_TOKEN: str = Field(
        default="",
        description="Cloudflare Calls API token (uses CLOUDFLARE_API_TOKEN if not set)"
    )

    # ==========================================
    # AINative AI Registry (REQUIRED)
    # ==========================================
    AINATIVE_API_KEY: str = Field(
        ...,
        min_length=10,
        description="AINative AI Registry API key"
    )

    AI_REGISTRY_API_KEY: str = Field(
        ...,
        min_length=10,
        description="AI Registry API key for LLM orchestration"
    )

    AI_REGISTRY_BASE_URL: HttpUrl = Field(
        default="https://api.ainative.studio",
        description="AI Registry API base URL"
    )

    AI_REGISTRY_MODEL: str = Field(
        default="gpt-4",
        description="Primary LLM model for AI Registry (gpt-4, claude-3-sonnet, etc.)"
    )

    AI_REGISTRY_FALLBACK_MODEL: str = Field(
        default="gpt-3.5-turbo",
        description="Fallback LLM model when primary fails"
    )

    AI_REGISTRY_MAX_TOKENS: int = Field(
        default=2000,
        ge=100,
        le=32000,
        description="Maximum tokens for LLM responses"
    )

    AI_REGISTRY_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses (0.0-2.0)"
    )

    AI_REGISTRY_TIMEOUT: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Request timeout in seconds for AI Registry calls"
    )

    # ==========================================
    # OpenAI Configuration (REQUIRED for Content Indexing)
    # ==========================================
    OPENAI_API_KEY: str = Field(
        ...,
        min_length=10,
        description="OpenAI API key for embeddings generation"
    )

    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-ada-002",
        description="OpenAI embedding model to use"
    )

    # ==========================================
    # Content Indexing Configuration
    # ==========================================
    INDEXING_SCHEDULE_INTERVAL_HOURS: int = Field(
        default=6,
        ge=1,
        le=24,
        description="Interval in hours for automatic content indexing (1-24)"
    )

    INDEXING_CHUNK_SIZE: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Maximum tokens per content chunk (100-2000)"
    )

    INDEXING_CHUNK_OVERLAP: int = Field(
        default=50,
        ge=0,
        le=200,
        description="Token overlap between chunks (0-200)"
    )

    INDEXING_BATCH_SIZE: int = Field(
        default=100,
        ge=1,
        le=2048,
        description="Batch size for OpenAI embedding requests (1-2048)"
    )

    # ==========================================
    # OpenTelemetry Configuration (Sprint 7 - US-065)
    # ==========================================
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="",
        description="OpenTelemetry OTLP exporter endpoint (e.g., https://api.honeycomb.io)"
    )

    OTEL_EXPORTER_OTLP_HEADERS: str = Field(
        default="",
        description="OpenTelemetry OTLP headers (e.g., x-honeycomb-team=api_key)"
    )

    OTEL_SERVICE_NAME: str = Field(
        default="wwmaa-backend",
        description="OpenTelemetry service name"
    )

    OTEL_DEPLOYMENT_ENVIRONMENT: str = Field(
        default="",
        description="OpenTelemetry deployment environment (uses PYTHON_ENV if not set)"
    )

    OTEL_TRACES_SAMPLER: str = Field(
        default="parentbased_traceidratio",
        description="OpenTelemetry trace sampling strategy"
    )

    OTEL_TRACES_SAMPLER_ARG: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="OpenTelemetry sampling ratio (0.0-1.0)"
    )

    OTEL_EXPORTER_TYPE: str = Field(
        default="grpc",
        description="OpenTelemetry exporter type (grpc, http, or console)"
    )

    # ==========================================
    # Sentry Error Tracking Configuration (Sprint 7 - US-066)
    # ==========================================
    SENTRY_DSN: str = Field(
        default="",
        description="Sentry DSN for error tracking (optional)"
    )

    SENTRY_ENVIRONMENT: str = Field(
        default="",
        description="Sentry environment (defaults to PYTHON_ENV if not set)"
    )

    SENTRY_RELEASE: str = Field(
        default="",
        description="Sentry release version (auto-detected from git if not set)"
    )

    SENTRY_TRACES_SAMPLE_RATE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry traces sample rate for performance monitoring (0.0-1.0)"
    )

    SENTRY_PROFILES_SAMPLE_RATE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry profiles sample rate for performance profiling (0.0-1.0)"
    )

    # ==========================================
    # Security Headers Configuration (Sprint 7 - US-069)
    # ==========================================
    SECURITY_HEADERS_ENABLED: bool = Field(
        default=True,
        description="Enable security headers middleware"
    )

    CSP_REPORT_ONLY: bool = Field(
        default=False,
        description="Use Content-Security-Policy-Report-Only instead of enforcement"
    )

    CSP_REPORT_URI: str = Field(
        default="/api/csp-report",
        description="URI for CSP violation reports"
    )

    HSTS_MAX_AGE: int = Field(
        default=31536000,
        ge=0,
        description="HSTS max-age in seconds (31536000 = 1 year)"
    )

    HSTS_INCLUDE_SUBDOMAINS: bool = Field(
        default=True,
        description="Include subdomains in HSTS policy"
    )

    HSTS_PRELOAD: bool = Field(
        default=True,
        description="Make HSTS preload eligible"
    )

    # ==========================================
    # Backend Configuration
    # ==========================================
    PYTHON_BACKEND_URL: str = Field(
        default="http://localhost:8000",
        description="Python backend URL"
    )

    # ==========================================
    # Testing Configuration
    # ==========================================
    TEST_COVERAGE_MINIMUM: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimum test coverage percentage required"
    )

    # ==========================================
    # Performance Monitoring Configuration (Sprint 7 - US-067)
    # ==========================================
    PROMETHEUS_ENABLED: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection"
    )

    METRICS_ENDPOINT: str = Field(
        default="/metrics",
        description="Endpoint for Prometheus metrics"
    )

    SLOW_QUERY_THRESHOLD_SECONDS: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Threshold in seconds for slow query logging (0.1-10.0)"
    )

    SLOW_QUERY_LOG_FILE: str = Field(
        default="/var/log/wwmaa/slow_queries.log",
        description="Path to slow query log file"
    )

    # ==========================================
    # Pydantic Configuration
    # ==========================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
        validate_default=True
    )

    # ==========================================
    # Validators
    # ==========================================
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret meets security requirements."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator("PYTHON_ENV")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        if v not in ["development", "staging", "production"]:
            raise ValueError(
                f"PYTHON_ENV must be one of: development, staging, production. Got: {v}"
            )
        return v

    # ==========================================
    # Properties for Environment-Specific Settings
    # ==========================================
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.PYTHON_ENV == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.PYTHON_ENV == "staging"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.PYTHON_ENV == "production"

    @property
    def debug(self) -> bool:
        """Return debug mode based on environment."""
        return self.is_development

    @property
    def cors_origins(self) -> list[str]:
        """Return CORS origins based on environment."""
        origins = []

        if self.is_production:
            origins = [
                "https://wwmaa.com",
                "https://www.wwmaa.com",
                "https://api.wwmaa.com",
                "https://wwmaa.ainative.studio",
                "https://athletic-curiosity-production.up.railway.app"
            ]
        elif self.is_staging:
            origins = [
                "https://staging.wwmaa.com",
                "https://staging-api.wwmaa.com"
            ]
        else:  # development
            origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000"
            ]

        # Always include PYTHON_BACKEND_URL if it's not localhost (for Railway/cloud deployments)
        if self.PYTHON_BACKEND_URL and "localhost" not in self.PYTHON_BACKEND_URL and "127.0.0.1" not in self.PYTHON_BACKEND_URL:
            if self.PYTHON_BACKEND_URL not in origins:
                origins.append(self.PYTHON_BACKEND_URL)

        return origins

    @property
    def log_level(self) -> str:
        """Return log level based on environment."""
        if self.is_production:
            return "WARNING"
        elif self.is_staging:
            return "INFO"
        else:  # development
            return "DEBUG"

    def get_database_config(self) -> dict:
        """
        Get ZeroDB configuration as a dictionary.

        Returns:
            Dictionary with ZeroDB connection parameters
        """
        return {
            "api_key": self.ZERODB_API_KEY,
            "base_url": str(self.ZERODB_API_BASE_URL),
            "email": self.ZERODB_EMAIL,
            "password": self.ZERODB_PASSWORD,
            "project_id": self.ZERODB_PROJECT_ID
        }

    def get_stripe_config(self) -> dict:
        """
        Get Stripe configuration as a dictionary.

        Returns:
            Dictionary with Stripe configuration
        """
        return {
            "secret_key": self.STRIPE_SECRET_KEY,
            "webhook_secret": self.STRIPE_WEBHOOK_SECRET,
            "publishable_key": self.STRIPE_PUBLISHABLE_KEY
        }

    def get_email_config(self) -> dict:
        """
        Get email configuration as a dictionary.

        Returns:
            Dictionary with email configuration
        """
        return {
            "api_key": self.POSTMARK_API_KEY,
            "from_email": self.FROM_EMAIL
        }

    def get_strapi_config(self) -> dict:
        """
        Get Strapi CMS configuration as a dictionary.

        Returns:
            Dictionary with Strapi configuration
        """
        return {
            "strapi_url": self.STRAPI_URL,
            "api_token": self.STRAPI_API_TOKEN
        }

    def get_ai_registry_config(self) -> dict:
        """
        Get AI Registry configuration as a dictionary.

        Returns:
            Dictionary with AI Registry configuration
        """
        return {
            "api_key": self.AI_REGISTRY_API_KEY,
            "base_url": str(self.AI_REGISTRY_BASE_URL),
            "model": self.AI_REGISTRY_MODEL,
            "fallback_model": self.AI_REGISTRY_FALLBACK_MODEL,
            "max_tokens": self.AI_REGISTRY_MAX_TOKENS,
            "temperature": self.AI_REGISTRY_TEMPERATURE,
            "timeout": self.AI_REGISTRY_TIMEOUT
        }

    def get_cloudflare_calls_config(self) -> dict:
        """
        Get Cloudflare Calls configuration as a dictionary.

        Returns:
            Dictionary with Cloudflare Calls configuration
        """
        # Use CLOUDFLARE_CALLS_API_TOKEN if set, otherwise fall back to CLOUDFLARE_API_TOKEN
        api_token = self.CLOUDFLARE_CALLS_API_TOKEN or self.CLOUDFLARE_API_TOKEN

        return {
            "account_id": self.CLOUDFLARE_ACCOUNT_ID,
            "api_token": api_token,
            "app_id": self.CLOUDFLARE_CALLS_APP_ID,
            "webhook_secret": self.CLOUDFLARE_WEBHOOK_SECRET
        }

    def get_opentelemetry_config(self) -> dict:
        """
        Get OpenTelemetry configuration as a dictionary.

        Returns:
            Dictionary with OpenTelemetry configuration
        """
        return {
            "endpoint": self.OTEL_EXPORTER_OTLP_ENDPOINT,
            "headers": self.OTEL_EXPORTER_OTLP_HEADERS,
            "service_name": self.OTEL_SERVICE_NAME,
            "environment": self.OTEL_DEPLOYMENT_ENVIRONMENT or self.PYTHON_ENV,
            "sampler": self.OTEL_TRACES_SAMPLER,
            "sampler_arg": self.OTEL_TRACES_SAMPLER_ARG,
            "exporter_type": self.OTEL_EXPORTER_TYPE,
        }

    @property
    def is_tracing_enabled(self) -> bool:
        """Check if OpenTelemetry tracing is enabled."""
        return bool(self.OTEL_EXPORTER_OTLP_ENDPOINT) or self.OTEL_EXPORTER_TYPE == "console"

    def get_security_headers_config(self) -> dict:
        """
        Get security headers configuration as a dictionary.

        Returns:
            Dictionary with security headers configuration
        """
        return {
            "enabled": self.SECURITY_HEADERS_ENABLED,
            "csp_report_only": self.CSP_REPORT_ONLY,
            "csp_report_uri": self.CSP_REPORT_URI,
            "hsts_max_age": self.HSTS_MAX_AGE,
            "hsts_include_subdomains": self.HSTS_INCLUDE_SUBDOMAINS,
            "hsts_preload": self.HSTS_PRELOAD,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings instance.

    This function uses lru_cache to ensure only one Settings instance
    is created during the application lifetime, improving performance
    and ensuring consistency.

    Returns:
        Settings: Validated application settings

    Raises:
        ValidationError: If required environment variables are missing
                        or have invalid values

    Example:
        >>> from backend.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.PYTHON_ENV)
        'development'
    """
    return Settings()


# Create a global settings instance for convenience
settings = get_settings()
