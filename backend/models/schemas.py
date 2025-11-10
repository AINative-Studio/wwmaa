"""
ZeroDB Collection Schemas - Pydantic Models

This module defines all Pydantic models for ZeroDB collections.
Each model represents a document schema in ZeroDB with validation rules.

Collections:
- users: User authentication and basic info
- applications: Membership applications
- approvals: Application approval workflow
- subscriptions: Membership subscription tiers
- payments: Payment transactions
- profiles: Extended user profile data
- events: Community events
- rsvps: Event RSVPs
- training_sessions: Training session metadata
- session_attendance: Training attendance records
- search_queries: AI search query logs
- content_index: Searchable content with embeddings
- media_assets: Media file metadata
- audit_logs: System audit trail
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator, HttpUrl, ConfigDict
from uuid import UUID, uuid4


# ============================================================================
# ENUMS - Define all enumeration types
# ============================================================================

class UserRole(str, Enum):
    """User role types"""
    PUBLIC = "public"
    MEMBER = "member"
    INSTRUCTOR = "instructor"
    BOARD_MEMBER = "board_member"
    ADMIN = "admin"


class ApplicationStatus(str, Enum):
    """Membership application status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApprovalStatus(str, Enum):
    """Approval workflow status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalAction(str, Enum):
    """Approval action types"""
    APPROVE = "approve"
    REJECT = "reject"
    INVALIDATE = "invalidate"


class SubscriptionTier(str, Enum):
    """Membership subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    LIFETIME = "lifetime"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PaymentStatus(str, Enum):
    """Payment transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class EventType(str, Enum):
    """Event types"""
    LIVE_TRAINING = "live_training"
    SEMINAR = "seminar"
    TOURNAMENT = "tournament"
    CERTIFICATION = "certification"
    TRAINING = "training"
    COMPETITION = "competition"
    SOCIAL = "social"
    MEETING = "meeting"
    OTHER = "other"


class EventStatus(str, Enum):
    """Event status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DELETED = "deleted"
    CANCELED = "canceled"


class EventVisibility(str, Enum):
    """Event visibility levels"""
    PUBLIC = "public"
    MEMBERS_ONLY = "members_only"
    INVITE_ONLY = "invite_only"


class RSVPStatus(str, Enum):
    """RSVP status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    WAITLIST = "waitlist"
    CANCELED = "canceled"


class AttendanceStatus(str, Enum):
    """Attendance status"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class MediaType(str, Enum):
    """Media asset types"""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    CERTIFICATE = "certificate"
    BACKUP = "backup"
    OTHER = "other"


class AuditAction(str, Enum):
    """Audit log action types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"
    PAYMENT = "payment"


# ============================================================================
# BASE MODELS - Common fields for all documents
# ============================================================================

class BaseDocument(BaseModel):
    """Base model with common fields for all ZeroDB documents"""
    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique document identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Document last update timestamp")


# ============================================================================
# USERS COLLECTION
# ============================================================================

class User(BaseDocument):
    """User authentication and basic information"""
    email: EmailStr = Field(..., description="User email address (unique)")
    password_hash: str = Field(..., description="Hashed password")
    role: UserRole = Field(default=UserRole.PUBLIC, description="User role")
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Email verification status")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    profile_id: Optional[UUID] = Field(None, description="Reference to profiles collection")
    reapplication_count: int = Field(default=0, ge=0, description="Number of membership reapplications")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


# ============================================================================
# APPLICATIONS COLLECTION
# ============================================================================

class Application(BaseDocument):
    """Membership application"""
    user_id: UUID = Field(..., description="Reference to users collection")
    status: ApplicationStatus = Field(default=ApplicationStatus.DRAFT, description="Application status")

    # Applicant Information
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")

    # Address
    address_line1: Optional[str] = Field(None, max_length=200, description="Street address")
    address_line2: Optional[str] = Field(None, max_length=200, description="Apt/Suite number")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP code")
    country: str = Field(default="USA", max_length=100, description="Country")

    # Martial Arts Information
    disciplines: List[str] = Field(default_factory=list, description="Martial arts disciplines")
    experience_years: Optional[int] = Field(None, ge=0, le=100, description="Years of experience")
    current_rank: Optional[str] = Field(None, max_length=50, description="Current rank/belt")
    school_affiliation: Optional[str] = Field(None, max_length=200, description="School affiliation")
    instructor_name: Optional[str] = Field(None, max_length=200, description="Instructor name")

    # Application Details
    motivation: Optional[str] = Field(None, max_length=2000, description="Why joining WWMAA")
    goals: Optional[str] = Field(None, max_length=2000, description="Training goals")
    referral_source: Optional[str] = Field(None, max_length=200, description="How they heard about WWMAA")

    # Workflow
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    reviewed_by: Optional[UUID] = Field(None, description="Reference to reviewing user")
    decision_notes: Optional[str] = Field(None, max_length=2000, description="Review notes")

    # Rejection Fields
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    rejected_by: Optional[UUID] = Field(None, description="Reference to board member who rejected")
    rejection_reason: Optional[str] = Field(None, max_length=2000, description="Reason for rejection")
    recommended_improvements: Optional[str] = Field(None, max_length=2000, description="Recommended improvements for reapplication")
    allow_reapplication: bool = Field(default=True, description="Whether applicant can reapply")
    reapplication_allowed_at: Optional[datetime] = Field(None, description="Date when reapplication is allowed")
    reapplication_count: int = Field(default=0, ge=0, description="Number of times applicant has reapplied")

    # Appeal Process
    appeal_submitted: bool = Field(default=False, description="Whether an appeal has been submitted")
    appeal_reason: Optional[str] = Field(None, max_length=2000, description="Reason for appeal")
    appeal_submitted_at: Optional[datetime] = Field(None, description="Appeal submission timestamp")
    appeal_reviewed_at: Optional[datetime] = Field(None, description="Appeal review timestamp")
    appeal_decision: Optional[str] = Field(None, max_length=50, description="Appeal decision (approved/rejected)")

    # Metadata
    subscription_tier: SubscriptionTier = Field(default=SubscriptionTier.FREE, description="Requested tier")
    certificate_url: Optional[str] = Field(None, description="Certificate file URL if approved")


# ============================================================================
# APPROVALS COLLECTION
# ============================================================================

class Approval(BaseDocument):
    """Application approval workflow"""
    application_id: UUID = Field(..., description="Reference to applications collection")
    approver_id: UUID = Field(..., description="Reference to users collection (board member)")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, description="Approval status")
    action: ApprovalAction = Field(default=ApprovalAction.APPROVE, description="Approval action type")
    notes: Optional[str] = Field(None, max_length=2000, description="Approval notes")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    invalidated_at: Optional[datetime] = Field(None, description="Invalidation timestamp")
    conditions: Optional[List[str]] = Field(default_factory=list, description="Conditional approval requirements")
    priority: int = Field(default=0, ge=0, le=10, description="Priority level (0-10)")
    is_active: bool = Field(default=True, description="Whether this approval is currently active")


# ============================================================================
# SUBSCRIPTIONS COLLECTION
# ============================================================================

class Subscription(BaseDocument):
    """Membership subscription"""
    user_id: UUID = Field(..., description="Reference to users collection")
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE, description="Subscription status")

    # Billing
    stripe_subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID")

    # Dates
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: Optional[datetime] = Field(None, description="Subscription end date")
    trial_end_date: Optional[datetime] = Field(None, description="Trial period end date")
    canceled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")

    # Pricing
    amount: float = Field(..., ge=0, description="Subscription amount")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    interval: str = Field(default="month", description="Billing interval (month/year)")

    # Features
    features: Dict[str, Any] = Field(default_factory=dict, description="Tier-specific features")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# PAYMENTS COLLECTION
# ============================================================================

class Payment(BaseDocument):
    """Payment transaction"""
    user_id: UUID = Field(..., description="Reference to users collection")
    subscription_id: Optional[UUID] = Field(None, description="Reference to subscriptions collection")

    # Payment Details
    amount: float = Field(..., ge=0, description="Payment amount")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    status: PaymentStatus = Field(..., description="Payment status")

    # Stripe Integration
    stripe_payment_intent_id: Optional[str] = Field(None, description="Stripe payment intent ID")
    stripe_charge_id: Optional[str] = Field(None, description="Stripe charge ID")
    payment_method: Optional[str] = Field(None, description="Payment method type")

    # Transaction Info
    description: Optional[str] = Field(None, max_length=500, description="Payment description")
    receipt_url: Optional[HttpUrl] = Field(None, description="Receipt URL")

    # Refunds
    refunded_amount: float = Field(default=0.0, ge=0, description="Refunded amount")
    refunded_at: Optional[datetime] = Field(None, description="Refund timestamp")
    refund_reason: Optional[str] = Field(None, max_length=500, description="Refund reason")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")


# ============================================================================
# PROFILES COLLECTION
# ============================================================================

class Profile(BaseDocument):
    """Extended user profile information"""
    user_id: UUID = Field(..., description="Reference to users collection (1-to-1)")

    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    display_name: Optional[str] = Field(None, max_length=100, description="Public display name")
    bio: Optional[str] = Field(None, max_length=2000, description="Biography")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")

    # Contact
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    website: Optional[HttpUrl] = Field(None, description="Personal website")

    # Location
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    country: str = Field(default="USA", max_length=100, description="Country")

    # Martial Arts
    disciplines: List[str] = Field(default_factory=list, description="Martial arts disciplines")
    ranks: Dict[str, str] = Field(default_factory=dict, description="Ranks by discipline")
    instructor_certifications: List[str] = Field(default_factory=list, description="Instructor certifications")
    schools_affiliated: List[str] = Field(default_factory=list, description="School affiliations")

    # Preferences
    newsletter_subscribed: bool = Field(default=False, description="Newsletter subscription")
    public_profile: bool = Field(default=False, description="Public profile visibility")
    event_notifications: bool = Field(default=True, description="Event notifications enabled")

    # Social Links
    social_links: Dict[str, str] = Field(default_factory=dict, description="Social media links")

    # Metadata
    member_since: Optional[datetime] = Field(None, description="Membership start date")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")


# ============================================================================
# EVENTS COLLECTION
# ============================================================================

class Event(BaseDocument):
    """Community event"""
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, max_length=10000, description="Event description (supports rich text)")

    # Classification
    event_type: EventType = Field(..., description="Event type")
    visibility: EventVisibility = Field(default=EventVisibility.PUBLIC, description="Visibility level")
    status: EventStatus = Field(default=EventStatus.DRAFT, description="Event status")

    # Scheduling
    start_date: datetime = Field(..., description="Event start date and time")
    end_date: datetime = Field(..., description="Event end date and time")
    timezone: str = Field(default="America/Los_Angeles", description="Timezone (e.g., America/Los_Angeles, America/New_York)")
    is_all_day: bool = Field(default=False, description="All-day event flag")

    # Location - support both physical and online
    location: Optional[str] = Field(None, max_length=500, description="Location description (address or 'Online')")
    is_online: bool = Field(default=False, description="Online event flag")
    location_name: Optional[str] = Field(None, max_length=200, description="Venue name")
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    virtual_url: Optional[HttpUrl] = Field(None, description="Virtual event URL")
    is_virtual: bool = Field(default=False, description="Virtual event flag")

    # Capacity
    capacity: Optional[int] = Field(None, ge=1, description="Maximum number of attendees (optional)")
    max_attendees: Optional[int] = Field(None, ge=1, description="Maximum attendees")
    current_attendees: int = Field(default=0, ge=0, description="Current RSVP count")
    waitlist_enabled: bool = Field(default=False, description="Waitlist enabled")

    # Pricing
    price: Optional[float] = Field(None, ge=0, description="Event price (0 or null for free)")
    registration_fee: Optional[float] = Field(None, ge=0, description="Registration fee")
    currency: str = Field(default="USD", max_length=3, description="Currency code")

    # Instructor/Speaker Information
    instructor_info: Optional[str] = Field(None, max_length=1000, description="Instructor or speaker information")
    organizer_id: UUID = Field(..., description="Reference to users collection (creator)")
    instructors: List[UUID] = Field(default_factory=list, description="Instructor user IDs")

    # Media
    featured_image_url: Optional[str] = Field(None, description="Featured image URL in ZeroDB Object Storage")
    gallery_urls: List[str] = Field(default_factory=list, description="Gallery image URLs")

    # Registration
    registration_required: bool = Field(default=False, description="Registration required")
    registration_deadline: Optional[datetime] = Field(None, description="Registration deadline")

    # Publishing
    is_published: bool = Field(default=False, description="Published status")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")

    # Soft Delete
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[UUID] = Field(None, description="User who deleted the event")

    # Cancellation
    is_canceled: bool = Field(default=False, description="Canceled status")
    canceled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    canceled_reason: Optional[str] = Field(None, max_length=500, description="Cancellation reason")

    # Audit
    created_by: UUID = Field(..., description="User who created the event")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the event")

    # Training Session Reference
    training_session_id: Optional[UUID] = Field(None, description="Reference to training_sessions")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Event tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('end_date')
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Validate that end_date is after start_date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator('capacity')
    @classmethod
    def validate_capacity_positive(cls, v):
        """Validate that capacity is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("capacity must be greater than 0")
        return v

    @field_validator('price')
    @classmethod
    def validate_price_non_negative(cls, v):
        """Validate that price is non-negative if provided"""
        if v is not None and v < 0:
            raise ValueError("price must be 0 or greater")
        return v


# ============================================================================
# RSVPS COLLECTION
# ============================================================================

class RSVP(BaseDocument):
    """Event RSVP"""
    event_id: UUID = Field(..., description="Reference to events collection")
    user_id: UUID = Field(..., description="Reference to users collection")
    status: RSVPStatus = Field(default=RSVPStatus.PENDING, description="RSVP status")

    # Details
    guests_count: int = Field(default=0, ge=0, le=10, description="Number of guests")
    notes: Optional[str] = Field(None, max_length=500, description="RSVP notes")

    # Timestamps
    responded_at: Optional[datetime] = Field(None, description="Response timestamp")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in timestamp")

    # Notifications
    reminder_sent: bool = Field(default=False, description="Reminder sent flag")
    confirmation_sent: bool = Field(default=False, description="Confirmation sent flag")


# ============================================================================
# TRAINING_SESSIONS COLLECTION
# ============================================================================

class TrainingSession(BaseDocument):
    """Training session with video recording"""
    event_id: Optional[UUID] = Field(None, description="Reference to events collection")
    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    description: Optional[str] = Field(None, max_length=2000, description="Session description")

    # Instructor
    instructor_id: UUID = Field(..., description="Reference to users collection")
    assistant_instructors: List[UUID] = Field(default_factory=list, description="Assistant instructor IDs")

    # Scheduling
    session_date: datetime = Field(..., description="Session date")
    duration_minutes: int = Field(..., ge=1, le=480, description="Duration in minutes")

    # Content
    discipline: str = Field(..., max_length=100, description="Martial arts discipline")
    topics: List[str] = Field(default_factory=list, description="Topics covered")
    skill_level: Optional[str] = Field(None, max_length=50, description="Skill level (beginner/intermediate/advanced)")

    # Video Recording
    cloudflare_stream_id: Optional[str] = Field(None, description="Cloudflare Stream video ID")
    video_url: Optional[HttpUrl] = Field(None, description="Video playback URL")
    video_duration_seconds: Optional[int] = Field(None, ge=0, description="Video duration")
    recording_status: str = Field(default="not_recorded", description="Recording status")

    # Access Control
    is_public: bool = Field(default=False, description="Public access")
    members_only: bool = Field(default=True, description="Members-only access")

    # Metadata
    attendance_count: int = Field(default=0, ge=0, description="Attendance count")
    tags: List[str] = Field(default_factory=list, description="Session tags")


# ============================================================================
# SESSION_ATTENDANCE COLLECTION
# ============================================================================

class SessionAttendance(BaseDocument):
    """Training session attendance record"""
    training_session_id: UUID = Field(..., description="Reference to training_sessions collection")
    user_id: UUID = Field(..., description="Reference to users collection")
    status: AttendanceStatus = Field(..., description="Attendance status")

    # Check-in
    checked_in_at: Optional[datetime] = Field(None, description="Check-in timestamp")
    checked_out_at: Optional[datetime] = Field(None, description="Check-out timestamp")

    # Details
    notes: Optional[str] = Field(None, max_length=500, description="Attendance notes")
    participation_score: Optional[int] = Field(None, ge=0, le=100, description="Participation score (0-100)")

    # Video Tracking
    video_watch_percentage: Optional[float] = Field(None, ge=0, le=100, description="Video completion percentage")
    last_watched_position: Optional[int] = Field(None, ge=0, description="Last watched position in seconds")


# ============================================================================
# SEARCH_QUERIES COLLECTION
# ============================================================================

class SearchQuery(BaseDocument):
    """AI-powered search query log"""
    user_id: Optional[UUID] = Field(None, description="Reference to users collection (null for anonymous)")
    query_text: str = Field(..., min_length=1, max_length=1000, description="Search query text")

    # AI Processing
    embedding_vector: Optional[List[float]] = Field(None, description="Query embedding vector")
    intent: Optional[str] = Field(None, max_length=100, description="Detected search intent")

    # Results
    results_count: int = Field(default=0, ge=0, description="Number of results returned")
    top_result_ids: List[UUID] = Field(default_factory=list, description="Top result document IDs")

    # Performance
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")

    # User Interaction
    clicked_result_ids: List[UUID] = Field(default_factory=list, description="Clicked result IDs")
    click_through_rate: Optional[float] = Field(None, ge=0, le=1, description="Click-through rate")

    # Metadata
    session_id: Optional[str] = Field(None, description="User session ID")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")


# ============================================================================
# CONTENT_INDEX COLLECTION
# ============================================================================

class ContentIndex(BaseDocument):
    """Searchable content with vector embeddings"""
    content_type: str = Field(..., max_length=50, description="Content type (event/article/profile/etc)")
    content_id: UUID = Field(..., description="Reference to source document")

    # Content
    title: str = Field(..., min_length=1, max_length=500, description="Content title")
    body: str = Field(..., description="Content body text")
    summary: Optional[str] = Field(None, max_length=1000, description="Content summary")

    # Vector Search
    embedding_vector: List[float] = Field(..., description="Content embedding vector (1536 dimensions)")
    embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model used")

    # Metadata
    author_id: Optional[UUID] = Field(None, description="Author user ID")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    category: Optional[str] = Field(None, max_length=100, description="Content category")

    # Access Control
    visibility: str = Field(default="public", max_length=50, description="Visibility level")

    # Search Optimization
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    search_weight: float = Field(default=1.0, ge=0, le=10, description="Search result weight")

    # Publishing
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    is_active: bool = Field(default=True, description="Active in search index")


# ============================================================================
# MEDIA_ASSETS COLLECTION
# ============================================================================

class MediaAsset(BaseDocument):
    """Media file metadata"""
    media_type: MediaType = Field(..., description="Media asset type")

    # File Information
    filename: str = Field(..., min_length=1, max_length=500, description="Original filename")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    mime_type: str = Field(..., max_length=100, description="MIME type")

    # Storage
    storage_provider: str = Field(default="zerodb", description="Storage provider (zerodb/cloudflare)")
    object_id: Optional[str] = Field(None, description="ZeroDB object ID or Cloudflare ID")
    url: Optional[str] = Field(None, description="Public URL")

    # Image-Specific
    width: Optional[int] = Field(None, ge=1, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=1, description="Image height in pixels")

    # Video-Specific
    duration_seconds: Optional[int] = Field(None, ge=0, description="Video duration")
    cloudflare_stream_id: Optional[str] = Field(None, description="Cloudflare Stream ID")

    # Ownership
    uploaded_by: UUID = Field(..., description="Reference to users collection")
    entity_type: Optional[str] = Field(None, max_length=50, description="Related entity type")
    entity_id: Optional[UUID] = Field(None, description="Related entity ID")

    # Metadata
    alt_text: Optional[str] = Field(None, max_length=500, description="Alt text for accessibility")
    caption: Optional[str] = Field(None, max_length=1000, description="Media caption")
    tags: List[str] = Field(default_factory=list, description="Media tags")

    # Access Control
    is_public: bool = Field(default=False, description="Public access")
    access_roles: List[UserRole] = Field(default_factory=list, description="Roles with access")


# ============================================================================
# AUDIT_LOGS COLLECTION
# ============================================================================

class AuditLog(BaseDocument):
    """System audit trail"""
    user_id: Optional[UUID] = Field(None, description="Reference to users collection (null for system actions)")
    action: AuditAction = Field(..., description="Action performed")

    # Target
    resource_type: str = Field(..., max_length=100, description="Resource type (collection name)")
    resource_id: Optional[UUID] = Field(None, description="Resource document ID")

    # Details
    description: str = Field(..., min_length=1, max_length=1000, description="Action description")
    changes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Before/after changes")

    # Context
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session ID")

    # Result
    success: bool = Field(default=True, description="Action success status")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if failed")

    # Metadata
    severity: str = Field(default="info", max_length=20, description="Log severity (info/warning/error/critical)")
    tags: List[str] = Field(default_factory=list, description="Log tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# WEBHOOK_EVENTS COLLECTION
# ============================================================================

class WebhookEvent(BaseDocument):
    """Stripe webhook event storage for idempotency and debugging"""
    stripe_event_id: str = Field(..., min_length=1, max_length=200, description="Stripe event ID (unique)")
    event_type: str = Field(..., max_length=100, description="Event type (e.g., 'checkout.session.completed')")

    # Event Data
    event_data: Dict[str, Any] = Field(..., description="Full event data from Stripe")

    # Processing Status
    processing_status: str = Field(
        default="processed",
        max_length=50,
        description="Processing status (processed/failed/pending)"
    )
    error_message: Optional[str] = Field(None, max_length=2000, description="Error message if processing failed")
    processed_at: datetime = Field(..., description="Processing timestamp")

    # Retry Information
    retry_count: int = Field(default=0, ge=0, description="Number of processing retries")
    last_retry_at: Optional[datetime] = Field(None, description="Last retry timestamp")

    # Metadata
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Processing time in seconds")
    webhook_version: str = Field(default="1.0", description="Webhook handler version")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_models():
    """Return all Pydantic models for ZeroDB collections"""
    return {
        "users": User,
        "applications": Application,
        "approvals": Approval,
        "subscriptions": Subscription,
        "payments": Payment,
        "profiles": Profile,
        "events": Event,
        "rsvps": RSVP,
        "training_sessions": TrainingSession,
        "session_attendance": SessionAttendance,
        "search_queries": SearchQuery,
        "content_index": ContentIndex,
        "media_assets": MediaAsset,
        "audit_logs": AuditLog,
        "webhook_events": WebhookEvent,
    }


def get_model_by_collection(collection_name: str):
    """Get Pydantic model by collection name"""
    models = get_all_models()
    return models.get(collection_name)
