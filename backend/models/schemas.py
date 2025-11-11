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


class ReactionType(str, Enum):
    """Chat emoji reaction types"""
    THUMBS_UP = "👍"
    CLAP = "👏"
    HEART = "❤️"
    FIRE = "🔥"


class SessionStatus(str, Enum):
    """Training session status"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    CANCELED = "canceled"


class MediaType(str, Enum):
    """Media asset types"""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    CERTIFICATE = "certificate"
    BACKUP = "backup"
    OTHER = "other"


class ArticleStatus(str, Enum):
    """Article/blog post status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


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

class RecordingStatus(str, Enum):
    """Training session recording status"""
    NOT_RECORDED = "not_recorded"
    STARTING = "starting"
    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


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
    session_status: str = Field(default="scheduled", description="Session status (scheduled/live/ended)")

    # Content
    discipline: str = Field(..., max_length=100, description="Martial arts discipline")
    topics: List[str] = Field(default_factory=list, description="Topics covered")
    skill_level: Optional[str] = Field(None, max_length=50, description="Skill level (beginner/intermediate/advanced)")

    # Live Session - Cloudflare Calls Integration (US-043)
    cloudflare_room_id: Optional[str] = Field(None, description="Cloudflare Calls room ID for live sessions")
    room_url: Optional[str] = Field(None, description="Live session room URL")
    is_live: bool = Field(default=False, description="Whether session is currently live")
    started_at: Optional[datetime] = Field(None, description="Actual session start timestamp")
    ended_at: Optional[datetime] = Field(None, description="Actual session end timestamp")

    # Recording Configuration (US-046)
    recording_enabled: bool = Field(default=True, description="Whether to record this session")
    recording_id: Optional[str] = Field(None, description="Cloudflare recording ID")
    recording_status: RecordingStatus = Field(
        default=RecordingStatus.NOT_RECORDED,
        description="Recording status"
    )
    recording_started_at: Optional[datetime] = Field(None, description="Recording start timestamp")
    recording_ended_at: Optional[datetime] = Field(None, description="Recording end timestamp")
    recording_error: Optional[str] = Field(None, max_length=1000, description="Recording error message if failed")
    recording_retry_count: int = Field(default=0, ge=0, le=3, description="Number of recording retry attempts")

    # Video On Demand (VOD) - Cloudflare Stream (US-046)
    cloudflare_stream_id: Optional[str] = Field(None, description="Cloudflare Stream video ID")
    vod_stream_url: Optional[str] = Field(None, description="VOD playback URL (Cloudflare Stream)")
    video_url: Optional[HttpUrl] = Field(None, description="Alternative video playback URL")
    video_duration_seconds: Optional[int] = Field(None, ge=0, description="Video duration in seconds")
    recording_file_size_bytes: Optional[int] = Field(None, ge=0, description="Recording file size in bytes")

    # Chat Recording (US-046)
    chat_recording_url: Optional[str] = Field(None, description="Chat transcript JSON file URL in ZeroDB Object Storage")
    chat_message_count: int = Field(default=0, ge=0, description="Number of chat messages in session")

    # Access Control
    is_public: bool = Field(default=False, description="Public access")
    members_only: bool = Field(default=True, description="Members-only access")

    # Metadata
    attendance_count: int = Field(default=0, ge=0, description="Attendance count")
    tags: List[str] = Field(default_factory=list, description="Session tags")
    max_participants: Optional[int] = Field(None, ge=1, description="Maximum participants allowed")


# ============================================================================
# SESSION_ATTENDANCE COLLECTION
# ============================================================================

class SessionAttendance(BaseDocument):
    """Training session attendance record"""
    session_id: UUID = Field(..., description="Reference to training_sessions collection")
    user_id: UUID = Field(..., description="Reference to users collection")

    # Live Session Tracking
    joined_at: Optional[datetime] = Field(None, description="When user joined live session")
    left_at: Optional[datetime] = Field(None, description="When user left live session")
    watch_time_seconds: int = Field(default=0, ge=0, description="Total watch time in seconds")

    # Details
    notes: Optional[str] = Field(None, max_length=500, description="Attendance notes")


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

    # Feedback - US-040
    feedback_rating: Optional[str] = Field(None, max_length=20, description="Feedback rating: 'positive' or 'negative'")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Optional text feedback from user")
    feedback_timestamp: Optional[datetime] = Field(None, description="Timestamp when feedback was provided")
    flagged_for_review: bool = Field(default=False, description="True if negative feedback flagged for admin review")

    # Metadata
    session_id: Optional[str] = Field(None, description="User session ID")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    ip_hash: Optional[str] = Field(None, max_length=64, description="SHA256 hash of IP address for privacy")


# ============================================================================
# CONTENT_INDEX COLLECTION - Vector Search Schema
# ============================================================================

class SourceType(str, Enum):
    """Content source types for vector search indexing"""
    EVENT = "event"
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    PROFILE = "profile"
    VIDEO = "video"
    TRAINING_SESSION = "training_session"
    DOCUMENT = "document"


class ContentIndex(BaseDocument):
    """
    Searchable content with vector embeddings for semantic search

    This model represents documents in the content_index collection,
    which stores content chunks with their vector embeddings for
    similarity-based semantic search using cosine similarity.

    Vector Configuration:
    - Dimensions: 1536 (OpenAI text-embedding-ada-002)
    - Similarity Metric: Cosine similarity
    - Collection: content_index
    """
    # Source Reference
    source_type: SourceType = Field(
        ...,
        description="Type of content being indexed (event/article/profile/video)"
    )
    source_id: UUID = Field(..., description="Reference to source document ID")

    # URL and Identification
    url: Optional[str] = Field(None, max_length=1000, description="URL to the content")

    # Content Fields
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Content title for display in search results"
    )
    content_chunk: str = Field(
        ...,
        min_length=1,
        description="Text content chunk (optimally 200-1000 tokens for embeddings)"
    )
    summary: Optional[str] = Field(
        None,
        max_length=1000,
        description="Brief summary of content"
    )

    # Vector Embedding
    embedding: List[float] = Field(
        ...,
        description="Content embedding vector (1536 dimensions for OpenAI ada-002)",
        min_length=1536,
        max_length=1536
    )
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="Model used to generate embeddings"
    )

    # Metadata for Search Filtering
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for filtering (location, date, tags, etc.)"
    )

    # Author/Owner
    author_id: Optional[UUID] = Field(None, description="Content author/creator user ID")

    # Categorization
    tags: List[str] = Field(
        default_factory=list,
        description="Content tags for filtering"
    )
    category: Optional[str] = Field(
        None,
        max_length=100,
        description="Content category"
    )

    # Access Control
    visibility: str = Field(
        default="public",
        max_length=50,
        description="Visibility level (public/members_only/private)"
    )

    # Search Optimization
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords extracted from content for hybrid search"
    )
    search_weight: float = Field(
        default=1.0,
        ge=0,
        le=10,
        description="Search result ranking weight (higher = more important)"
    )

    # Status and Publishing
    published_at: Optional[datetime] = Field(
        None,
        description="Publication timestamp"
    )
    is_active: bool = Field(
        default=True,
        description="Whether this content is active in search index"
    )

    # Performance Tracking
    search_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this content appeared in search results"
    )
    click_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this content was clicked from search results"
    )

    @field_validator('embedding')
    @classmethod
    def validate_embedding_dimension(cls, v):
        """Validate embedding vector has exactly 1536 dimensions"""
        if len(v) != 1536:
            raise ValueError(
                f"Embedding vector must have exactly 1536 dimensions, got {len(v)}"
            )
        return v

    @field_validator('content_chunk')
    @classmethod
    def validate_content_chunk_length(cls, v):
        """Validate content chunk is not too short or too long"""
        if len(v) < 10:
            raise ValueError("Content chunk must be at least 10 characters")
        if len(v) > 8000:
            raise ValueError(
                "Content chunk should not exceed 8000 characters for optimal embeddings"
            )
        return v



# ============================================================================
# ARTICLES COLLECTION - Blog Posts from BeeHiiv
# ============================================================================

class ArticleAuthor(BaseModel):
    """Article author information"""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=200, description="Author name")
    email: Optional[EmailStr] = Field(None, description="Author email")
    avatar_url: Optional[str] = Field(None, description="Author avatar URL")
    bio: Optional[str] = Field(None, max_length=1000, description="Author bio")


class ArticleSEOMetadata(BaseModel):
    """SEO metadata for articles"""
    model_config = ConfigDict(use_enum_values=True)

    meta_title: Optional[str] = Field(None, max_length=200, description="Meta title (override article title)")
    meta_description: Optional[str] = Field(None, max_length=500, description="Meta description")
    og_title: Optional[str] = Field(None, max_length=200, description="Open Graph title")
    og_description: Optional[str] = Field(None, max_length=500, description="Open Graph description")
    og_image: Optional[str] = Field(None, description="Open Graph image URL")
    twitter_card: Optional[str] = Field(None, max_length=50, description="Twitter card type (summary/summary_large_image)")
    twitter_title: Optional[str] = Field(None, max_length=200, description="Twitter title")
    twitter_description: Optional[str] = Field(None, max_length=500, description="Twitter description")
    twitter_image: Optional[str] = Field(None, description="Twitter image URL")
    keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    canonical_url: Optional[str] = Field(None, description="Canonical URL")


class Article(BaseDocument):
    """
    Blog post/article synced from BeeHiiv

    This model stores blog content synced from BeeHiiv via webhooks.
    Posts are indexed for search and displayed on the website blog.
    """
    # BeeHiiv Integration
    beehiiv_post_id: str = Field(..., min_length=1, max_length=200, description="BeeHiiv post ID (unique)")
    beehiiv_url: Optional[str] = Field(None, description="Canonical BeeHiiv URL")

    # Content
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    slug: str = Field(..., min_length=1, max_length=300, description="URL-friendly slug (unique)")
    excerpt: Optional[str] = Field(None, max_length=1000, description="Short excerpt/summary")
    content: str = Field(..., min_length=1, description="Full article content (HTML or Markdown)")
    content_format: str = Field(default="html", max_length=20, description="Content format (html/markdown)")

    # Author
    author: ArticleAuthor = Field(..., description="Article author information")

    # Media
    featured_image_url: Optional[str] = Field(None, description="Featured image URL (stored in ZeroDB)")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL (300x200, stored in ZeroDB)")
    original_featured_image_url: Optional[str] = Field(None, description="Original BeeHiiv image URL")
    gallery_images: List[str] = Field(default_factory=list, description="Gallery image URLs")

    # Categorization
    category: Optional[str] = Field(None, max_length=100, description="Article category")
    tags: List[str] = Field(default_factory=list, description="Article tags")

    # Publishing
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT, description="Article status")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")

    # Metrics
    view_count: int = Field(default=0, ge=0, description="Number of views")
    read_time_minutes: int = Field(default=0, ge=0, description="Estimated read time in minutes")

    # SEO
    seo_metadata: ArticleSEOMetadata = Field(
        default_factory=ArticleSEOMetadata,
        description="SEO metadata (title, description, OG tags)"
    )

    # Sync Information
    last_synced_at: datetime = Field(default_factory=datetime.utcnow, description="Last sync timestamp")
    sync_source: str = Field(default="beehiiv", max_length=50, description="Sync source (beehiiv/manual)")

    # Content Index Reference (for search)
    indexed_at: Optional[datetime] = Field(None, description="Search index timestamp")
    index_ids: List[UUID] = Field(default_factory=list, description="References to content_index documents")

    @field_validator('slug')
    @classmethod
    def validate_slug_format(cls, v):
        """Validate slug is URL-friendly (lowercase, hyphens, no special chars)"""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v

    @field_validator('read_time_minutes')
    @classmethod
    def validate_read_time_positive(cls, v):
        """Ensure read time is non-negative"""
        if v < 0:
            raise ValueError("read_time_minutes must be non-negative")
        return v


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
    # Import newsletter models defined later in file
    from backend.models.schemas import NewsletterSubscription

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
        "newsletter_subscriptions": NewsletterSubscription,
        "newsletter_subscribers": NewsletterSubscriber,
        "beehiiv_config": BeeHiivConfig,
        "session_chat_messages": SessionChatMessage,
        "session_mutes": SessionMute,
        "session_raised_hands": SessionRaisedHand,
    }


def get_model_by_collection(collection_name: str):
    """Get Pydantic model by collection name"""
    models = get_all_models()
    return models.get(collection_name)


# ============================================================================
# NEWSLETTER SUBSCRIPTIONS COLLECTION (US-058 - Double Opt-In)
# ============================================================================

class NewsletterSubscriptionStatus(str, Enum):
    """Newsletter subscription status for public subscribers"""
    PENDING = "pending"
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"


class NewsletterSubscriptionSource(str, Enum):
    """Newsletter subscription source"""
    WEBSITE = "website"
    CHECKOUT = "checkout"
    MEMBER_SIGNUP = "member_signup"
    ADMIN = "admin"


class NewsletterSubscription(BaseDocument):
    """
    Newsletter subscription record with double opt-in (US-058)

    For public newsletter subscriptions requiring email confirmation.
    Separate from NewsletterSubscriber which is for member auto-subscriptions.
    """
    email: EmailStr = Field(..., description="Subscriber email address")
    name: Optional[str] = Field(None, max_length=200, description="Subscriber name")

    # Interests/Preferences
    interests: List[str] = Field(
        default_factory=list,
        description="Subscriber interests (e.g., ['events', 'training', 'articles', 'news'])"
    )

    # Status and Confirmation
    status: NewsletterSubscriptionStatus = Field(
        default=NewsletterSubscriptionStatus.PENDING,
        description="Subscription status"
    )
    confirmation_token: Optional[str] = Field(None, description="JWT token for email confirmation")
    confirmation_token_expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")

    # Timestamps
    subscribed_at: datetime = Field(default_factory=datetime.utcnow, description="Initial subscription request timestamp")
    confirmed_at: Optional[datetime] = Field(None, description="Email confirmation timestamp")
    unsubscribed_at: Optional[datetime] = Field(None, description="Unsubscription timestamp")

    # Source and Tracking
    subscription_source: NewsletterSubscriptionSource = Field(
        default=NewsletterSubscriptionSource.WEBSITE,
        description="Source of subscription"
    )

    # GDPR Compliance
    ip_address_hash: Optional[str] = Field(None, max_length=64, description="SHA256 hash of subscriber IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="Browser user agent string")
    consent_given: bool = Field(default=True, description="Whether GDPR consent was given")
    consent_timestamp: Optional[datetime] = Field(None, description="Timestamp when consent was given")

    # BeeHiiv Integration
    beehiiv_subscriber_id: Optional[str] = Field(None, description="BeeHiiv subscriber ID")

    # User Association
    user_id: Optional[UUID] = Field(None, description="Reference to users collection (if registered user)")

    # Unsubscribe Details
    unsubscribe_reason: Optional[str] = Field(None, max_length=500, description="Reason for unsubscribing")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


# ============================================================================
# NEWSLETTER SUBSCRIBERS COLLECTION
# ============================================================================

class NewsletterSubscriberStatus(str, Enum):
    """Newsletter subscriber status"""
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    PENDING = "pending"


class NewsletterSubscriber(BaseDocument):
    """Newsletter subscriber record"""
    email: EmailStr = Field(..., description="Subscriber email address")
    name: Optional[str] = Field(None, max_length=200, description="Subscriber name")

    # List Membership
    list_ids: List[str] = Field(default_factory=list, description="BeeHiiv list IDs subscriber belongs to")

    # Status
    status: NewsletterSubscriberStatus = Field(
        default=NewsletterSubscriberStatus.ACTIVE,
        description="Subscription status"
    )

    # Timestamps
    subscribed_at: datetime = Field(default_factory=datetime.utcnow, description="Initial subscription timestamp")
    unsubscribed_at: Optional[datetime] = Field(None, description="Unsubscription timestamp")

    # BeeHiiv Integration
    beehiiv_subscriber_id: Optional[str] = Field(None, description="BeeHiiv subscriber ID")
    last_synced_at: Optional[datetime] = Field(None, description="Last sync with BeeHiiv timestamp")

    # User Association
    user_id: Optional[UUID] = Field(None, description="Reference to users collection (if registered user)")

    # Custom Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom metadata (preferences, source, etc.)"
    )

    # Engagement Tracking
    email_opens: int = Field(default=0, ge=0, description="Total email opens")
    email_clicks: int = Field(default=0, ge=0, description="Total email clicks")
    last_opened_at: Optional[datetime] = Field(None, description="Last email open timestamp")
    last_clicked_at: Optional[datetime] = Field(None, description="Last email click timestamp")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()


# ============================================================================
# BEEHIIV CONFIGURATION COLLECTION
# ============================================================================

class BeeHiivConfig(BaseDocument):
    """BeeHiiv service configuration"""
    # API Configuration
    api_key: str = Field(..., description="BeeHiiv API key (encrypted in production)")
    publication_id: str = Field(..., description="BeeHiiv publication ID")

    # Email List IDs
    list_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Email list IDs mapped by type (general, members_only, instructors)"
    )

    # Domain Configuration
    custom_domain: Optional[str] = Field(None, max_length=255, description="Custom newsletter domain (e.g., newsletter.wwmaa.com)")
    from_email: str = Field(default="newsletter@wwmaa.com", description="From email address")
    from_name: str = Field(default="WWMAA Team", max_length=100, description="From name")

    # DNS Records Status
    dkim_configured: bool = Field(default=False, description="DKIM record configured")
    spf_configured: bool = Field(default=False, description="SPF record configured")
    dmarc_configured: bool = Field(default=False, description="DMARC record configured")
    domain_verified: bool = Field(default=False, description="Custom domain verified")

    # Feature Flags
    is_active: bool = Field(default=True, description="Service active status")
    auto_sync_enabled: bool = Field(default=True, description="Auto-sync subscribers")
    welcome_email_enabled: bool = Field(default=True, description="Send welcome emails")

    # Sync Configuration
    last_sync_at: Optional[datetime] = Field(None, description="Last subscriber sync timestamp")
    sync_frequency_hours: int = Field(default=24, ge=1, le=168, description="Sync frequency in hours")

    # Metadata
    setup_completed_at: Optional[datetime] = Field(None, description="Initial setup completion timestamp")
    setup_by: Optional[UUID] = Field(None, description="Admin who completed setup")


# ============================================================================
# SESSION_CHAT COLLECTION - US-050: Chat & Interaction Features
# ============================================================================

class SessionChatMessage(BaseDocument):
    """
    Training session chat message with reactions and moderation

    Supports real-time chat, emoji reactions, private messaging, and moderation
    controls for live training sessions.
    """
    session_id: UUID = Field(..., description="Reference to training_sessions collection")
    user_id: UUID = Field(..., description="Reference to users collection (message sender)")
    user_name: str = Field(..., min_length=1, max_length=200, description="Display name of sender")

    # Message Content
    message: str = Field(..., min_length=1, max_length=2000, description="Chat message content")

    # Private Messaging
    is_private: bool = Field(default=False, description="Whether this is a private message")
    recipient_id: Optional[UUID] = Field(None, description="Reference to users collection (private message recipient)")
    recipient_name: Optional[str] = Field(None, max_length=200, description="Display name of recipient")

    # Reactions
    reactions: Dict[str, int] = Field(
        default_factory=dict,
        description="Emoji reactions map: {'👍': 5, '👏': 3, '❤️': 2, '🔥': 1}"
    )

    # Moderation
    is_deleted: bool = Field(default=False, description="Whether message has been deleted")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[UUID] = Field(None, description="Reference to users collection (moderator who deleted)")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class SessionMute(BaseDocument):
    """
    User mute record for chat moderation

    Tracks muted users in training sessions with temporary or permanent mutes.
    """
    session_id: UUID = Field(..., description="Reference to training_sessions collection")
    user_id: UUID = Field(..., description="Reference to users collection (muted user)")
    muted_by: UUID = Field(..., description="Reference to users collection (moderator)")

    # Mute Details
    muted_until: Optional[datetime] = Field(None, description="Mute expiration (null for permanent)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for muting")

    # Status
    is_active: bool = Field(default=True, description="Whether mute is currently active")
    unmuted_at: Optional[datetime] = Field(None, description="Unmute timestamp")

    # Metadata
    muted_at: datetime = Field(default_factory=datetime.utcnow, description="Mute timestamp")


class SessionRaisedHand(BaseDocument):
    """
    Raised hand record for session interaction

    Tracks when participants raise their hand to ask questions or get attention.
    """
    session_id: UUID = Field(..., description="Reference to training_sessions collection")
    user_id: UUID = Field(..., description="Reference to users collection (participant)")
    user_name: str = Field(..., min_length=1, max_length=200, description="Display name of participant")

    # Status
    is_active: bool = Field(default=True, description="Whether hand is currently raised")
    raised_at: datetime = Field(default_factory=datetime.utcnow, description="When hand was raised")
    lowered_at: Optional[datetime] = Field(None, description="When hand was lowered")
    acknowledged_by: Optional[UUID] = Field(None, description="Reference to users collection (instructor who acknowledged)")
