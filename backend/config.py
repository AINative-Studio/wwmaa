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
        if self.is_production:
            return [
                "https://wwmaa.com",
                "https://www.wwmaa.com",
                "https://api.wwmaa.com"
            ]
        elif self.is_staging:
            return [
                "https://staging.wwmaa.com",
                "https://staging-api.wwmaa.com"
            ]
        else:  # development
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000"
            ]

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
            "password": self.ZERODB_PASSWORD
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
