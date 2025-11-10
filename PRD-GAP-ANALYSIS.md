# 🎯 PRD Gap Analysis - WWMAA Platform

**Version:** 1.0
**Date:** January 2025
**Status:** Pre-Implementation

---

## Executive Summary

**Current Completion:** ~30% (Frontend UI/UX foundation complete, backend infrastructure pending)

**Critical Path Items:** 12 major backend systems + 8 frontend enhancements needed
**Estimated Effort:** 8-11 weeks as per PRD timeline
**Risk Level:** Medium (architectural foundation solid, integration work substantial)

---

## 📊 Gap Analysis Overview

| Category | PRD Requirement | Current Status | Gap Severity | Estimated Effort |
|----------|----------------|----------------|--------------|------------------|
| **Membership & Subscriptions** | Full workflow with approvals | Mock data only | 🔴 Critical | 2-3 weeks |
| **AI Semantic Search** | ZeroDB + AI Registry | UI only, no backend | 🔴 Critical | 2-3 weeks |
| **Live Training (RTC)** | Cloudflare Calls/Stream | Not implemented | 🔴 Critical | 2 weeks |
| **Payment Processing** | Stripe integration | No integration | 🔴 Critical | 1-2 weeks |
| **Admin Panel** | Full CRUD + reports | Static pages | 🔴 Critical | 2 weeks |
| **Newsletter Integration** | BeeHiiv API | Form UI only | 🟡 High | 1 week |
| **Authentication** | JWT + role-based | localStorage mock | 🟡 High | 1 week |
| **Database** | PostgreSQL via Supabase | Mock data | 🔴 Critical | 2 weeks |
| **Analytics & Observability** | GA4 + OpenTelemetry | None | 🟡 High | 1 week |
| **Security & Compliance** | WAF, GDPR, audit logs | None | 🟡 High | 1-2 weeks |
| **Testing Infrastructure** | Unit/E2E/Load tests | None | 🟡 High | Ongoing |
| **Deployment Pipeline** | Railway + CI/CD | Config only | 🟡 High | 1 week |

---

## 🔴 CRITICAL GAPS - Backend Infrastructure

### 1. Membership & Subscription System (PRD Section 4.1)

#### PRD Requirements:
- **Two-board-member approval workflow** with audit trail
- Stripe subscription creation on approval
- Application status tracking (Pending → Approved/Rejected)
- Email notifications at each stage
- Member dashboard with payment history, receipts
- Grace period for lapsed memberships
- Dunning for failed payments
- GDPR data deletion
- CSV export for reports

#### Current Implementation:
✅ Membership tier cards with benefits display
✅ Basic application form UI
✅ Mock user roles (Guest, Member, BoardMember, Admin, SuperAdmin)
✅ Dashboard page structure

❌ **Missing:**
- Application submission API endpoint
- Approval workflow (requires 2 distinct Board approvals)
- Approval tracking database tables
- Stripe integration (checkout, webhooks, subscriptions)
- Email notification system
- Payment history storage
- Receipt generation
- Renewal/cancellation flows
- Dunning logic
- GDPR deletion endpoints
- Board approval queue UI
- CSV export functionality

#### Data Model Needed:
```typescript
// Applications table
Application {
  id: uuid
  user_id: uuid (FK → users)
  discipline: string
  experience_years: number
  references: json
  status: "pending" | "approved" | "rejected"
  rejection_reason?: string
  created_at: timestamp
  updated_at: timestamp
}

// Approvals table (for two-board-member tracking)
Approval {
  id: uuid
  application_id: uuid (FK)
  approver_user_id: uuid (FK → users, role must be BoardMember)
  decision: "approved" | "rejected"
  note?: string
  created_at: timestamp
}

// Subscriptions table
Subscription {
  id: uuid
  user_id: uuid (FK)
  tier_id: uuid (FK → membership_tiers)
  stripe_customer_id: string
  stripe_subscription_id: string
  status: "active" | "past_due" | "canceled" | "incomplete"
  current_period_start: timestamp
  current_period_end: timestamp
  cancel_at_period_end: boolean
  created_at: timestamp
}

// Payments table
Payment {
  id: uuid
  subscription_id: uuid (FK)
  amount: decimal
  currency: string
  status: "succeeded" | "failed" | "pending"
  stripe_invoice_id: string
  invoice_url: string
  receipt_url: string
  created_at: timestamp
}
```

#### API Endpoints Needed:
```typescript
// Application Management
POST   /api/applications                      // Submit new application
GET    /api/applications?status=pending       // List applications (filtered)
GET    /api/applications/:id                  // Get single application
POST   /api/applications/:id/approve          // Board member approves
POST   /api/applications/:id/reject           // Board member rejects
GET    /api/applications/:id/approvals        // Get approval history

// Subscription Management
POST   /api/subscriptions/checkout            // Create Stripe checkout session
POST   /api/subscriptions/:id/cancel          // Cancel subscription
POST   /api/subscriptions/:id/reactivate      // Reactivate canceled subscription
GET    /api/subscriptions/current             // Get user's active subscription
POST   /api/webhooks/stripe                   // Stripe webhook handler

// Payment History
GET    /api/payments                          // Get user's payment history
GET    /api/payments/:id/receipt              // Download receipt PDF

// Admin/Board Tools
GET    /api/admin/applications/queue          // Approval queue with filters
GET    /api/admin/applications/export         // CSV export
GET    /api/admin/reports/membership          // Membership funnel report
GET    /api/admin/reports/mrr                 // Monthly recurring revenue
```

#### Estimated Effort: **2-3 weeks**
- Database schema + migrations: 2 days
- Stripe integration + webhooks: 4 days
- Approval workflow logic: 3 days
- Email notification system: 2 days
- Admin dashboard functionality: 4 days
- Testing + edge cases: 3 days

---

### 2. AI-Powered Semantic Search (PRD Section 4.2)

#### PRD Requirements:
- **ZeroDB vector search** for semantic queries
- **AINative AI Registry** LLM orchestration
- Video embedding in results (Cloudflare Stream)
- Image embedding (licensed/curated)
- IP-based rate limiting (50 req/hr unauthenticated, 150/hr authenticated)
- Query caching with short TTL
- Feedback mechanism ("Was this helpful?")
- Query logging for analytics
- Abuse protection
- Result latency ≤ 1.2s p95

#### Current Implementation:
✅ Search UI component with input field
✅ Search results page structure
✅ Result card components

❌ **Missing:**
- ZeroDB integration (vector embeddings)
- Content indexing pipeline
- AI Registry API integration
- LLM answer generation
- Video/image embedding in results
- Rate limiting middleware
- Redis/KV caching layer
- Feedback collection API
- Query logging/analytics
- Expandable detail sections
- Source citation display
- Media licensing validation

#### Architecture Needed:
```typescript
// Search Pipeline
Query Input
  ↓
Normalize & Validate
  ↓
Rate Limit Check (IP-based)
  ↓
Cache Lookup (Redis/KV)
  ↓ (cache miss)
ZeroDB Vector Search (kNN)
  ↓
Retrieve Top K Results (k=10)
  ↓
AI Registry API (LLM enrichment)
  ↓
Attach Media (videos, images)
  ↓
Store in Cache (TTL: 5min)
  ↓
Return Results + Metadata
```

#### Data Model Needed:
```typescript
// SearchQueries table (logging)
SearchQuery {
  id: uuid
  query_text: string
  ip_hash: string (hashed for privacy)
  user_id?: uuid (if authenticated)
  latency_ms: integer
  result_count: integer
  feedback?: "helpful" | "not_helpful"
  feedback_note?: string
  created_at: timestamp
}

// ContentIndex table (ZeroDB sync)
ContentIndex {
  id: uuid
  source_type: "article" | "video" | "event" | "training"
  source_id: string
  title: string
  content_text: text
  embedding_vector: vector (stored in ZeroDB)
  metadata: json
  indexed_at: timestamp
  updated_at: timestamp
}

// MediaAssets table (licensed content)
MediaAsset {
  id: uuid
  type: "image" | "video"
  source: string (Cloudflare Stream ID, etc.)
  url: string
  thumbnail_url?: string
  title: string
  description?: string
  license_type: "owned" | "creative_commons" | "licensed"
  license_attribution?: string
  tags: string[]
  created_at: timestamp
}
```

#### API Endpoints Needed:
```typescript
// Search API
POST   /api/search/query                      // Execute semantic search
POST   /api/search/feedback                   // Submit search feedback
GET    /api/search/suggestions                // Autocomplete suggestions

// Admin - Content Indexing
POST   /api/admin/search/index                // Trigger reindexing
GET    /api/admin/search/status               // Get indexing status
GET    /api/admin/search/analytics            // Top queries, avg latency
POST   /api/admin/search/media                // Upload/manage media assets
```

#### Integration Requirements:
1. **ZeroDB Setup:**
   - Create vector database project
   - Define embedding dimensions (e.g., 1536 for OpenAI ada-002)
   - Set up indexing pipelines
   - Configure similarity search (cosine/euclidean)

2. **AINative AI Registry:**
   - API key configuration
   - Prompt templates for answer generation
   - Context window management
   - Token usage tracking

3. **Cloudflare Stream:**
   - Video upload API integration
   - Embed code generation
   - Thumbnail extraction
   - Access control (public vs member-only)

#### Estimated Effort: **2-3 weeks**
- ZeroDB setup + indexing pipeline: 4 days
- AI Registry integration: 3 days
- Search API + caching: 3 days
- Rate limiting middleware: 1 day
- Media embedding: 2 days
- Feedback system: 1 day
- Frontend result enhancements: 2 days
- Testing + optimization: 2 days

---

### 3. Events & Live Training System (PRD Section 4.3)

#### PRD Requirements:
- **Cloudflare Calls (WebRTC)** for live training sessions
- **Cloudflare Stream** for video-on-demand (VOD)
- Automatic recording upload with metadata
- Paid event registration via Stripe
- Event RSVP tracking
- Member-only vs public event visibility
- Post-event VOD with gated access
- Schema.org Event markup for SEO
- 50 concurrent attendees with <1% drop rate

#### Current Implementation:
✅ Event listing page
✅ Event card components
✅ RSVP button UI
✅ Event schema.org markup
✅ Mock event data

❌ **Missing:**
- Cloudflare Calls integration (RTC rooms)
- Cloudflare Stream integration (VOD storage)
- Live session join interface
- Recording upload automation
- Paid registration flow
- RSVP database storage
- Attendance tracking
- Member-only access control
- Video player with gating
- Session analytics (concurrent viewers, drop rate)

#### Architecture Needed:
```typescript
// Live Training Flow
Event Created
  ↓
Cloudflare Calls Room Created
  ↓
User Clicks "Join Live Session"
  ↓
Auth Check + Payment Verification
  ↓
Generate Signed Join Token (ephemeral, 5min TTL)
  ↓
Redirect to RTC Interface
  ↓
WebRTC Connection Established
  ↓
Recording Starts (Cloudflare Calls Recording API)
  ↓
Session Ends
  ↓
Automatic Upload to Cloudflare Stream
  ↓
Metadata Tagged (event_id, date, instructor, etc.)
  ↓
VOD Available (gated for members)
```

#### Data Model Needed:
```typescript
// Events table (enhance existing)
Event {
  id: uuid
  title: string
  description: text
  start_datetime: timestamp
  end_datetime: timestamp
  timezone: string
  location?: string (or "Online")
  type: "live_training" | "seminar" | "tournament" | "certification"
  visibility: "public" | "members_only"
  capacity?: integer
  price_usd: decimal
  requires_payment: boolean
  rtc_room_id?: string (Cloudflare Calls room ID)
  vod_id?: string (Cloudflare Stream video ID)
  status: "scheduled" | "live" | "ended" | "canceled"
  created_by: uuid (FK → users)
  created_at: timestamp
}

// RSVPs table
RSVP {
  id: uuid
  event_id: uuid (FK)
  user_id: uuid (FK)
  status: "registered" | "attended" | "no_show" | "canceled"
  payment_id?: uuid (FK → payments, if paid event)
  rsvp_date: timestamp
  attended_at?: timestamp
  created_at: timestamp
}

// TrainingSessions table (live session metadata)
TrainingSession {
  id: uuid
  event_id: uuid (FK)
  rtc_room_id: string
  vod_id?: string
  started_at: timestamp
  ended_at?: timestamp
  max_concurrent_viewers: integer
  total_unique_viewers: integer
  recording_url?: string
  recording_duration_seconds?: integer
  created_at: timestamp
}

// SessionAttendance table (tracking)
SessionAttendance {
  id: uuid
  training_session_id: uuid (FK)
  user_id: uuid (FK)
  joined_at: timestamp
  left_at?: timestamp
  duration_seconds: integer
  connection_quality?: "excellent" | "good" | "poor"
}
```

#### API Endpoints Needed:
```typescript
// Event Management
POST   /api/events                            // Create event (Admin)
PUT    /api/events/:id                        // Update event (Admin)
DELETE /api/events/:id                        // Cancel event (Admin)
GET    /api/events                            // List events (filtered by visibility)
GET    /api/events/:id                        // Get single event details

// RSVP Management
POST   /api/events/:id/rsvp                   // Register for event (+ payment if required)
DELETE /api/events/:id/rsvp                   // Cancel RSVP
GET    /api/events/:id/attendees              // List attendees (Admin)

// Live Training
POST   /api/training/:id/join                 // Get signed token to join RTC room
POST   /api/training/:id/start                // Start recording (Admin/Instructor)
POST   /api/training/:id/end                  // End session + upload recording
GET    /api/training/:id/status               // Get live session status (viewer count, etc.)

// VOD Access
GET    /api/vod/:id                           // Get VOD details (gated)
POST   /api/vod/:id/request-access            // Request access (if member-only)

// Webhooks
POST   /api/webhooks/cloudflare/recording     // Recording ready callback
POST   /api/webhooks/cloudflare/stream        // Stream processing complete
```

#### Integration Requirements:
1. **Cloudflare Calls:**
   - API credentials configuration
   - Room creation/deletion
   - Signed URL generation for joining
   - Recording API setup

2. **Cloudflare Stream:**
   - Upload API integration
   - Webhook configuration for processing status
   - Embed code generation
   - Access control (signed URLs for member-only)

#### Frontend Components Needed:
```typescript
// Join Live Session Modal
<LiveSessionJoinModal>
  - Event details
  - Start time countdown
  - Payment verification
  - Terms acceptance
  - "Join Now" CTA

// RTC Interface (in-session)
<RTCSessionInterface>
  - Video grid (instructor + participants)
  - Audio/video controls
  - Chat sidebar
  - Screen sharing
  - Participant list
  - "Leave Session" button

// VOD Player (post-session)
<VODPlayer>
  - Video player with controls
  - Playback speed
  - Transcript/captions
  - Related sessions
  - Member-only gate (if applicable)
```

#### Estimated Effort: **2 weeks**
- Cloudflare Calls integration: 3 days
- Cloudflare Stream integration: 2 days
- Event CRUD operations: 2 days
- RSVP + payment flow: 2 days
- Live session UI: 2 days
- Recording automation: 1 day
- Testing (concurrent load): 2 days

---

### 4. Payment Processing & Stripe Integration (PRD Section 4.1)

#### PRD Requirements:
- Stripe subscription creation on approval
- Checkout session for membership tiers
- Webhook handling (invoice.paid, payment_failed, etc.)
- Receipt generation
- Payment history
- Dunning for failed payments
- Paid event registration
- PCI scope minimized (no card data stored)

#### Current Implementation:
✅ Checkout page structure
✅ Membership tier pricing display

❌ **Missing:**
- Stripe API integration
- Webhook endpoint
- Checkout session creation
- Subscription management
- Payment intent handling
- Receipt storage/download
- Failed payment retry logic
- Refund processing
- Invoice generation
- Payout reconciliation

#### Integration Requirements:
1. **Stripe Setup:**
   - Create Stripe account + API keys
   - Configure webhook endpoints
   - Set up products/prices for membership tiers
   - Configure subscription settings (trial periods, grace periods)

2. **Webhook Events to Handle:**
   - `checkout.session.completed` → Activate subscription
   - `invoice.paid` → Record payment
   - `invoice.payment_failed` → Trigger dunning
   - `customer.subscription.updated` → Update subscription status
   - `customer.subscription.deleted` → Deactivate membership
   - `charge.refunded` → Update payment record

#### API Endpoints Needed:
```typescript
// Checkout
POST   /api/checkout/create-session           // Create Stripe checkout session
GET    /api/checkout/success                  // Redirect after successful payment
GET    /api/checkout/cancel                   // Redirect after canceled payment

// Webhooks
POST   /api/webhooks/stripe                   // Stripe webhook handler (verify signature)

// Customer Portal
POST   /api/billing/portal                    // Generate Stripe Customer Portal link

// Invoices
GET    /api/invoices                          // List user's invoices
GET    /api/invoices/:id/download             // Download invoice PDF
```

#### Estimated Effort: **1-2 weeks**
- Stripe account setup: 1 day
- Checkout flow: 2 days
- Webhook handling: 2 days
- Subscription management: 2 days
- Receipt generation: 1 day
- Testing + edge cases: 2 days

---

### 5. Admin Panel Functionality (PRD Section 8)

#### PRD Requirements:
- **Dashboards**: Membership funnel, MRR, event RSVPs, search usage
- **Membership Ops**: Application queue, approvals, tier/pricing config
- **Content Ops**: Event CRUD, VOD gates, homepage hero, nav, footer
- **Search Ops**: Reindex sources, view top queries, bad results queue
- **Integrations**: BeeHiiv lists, Cloudflare Stream library, Stripe payouts
- **Security**: User roles, audit logs, API keys rotation
- **SEO**: Sitemaps, schema previews, broken links, robots rules

#### Current Implementation:
✅ Admin page routes created
✅ Admin navigation structure
✅ Basic dashboard layout

❌ **Missing:**
- Dashboard analytics/charts
- Application approval queue UI
- Event CRUD forms
- Member management (search, edit, delete)
- Tier/pricing configuration UI
- Search reindexing controls
- Integration settings forms
- Audit log viewer
- Role management UI
- SEO tools (sitemap editor, schema validator)

#### Components Needed:
```typescript
// Dashboards
<MembershipFunnelChart>          // Conversions by stage
<MRRChart>                        // Monthly recurring revenue over time
<RSVPAnalytics>                   // Event attendance trends
<SearchUsageChart>                // Query volume, popular terms

// Application Queue
<ApplicationQueue>
  - Filterable table (status, date, discipline)
  - Quick approve/reject actions
  - Bulk operations
  - Export to CSV

// Event Management
<EventCRUD>
  - Create/edit event form
  - Date/time picker with timezone
  - Capacity limits
  - Pricing settings
  - Visibility controls

// Member Management
<MemberDirectory>
  - Searchable/filterable table
  - Edit member details
  - View subscription status
  - Deactivate/delete accounts
  - Send bulk emails

// Integration Settings
<IntegrationConfig>
  - BeeHiiv API key
  - Cloudflare credentials
  - Stripe webhook secret
  - ZeroDB connection
  - Test connection buttons

// Audit Logs
<AuditLogViewer>
  - Filterable by user, action, date
  - Export logs
  - Retention policy settings
```

#### API Endpoints Needed:
```typescript
// Analytics/Reports
GET    /api/admin/analytics/membership-funnel
GET    /api/admin/analytics/mrr
GET    /api/admin/analytics/rsvps
GET    /api/admin/analytics/search-usage

// Tier Management
GET    /api/admin/tiers
POST   /api/admin/tiers
PUT    /api/admin/tiers/:id
DELETE /api/admin/tiers/:id

// Member Management
GET    /api/admin/members?search=&status=
PUT    /api/admin/members/:id
DELETE /api/admin/members/:id

// Audit Logs
GET    /api/admin/audit-logs?user_id=&action=&start_date=
POST   /api/admin/audit-logs/export

// System Settings
GET    /api/admin/settings
PUT    /api/admin/settings
POST   /api/admin/settings/api-keys/rotate
```

#### Estimated Effort: **2 weeks**
- Dashboard analytics: 3 days
- Application queue: 2 days
- Event CRUD: 2 days
- Member management: 2 days
- Integration settings: 2 days
- Audit logs: 1 day
- Testing: 2 days

---

### 6. Newsletter Integration (BeeHiiv) (PRD Section 4.4)

#### PRD Requirements:
- BeeHiiv API integration for blog/news
- Newsletter opt-in form → BeeHiiv lists
- Automated email sequences (welcome, weekly digest, event announcements)
- Embedded content with canonical links

#### Current Implementation:
✅ Newsletter signup form UI (footer + standalone)
✅ Blog posts hardcoded in TypeScript

❌ **Missing:**
- BeeHiiv API integration
- Form submission backend
- List segmentation (members vs non-members)
- Automated email triggers
- Content import pipeline
- Canonical URL configuration

#### Integration Requirements:
1. **BeeHiiv Setup:**
   - Create BeeHiiv account
   - Configure API credentials
   - Set up audience lists (General, Members, Instructors)
   - Create email templates

2. **Content Sync:**
   - Blog posts published in BeeHiiv
   - Webhook to sync to site database
   - Canonical URL pointing to BeeHiiv or site (per SEO recommendation)

#### API Endpoints Needed:
```typescript
// Newsletter Subscription
POST   /api/newsletter/subscribe              // Add email to BeeHiiv list
POST   /api/newsletter/unsubscribe            // Remove from list
GET    /api/newsletter/status                 // Check subscription status

// Blog Sync (from BeeHiiv)
POST   /api/webhooks/beehiiv/post             // New post published
POST   /api/webhooks/beehiiv/subscriber       // Subscriber event
```

#### Estimated Effort: **1 week**
- BeeHiiv API integration: 2 days
- Form backend: 1 day
- Content sync: 2 days
- Testing: 1 day

---

### 7. Database Schema & Migrations (PRD Section 6)

#### PRD Requirements:
- PostgreSQL via Supabase
- 14+ core entities with relationships
- Audit trails
- GDPR-compliant data retention

#### Current Implementation:
✅ Supabase package installed
✅ TypeScript interfaces defined
✅ Mock data structure

❌ **Missing:**
- Database initialization
- Table creation scripts
- Foreign key relationships
- Indexes for performance
- Row-level security (RLS) policies
- Migration files
- Seed data for development

#### Tables Needed:
```sql
-- Core Tables (from PRD Section 6)
1. users
2. applications
3. approvals
4. membership_tiers
5. subscriptions
6. payments
7. profiles
8. events
9. rsvps
10. training_sessions
11. session_attendance
12. search_queries
13. content_index
14. media_assets
15. audit_logs

-- Additional Tables
16. notifications (email/in-app)
17. user_preferences
18. api_keys (for integrations)
19. rate_limits (IP tracking)
20. content_metadata (for SEO)
```

#### Migration Strategy:
```typescript
// Example migration structure
migrations/
  001_initial_schema.sql
  002_add_approval_workflow.sql
  003_add_search_indexes.sql
  004_add_audit_logs.sql
  005_add_rls_policies.sql
```

#### Estimated Effort: **2 weeks**
- Schema design: 2 days
- Table creation + relationships: 2 days
- Indexes + performance tuning: 1 day
- RLS policies: 2 days
- Migration framework setup: 1 day
- Seed data: 1 day
- Testing + validation: 2 days

---

### 8. Authentication & Authorization (PRD Section 7)

#### PRD Requirements:
- JWT tokens with role claims
- CSRF protection for forms
- Signed URLs for media access
- Session management
- Password reset flow
- Email verification
- OAuth (optional for MVP)

#### Current Implementation:
✅ Auth context with React Context API
✅ Role-based UI rendering
✅ Protected route wrapper
✅ localStorage session persistence

❌ **Missing:**
- JWT token generation/validation
- Refresh token rotation
- CSRF token middleware
- Email verification system
- Password reset flow
- Session expiration handling
- OAuth providers (Google, Apple)
- Rate limiting on auth endpoints
- Account lockout after failed attempts

#### API Endpoints Needed:
```typescript
// Authentication
POST   /api/auth/register                     // Create new account
POST   /api/auth/login                        // Login + return JWT
POST   /api/auth/refresh                      // Refresh access token
POST   /api/auth/logout                       // Invalidate tokens
POST   /api/auth/forgot-password              // Send reset email
POST   /api/auth/reset-password               // Reset with token
POST   /api/auth/verify-email                 // Verify email with token
POST   /api/auth/resend-verification          // Resend verification email

// Session Management
GET    /api/auth/me                           // Get current user
GET    /api/auth/sessions                     // List active sessions
DELETE /api/auth/sessions/:id                 // Revoke session
```

#### Security Considerations:
- Password hashing (bcrypt/argon2)
- JWT secret rotation
- Refresh token storage (database, not localStorage)
- CSRF token validation
- Rate limiting (5 login attempts per 15min)
- Email verification required for sensitive actions
- Session expiration (access: 15min, refresh: 7 days)

#### Estimated Effort: **1 week**
- JWT implementation: 2 days
- Password reset flow: 1 day
- Email verification: 1 day
- Session management: 1 day
- Security hardening: 1 day

---

### 9. Analytics & Observability (PRD Section 12)

#### PRD Requirements:
- Google Analytics 4 with custom events
- OpenTelemetry traces for API latency
- Error budgets and SLO monitoring
- Alerting on p95 > SLO thresholds

#### Current Implementation:
❌ **Missing:**
- GA4 setup
- Custom event tracking
- OpenTelemetry instrumentation
- Error tracking (Sentry/similar)
- Performance monitoring
- Uptime monitoring
- Log aggregation
- Alerting system

#### GA4 Custom Events Needed:
```javascript
// User Actions
- search_started
- search_result_viewed
- search_feedback_submitted
- rsvp_submitted
- rsvp_canceled
- subscription_created
- subscription_canceled
- application_submitted
- application_approved
- application_rejected
- event_joined (live training)
- vod_viewed
- newsletter_subscribed

// Business Metrics
- checkout_started
- payment_completed
- payment_failed
- profile_updated
- belt_rank_updated
```

#### OpenTelemetry Traces:
```typescript
// API Endpoint Instrumentation
- Request start/end timestamps
- HTTP method, path, status code
- User ID, role
- Latency breakdown:
  - Authentication: Xms
  - Database query: Yms
  - External API: Zms
  - Total: Tms
```

#### Monitoring Dashboards:
1. **API Performance**
   - p50, p95, p99 latency by endpoint
   - Error rate (4xx, 5xx)
   - Request volume

2. **Search Performance**
   - Query latency (ZeroDB + AI Registry)
   - Cache hit rate
   - Top queries
   - Failed queries

3. **Business Metrics**
   - New signups (daily, weekly, monthly)
   - Active subscriptions
   - MRR growth
   - Event RSVPs
   - Content engagement

4. **System Health**
   - CPU/memory usage
   - Database connection pool
   - Queue depth (background jobs)
   - CDN hit rate

#### Estimated Effort: **1 week**
- GA4 setup: 1 day
- Custom events: 1 day
- OpenTelemetry instrumentation: 2 days
- Dashboard setup: 1 day
- Alerting configuration: 1 day

---

### 10. Security & Compliance (PRD Section 10)

#### PRD Requirements:
- Cloudflare WAF
- TLS 1.2+, HSTS
- Bot protection, Turnstile CAPTCHA
- Role-based access control (RBAC)
- Audit trails
- GDPR/CCPA compliance (DSR endpoints)
- Privacy policy, cookie banner

#### Current Implementation:
❌ **Missing:**
- Cloudflare WAF configuration
- HSTS headers
- Bot protection
- CAPTCHA on forms
- Audit log system
- GDPR endpoints (data export, deletion)
- Privacy policy page
- Cookie consent banner
- Terms of service

#### Security Checklist:
- [ ] Cloudflare WAF rules configured
- [ ] SSL/TLS certificates installed
- [ ] HSTS, CSP, X-Frame-Options headers
- [ ] Rate limiting on all public endpoints
- [ ] Input validation and sanitization
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (React escaping + CSP)
- [ ] CSRF tokens on mutations
- [ ] Secrets rotation (quarterly)
- [ ] Dependency vulnerability scanning
- [ ] Regular security audits

#### GDPR/CCPA Endpoints:
```typescript
POST   /api/privacy/export-data               // Export user data (JSON)
POST   /api/privacy/delete-account            // Request account deletion
GET    /api/privacy/status                    // Check DSR status
POST   /api/privacy/opt-out                   // Opt out of data collection
```

#### Estimated Effort: **1-2 weeks**
- Cloudflare setup: 1 day
- Security headers: 1 day
- CAPTCHA integration: 1 day
- Audit log system: 2 days
- GDPR endpoints: 2 days
- Legal pages: 1 day
- Cookie banner: 1 day
- Security testing: 2 days

---

### 11. Internationalization (i18n) (PRD Section 13)

#### PRD Requirements:
- Locale routing (`/en`, `/es`, `/jp`)
- Translated content keys
- Right-to-left (RTL) support ready
- Currency/date formatting per locale

#### Current Implementation:
✅ i18n utilities file (`lib/i18n.ts`)

❌ **Missing:**
- Locale detection
- Translation files (JSON)
- Dynamic locale routing
- RTL CSS support
- Currency conversion
- Date/time localization

#### Translation Structure:
```typescript
// locales/en.json
{
  "common": {
    "loading": "Loading...",
    "error": "An error occurred",
    "save": "Save",
    "cancel": "Cancel"
  },
  "nav": {
    "home": "Home",
    "membership": "Membership",
    "events": "Events",
    "search": "Search"
  },
  "membership": {
    "tiers": {
      "basic": {
        "name": "Basic",
        "price": "$29/year",
        "benefits": [...]
      }
    }
  }
}
```

#### Estimated Effort: **1 week** (post-MVP)
- Translation infrastructure: 2 days
- Translation files (3 languages): 2 days
- RTL support: 1 day
- Testing: 1 day

---

### 12. Testing Infrastructure (PRD Section 14)

#### PRD Requirements:
- Unit tests (business logic)
- Integration tests (API endpoints, webhooks)
- E2E tests (user flows)
- Accessibility tests (axe)
- Load tests (search, RTC concurrency)

#### Current Implementation:
❌ **Missing:**
- Test framework setup
- Unit test files
- Integration test files
- E2E test files
- CI/CD test automation
- Code coverage reporting
- Load testing scripts

#### Testing Strategy:
```typescript
// Unit Tests (Jest/Vitest)
- Approval workflow logic
- Role-based permission checks
- Validation functions
- Utility functions

// Integration Tests (Supertest)
- POST /api/applications (create application)
- POST /api/applications/:id/approve (approval workflow)
- POST /api/webhooks/stripe (webhook handling)
- POST /api/search/query (search pipeline)

// E2E Tests (Playwright/Cypress)
- User registration → approval → subscription flow
- Search → view result → feedback
- Event RSVP → payment → attendance
- VOD playback (member-only gating)

// Accessibility Tests (jest-axe)
- All public pages
- Form validation errors
- Modal dialogs
- Keyboard navigation

// Load Tests (k6/Artillery)
- Search endpoint (100 concurrent users)
- RTC room join (50 concurrent users)
- Webhook endpoint (burst of 100 events)
```

#### Estimated Effort: **Ongoing** (1 week initial setup, then continuous)
- Test framework setup: 1 day
- Unit test examples: 2 days
- Integration test examples: 2 days
- E2E test setup: 2 days

---

## 🟡 HIGH PRIORITY GAPS - Frontend Enhancements

### 1. Search Interface Enhancements

#### Current State:
- Basic search input
- Simple result cards

#### PRD Requirements:
- Expandable result details
- Video embedding
- Image embedding
- Source citations
- "Was this helpful?" feedback
- Related queries

#### Components to Build:
```typescript
<SearchResultCard>
  - AI-generated answer (expandable)
  - Video embed (if available)
  - Image gallery (if available)
  - Source links with metadata
  - Feedback buttons
  - "View more" action

<SearchFeedbackModal>
  - Thumbs up/down
  - Optional text feedback
  - Submit button
```

#### Estimated Effort: **1 week**

---

### 2. Board Approval UI

#### Current State:
- No approval interface exists

#### PRD Requirements:
- Application queue with filters
- Two-approval tracking visualization
- Approve/reject actions
- Feedback notes
- Email preview before sending

#### Components to Build:
```typescript
<ApplicationQueue>
  - Filterable table (pending, approved, rejected)
  - Application details modal
  - Approval history timeline
  - Quick actions (approve, reject)

<ApprovalModal>
  - Application details review
  - Reference information
  - Approve/reject buttons
  - Optional note field
  - Email template preview
```

#### Estimated Effort: **3 days**

---

### 3. Live Training Interface

#### Current State:
- Does not exist

#### PRD Requirements:
- RTC video grid
- Audio/video controls
- Participant list
- Chat sidebar
- Screen sharing
- Recording indicator

#### Components to Build:
```typescript
<LiveSessionJoinModal>
  - Event countdown
  - Terms acceptance
  - Join button

<RTCSessionInterface>
  - Video grid (instructor + participants)
  - Audio/video toggle buttons
  - Participant list
  - Chat panel
  - Screen share button
  - Leave session button
  - Recording indicator
```

#### Estimated Effort: **1 week**

---

### 4. Member Dashboard Enhancements

#### Current State:
- Basic dashboard layout
- Profile display

#### PRD Requirements:
- Belt progress visualization
- Payment history table
- Upcoming events
- Recent activity feed
- Subscription management (renew, cancel)

#### Components to Build:
```typescript
<BeltProgressTracker>
  - Current belt rank
  - Progress to next rank
  - Training hours logged
  - Upcoming promotion date

<PaymentHistoryTable>
  - Date, amount, status
  - Download receipt button
  - Invoice links

<SubscriptionCard>
  - Current tier
  - Next billing date
  - Manage subscription (Stripe portal)
  - Upgrade/downgrade options
```

#### Estimated Effort: **1 week**

---

### 5. Event RSVP & Payment Flow

#### Current State:
- Basic RSVP button

#### PRD Requirements:
- Payment flow for paid events
- RSVP confirmation
- Calendar export (.ics)
- Email reminder opt-in

#### Components to Build:
```typescript
<EventRSVPModal>
  - Event details
  - Payment information (if paid)
  - Calendar export option
  - Email reminder checkbox
  - Confirm RSVP button

<RSVPConfirmation>
  - Success message
  - Add to calendar link
  - Event details recap
  - Join instructions (for live events)
```

#### Estimated Effort: **3 days**

---

### 6. Admin Dashboard Enhancements

#### Current State:
- Static admin pages

#### PRD Requirements:
- Interactive dashboards with charts
- CRUD operations for events, members
- Search analytics
- Integration settings

#### Components to Build:
```typescript
<AdminDashboard>
  - KPI cards (MRR, active members, pending approvals)
  - Charts (membership growth, event RSVPs)
  - Recent activity feed
  - Quick actions

<EventCRUDForm>
  - Title, description, date/time
  - Visibility settings
  - Pricing options
  - Capacity limits
  - Save/publish button

<MemberManagementTable>
  - Searchable/filterable
  - Edit member details
  - View subscription
  - Deactivate/delete actions

<SearchAnalyticsDashboard>
  - Top queries
  - Average latency
  - Feedback sentiment
  - Reindex controls
```

#### Estimated Effort: **1.5 weeks**

---

### 7. VOD Player with Gating

#### Current State:
- Does not exist

#### PRD Requirements:
- Video player with controls
- Member-only access verification
- Playback speed options
- Transcript/captions
- Related videos

#### Components to Build:
```typescript
<VODPlayer>
  - Cloudflare Stream embed
  - Custom controls
  - Playback speed selector
  - Quality selector
  - Fullscreen toggle
  - Transcript panel (toggleable)

<MemberOnlyGate>
  - Upgrade prompt for non-members
  - Login prompt for guests
  - Access verification
```

#### Estimated Effort: **3 days**

---

### 8. Application Form Enhancements

#### Current State:
- Basic application form

#### PRD Requirements:
- Reference fields (2-3 references)
- Experience validation
- Discipline selection (multiple)
- File upload (certificates, credentials)
- Form progress indicator

#### Form Fields to Add:
```typescript
<ApplicationForm>
  - Personal info (name, email, phone)
  - Discipline selection (multi-select)
  - Experience level (years, rank)
  - References (name, email, relationship) x3
  - Certificate upload (optional for Instructor tier)
  - Statement of purpose (textarea)
  - Terms acceptance (checkbox)
  - Submit button
```

#### Estimated Effort: **2 days**

---

## 📋 Summary of Estimated Efforts

| Category | Effort | Priority |
|----------|--------|----------|
| **Backend - Critical** | | |
| Membership & Subscriptions | 2-3 weeks | 🔴 Critical |
| AI Semantic Search | 2-3 weeks | 🔴 Critical |
| Live Training (RTC + VOD) | 2 weeks | 🔴 Critical |
| Payment Processing (Stripe) | 1-2 weeks | 🔴 Critical |
| Admin Panel Functionality | 2 weeks | 🔴 Critical |
| Database Schema & Migrations | 2 weeks | 🔴 Critical |
| **Backend - High Priority** | | |
| Newsletter Integration (BeeHiiv) | 1 week | 🟡 High |
| Authentication & Authorization | 1 week | 🟡 High |
| Analytics & Observability | 1 week | 🟡 High |
| Security & Compliance | 1-2 weeks | 🟡 High |
| **Frontend - High Priority** | | |
| Search Interface Enhancements | 1 week | 🟡 High |
| Board Approval UI | 3 days | 🟡 High |
| Live Training Interface | 1 week | 🟡 High |
| Member Dashboard Enhancements | 1 week | 🟡 High |
| Event RSVP & Payment Flow | 3 days | 🟡 High |
| Admin Dashboard Enhancements | 1.5 weeks | 🟡 High |
| VOD Player with Gating | 3 days | 🟡 High |
| Application Form Enhancements | 2 days | 🟡 High |
| **Post-MVP** | | |
| Internationalization (i18n) | 1 week | 🟢 Medium |
| Testing Infrastructure | Ongoing | 🟢 Medium |

**Total Estimated Effort:** 8-11 weeks (aligns with PRD timeline)

---

## 🎯 Implementation Roadmap (Aligned with PRD Section 19)

### Phase 1: Foundation (Weeks 1-2)
- [ ] Database schema design + migrations
- [ ] Authentication system (JWT + sessions)
- [ ] Basic API structure
- [ ] Admin panel layout

### Phase 2: Core Features (Weeks 3-6)
- [ ] Membership application workflow
- [ ] Two-board approval system
- [ ] Stripe integration + subscriptions
- [ ] Event CRUD operations
- [ ] RSVP system
- [ ] Admin approval queue

### Phase 3: Advanced Features (Weeks 5-7)
- [ ] ZeroDB integration + indexing
- [ ] AI Registry integration
- [ ] Search interface + results
- [ ] Cloudflare Calls setup
- [ ] Cloudflare Stream integration
- [ ] Live training interface
- [ ] VOD player

### Phase 4: Content & SEO (Weeks 6-8)
- [ ] BeeHiiv integration
- [ ] Newsletter opt-in backend
- [ ] Schema.org enhancements
- [ ] GA4 + custom events
- [ ] OpenTelemetry instrumentation

### Phase 5: QA & Launch (Weeks 7-10)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security audit
- [ ] Accessibility testing
- [ ] Load testing (search, RTC)
- [ ] Production deployment
- [ ] Monitoring setup

---

## ⚠️ Critical Risks & Mitigation

### Risk 1: ZeroDB Integration Complexity
**Mitigation:** Start indexing pipeline early, use sample data for testing, have fallback to traditional search

### Risk 2: Cloudflare Calls Concurrent Limits
**Mitigation:** Test with 50 concurrent users early, implement queue system if needed, have backup provider

### Risk 3: Stripe Webhook Reliability
**Mitigation:** Implement idempotent handlers, retry logic, manual reconciliation tools

### Risk 4: AI Registry Cost Overruns
**Mitigation:** Aggressive caching, rate limiting, cost monitoring dashboard, usage alerts

### Risk 5: Approval Bottleneck (Board Members)
**Mitigation:** Backup approvers, email reminders, SLA tracking, escalation process

---

## 🔧 Development Environment Setup Needed

### Local Development:
- [ ] Supabase local instance
- [ ] Stripe test mode API keys
- [ ] BeeHiiv sandbox account
- [ ] Cloudflare test accounts
- [ ] ZeroDB development project
- [ ] Redis/KV cache (local)
- [ ] OpenTelemetry collector (local)

### CI/CD Pipeline:
- [ ] GitHub Actions workflows
- [ ] Railway staging environment
- [ ] Railway production environment
- [ ] Automated testing in CI
- [ ] Environment variable management
- [ ] Secret rotation strategy

---

## 📊 Success Metrics Tracking (from PRD Section 2)

To validate implementation success, track these KPIs:

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| **Membership Growth** | +25% in 90 days | 0 (no backend) | Implementation needed |
| **Profile Completion** | ≥70% within 7 days | N/A | Tracking needed |
| **Search Latency** | ≤1.2s p95 | N/A | Implementation + monitoring |
| **Search Adoption** | ≥35% of visitors | N/A | GA4 events needed |
| **SEO Rankings** | 20 keywords top-20 in 60 days | In progress | Continue SEO work |
| **Event RSVP Rate** | ≥20% quarterly | N/A | Implementation needed |
| **Training Call Reliability** | ≥60% p99 uptime | N/A | RTC implementation + monitoring |
| **Support Resolution** | <2 business days | N/A | Support system needed |

---

## 💰 Cost Breakdown (from PRD Section 18)

| Service | Monthly Cost | Status |
|---------|--------------|--------|
| AINative SEO Agent | $100 | ✅ Active |
| AINative APIs | $200 base + usage | ⏳ Pending integration |
| ZeroDB Scale Plan | $99 | ⏳ Pending setup |
| Cloudflare (Calls/Stream/CDN) | Usage-based | ⏳ Pending setup |
| Railway Hosting | $20-50 | ⏳ Pending deployment |
| BeeHiiv | $0-49 | ⏳ Pending setup |
| Stripe | Pass-through fees | ⏳ Pending integration |
| **Estimated Total** | **~$419-518/month** | |

---

## 🎓 Open Questions (from PRD Section 23)

1. **KYC for Instructor Tier:** Do we require manual certificate upload verification?
   - **Recommendation:** Start with optional upload, add manual review post-MVP

2. **Coupons/Referral Links:** Support at launch?
   - **Recommendation:** Post-MVP feature (Stripe supports this natively)

3. **Regional Pricing:** Multi-currency from day one?
   - **Recommendation:** USD only at launch, add currencies post-MVP

4. **Transactional Email Provider:** Postmark vs SendGrid?
   - **Recommendation:** Postmark (better deliverability, cleaner API)

---

## ✅ Next Steps

1. **Review & Prioritize** this gap analysis with stakeholders
2. **Validate cost estimates** for AINative APIs, ZeroDB, Cloudflare
3. **Set up development environments** (Supabase, Stripe test, etc.)
4. **Begin Phase 1** (Database + Auth) immediately
5. **Schedule weekly sprint reviews** to track progress against PRD timeline
6. **Identify blockers** early (API access, credentials, etc.)

---

**Document Status:** Ready for Review
**Next Review Date:** Upon implementation kickoff
**Owner:** Development Team Lead
