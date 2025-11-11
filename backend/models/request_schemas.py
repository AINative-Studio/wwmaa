"""
Request/Response Schemas with Enhanced Validation (US-070)

This module defines Pydantic models for API request/response validation
with comprehensive input validation to prevent injection attacks.

All models include:
- Field constraints (min/max length, regex patterns)
- Custom validators for complex rules
- Type validation
- Sanitization where appropriate
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator, ConfigDict
from backend.models.schemas import (
    UserRole,
    SubscriptionTier,
    EventType,
    EventVisibility,
    RSVPStatus,
)
from backend.utils.validation import (
    validate_username,
    validate_password_strength,
    validate_phone_number,
    validate_url,
    sanitize_html,
    detect_sql_injection,
)


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request"""
    model_config = ConfigDict(use_enum_values=True)

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name"
    )

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v):
        """Validate name doesn't contain SQL injection patterns"""
        if detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected in name")
        # Remove any HTML tags
        return strip_html(v).strip()


class UserLoginRequest(BaseModel):
    """User login request"""
    model_config = ConfigDict(use_enum_values=True)

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    model_config = ConfigDict(use_enum_values=True)

    email: EmailStr = Field(..., description="User email address")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    model_config = ConfigDict(use_enum_values=True)

    token: str = Field(..., min_length=1, description="Reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        is_valid, errors = validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v


# ============================================================================
# PROFILE SCHEMAS
# ============================================================================

class ProfileUpdateRequest(BaseModel):
    """Profile update request"""
    model_config = ConfigDict(use_enum_values=True)

    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Last name"
    )
    display_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Display name"
    )
    bio: Optional[str] = Field(
        None,
        max_length=2000,
        description="Biography"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Phone number"
    )
    website: Optional[HttpUrl] = Field(
        None,
        description="Personal website"
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City"
    )
    state: Optional[str] = Field(
        None,
        max_length=50,
        description="State"
    )

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number"""
        if v and not validate_phone_number(v):
            raise ValueError("Invalid phone number format. Use E.164 format (e.g., +12025551234)")
        return v

    @field_validator('bio')
    @classmethod
    def sanitize_bio(cls, v):
        """Sanitize bio HTML"""
        if v:
            return sanitize_html(v)
        return v

    @field_validator('display_name', 'city', 'state')
    @classmethod
    def validate_text_field(cls, v):
        """Validate text fields don't contain SQL injection"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        return v


# ============================================================================
# APPLICATION SCHEMAS
# ============================================================================

class ApplicationCreateRequest(BaseModel):
    """Membership application creation request"""
    model_config = ConfigDict(use_enum_values=True)

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    disciplines: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = Field(None, ge=0, le=100)
    motivation: Optional[str] = Field(None, max_length=2000)
    goals: Optional[str] = Field(None, max_length=2000)

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number"""
        if v and not validate_phone_number(v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator('motivation', 'goals')
    @classmethod
    def sanitize_text(cls, v):
        """Sanitize rich text fields"""
        if v:
            return sanitize_html(v)
        return v

    @field_validator('zip_code')
    @classmethod
    def validate_zip(cls, v):
        """Validate ZIP code format"""
        if v:
            # US ZIP code: 5 digits or 5+4 format
            import re
            if not re.match(r'^\d{5}(-\d{4})?$', v):
                raise ValueError("Invalid ZIP code format")
        return v


# ============================================================================
# EVENT SCHEMAS
# ============================================================================

class EventCreateRequest(BaseModel):
    """Event creation request"""
    model_config = ConfigDict(use_enum_values=True)

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    event_type: EventType = Field(...)
    visibility: EventVisibility = Field(default=EventVisibility.PUBLIC)
    start_date: datetime = Field(...)
    end_date: datetime = Field(...)
    timezone: str = Field(default="America/Los_Angeles", max_length=50)
    location: Optional[str] = Field(None, max_length=500)
    is_online: bool = Field(default=False)
    virtual_url: Optional[HttpUrl] = Field(None)
    capacity: Optional[int] = Field(None, ge=1, le=10000)
    price: Optional[float] = Field(None, ge=0)

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        """Sanitize event description HTML"""
        if v:
            return sanitize_html(v)
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Validate end_date is after start_date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator('title', 'location')
    @classmethod
    def validate_text(cls, v):
        """Validate text fields"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        return v


# ============================================================================
# SEARCH SCHEMAS
# ============================================================================

class SearchQueryRequest(BaseModel):
    """Search query request"""
    model_config = ConfigDict(use_enum_values=True)

    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Result offset for pagination")
    filters: Optional[dict] = Field(default=None, description="Optional filters")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate search query"""
        # Check for SQL injection attempts
        if detect_sql_injection(v, strict=False):
            raise ValueError("Invalid search query")
        # Strip HTML
        from backend.utils.validation import strip_html
        return strip_html(v).strip()


class SearchFeedbackRequest(BaseModel):
    """Search feedback request"""
    model_config = ConfigDict(use_enum_values=True)

    query_id: str = Field(..., description="Search query ID")
    rating: str = Field(..., pattern="^(positive|negative)$", description="Feedback rating")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Optional feedback text")

    @field_validator('feedback_text')
    @classmethod
    def sanitize_feedback(cls, v):
        """Sanitize feedback text"""
        if v:
            return sanitize_html(v)
        return v


# ============================================================================
# NEWSLETTER SCHEMAS
# ============================================================================

class NewsletterSubscribeRequest(BaseModel):
    """Newsletter subscription request"""
    model_config = ConfigDict(use_enum_values=True)

    email: EmailStr = Field(..., description="Subscriber email")
    name: Optional[str] = Field(None, max_length=200, description="Subscriber name")
    interests: List[str] = Field(
        default_factory=list,
        description="Subscriber interests"
    )

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name"""
        if v:
            if detect_sql_injection(v, strict=False):
                raise ValueError("Invalid characters in name")
            from backend.utils.validation import strip_html
            return strip_html(v).strip()
        return v


# ============================================================================
# CHAT SCHEMAS
# ============================================================================

class ChatMessageRequest(BaseModel):
    """Chat message request"""
    model_config = ConfigDict(use_enum_values=True)

    session_id: str = Field(..., description="Training session ID")
    message: str = Field(..., min_length=1, max_length=2000, description="Chat message")
    is_private: bool = Field(default=False, description="Private message flag")
    recipient_id: Optional[str] = Field(None, description="Private message recipient ID")

    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v):
        """Sanitize chat message"""
        # Strip HTML tags
        from backend.utils.validation import strip_html
        cleaned = strip_html(v).strip()

        # Check for SQL injection
        if detect_sql_injection(cleaned, strict=False):
            raise ValueError("Invalid characters in message")

        return cleaned


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class CheckoutSessionRequest(BaseModel):
    """Checkout session creation request"""
    model_config = ConfigDict(use_enum_values=True)

    subscription_tier: SubscriptionTier = Field(..., description="Subscription tier")
    success_url: HttpUrl = Field(..., description="Success redirect URL")
    cancel_url: HttpUrl = Field(..., description="Cancel redirect URL")

    @field_validator('success_url', 'cancel_url')
    @classmethod
    def validate_urls(cls, v):
        """Validate redirect URLs"""
        # Ensure URLs are for wwmaa.com domain
        if not validate_url(str(v), allowed_domains=['wwmaa.com', 'localhost']):
            raise ValueError("Invalid redirect URL domain")
        return v


# ============================================================================
# MEDIA UPLOAD SCHEMAS
# ============================================================================

class MediaUploadMetadata(BaseModel):
    """Media upload metadata"""
    model_config = ConfigDict(use_enum_values=True)

    alt_text: Optional[str] = Field(None, max_length=500, description="Alt text for accessibility")
    caption: Optional[str] = Field(None, max_length=1000, description="Media caption")
    tags: List[str] = Field(default_factory=list, description="Media tags")

    @field_validator('alt_text', 'caption')
    @classmethod
    def sanitize_text(cls, v):
        """Sanitize text fields"""
        if v:
            from backend.utils.validation import strip_html
            return strip_html(v).strip()
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate tags"""
        if v:
            # Limit number of tags
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")

            # Validate each tag
            validated_tags = []
            for tag in v:
                # Strip HTML and whitespace
                from backend.utils.validation import strip_html
                cleaned_tag = strip_html(tag).strip()

                # Limit tag length
                if len(cleaned_tag) > 50:
                    raise ValueError("Tag too long (max 50 characters)")

                # Check for SQL injection
                if detect_sql_injection(cleaned_tag, strict=False):
                    raise ValueError("Invalid characters in tag")

                validated_tags.append(cleaned_tag)

            return validated_tags
        return v


# Import strip_html for validators
from backend.utils.validation import strip_html
