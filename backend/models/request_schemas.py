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

class EmergencyContact(BaseModel):
    """Emergency contact information"""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=200, description="Emergency contact name")
    relationship: str = Field(..., min_length=1, max_length=100, description="Relationship to user")
    phone: str = Field(..., max_length=20, description="Emergency contact phone number")
    email: Optional[EmailStr] = Field(None, description="Emergency contact email")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number"""
        if v and not validate_phone_number(v):
            raise ValueError("Invalid phone number format. Use E.164 format (e.g., +12025551234)")
        return v

    @field_validator('name', 'relationship')
    @classmethod
    def validate_text_field(cls, v):
        """Validate text fields don't contain SQL injection"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        from backend.utils.validation import strip_html
        return strip_html(v).strip()


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
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Full address"
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
    zip_code: Optional[str] = Field(
        None,
        max_length=20,
        description="ZIP/Postal code"
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country"
    )
    emergency_contact: Optional[EmergencyContact] = Field(
        None,
        description="Emergency contact information"
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

    @field_validator('display_name', 'city', 'state', 'address', 'country')
    @classmethod
    def validate_text_field(cls, v):
        """Validate text fields don't contain SQL injection"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        from backend.utils.validation import strip_html
        return strip_html(v).strip()

    @field_validator('zip_code')
    @classmethod
    def validate_zip(cls, v):
        """Validate ZIP code format"""
        if v:
            # Support US ZIP and international postal codes
            import re
            # US: 5 digits or 5+4, or international alphanumeric
            if not re.match(r'^[A-Z0-9\s-]{3,20}$', v.upper()):
                raise ValueError("Invalid ZIP/postal code format")
        return v


class ProfilePhotoUploadResponse(BaseModel):
    """Response model for profile photo upload"""
    model_config = ConfigDict(use_enum_values=True)

    message: str = Field(..., description="Success message")
    photo_url: str = Field(..., description="Profile photo URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")


class ProfileUpdateResponse(BaseModel):
    """Response model for profile update"""
    model_config = ConfigDict(use_enum_values=True)

    message: str = Field(..., description="Success message")
    user: dict = Field(..., description="Updated user profile data")


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


# ============================================================================
# ADMIN SETTINGS SCHEMAS
# ============================================================================

class OrganizationSettingsUpdate(BaseModel):
    """Organization settings update request"""
    model_config = ConfigDict(use_enum_values=True)

    org_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Organization name")
    org_email: Optional[EmailStr] = Field(None, description="Organization contact email")
    org_phone: Optional[str] = Field(None, max_length=20, description="Organization phone number")
    org_address: Optional[str] = Field(None, max_length=500, description="Organization address")
    org_website: Optional[HttpUrl] = Field(None, description="Organization website URL")
    org_description: Optional[str] = Field(None, max_length=2000, description="Organization description")

    @field_validator('org_name', 'org_address', 'org_description')
    @classmethod
    def validate_no_injection(cls, v):
        """Validate fields don't contain SQL injection patterns"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        return v

    @field_validator('org_phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v and not validate_phone_number(v):
            raise ValueError("Invalid phone number format")
        return v


class EmailSettingsUpdate(BaseModel):
    """Email/SMTP settings update request"""
    model_config = ConfigDict(use_enum_values=True)

    smtp_host: Optional[str] = Field(None, max_length=255, description="SMTP server host")
    smtp_port: Optional[int] = Field(None, ge=1, le=65535, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, max_length=255, description="SMTP username")
    smtp_password: Optional[str] = Field(None, max_length=255, description="SMTP password (will be encrypted)")
    smtp_from_email: Optional[EmailStr] = Field(None, description="SMTP from email address")
    smtp_from_name: Optional[str] = Field(None, max_length=200, description="SMTP from name")
    smtp_use_tls: Optional[bool] = Field(None, description="Use TLS for SMTP connection")
    smtp_use_ssl: Optional[bool] = Field(None, description="Use SSL for SMTP connection")

    @field_validator('smtp_host')
    @classmethod
    def validate_smtp_host(cls, v):
        """Validate SMTP host doesn't contain injection patterns"""
        if v and detect_sql_injection(v, strict=True):
            raise ValueError("Invalid SMTP host")
        return v

    @field_validator('smtp_port')
    @classmethod
    def validate_port_range(cls, v):
        """Validate port is in valid range"""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class StripeSettingsUpdate(BaseModel):
    """Stripe settings update request"""
    model_config = ConfigDict(use_enum_values=True)

    stripe_publishable_key: Optional[str] = Field(None, max_length=500, description="Stripe publishable key")
    stripe_secret_key: Optional[str] = Field(None, max_length=500, description="Stripe secret key (will be encrypted)")
    stripe_webhook_secret: Optional[str] = Field(None, max_length=500, description="Stripe webhook secret (will be encrypted)")
    stripe_enabled: Optional[bool] = Field(None, description="Stripe integration enabled")

    @field_validator('stripe_publishable_key')
    @classmethod
    def validate_publishable_key_format(cls, v):
        """Validate Stripe publishable key format"""
        if v and not v.startswith('pk_'):
            raise ValueError("Stripe publishable key must start with 'pk_'")
        return v

    @field_validator('stripe_secret_key')
    @classmethod
    def validate_secret_key_format(cls, v):
        """Validate Stripe secret key format"""
        if v and not v.startswith('sk_'):
            raise ValueError("Stripe secret key must start with 'sk_'")
        return v

    @field_validator('stripe_webhook_secret')
    @classmethod
    def validate_webhook_secret_format(cls, v):
        """Validate Stripe webhook secret format"""
        if v and not v.startswith('whsec_'):
            raise ValueError("Stripe webhook secret must start with 'whsec_'")
        return v


class MembershipTierConfig(BaseModel):
    """Single membership tier configuration"""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=100, description="Tier display name")
    price: float = Field(..., ge=0, description="Price (must be non-negative)")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code (ISO 4217)")
    interval: str = Field(..., description="Billing interval (month/year/one_time)")
    features: List[str] = Field(..., min_length=1, description="List of tier features")
    stripe_price_id: Optional[str] = Field(None, max_length=200, description="Stripe price ID")

    @field_validator('interval')
    @classmethod
    def validate_interval(cls, v):
        """Validate billing interval"""
        valid_intervals = ['month', 'year', 'one_time']
        if v not in valid_intervals:
            raise ValueError(f"Interval must be one of: {', '.join(valid_intervals)}")
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code"""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()

    @field_validator('features')
    @classmethod
    def validate_features(cls, v):
        """Validate features list"""
        if not v or len(v) == 0:
            raise ValueError("At least one feature must be provided")
        for feature in v:
            if len(feature) > 200:
                raise ValueError("Feature description too long (max 200 characters)")
        return v


class MembershipTiersUpdate(BaseModel):
    """Membership tiers configuration update request"""
    model_config = ConfigDict(use_enum_values=True)

    basic: Optional[MembershipTierConfig] = Field(None, description="Basic tier configuration")
    premium: Optional[MembershipTierConfig] = Field(None, description="Premium tier configuration")
    lifetime: Optional[MembershipTierConfig] = Field(None, description="Lifetime tier configuration")


class EmailTestRequest(BaseModel):
    """Email test request"""
    model_config = ConfigDict(use_enum_values=True)

    test_email: EmailStr = Field(..., description="Email address to send test to")
    test_subject: str = Field(
        default="WWMAA Test Email",
        max_length=200,
        description="Test email subject"
    )
    test_message: str = Field(
        default="This is a test email from WWMAA admin settings.",
        max_length=1000,
        description="Test email message"
    )

    @field_validator('test_subject', 'test_message')
    @classmethod
    def validate_no_html(cls, v):
        """Validate fields don't contain HTML"""
        cleaned = strip_html(v)
        if cleaned != v:
            raise ValueError("HTML not allowed in test email fields")
        return v


class AdminSettingsResponse(BaseModel):
    """Admin settings response (with decrypted sensitive fields)"""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Settings document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Organization Information
    org_name: str
    org_email: str
    org_phone: Optional[str] = None
    org_address: Optional[str] = None
    org_website: Optional[str] = None
    org_description: Optional[str] = None

    # Email Configuration (decrypted password)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None  # Decrypted for display
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    # Stripe Configuration (decrypted secrets)
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None  # Decrypted for display
    stripe_webhook_secret: Optional[str] = None  # Decrypted for display
    stripe_enabled: bool = False

    # Membership Tiers
    membership_tiers: dict

    # Email Test Tracking
    last_email_test_at: Optional[datetime] = None
    last_email_test_result: Optional[str] = None
    last_email_test_error: Optional[str] = None

    # Metadata
    settings_version: int = 1
    last_modified_by: Optional[str] = None
