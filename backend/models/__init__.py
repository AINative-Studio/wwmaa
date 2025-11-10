"""
ZeroDB Models Package

This package contains all Pydantic models for ZeroDB collections.

Available Models:
- User: User authentication and basic information
- Application: Membership applications
- Approval: Application approval workflow
- Subscription: Membership subscription tiers
- Payment: Payment transactions
- Profile: Extended user profile data
- Event: Community events
- RSVP: Event RSVPs
- TrainingSession: Training session metadata
- SessionAttendance: Training attendance records
- SearchQuery: AI search query logs
- ContentIndex: Searchable content with embeddings
- MediaAsset: Media file metadata
- AuditLog: System audit trail

Enums:
- UserRole, ApplicationStatus, ApprovalStatus, SubscriptionTier,
  SubscriptionStatus, PaymentStatus, EventType, EventVisibility,
  RSVPStatus, AttendanceStatus, MediaType, AuditAction
"""

from .schemas import (
    # Base Model
    BaseDocument,

    # Enums
    UserRole,
    ApplicationStatus,
    ApprovalStatus,
    SubscriptionTier,
    SubscriptionStatus,
    PaymentStatus,
    EventType,
    EventVisibility,
    RSVPStatus,
    AttendanceStatus,
    MediaType,
    AuditAction,

    # Collection Models
    User,
    Application,
    Approval,
    Subscription,
    Payment,
    Profile,
    Event,
    RSVP,
    TrainingSession,
    SessionAttendance,
    SearchQuery,
    ContentIndex,
    MediaAsset,
    AuditLog,

    # Helper Functions
    get_all_models,
    get_model_by_collection,
)

__all__ = [
    # Base
    "BaseDocument",

    # Enums
    "UserRole",
    "ApplicationStatus",
    "ApprovalStatus",
    "SubscriptionTier",
    "SubscriptionStatus",
    "PaymentStatus",
    "EventType",
    "EventVisibility",
    "RSVPStatus",
    "AttendanceStatus",
    "MediaType",
    "AuditAction",

    # Models
    "User",
    "Application",
    "Approval",
    "Subscription",
    "Payment",
    "Profile",
    "Event",
    "RSVP",
    "TrainingSession",
    "SessionAttendance",
    "SearchQuery",
    "ContentIndex",
    "MediaAsset",
    "AuditLog",

    # Helpers
    "get_all_models",
    "get_model_by_collection",
]
