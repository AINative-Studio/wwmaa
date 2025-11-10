# ZeroDB Schema Documentation

**Version:** 1.0
**Date:** January 2025
**Project:** WWMAA (World-Wide Martial Arts Association)

---

## Overview

This document describes the complete ZeroDB schema design for the WWMAA platform. All data is stored in ZeroDB collections (document-based NoSQL) accessed via HTTP APIs.

### Technology Stack
- **Database:** ZeroDB (Document/NoSQL via HTTP API)
- **Validation:** Pydantic models in Python backend
- **Access:** RESTful API calls to ZeroDB endpoints
- **IDs:** UUID v4 for all documents
- **Timestamps:** ISO 8601 format (UTC)

---

## Collections Overview

The WWMAA platform uses **14 primary collections**:

| Collection | Purpose | Document Count (est.) | Key Relationships |
|------------|---------|----------------------|-------------------|
| `users` | User authentication & basic info | 1,000+ | → profiles, applications |
| `applications` | Membership applications | 500+ | ← users, → approvals |
| `approvals` | Application approval workflow | 500+ | ← applications, ← users |
| `subscriptions` | Membership subscription tiers | 800+ | ← users, → payments |
| `payments` | Payment transactions | 5,000+ | ← users, ← subscriptions |
| `profiles` | Extended user profile data | 1,000+ | ← users (1:1) |
| `events` | Community events | 200+ | ← users, → rsvps |
| `rsvps` | Event RSVPs | 2,000+ | ← events, ← users |
| `training_sessions` | Training session metadata | 100+ | ← events, ← users |
| `session_attendance` | Training attendance records | 1,000+ | ← training_sessions, ← users |
| `search_queries` | AI search query logs | 10,000+ | ← users (optional) |
| `content_index` | Searchable content with embeddings | 1,000+ | Various sources |
| `media_assets` | Media file metadata | 2,000+ | ← users, various entities |
| `audit_logs` | System audit trail | 50,000+ | ← users, all resources |

---

## Schema Conventions

### Universal Fields (All Collections)

Every document in every collection includes these base fields:

```python
{
    "id": UUID,              # Unique document identifier (UUID v4)
    "created_at": datetime,  # Document creation timestamp (UTC, ISO 8601)
    "updated_at": datetime   # Last update timestamp (UTC, ISO 8601)
}
```

### ID References

- **Primary IDs:** All collections use UUID v4 as primary identifiers
- **Foreign References:** Use `*_id` suffix (e.g., `user_id`, `event_id`)
- **No SQL Joins:** Relationships are logical references, queries require multiple API calls
- **One-to-Many:** Parent stores array of child IDs OR children store parent ID
- **Many-to-Many:** Implemented via junction collections (e.g., RSVPs link users and events)

### Timestamps

- **Format:** ISO 8601 (e.g., `2025-01-09T15:30:00.000Z`)
- **Timezone:** Always UTC
- **Auto-generated:** `created_at` and `updated_at` managed by Pydantic models
- **Optional Timestamps:** Workflow timestamps (e.g., `submitted_at`, `approved_at`)

### Enumerations

All enums are defined as string values for flexibility and readability:

```python
UserRole = "public" | "member" | "instructor" | "board_member" | "admin"
ApplicationStatus = "draft" | "submitted" | "under_review" | "approved" | "rejected" | "withdrawn"
```

---

## Collection Schemas

### 1. Users Collection

**Purpose:** User authentication and basic account information

**Collection Name:** `users`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "email": "EmailStr",             // Unique, lowercase
    "password_hash": "str",          // Hashed with bcrypt
    "role": "UserRole",              // public/member/instructor/board_member/admin
    "is_active": "bool",             // Account active status
    "is_verified": "bool",           // Email verification status
    "last_login": "datetime | null", // Last login timestamp
    "profile_id": "UUID | null"      // Reference to profiles collection
}
```

**Indexes:**
- `email` (unique)
- `role`
- `is_active`

**Relationships:**
- **1:1** with `profiles` (via `profile_id`)
- **1:Many** with `applications` (user can have multiple applications)
- **1:Many** with `subscriptions` (user can have subscription history)
- **1:Many** with `payments` (user payment history)

**Access Control:**
- Users can read their own user document
- Admins can read all user documents
- Only system can write password_hash

---

### 2. Applications Collection

**Purpose:** Membership application submissions and workflow

**Collection Name:** `applications`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "user_id": "UUID",                    // Reference to users
    "status": "ApplicationStatus",        // draft/submitted/under_review/approved/rejected/withdrawn

    // Applicant Information
    "first_name": "str",
    "last_name": "str",
    "email": "EmailStr",
    "phone": "str | null",
    "date_of_birth": "datetime | null",

    // Address
    "address_line1": "str | null",
    "address_line2": "str | null",
    "city": "str | null",
    "state": "str | null",
    "zip_code": "str | null",
    "country": "str",                     // Default: "USA"

    // Martial Arts Information
    "disciplines": ["str"],               // e.g., ["Karate", "Judo"]
    "experience_years": "int | null",     // 0-100
    "current_rank": "str | null",
    "school_affiliation": "str | null",
    "instructor_name": "str | null",

    // Application Details
    "motivation": "str | null",           // Max 2000 chars
    "goals": "str | null",                // Max 2000 chars
    "referral_source": "str | null",

    // Workflow
    "submitted_at": "datetime | null",
    "reviewed_at": "datetime | null",
    "reviewed_by": "UUID | null",         // Reference to users (reviewer)
    "decision_notes": "str | null",

    // Metadata
    "subscription_tier": "SubscriptionTier",  // Requested tier
    "certificate_url": "str | null"       // Certificate file URL if approved
}
```

**Indexes:**
- `user_id`
- `status`
- `submitted_at`
- `email`

**Relationships:**
- **Many:1** with `users` (via `user_id`)
- **1:Many** with `approvals` (application can have multiple approval records)

**Workflow States:**
1. `draft` → User is filling out application
2. `submitted` → User submitted application
3. `under_review` → Board member is reviewing
4. `approved` → Application approved
5. `rejected` → Application rejected
6. `withdrawn` → User withdrew application

---

### 3. Approvals Collection

**Purpose:** Application approval workflow and board member reviews

**Collection Name:** `approvals`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "application_id": "UUID",         // Reference to applications
    "approver_id": "UUID",            // Reference to users (board member)
    "status": "ApprovalStatus",       // pending/approved/rejected
    "notes": "str | null",            // Max 2000 chars
    "approved_at": "datetime | null",
    "conditions": ["str"],            // Conditional approval requirements
    "priority": "int"                 // 0-10
}
```

**Indexes:**
- `application_id`
- `approver_id`
- `status`
- `priority`

**Relationships:**
- **Many:1** with `applications` (via `application_id`)
- **Many:1** with `users` (via `approver_id`)

**Business Rules:**
- Only users with role `board_member` or `admin` can create approvals
- Application requires approval from 2+ board members to be approved

---

### 4. Subscriptions Collection

**Purpose:** Membership subscription plans and billing cycles

**Collection Name:** `subscriptions`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "user_id": "UUID",                    // Reference to users
    "tier": "SubscriptionTier",           // free/basic/premium/lifetime
    "status": "SubscriptionStatus",       // active/past_due/canceled/expired

    // Stripe Integration
    "stripe_subscription_id": "str | null",
    "stripe_customer_id": "str | null",

    // Dates
    "start_date": "datetime",
    "end_date": "datetime | null",
    "trial_end_date": "datetime | null",
    "canceled_at": "datetime | null",

    // Pricing
    "amount": "float",                    // Subscription amount (≥ 0)
    "currency": "str",                    // Default: "USD"
    "interval": "str",                    // "month" or "year"

    // Features
    "features": {"key": "value"},         // Tier-specific features
    "metadata": {"key": "value"}          // Additional metadata
}
```

**Indexes:**
- `user_id`
- `tier`
- `status`
- `stripe_subscription_id` (unique)
- `end_date`

**Relationships:**
- **Many:1** with `users` (via `user_id`)
- **1:Many** with `payments` (subscription can have multiple payments)

**Subscription Tiers:**
- **Free:** Basic access, no payment required
- **Basic:** Monthly/annual payment, basic member features
- **Premium:** Enhanced features, priority access
- **Lifetime:** One-time payment, lifetime access

---

### 5. Payments Collection

**Purpose:** Payment transaction history and Stripe integration

**Collection Name:** `payments`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "user_id": "UUID",                    // Reference to users
    "subscription_id": "UUID | null",     // Reference to subscriptions

    // Payment Details
    "amount": "float",                    // Payment amount (≥ 0)
    "currency": "str",                    // Default: "USD"
    "status": "PaymentStatus",            // pending/processing/succeeded/failed/refunded

    // Stripe Integration
    "stripe_payment_intent_id": "str | null",
    "stripe_charge_id": "str | null",
    "payment_method": "str | null",       // e.g., "card", "bank_transfer"

    // Transaction Info
    "description": "str | null",
    "receipt_url": "HttpUrl | null",

    // Refunds
    "refunded_amount": "float",           // Default: 0.0
    "refunded_at": "datetime | null",
    "refund_reason": "str | null",

    // Metadata
    "metadata": {"key": "value"},
    "processed_at": "datetime | null"
}
```

**Indexes:**
- `user_id`
- `subscription_id`
- `status`
- `stripe_payment_intent_id` (unique)
- `created_at`

**Relationships:**
- **Many:1** with `users` (via `user_id`)
- **Many:1** with `subscriptions` (via `subscription_id`)

---

### 6. Profiles Collection

**Purpose:** Extended user profile information and public member directory

**Collection Name:** `profiles`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "user_id": "UUID",                    // Reference to users (1:1 relationship)

    // Personal Information
    "first_name": "str",
    "last_name": "str",
    "display_name": "str | null",
    "bio": "str | null",                  // Max 2000 chars
    "avatar_url": "str | null",

    // Contact
    "phone": "str | null",
    "website": "HttpUrl | null",

    // Location
    "city": "str | null",
    "state": "str | null",
    "country": "str",                     // Default: "USA"

    // Martial Arts
    "disciplines": ["str"],
    "ranks": {"discipline": "rank"},      // e.g., {"Karate": "Black Belt 3rd Dan"}
    "instructor_certifications": ["str"],
    "schools_affiliated": ["str"],

    // Preferences
    "newsletter_subscribed": "bool",
    "public_profile": "bool",             // Show in member directory
    "event_notifications": "bool",

    // Social Links
    "social_links": {"platform": "url"}, // e.g., {"instagram": "https://..."}

    // Metadata
    "member_since": "datetime | null",
    "last_activity": "datetime | null"
}
```

**Indexes:**
- `user_id` (unique)
- `public_profile`
- `state`
- `disciplines`

**Relationships:**
- **1:1** with `users` (via `user_id`)

**Access Control:**
- Public profiles visible to all
- Private profiles visible only to owner and admins

---

### 7. Events Collection

**Purpose:** Community events, training sessions, seminars, and competitions

**Collection Name:** `events`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "title": "str",
    "description": "str | null",          // Max 5000 chars

    // Classification
    "event_type": "EventType",            // training/seminar/competition/social/meeting/other
    "visibility": "EventVisibility",      // public/members_only/invite_only

    // Scheduling
    "start_datetime": "datetime",
    "end_datetime": "datetime",
    "timezone": "str",                    // Default: "America/Los_Angeles"
    "is_all_day": "bool",

    // Location
    "location_name": "str | null",
    "address": "str | null",
    "city": "str | null",
    "state": "str | null",
    "virtual_url": "HttpUrl | null",
    "is_virtual": "bool",

    // Capacity
    "max_attendees": "int | null",        // ≥ 1
    "current_attendees": "int",           // Default: 0
    "waitlist_enabled": "bool",

    // Organizer
    "organizer_id": "UUID",               // Reference to users
    "instructors": ["UUID"],              // Instructor user IDs

    // Media
    "featured_image_url": "str | null",
    "gallery_urls": ["str"],

    // Registration
    "registration_required": "bool",
    "registration_deadline": "datetime | null",
    "registration_fee": "float | null",   // ≥ 0

    // Status
    "is_published": "bool",
    "is_canceled": "bool",
    "canceled_reason": "str | null",

    // Training Session Reference
    "training_session_id": "UUID | null",

    // Metadata
    "tags": ["str"],
    "metadata": {"key": "value"}
}
```

**Indexes:**
- `event_type`
- `visibility`
- `start_datetime`
- `organizer_id`
- `is_published`
- `state`

**Relationships:**
- **Many:1** with `users` (via `organizer_id`)
- **Many:Many** with `users` via `instructors` array
- **1:Many** with `rsvps`
- **1:1** with `training_sessions` (optional)

---

### 8. RSVPs Collection

**Purpose:** Event registration and attendance tracking

**Collection Name:** `rsvps`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "event_id": "UUID",                   // Reference to events
    "user_id": "UUID",                    // Reference to users
    "status": "RSVPStatus",               // pending/confirmed/declined/waitlist/canceled

    // Details
    "guests_count": "int",                // 0-10
    "notes": "str | null",                // Max 500 chars

    // Timestamps
    "responded_at": "datetime | null",
    "checked_in_at": "datetime | null",

    // Notifications
    "reminder_sent": "bool",
    "confirmation_sent": "bool"
}
```

**Indexes:**
- `event_id`
- `user_id`
- `status`
- Unique constraint on `(event_id, user_id)`

**Relationships:**
- **Many:1** with `events` (via `event_id`)
- **Many:1** with `users` (via `user_id`)

---

### 9. Training Sessions Collection

**Purpose:** Training session metadata with video recording references

**Collection Name:** `training_sessions`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "event_id": "UUID | null",            // Reference to events (optional)
    "title": "str",
    "description": "str | null",          // Max 2000 chars

    // Instructor
    "instructor_id": "UUID",              // Reference to users
    "assistant_instructors": ["UUID"],

    // Scheduling
    "session_date": "datetime",
    "duration_minutes": "int",            // 1-480 minutes

    // Content
    "discipline": "str",
    "topics": ["str"],
    "skill_level": "str | null",          // beginner/intermediate/advanced

    // Video Recording (Cloudflare Stream)
    "cloudflare_stream_id": "str | null",
    "video_url": "HttpUrl | null",
    "video_duration_seconds": "int | null",
    "recording_status": "str",            // Default: "not_recorded"

    // Access Control
    "is_public": "bool",
    "members_only": "bool",               // Default: true

    // Metadata
    "attendance_count": "int",            // Default: 0
    "tags": ["str"]
}
```

**Indexes:**
- `event_id`
- `instructor_id`
- `session_date`
- `discipline`
- `is_public`

**Relationships:**
- **1:1** with `events` (via `event_id`, optional)
- **Many:1** with `users` (via `instructor_id`)
- **1:Many** with `session_attendance`

---

### 10. Session Attendance Collection

**Purpose:** Training session attendance and video viewing tracking

**Collection Name:** `session_attendance`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "training_session_id": "UUID",        // Reference to training_sessions
    "user_id": "UUID",                    // Reference to users
    "status": "AttendanceStatus",         // present/absent/late/excused

    // Check-in
    "checked_in_at": "datetime | null",
    "checked_out_at": "datetime | null",

    // Details
    "notes": "str | null",                // Max 500 chars
    "participation_score": "int | null",  // 0-100

    // Video Tracking (for VOD)
    "video_watch_percentage": "float | null",     // 0-100
    "last_watched_position": "int | null"         // Seconds
}
```

**Indexes:**
- `training_session_id`
- `user_id`
- `status`
- Unique constraint on `(training_session_id, user_id)`

**Relationships:**
- **Many:1** with `training_sessions` (via `training_session_id`)
- **Many:1** with `users` (via `user_id`)

---

### 11. Search Queries Collection

**Purpose:** AI-powered search query logging and analytics

**Collection Name:** `search_queries`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "user_id": "UUID | null",             // Reference to users (null for anonymous)
    "query_text": "str",                  // Max 1000 chars

    // AI Processing
    "embedding_vector": ["float"] | null, // Query embedding (1536 dimensions)
    "intent": "str | null",               // Detected search intent

    // Results
    "results_count": "int",               // Default: 0
    "top_result_ids": ["UUID"],           // Top result document IDs

    // Performance
    "response_time_ms": "int | null",     // Response time in milliseconds

    // User Interaction
    "clicked_result_ids": ["UUID"],       // Clicked result IDs
    "click_through_rate": "float | null", // 0-1

    // Metadata
    "session_id": "str | null",
    "user_agent": "str | null",
    "ip_address": "str | null"
}
```

**Indexes:**
- `user_id`
- `created_at`
- `query_text` (text search)
- `intent`

**Use Cases:**
- Search analytics
- Query suggestion improvements
- Intent classification training
- User behavior analysis

---

### 12. Content Index Collection

**Purpose:** Searchable content with vector embeddings for AI search

**Collection Name:** `content_index`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "content_type": "str",                // event/article/profile/training_session/etc
    "content_id": "UUID",                 // Reference to source document

    // Content
    "title": "str",
    "body": "str",                        // Full text content
    "summary": "str | null",              // Max 1000 chars

    // Vector Search
    "embedding_vector": ["float"],        // 1536 dimensions (OpenAI ada-002)
    "embedding_model": "str",             // Default: "text-embedding-ada-002"

    // Metadata
    "author_id": "UUID | null",
    "tags": ["str"],
    "category": "str | null",

    // Access Control
    "visibility": "str",                  // public/members_only/private

    // Search Optimization
    "keywords": ["str"],
    "search_weight": "float",             // 0-10, default: 1.0

    // Publishing
    "published_at": "datetime | null",
    "is_active": "bool"                   // Active in search index
}
```

**Indexes:**
- `content_type`
- `content_id`
- `visibility`
- `is_active`
- `published_at`
- `tags`
- Vector index on `embedding_vector` (ZeroDB vector search)

**Vector Search:**
- Uses ZeroDB Vector Search API
- Similarity search with cosine distance
- Returns top K most similar documents

---

### 13. Media Assets Collection

**Purpose:** Media file metadata for all uploaded files

**Collection Name:** `media_assets`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "media_type": "MediaType",            // image/video/document/certificate/backup/other

    // File Information
    "filename": "str",
    "file_size_bytes": "int",             // ≥ 0
    "mime_type": "str",

    // Storage
    "storage_provider": "str",            // Default: "zerodb" (or "cloudflare")
    "object_id": "str | null",            // ZeroDB object ID or Cloudflare ID
    "url": "str | null",                  // Public URL

    // Image-Specific
    "width": "int | null",                // ≥ 1
    "height": "int | null",               // ≥ 1

    // Video-Specific
    "duration_seconds": "int | null",     // ≥ 0
    "cloudflare_stream_id": "str | null",

    // Ownership
    "uploaded_by": "UUID",                // Reference to users
    "entity_type": "str | null",          // Related entity type (e.g., "event", "profile")
    "entity_id": "UUID | null",           // Related entity ID

    // Metadata
    "alt_text": "str | null",             // For accessibility
    "caption": "str | null",
    "tags": ["str"],

    // Access Control
    "is_public": "bool",
    "access_roles": ["UserRole"]          // Roles with access
}
```

**Indexes:**
- `media_type`
- `uploaded_by`
- `entity_type`
- `entity_id`
- `storage_provider`

**Storage Providers:**
- **zerodb:** All images, documents, certificates, backups (ZeroDB Object Storage)
- **cloudflare:** All video files (Cloudflare Stream)

---

### 14. Audit Logs Collection

**Purpose:** System audit trail for compliance and debugging

**Collection Name:** `audit_logs`

**Schema:**
```json
{
    "id": "UUID",
    "created_at": "datetime",
    "updated_at": "datetime",
    "user_id": "UUID | null",             // Reference to users (null for system)
    "action": "AuditAction",              // create/read/update/delete/login/logout/approve/reject/payment

    // Target
    "resource_type": "str",               // Collection name (e.g., "applications")
    "resource_id": "UUID | null",         // Resource document ID

    // Details
    "description": "str",                 // Action description
    "changes": {"field": {"old": "value", "new": "value"}},  // Before/after changes

    // Context
    "ip_address": "str | null",
    "user_agent": "str | null",
    "session_id": "str | null",

    // Result
    "success": "bool",                    // Default: true
    "error_message": "str | null",

    // Metadata
    "severity": "str",                    // info/warning/error/critical
    "tags": ["str"],
    "metadata": {"key": "value"}
}
```

**Indexes:**
- `user_id`
- `action`
- `resource_type`
- `resource_id`
- `created_at`
- `severity`

**Retention Policy:**
- Keep for 1 year minimum
- Archive to ZeroDB Object Storage after 90 days
- Critical logs (payments, approvals) kept indefinitely

---

## Relationship Diagram

```
users
├─→ profiles (1:1)
├─→ applications (1:many)
├─→ subscriptions (1:many)
├─→ payments (1:many)
├─→ events (as organizer) (1:many)
├─→ rsvps (1:many)
├─→ training_sessions (as instructor) (1:many)
├─→ session_attendance (1:many)
├─→ search_queries (1:many)
├─→ media_assets (as uploader) (1:many)
└─→ audit_logs (1:many)

applications
├─→ approvals (1:many)
└─← users (many:1)

events
├─→ rsvps (1:many)
├─→ training_sessions (1:1, optional)
└─← users (many:1, organizer)

training_sessions
├─→ session_attendance (1:many)
└─← events (1:1, optional)

subscriptions
├─→ payments (1:many)
└─← users (many:1)

content_index
└─→ various entities (via content_id)
```

---

## Data Access Patterns

### Common Queries

#### Get user with profile
```python
# Step 1: Get user
user = zerodb_client.get_document("users", user_id)

# Step 2: Get profile
profile = zerodb_client.get_document("profiles", user["profile_id"])
```

#### Get all pending applications
```python
applications = zerodb_client.query_documents(
    "applications",
    filters={"status": "submitted"},
    limit=50
)
```

#### Get upcoming events for a user
```python
# Step 1: Get user's RSVPs
rsvps = zerodb_client.query_documents(
    "rsvps",
    filters={"user_id": user_id, "status": "confirmed"},
    limit=100
)

# Step 2: Get events
event_ids = [rsvp["event_id"] for rsvp in rsvps]
events = [zerodb_client.get_document("events", eid) for eid in event_ids]

# Step 3: Filter future events
from datetime import datetime
upcoming = [e for e in events if e["start_datetime"] > datetime.utcnow()]
```

#### Vector search for content
```python
# Step 1: Get query embedding
query_embedding = get_embedding("martial arts techniques")

# Step 2: Vector search
results = zerodb_client.vector_search(
    collection="content_index",
    query_vector=query_embedding,
    top_k=10,
    filters={"visibility": "public", "is_active": True}
)
```

---

## Validation Rules

### Email Validation
- Must be valid email format (Pydantic `EmailStr`)
- Converted to lowercase
- Unique in `users` collection

### UUID Validation
- All IDs are UUID v4 format
- Generated with Python `uuid.uuid4()`
- Stored as strings in JSON

### Date/Time Validation
- ISO 8601 format
- UTC timezone
- Pydantic `datetime` type auto-validates

### String Length Limits
- Short text: 100-200 chars (names, titles)
- Medium text: 500-1000 chars (descriptions)
- Long text: 2000-5000 chars (bio, motivation)
- Query text: 1000 chars max

### Numeric Constraints
- Amounts: `≥ 0` (no negative values)
- Percentages: `0-100`
- Scores: `0-100`
- Priority: `0-10`

---

## Security Considerations

### Sensitive Data
- **Password Hashes:** Never expose in API responses
- **Stripe IDs:** Only expose to user who owns subscription
- **IP Addresses:** Only store for audit/security purposes
- **Payment Details:** PCI compliance - use Stripe, don't store card numbers

### Access Control
- Enforce at API level (not database level)
- Use role-based access control (RBAC)
- Validate user permissions before queries
- Audit all data access in `audit_logs`

### Data Encryption
- All data encrypted at rest (ZeroDB managed)
- TLS for all API communications
- Passwords hashed with bcrypt (cost factor 12+)

---

## Performance Optimization

### Indexes
- Create indexes on frequently queried fields
- Compound indexes for multi-field queries
- Vector index for semantic search

### Caching Strategy
- Cache user sessions in Redis
- Cache frequently accessed profiles
- Cache public events list
- TTL: 5-15 minutes depending on data type

### Pagination
- Limit queries to 50-100 documents
- Use cursor-based pagination for large result sets
- Implement infinite scroll for UX

---

## Migration Strategy

### Initial Setup
1. Create all collections via ZeroDB API
2. No migrations needed (NoSQL, schemaless)
3. Validation enforced in Pydantic models

### Schema Evolution
- Add new fields to Pydantic models
- Old documents auto-fill with defaults
- No breaking changes to existing data
- Use `metadata` dict for experimental fields

### Data Backups
- Daily exports to JSON via ZeroDB API
- Store backups in ZeroDB Object Storage
- Retention: 30 days rolling backups
- See `/backend/scripts/backup_to_zerodb.py`

---

## Testing Strategy

### Unit Tests
- Test all Pydantic models with `pytest`
- Validate field constraints
- Test enum values
- Test validators (e.g., email lowercase)

### Integration Tests
- Test ZeroDB API calls
- Test relationship queries
- Test vector search
- Test access control

### Test Coverage
- Target: 80%+ code coverage
- Use `pytest-cov` for coverage reports

---

## Documentation References

- **Architecture:** `/ARCHITECTURE-CLARIFICATION.md`
- **Storage:** `/STORAGE-ARCHITECTURE.md`
- **Backlog:** `/BACKLOG.md`
- **Models:** `/backend/models/schemas.py`
- **Tests:** `/backend/tests/test_models.py`

---

## Changelog

### Version 1.0 (January 2025)
- Initial schema design
- 14 collections defined
- All Pydantic models created
- Complete documentation

---

**Document Owner:** WWMAA Development Team
**Last Updated:** January 9, 2025
