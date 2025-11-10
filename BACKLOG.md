# 📋 WWMAA Product Backlog

**Version:** 2.0 - CORRECTED ARCHITECTURE
**Last Updated:** January 2025
**Sprint Duration:** 2 weeks
**Story Point Scale:** Fibonacci (1, 2, 3, 5, 8, 13, 21)

**Tech Stack:** Python Backend + ZeroDB + Next.js Frontend + Railway + Cloudflare Video

---

## 📚 Table of Contents

1. [Epic Overview](#epic-overview)
2. [Sprint Planning Guide](#sprint-planning-guide)
3. [Phase 1: Foundation (Weeks 1-2)](#phase-1-foundation-weeks-1-2)
4. [Phase 2: Core Features (Weeks 3-6)](#phase-2-core-features-weeks-3-6)
5. [Phase 3: Advanced Features (Weeks 5-7)](#phase-3-advanced-features-weeks-5-7)
6. [Phase 4: Content & Analytics (Weeks 6-8)](#phase-4-content--analytics-weeks-6-8)
7. [Phase 5: QA & Launch (Weeks 7-10)](#phase-5-qa--launch-weeks-7-10)
8. [Post-MVP Backlog](#post-mvp-backlog)
9. [Technical Debt & Improvements](#technical-debt--improvements)

---

## Epic Overview

| Epic ID | Epic Name | Priority | Total Story Points | Status | Target Sprint |
|---------|-----------|----------|-------------------|--------|---------------|
| **EP-01** | ZeroDB & Infrastructure | 🔴 Critical | 34 | Not Started | Sprint 1 |
| **EP-02** | Authentication & Authorization | 🔴 Critical | 21 | Not Started | Sprint 1 |
| **EP-03** | Membership Application Workflow | 🔴 Critical | 34 | Not Started | Sprint 2-3 |
| **EP-04** | Payment Processing & Subscriptions | 🔴 Critical | 55 | Not Started | Sprint 3-4 |
| **EP-05** | Event Management System | 🔴 Critical | 34 | Not Started | Sprint 4 |
| **EP-06** | AI-Powered Semantic Search | 🔴 Critical | 55 | Not Started | Sprint 5-6 |
| **EP-07** | Live Training (RTC & VOD) | 🔴 Critical | 55 | Not Started | Sprint 6-7 |
| **EP-08** | Admin Panel & Dashboards | 🔴 Critical | 34 | Not Started | Sprint 4-5 |
| **EP-09** | Newsletter & Content Integration | 🟡 High | 21 | Not Started | Sprint 6 |
| **EP-10** | Analytics & Observability | 🟡 High | 21 | Not Started | Sprint 7 |
| **EP-11** | Security & Compliance | 🟡 High | 34 | Not Started | Sprint 7-8 |
| **EP-12** | Testing & Quality Assurance | 🟡 High | Ongoing | Not Started | All Sprints |
| **EP-13** | Deployment & CI/CD | 🟡 High | 13 | Not Started | Sprint 8 |
| **EP-14** | Internationalization (i18n) | 🟢 Medium | 21 | Not Started | Post-MVP |

**Total Story Points (MVP):** 411
**Estimated Team Velocity:** 40-50 points/sprint (2-week sprints)
**Estimated Duration:** 8-10 sprints (16-20 weeks with buffer)

---

## Sprint Planning Guide

### Team Assumptions
- **Team Size:** 2-3 full-stack developers (Python + React) + 1 designer
- **Velocity:** 40-50 story points per 2-week sprint
- **Definition of Done:**
  - Code complete and peer-reviewed
  - Unit tests written and passing (pytest)
  - Integration tests passing
  - Documentation updated
  - Deployed to staging
  - Product owner acceptance

### Priority Legend
- 🔴 **Critical:** Must-have for MVP launch
- 🟡 **High:** Should-have for MVP, can be delayed slightly
- 🟢 **Medium:** Nice-to-have, post-MVP
- 🔵 **Low:** Future enhancement

---

## Phase 1: Foundation (Weeks 1-2)

### EPIC-01: ZeroDB & Infrastructure Setup

**Epic Owner:** Backend Lead (Python)
**Business Value:** Foundation for all data persistence and retrieval
**Dependencies:** None (blocking epic for most others)
**Total Story Points:** 34

---

#### US-001: ZeroDB Collections & Schema Design
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 1

**As a** developer
**I want** well-designed ZeroDB collections with schemas
**So that** all application data can be stored securely and efficiently via ZeroDB APIs

**Acceptance Criteria:**
- [ ] 14+ collections defined (users, applications, approvals, subscriptions, payments, profiles, events, rsvps, training_sessions, session_attendance, search_queries, content_index, media_assets, audit_logs)
- [ ] Pydantic models created for each collection schema
- [ ] Document relationships defined (reference IDs between collections)
- [ ] created_at and updated_at timestamps in all document schemas
- [ ] UUID primary IDs for all documents
- [ ] Schema validation implemented in Python backend

**Technical Notes:**
- Use ZeroDB HTTP APIs for all CRUD operations
- Create Pydantic models in `/backend/models/schemas.py`
- Document collection structure in `/docs/zerodb-schema.md`
- Create ZeroDB client wrapper in `/backend/services/zerodb_service.py`
- Use Python `uuid` module for ID generation

**Dependencies:** None

---

#### US-002: API-Level Authorization & Access Control
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 1

**As a** system administrator
**I want** authorization policies enforced at the API level
**So that** users can only access data they're authorized to see

**Acceptance Criteria:**
- [ ] Authorization middleware implemented in Python backend
- [ ] Users can only read their own profile data
- [ ] Board members can read all applications
- [ ] Admins can read all data
- [ ] Members can only read member-visible events
- [ ] Public can read public events and articles
- [ ] Authorization policies tested with different user roles
- [ ] Role-based access control (RBAC) decorators created

**Technical Notes:**
- Implement authorization decorators in `/backend/middleware/auth_middleware.py`
- Create role checking functions: `@require_role("admin")`, `@require_auth`, `@require_board_member`
- Document authorization policies in `/docs/authorization.md`
- Enforce at API endpoint level before ZeroDB queries
- Use FastAPI dependencies or Flask decorators

**Dependencies:** US-001

---

#### US-003: ZeroDB Seed Data for Development
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 1

**As a** developer
**I want** realistic seed data in my development ZeroDB collections
**So that** I can test features without manually creating test data

**Acceptance Criteria:**
- [ ] 10+ test users with different roles
- [ ] 5+ pending applications
- [ ] 3+ membership tiers
- [ ] 10+ events (past, present, future)
- [ ] 20+ search queries logged
- [ ] 5+ training sessions with VOD references
- [ ] Seed script is idempotent (can run multiple times)

**Technical Notes:**
- Create `/backend/scripts/seed_data.py` Python script
- Use Faker library for realistic fake data: `pip install faker`
- Don't commit real user data
- Script uses ZeroDB API client to create documents
- Run via: `python backend/scripts/seed_data.py`

**Dependencies:** US-001

---

#### US-004: ZeroDB Client Wrapper Implementation
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 1

**As a** developer
**I want** a configured ZeroDB API client wrapper
**So that** I can query ZeroDB collections from my Python backend

**Acceptance Criteria:**
- [ ] ZeroDB client wrapper created in `/backend/services/zerodb_service.py`
- [ ] Environment variables configured (ZERODB_API_KEY, ZERODB_BASE_URL, ZERODB_PROJECT_ID)
- [ ] CRUD operations implemented (create, read, update, delete, query)
- [ ] Vector search operations implemented
- [ ] Object storage operations implemented (upload, download, delete)
- [ ] Connection tested and working
- [ ] Error handling for API failures
- [ ] Retry logic with exponential backoff

**Technical Notes:**
- Use `requests` library for HTTP calls to ZeroDB API
- Create wrapper class `ZeroDBClient` with methods for all operations
- Implement connection pooling for performance
- Add timeout handling (10 seconds default)
- Example methods: `create_document()`, `get_document()`, `query_documents()`, `vector_search()`, `upload_object()`, `download_object()`

**Dependencies:** US-001

---

#### US-005: ZeroDB Backup & Recovery Strategy
**Priority:** 🟡 High | **Story Points:** 2 | **Sprint:** 1

**As a** system administrator
**I want** data backup and recovery procedures
**So that** we can recover from data loss incidents

**Acceptance Criteria:**
- [ ] ZeroDB backup strategy documented
- [ ] Backup retention policy defined (30 days)
- [ ] Export scripts created for all collections (`/backend/scripts/export_data.py`)
- [ ] Import/restore scripts tested successfully
- [ ] Backup monitoring process documented
- [ ] Critical data export scheduled (daily via cron/scheduler)
- [ ] Backups stored in ZeroDB Object Storage

**Technical Notes:**
- Use ZeroDB API to export collection data to JSON files
- Store backups in **ZeroDB Object Storage** (NOT AWS S3 or Cloudflare R2)
- Document recovery procedures in `/docs/runbook.md`
- Test restore procedure quarterly
- Implement incremental backups for large collections
- Compress backup files before upload to ZeroDB Object Storage

**Dependencies:** US-001

---

#### US-006: API Rate Limiting Infrastructure
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 1

**As a** system administrator
**I want** rate limiting on all API endpoints
**So that** we can prevent abuse and control costs

**Acceptance Criteria:**
- [ ] Rate limiting middleware created
- [ ] IP-based rate limits: 50 req/hr for unauthenticated
- [ ] User-based rate limits: 150 req/hr for authenticated
- [ ] Rate limit headers returned (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] 429 status code returned when limit exceeded
- [ ] Redis configured for rate limit tracking
- [ ] Rate limits configurable per endpoint

**Technical Notes:**
- Use Upstash Redis (Railway add-on)
- Implement sliding window algorithm
- Create `/backend/middleware/rate_limit.py` middleware
- For FastAPI: Use `slowapi` library or custom middleware
- For Flask: Use `Flask-Limiter` library
- Store rate limit data in Redis with TTL

**Dependencies:** None

---

#### US-007: Caching Layer Implementation
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 1

**As a** developer
**I want** a caching layer for expensive ZeroDB queries
**So that** application performance is optimized

**Acceptance Criteria:**
- [ ] Redis cache configured
- [ ] Cache utility functions created (get, set, delete, invalidate)
- [ ] Search results cached (TTL: 5 minutes)
- [ ] Event listings cached (TTL: 10 minutes)
- [ ] Membership tiers cached (TTL: 1 hour)
- [ ] Cache invalidation on data updates
- [ ] Cache hit/miss metrics tracked

**Technical Notes:**
- Use same Redis instance as rate limiting
- Create `/backend/utils/cache.py` utility module
- Use `redis-py` library: `pip install redis`
- Implement cache-aside pattern
- Serialize cached data as JSON
- Example: `cache.get(key)`, `cache.set(key, value, ttl=300)`

**Dependencies:** US-006

---

#### US-008: Environment Configuration Management
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 1

**As a** developer
**I want** environment-specific configuration management
**So that** I can run the app in local, staging, and production environments

**Acceptance Criteria:**
- [ ] `.env` template created with all required variables
- [ ] `.env.example` documented with descriptions
- [ ] Environment variables validated at startup
- [ ] Separate configs for local, staging, production
- [ ] Secrets stored in Railway environment variables
- [ ] No secrets committed to git

**Technical Notes:**
- Required variables (Python Backend):
  - `ZERODB_API_KEY` - ZeroDB authentication
  - `ZERODB_BASE_URL` - ZeroDB API endpoint (e.g., https://api.zerodb.io/v1)
  - `ZERODB_PROJECT_ID` - ZeroDB project identifier
  - `STRIPE_SECRET_KEY` - Stripe payments
  - `STRIPE_WEBHOOK_SECRET` - Stripe webhook validation
  - `JWT_SECRET` - JWT token signing
  - `REDIS_URL` - Redis cache connection
  - `BEEHIIV_API_KEY` - Newsletter integration
  - `CLOUDFLARE_ACCOUNT_ID` - Cloudflare video services
  - `CLOUDFLARE_API_TOKEN` - Cloudflare authentication
  - `AINATIVE_API_KEY` - AI Registry access
  - `POSTMARK_API_KEY` - Transactional emails
  - `PYTHON_ENV` - Environment (development, staging, production)
- Required variables (Next.js Frontend):
  - `NEXT_PUBLIC_BACKEND_API_URL` - Python backend URL
- Use `python-dotenv` library: `pip install python-dotenv`

**Dependencies:** None

---

### EPIC-02: Authentication & Authorization System

**Epic Owner:** Backend Lead (Python)
**Business Value:** Secure user access and role-based permissions
**Dependencies:** EP-01
**Total Story Points:** 21

---

#### US-009: JWT Token Generation & Validation
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 1

**As a** user
**I want** secure authentication with JWT tokens
**So that** my session is secure and I don't need to log in repeatedly

**Acceptance Criteria:**
- [ ] JWT tokens generated on successful login
- [ ] Access tokens expire after 15 minutes
- [ ] Refresh tokens expire after 7 days
- [ ] Tokens include user ID, email, and role claims
- [ ] Token validation middleware created
- [ ] Invalid/expired tokens return 401 Unauthorized
- [ ] JWT secret rotated quarterly (documented procedure)

**Technical Notes:**
- Use `PyJWT` library for Python: `pip install pyjwt`
- Store refresh tokens in ZeroDB users collection
- Create `/backend/services/auth_service.py`
- Implement token generation and validation functions
- Use HS256 algorithm for signing
- Example: `jwt.encode(payload, SECRET, algorithm="HS256")`

**Dependencies:** US-001

---

#### US-010: User Registration & Email Verification
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 1

**As a** new user
**I want** to register for an account and verify my email
**So that** I can access member-only features

**Acceptance Criteria:**
- [ ] Registration form with email, password, name, phone
- [ ] Password strength validation (min 8 chars, uppercase, lowercase, number, special)
- [ ] Duplicate email check via ZeroDB query
- [ ] Verification email sent with token (24-hour expiry)
- [ ] Email verification endpoint (`POST /api/auth/verify-email`)
- [ ] Account status updated to 'verified' on success
- [ ] User cannot access protected resources until verified

**Technical Notes:**
- Use Postmark or SendGrid for transactional emails
- Create email templates in `/backend/templates/emails/`
- Store verification tokens in ZeroDB users collection with expiry field
- Use Python `secrets` module for secure token generation
- API endpoint: `POST /api/auth/register`
- Create endpoint in `/backend/routes/auth.py`

**Dependencies:** US-009

---

#### US-011: Login & Logout Functionality
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 1

**As a** registered user
**I want** to log in and log out securely
**So that** I can access my account and protect my data

**Acceptance Criteria:**
- [ ] Login form with email and password
- [ ] Credentials validated against ZeroDB users collection
- [ ] Access + refresh tokens returned on success
- [ ] Failed login attempts logged
- [ ] Account lockout after 5 failed attempts (15-minute cooldown)
- [ ] Logout invalidates refresh token in ZeroDB
- [ ] Logout clears client-side tokens

**Technical Notes:**
- Hash passwords with bcrypt: `pip install bcrypt`
- Store failed attempts in users document
- Create endpoints in `/backend/routes/auth.py`
- API endpoints: `POST /api/auth/login`, `POST /api/auth/logout`
- Update user document in ZeroDB with login metadata

**Dependencies:** US-009

---

#### US-012: Password Reset Flow
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 1

**As a** user who forgot my password
**I want** to reset my password via email
**So that** I can regain access to my account

**Acceptance Criteria:**
- [ ] "Forgot Password" link on login page
- [ ] Reset email sent with secure token (1-hour expiry)
- [ ] Reset form validates new password strength
- [ ] Password updated on successful reset in ZeroDB
- [ ] Old password no longer works
- [ ] User notified via email that password was changed
- [ ] Token can only be used once

**Technical Notes:**
- Generate cryptographically secure random tokens: `secrets.token_urlsafe(32)`
- Store tokens in ZeroDB users collection with expiry timestamp
- Create endpoints in `/backend/routes/auth.py`
- API endpoints: `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`
- Hash new password with bcrypt before storing

**Dependencies:** US-010

---

#### US-013: Refresh Token Rotation
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 1

**As a** security-conscious user
**I want** automatic token refresh
**So that** I stay logged in without compromising security

**Acceptance Criteria:**
- [ ] Client automatically requests new access token before expiry
- [ ] Refresh token endpoint (`POST /api/auth/refresh`)
- [ ] Old refresh token invalidated on use
- [ ] New refresh token issued and stored in ZeroDB
- [ ] Failed refresh redirects to login
- [ ] Refresh token reuse detected and all sessions invalidated

**Technical Notes:**
- Implement token rotation to prevent replay attacks
- Store refresh tokens in ZeroDB users collection (array of active tokens)
- Create auth middleware decorator in Python backend
- Frontend axios/fetch interceptor for automatic refresh
- Invalidate old token before issuing new one

**Dependencies:** US-009

---

### Summary: Phase 1 Story Points
- **EP-01 (ZeroDB):** 34 points
- **EP-02 (Auth):** 21 points
- **Total:** 55 points
- **Duration:** 2 sprints (4 weeks)

---

## Phase 2: Core Features (Weeks 3-6)

### EPIC-03: Membership Application Workflow

**Epic Owner:** Backend Lead (Python) + Frontend Dev
**Business Value:** Enable new members to apply and get approved
**Dependencies:** EP-01, EP-02
**Total Story Points:** 34

---

#### US-014: Membership Application Form (Frontend)
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 2

**As a** prospective member
**I want** to submit a membership application
**So that** I can join WWMAA

**Acceptance Criteria:**
- [ ] Form includes: name, email, phone, discipline (multi-select), experience years, current rank, 3 references (name, email, relationship), statement of purpose (500 chars)
- [ ] File upload for certificates (optional for Instructor tier)
- [ ] Form validation (required fields, email format, phone format)
- [ ] Terms & conditions checkbox
- [ ] Progress indicator (multi-step form)
- [ ] Submission success message
- [ ] Error handling with clear messages

**Technical Notes:**
- Use react-hook-form + Zod validation (frontend)
- Store uploaded files in **ZeroDB Object Storage** (NOT Cloudflare R2 or AWS S3)
- Create `/app/membership/apply/page.tsx`
- Files uploaded to Python backend first, then to ZeroDB Object Storage

**Dependencies:** US-010 (can be used by unauthenticated users)

---

#### US-015: Application Submission API
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 2

**As a** prospective member
**I want** my application to be securely stored
**So that** Board members can review it

**Acceptance Criteria:**
- [ ] `POST /api/applications` endpoint created
- [ ] Application data validated server-side (Pydantic models)
- [ ] Application document created in ZeroDB applications collection with status 'pending'
- [ ] Duplicate application check (query ZeroDB by email)
- [ ] File uploads processed and stored in ZeroDB Object Storage
- [ ] Confirmation email sent to applicant
- [ ] Notification email sent to Board members
- [ ] Application ID returned in response

**Technical Notes:**
- Create document in ZeroDB applications collection
- Store references as nested dict/JSON in document
- Send emails via Postmark
- Validate file types and sizes in Python backend
- Create endpoint in `/backend/routes/applications.py`
- Upload files to ZeroDB Object Storage via Object API
- Store object IDs in application document

**Dependencies:** US-001, US-010

---

#### US-016: Board Member Approval Queue
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 2

**As a** Board member
**I want** to see a queue of pending applications
**So that** I can review and approve/reject them

**Acceptance Criteria:**
- [ ] Board dashboard shows pending applications
- [ ] Filterable by status (pending, approved, rejected)
- [ ] Sortable by submission date
- [ ] Search by applicant name or email
- [ ] Application details modal with all info
- [ ] Reference information displayed
- [ ] Uploaded certificates viewable (from ZeroDB Object Storage)
- [ ] Approval history visible (who approved, when)
- [ ] Approve/reject buttons
- [ ] Bulk actions (approve selected, reject selected)

**Technical Notes:**
- Create `/app/dashboard/board/applications/page.tsx`
- Use shadcn/ui Table component
- Implement server-side pagination (query ZeroDB with limit/offset)
- Poll Python backend API for updates (every 30 seconds) or implement WebSocket
- Backend endpoint: `GET /api/applications?status=&page=&limit=`
- Download certificates from ZeroDB Object Storage for display

**Dependencies:** US-015

---

#### US-017: Two-Approval Workflow Logic
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 2

**As a** system administrator
**I want** applications to require two distinct Board member approvals
**So that** we maintain quality standards

**Acceptance Criteria:**
- [ ] First Board member can approve (creates Approval document in ZeroDB)
- [ ] Second Board member can approve (creates second Approval document)
- [ ] Same Board member cannot approve twice (validate in Python)
- [ ] After second approval, application status → 'approved'
- [ ] User role automatically upgraded to 'Member' in ZeroDB
- [ ] Welcome email sent with next steps
- [ ] Stripe subscription creation triggered
- [ ] Audit log records all approvals in ZeroDB
- [ ] Board members notified when first approval received

**Technical Notes:**
- Create `POST /api/applications/:id/approve` endpoint
- Query ZeroDB approvals collection for existing approvals by same user
- Use Python logic to enforce two-approval rule
- Update application document and user document atomically
- Trigger webhook to Stripe for subscription creation

**Dependencies:** US-016

---

#### US-018: Application Rejection Flow
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 2

**As a** Board member
**I want** to reject applications with a reason
**So that** applicants understand why they were not accepted

**Acceptance Criteria:**
- [ ] Reject button on application details
- [ ] Optional reason field (text input)
- [ ] Application status → 'rejected' in ZeroDB
- [ ] Rejection email sent to applicant with reason (if provided)
- [ ] Rejected applications filterable in queue
- [ ] Rejection recorded in audit log (ZeroDB)
- [ ] No Stripe subscription created

**Technical Notes:**
- Create `POST /api/applications/:id/reject` endpoint in `/backend/routes/applications.py`
- Store rejection reason in applications document
- Send polite rejection email template via Postmark

**Dependencies:** US-016

---

#### US-019: Applicant Status Portal
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 2

**As an** applicant
**I want** to check the status of my application
**So that** I know where I stand in the process

**Acceptance Criteria:**
- [ ] Status page accessible via link in confirmation email
- [ ] Shows current status: Pending, Approved (1 of 2), Approved, Rejected
- [ ] Displays submission date
- [ ] Shows expected timeline
- [ ] If rejected, displays reason
- [ ] If approved, shows onboarding next steps

**Technical Notes:**
- Create `/app/application-status/[id]/page.tsx`
- Use secure token for unauthenticated access
- Implement loading states
- Query ZeroDB for application and approvals data

**Dependencies:** US-015

---

#### US-020: Application Analytics for Admin
**Priority:** 🟢 Medium | **Story Points:** 2 | **Sprint:** 2

**As an** administrator
**I want** to see application metrics
**So that** I can understand our membership funnel

**Acceptance Criteria:**
- [ ] Dashboard shows: Total applications, Pending, Approved, Rejected
- [ ] Approval rate percentage
- [ ] Average time to approval
- [ ] Applications by discipline (chart)
- [ ] Applications over time (line chart)
- [ ] Export to CSV

**Technical Notes:**
- Create `/app/admin/analytics/applications/page.tsx`
- Use Recharts for visualizations
- Query aggregations from ZeroDB applications collection
- Cache results with Redis

**Dependencies:** US-015

---

### EPIC-04: Payment Processing & Subscriptions

**Epic Owner:** Backend Lead (Python)
**Business Value:** Generate revenue through membership fees
**Dependencies:** EP-01, EP-02, EP-03
**Total Story Points:** 55

---

#### US-021: Stripe Account Setup & Configuration
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 3

**As a** system administrator
**I want** Stripe configured for production and test modes
**So that** we can process payments securely

**Acceptance Criteria:**
- [ ] Stripe account created
- [ ] API keys obtained (test and live)
- [ ] Webhook endpoint configured in Stripe dashboard
- [ ] Products created for each membership tier
- [ ] Prices set (Basic: $29/yr, Premium: $79/yr, Instructor: $149/yr)
- [ ] Subscription settings configured (billing cycle, trial, grace period)
- [ ] Payment methods enabled (card, ACH)
- [ ] Test mode validated with test cards

**Technical Notes:**
- Create products in Stripe Dashboard
- Configure webhook URL: `https://api.wwmaa.com/api/webhooks/stripe`
- Store webhook secret in environment variables
- Document test card numbers in `/docs/stripe-testing.md`
- Use `stripe` Python library: `pip install stripe`

**Dependencies:** None (can start in parallel)

---

#### US-022: Checkout Session Creation
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 3

**As a** newly approved member
**I want** to complete my membership payment
**So that** I can access member benefits

**Acceptance Criteria:**
- [ ] After second approval, user receives email with payment link
- [ ] Clicking link redirects to Stripe Checkout
- [ ] Checkout displays correct membership tier and price
- [ ] User can enter payment details securely (Stripe hosted)
- [ ] Successful payment redirects to success page
- [ ] Failed payment redirects to error page with retry option
- [ ] Subscription created in Stripe
- [ ] Subscription ID stored in ZeroDB subscriptions collection

**Technical Notes:**
- Create `POST /api/checkout/create-session` endpoint
- Use Stripe Checkout (hosted page, not embedded)
- Set success_url and cancel_url
- Include metadata (user_id, tier_id, application_id)
- Python: `stripe.checkout.Session.create()`

**Dependencies:** US-017, US-021

---

#### US-023: Stripe Webhook Handler
**Priority:** 🔴 Critical | **Story Points:** 13 | **Sprint:** 3

**As a** system
**I want** to handle Stripe webhook events
**So that** subscription status stays synchronized with ZeroDB

**Acceptance Criteria:**
- [ ] Webhook endpoint: `POST /api/webhooks/stripe`
- [ ] Signature verification (HMAC)
- [ ] Handles event types:
  - `checkout.session.completed` → Create subscription document in ZeroDB, activate membership
  - `invoice.paid` → Record payment in ZeroDB payments collection
  - `invoice.payment_failed` → Update subscription status, send dunning email
  - `customer.subscription.updated` → Update subscription details in ZeroDB
  - `customer.subscription.deleted` → Deactivate membership, downgrade to guest
  - `charge.refunded` → Update payment record in ZeroDB, handle refund logic
- [ ] Idempotent processing (event ID check in ZeroDB)
- [ ] Error handling and retry logic
- [ ] Events logged in audit_logs collection (ZeroDB)
- [ ] Returns 200 OK to Stripe within 5 seconds

**Technical Notes:**
- Use `stripe.Webhook.construct_event()` for verification
- Store processed event IDs in ZeroDB to prevent duplicate processing
- Create/update documents in ZeroDB atomically
- Log all webhook events for debugging
- Create endpoint in `/backend/routes/webhooks.py`

**Dependencies:** US-022

---

#### US-024: Subscription Management (Member Portal)
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 3

**As a** member
**I want** to manage my subscription
**So that** I can upgrade, downgrade, or cancel

**Acceptance Criteria:**
- [ ] Member dashboard shows current subscription from ZeroDB
- [ ] Displays tier name, price, next billing date
- [ ] "Manage Subscription" button redirects to Stripe Customer Portal
- [ ] Customer Portal allows:
  - Update payment method
  - View invoices
  - Download receipts
  - Cancel subscription
  - Reactivate canceled subscription
- [ ] Changes in Stripe sync back to ZeroDB via webhooks
- [ ] Canceled subscriptions retain access until period end

**Technical Notes:**
- Use Stripe Customer Portal (no custom UI needed)
- Create `POST /api/billing/portal` to generate portal session
- Configure portal settings in Stripe Dashboard
- Python: `stripe.billing_portal.Session.create()`
- Query subscription from ZeroDB subscriptions collection

**Dependencies:** US-023

---

#### US-025: Payment History & Receipts
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 3

**As a** member
**I want** to view my payment history and download receipts
**So that** I can track expenses and file taxes

**Acceptance Criteria:**
- [ ] Payment history table on member dashboard
- [ ] Columns: Date, Amount, Status, Invoice, Receipt
- [ ] Download PDF receipt button
- [ ] Download invoice button
- [ ] Filter by date range
- [ ] Shows payment method used
- [ ] Pagination for long histories

**Technical Notes:**
- Create `GET /api/payments` endpoint
- Fetch from ZeroDB payments collection (query by user_id)
- Link to Stripe-hosted invoice and receipt URLs
- Use shadcn/ui Table component (frontend)
- Implement pagination (limit/offset)

**Dependencies:** US-023

---

#### US-026: Failed Payment Dunning
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 3

**As a** system administrator
**I want** automated dunning for failed payments
**So that** we can recover revenue and retain members

**Acceptance Criteria:**
- [ ] When `invoice.payment_failed` webhook received:
  - Send dunning email to member
  - Email includes retry payment link
  - Update subscription status to 'past_due' in ZeroDB
- [ ] Retry schedule: Day 3, Day 7, Day 14
- [ ] After 14 days, subscription canceled and member downgraded in ZeroDB
- [ ] Dunning emails track opens and clicks
- [ ] Member notified before cancellation (Day 12 warning)
- [ ] Grace period configurable (default: 14 days)

**Technical Notes:**
- Use Stripe's Smart Retries (configurable in Dashboard)
- Send emails via Postmark with tracking
- Create email templates for each dunning stage
- Use Python scheduler (APScheduler) or cron job for retry checks
- Update user role in ZeroDB on cancellation

**Dependencies:** US-023

---

#### US-027: Subscription Analytics
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 4

**As an** administrator
**I want** to see subscription metrics
**So that** I can understand revenue and churn

**Acceptance Criteria:**
- [ ] Dashboard shows:
  - Monthly Recurring Revenue (MRR)
  - Annual Recurring Revenue (ARR)
  - Active subscriptions by tier
  - New subscriptions this month
  - Canceled subscriptions this month
  - Churn rate
  - Customer Lifetime Value (LTV)
- [ ] Charts: MRR over time, Tier distribution (pie chart)
- [ ] Export to CSV
- [ ] Date range filter

**Technical Notes:**
- Create `/app/admin/analytics/subscriptions/page.tsx`
- Query aggregations from ZeroDB subscriptions and payments collections
- Use Recharts for visualizations
- Cache results with Redis for performance

**Dependencies:** US-023

---

#### US-028: Refund Processing
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 4

**As an** administrator
**I want** to process refunds for members
**So that** we can handle cancellations and disputes

**Acceptance Criteria:**
- [ ] Admin can initiate refund from member detail page
- [ ] Refund form: amount, reason, partial/full
- [ ] Refund processed in Stripe
- [ ] `charge.refunded` webhook updates payment record in ZeroDB
- [ ] Subscription canceled if full refund
- [ ] Member notified via email
- [ ] Refund recorded in audit log (ZeroDB)

**Technical Notes:**
- Create `POST /api/admin/refunds` endpoint
- Use Stripe Refund API: `stripe.Refund.create()`
- Validate refund amount ≤ original charge
- Implement refund reason tracking in ZeroDB
- Update payment document with refund status

**Dependencies:** US-023

---

### EPIC-05: Event Management System

**Epic Owner:** Full-stack Dev (Python + React)
**Business Value:** Enable event registration and attendance tracking
**Dependencies:** EP-01, EP-02, EP-04
**Total Story Points:** 34

---

#### US-029: Event CRUD Operations (Admin)
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 4

**As an** administrator
**I want** to create, edit, and delete events
**So that** I can manage our event calendar

**Acceptance Criteria:**
- [ ] Admin event management page
- [ ] Create event form:
  - Title, description, start/end datetime with timezone
  - Location (address or "Online")
  - Type (live_training, seminar, tournament, certification)
  - Visibility (public, members_only)
  - Capacity limit (optional)
  - Price (optional, $0 for free)
  - Featured image upload
- [ ] Edit event (all fields editable)
- [ ] Delete event (with confirmation, soft delete in ZeroDB)
- [ ] Deleted events archive
- [ ] Duplicate event feature
- [ ] Publish/unpublish toggle

**Technical Notes:**
- Create `/app/admin/events/page.tsx` and `/app/admin/events/new/page.tsx`
- API endpoints in `/backend/routes/events.py`:
  - `POST /api/events`
  - `PUT /api/events/:id`
  - `DELETE /api/events/:id` (soft delete: status='deleted')
- Store images in **ZeroDB Object Storage**
- Validate dates (end after start) in Python
- Create/update documents in ZeroDB events collection

**Dependencies:** US-001

---

#### US-030: Event Listing & Filtering (Public)
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 4

**As a** visitor
**I want** to browse upcoming events
**So that** I can find training opportunities

**Acceptance Criteria:**
- [ ] Event listing page shows upcoming events
- [ ] Card layout with image, title, date, location, price
- [ ] Filter by:
  - Event type
  - Date range
  - Location (in-person, online)
  - Price (free, paid)
- [ ] Sort by: Date (asc/desc), Price
- [ ] Pagination (12 events per page)
- [ ] "Members Only" badge for restricted events
- [ ] Click event card → event detail page

**Technical Notes:**
- Enhance existing `/app/events/page.tsx`
- Create `GET /api/events?type=&date_from=&date_to=&visibility=public`
- Query ZeroDB events collection with filters
- Cache results with Redis (10-minute TTL)
- Show only public events for unauthenticated users

**Dependencies:** US-029

---

#### US-031: Event Detail Page
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 4

**As a** visitor
**I want** to see full event details
**So that** I can decide whether to register

**Acceptance Criteria:**
- [ ] Event detail page shows:
  - Featured image (from ZeroDB Object Storage)
  - Title, description (formatted HTML)
  - Date/time with timezone and "Add to Calendar" button
  - Location with map embed (if in-person)
  - Instructor/speaker info
  - Price and payment details
  - Capacity (X spots remaining)
  - RSVP button (or "Members Only" message)
- [ ] Schema.org Event markup for SEO
- [ ] Social sharing buttons (Twitter, Facebook, LinkedIn)
- [ ] Related events section

**Technical Notes:**
- Create `/app/events/[id]/page.tsx`
- Use Google Maps Embed API for location
- Generate .ics file for calendar export
- Implement OG metadata for social sharing
- Query ZeroDB events collection for event details

**Dependencies:** US-030

---

#### US-032: Event RSVP System
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 4

**As a** member
**I want** to RSVP for events
**So that** I can secure my spot

**Acceptance Criteria:**
- [ ] RSVP button on event detail page
- [ ] For free events:
  - Confirm RSVP modal
  - RSVP recorded immediately in ZeroDB
  - Confirmation email sent
- [ ] For paid events:
  - Redirect to Stripe Checkout
  - RSVP recorded after successful payment
  - Ticket/confirmation email sent
- [ ] Capacity check (reject if full)
- [ ] Member can cancel RSVP (up to 24 hours before event)
- [ ] Cancellation refund policy enforced
- [ ] RSVP status visible on event page ("You're registered!")

**Technical Notes:**
- Create `POST /api/events/:id/rsvp` endpoint
- For paid events, create Stripe payment intent
- Link payment_id to RSVP document in ZeroDB rsvps collection
- Send different email templates for free vs paid
- Check event capacity before allowing RSVP

**Dependencies:** US-031, US-022 (Stripe checkout)

---

#### US-033: Attendee Management (Admin)
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 4

**As an** event organizer
**I want** to see who's registered for my event
**So that** I can plan accordingly

**Acceptance Criteria:**
- [ ] Event detail page (admin view) shows attendee list
- [ ] Attendee info: Name, email, phone, RSVP date, payment status
- [ ] Export attendee list to CSV
- [ ] Send bulk email to attendees
- [ ] Check-in feature (mark as attended)
- [ ] No-show tracking
- [ ] Waitlist management if event is full

**Technical Notes:**
- Create `GET /api/events/:id/attendees` (admin only)
- Query ZeroDB rsvps collection filtered by event_id
- Use shadcn/ui Table component
- Implement check-in via QR code (future enhancement)

**Dependencies:** US-032

---

#### US-034: Event Calendar View
**Priority:** 🟢 Medium | **Story Points:** 3 | **Sprint:** 4

**As a** user
**I want** to see events in a calendar view
**So that** I can visualize my schedule

**Acceptance Criteria:**
- [ ] Calendar view on events page (toggle with list view)
- [ ] Month, week, day views
- [ ] Events displayed on correct dates
- [ ] Click event → event detail modal
- [ ] Color-coded by event type
- [ ] Filter still works in calendar view

**Technical Notes:**
- Use `react-big-calendar` or `@fullcalendar/react`
- Integrate with existing event filtering
- Responsive on mobile
- Query events from ZeroDB with date range

**Dependencies:** US-030

---

### Summary: Phase 2 Story Points
- **EP-03 (Membership):** 34 points
- **EP-04 (Payments):** 55 points
- **EP-05 (Events):** 34 points
- **Total:** 123 points
- **Duration:** 3-4 sprints (6-8 weeks)

---

## Phase 3: Advanced Features (Weeks 5-7)

### EPIC-06: AI-Powered Semantic Search

**Epic Owner:** Full-stack Dev + AI Specialist (Python)
**Business Value:** Differentiate with best-in-class martial arts search
**Dependencies:** EP-01, EP-02
**Total Story Points:** 55

---

#### US-035: ZeroDB Vector Search Setup
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 5

**As a** developer
**I want** ZeroDB vector search configured
**So that** I can perform semantic search on content

**Acceptance Criteria:**
- [ ] ZeroDB vector search API tested and working
- [ ] Collection for content embeddings created
- [ ] Embedding dimensions configured (1536 for OpenAI ada-002)
- [ ] Similarity metric set (cosine similarity)
- [ ] Connection tested from Python backend
- [ ] Vector search query tested with sample data

**Technical Notes:**
- Use existing ZeroDB API client from US-004
- Create content_index collection with vector field
- Use `vector_search()` method from ZeroDBClient
- Store metadata with vectors: source_type, source_id, url, title
- Document vector schema in `/docs/zerodb-vector-schema.md`

**Dependencies:** US-004 (ZeroDB client)

---

#### US-036: Content Indexing Pipeline
**Priority:** 🔴 Critical | **Story Points:** 13 | **Sprint:** 5

**As a** system administrator
**I want** content automatically indexed in ZeroDB
**So that** search results are up-to-date

**Acceptance Criteria:**
- [ ] Indexing pipeline for content types:
  - Blog articles (title, content, keywords)
  - Events (title, description, location)
  - Training videos (title, transcript, metadata)
  - Member profiles (name, bio, discipline)
- [ ] Content chunked for optimal retrieval (500 tokens per chunk)
- [ ] Embeddings generated via OpenAI API
- [ ] Embeddings stored in ZeroDB content_index collection
- [ ] Incremental indexing (only new/updated content)
- [ ] Reindex command for full refresh
- [ ] Indexing status visible in admin panel

**Technical Notes:**
- Create background job with APScheduler or Celery
- Use OpenAI text-embedding-ada-002 model: `pip install openai`
- Store metadata: source_type, source_id, url, title, created_at
- Create `/backend/services/indexing_service.py`
- Chunk text using LangChain or custom chunker

**Dependencies:** US-035

---

#### US-037: AINative AI Registry Integration
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 5

**As a** developer
**I want** AI Registry configured for LLM orchestration
**So that** I can generate AI-powered answers

**Acceptance Criteria:**
- [ ] AI Registry API key configured
- [ ] LLM model selected (GPT-4 or Claude)
- [ ] Prompt templates created for:
  - General martial arts questions
  - Technique explanations
  - History and philosophy
  - Training recommendations
- [ ] Context window management (stay under token limits)
- [ ] Response streaming enabled
- [ ] Token usage tracked for cost monitoring
- [ ] Fallback model configured for failures

**Technical Notes:**
- Create `/backend/services/ai_registry_service.py`
- Store prompt templates in `/backend/prompts/`
- Implement retry logic with exponential backoff
- Log all LLM requests for debugging
- Use AINative AI Registry API endpoint

**Dependencies:** None (can start in parallel)

---

#### US-038: Search Query Endpoint
**Priority:** 🔴 Critical | **Story Points:** 13 | **Sprint:** 5

**As a** user
**I want** to search for martial arts information
**So that** I can learn and find resources

**Acceptance Criteria:**
- [ ] `POST /api/search/query` endpoint
- [ ] Query processing pipeline:
  1. Normalize query (lowercase, trim)
  2. Check rate limit (IP-based)
  3. Check cache (5-minute TTL in Redis)
  4. Generate query embedding (OpenAI)
  5. ZeroDB vector search (top 10 results)
  6. Send context to AI Registry
  7. Get LLM answer
  8. Attach relevant media (videos from Cloudflare Stream, images from ZeroDB Object Storage)
  9. Cache result in Redis
  10. Log query in ZeroDB
  11. Return formatted response
- [ ] Response format:
  - `answer` (string, markdown)
  - `sources` (array of source objects)
  - `media` (array of video/image objects)
  - `related_queries` (array of strings)
  - `latency_ms` (number)
- [ ] Error handling for each step
- [ ] Timeout after 10 seconds

**Technical Notes:**
- Implement as async function with parallel operations where possible
- Use Redis caching aggressively to reduce costs
- Create endpoint in `/backend/routes/search.py`
- Target p95 latency < 1.2s
- Store media references (videos in Cloudflare Stream, images in ZeroDB Object Storage)

**Dependencies:** US-035, US-036, US-037

---

#### US-039: Search Results UI
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 5

**As a** user
**I want** search results displayed beautifully
**So that** I can easily understand the answer

**Acceptance Criteria:**
- [ ] Search results page shows:
  - AI-generated answer (expandable/collapsible)
  - Video embed (if available, Cloudflare Stream)
  - Image gallery (if available, from ZeroDB Object Storage)
  - Source citations with links
  - "Was this helpful?" feedback buttons
  - Related queries
- [ ] Loading state with skeleton UI
- [ ] Error state with retry button
- [ ] Syntax highlighting for code snippets in answer
- [ ] Responsive design (mobile-friendly)

**Technical Notes:**
- Enhance `/app/search/page.tsx`
- Use react-markdown for rendering
- Implement lazy loading for media
- Add schema.org SearchResultsPage markup
- Embed videos using Cloudflare Stream player

**Dependencies:** US-038

---

#### US-040: Search Feedback System
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 5

**As a** user
**I want** to provide feedback on search results
**So that** the system improves over time

**Acceptance Criteria:**
- [ ] Thumbs up/down buttons on results
- [ ] Optional text feedback (textarea)
- [ ] Feedback stored in ZeroDB search_queries collection
- [ ] Admin can view feedback in analytics
- [ ] Negative feedback flagged for review
- [ ] Feedback anonymous (only IP hash stored)

**Technical Notes:**
- Create `POST /api/search/feedback` endpoint
- Update search query document in ZeroDB with feedback field
- Create admin page: `/app/admin/search/feedback/page.tsx`

**Dependencies:** US-038

---

#### US-041: Search Analytics Dashboard
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 6

**As an** administrator
**I want** to see search usage analytics
**So that** I can understand what users are searching for

**Acceptance Criteria:**
- [ ] Dashboard shows:
  - Total searches (daily, weekly, monthly)
  - Top 20 queries
  - Average latency (p50, p95, p99)
  - Cache hit rate
  - Feedback sentiment (% positive)
  - Failed queries (errors, timeouts)
  - Cost per query (AI Registry + ZeroDB)
- [ ] Query detail view (click query → see all searches, results, feedback)
- [ ] Export queries to CSV
- [ ] Trending queries (what's popular this week)

**Technical Notes:**
- Create `/app/admin/analytics/search/page.tsx`
- Use Recharts for visualizations
- Query ZeroDB search_queries collection with aggregations
- Cache dashboard data with Redis (1-hour TTL)

**Dependencies:** US-038, US-040

---

#### US-042: Media Asset Management
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 6

**As an** administrator
**I want** to manage media assets for search results
**So that** I can control what videos/images are shown

**Acceptance Criteria:**
- [ ] Media library page in admin
- [ ] Upload images to ZeroDB Object Storage
- [ ] Link videos from Cloudflare Stream
- [ ] Tag media with:
  - Title, description
  - Discipline, technique
  - License type (owned, CC, licensed)
  - Searchable keywords
- [ ] Edit media metadata
- [ ] Delete media (soft delete in ZeroDB)
- [ ] Preview media
- [ ] Link media to search topics

**Technical Notes:**
- Create `/app/admin/media/page.tsx`
- Use ZeroDB Object Storage API for image uploads
- Store video references to Cloudflare Stream
- Store metadata in ZeroDB media_assets collection
- Implement drag-and-drop upload

**Dependencies:** US-036

---

### EPIC-07: Live Training (RTC & VOD)

**Epic Owner:** Full-stack Dev + Video Specialist (Python)
**Business Value:** Enable live and recorded training sessions
**Dependencies:** EP-01, EP-02, EP-05
**Total Story Points:** 55

---

#### US-043: Cloudflare Calls Setup (WebRTC)
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 6

**As a** developer
**I want** Cloudflare Calls configured for WebRTC
**So that** I can host live video sessions

**Acceptance Criteria:**
- [ ] Cloudflare account with Calls enabled
- [ ] API credentials configured
- [ ] Test room created and validated
- [ ] Signed URL generation working
- [ ] Recording API configured
- [ ] Webhook endpoint for recording ready events
- [ ] Documentation for room lifecycle

**Technical Notes:**
- Create `/backend/services/cloudflare_calls_service.py`
- Store credentials in environment variables
- Test with multiple participants (min 10)
- Cloudflare Calls API endpoint: `https://api.cloudflare.com/client/v4/accounts/{account_id}/calls`

**Dependencies:** None (can start early)

---

#### US-044: Live Session Creation & Scheduling
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 6

**As an** instructor
**I want** to schedule a live training session
**So that** members can join at the specified time

**Acceptance Criteria:**
- [ ] Admin/instructor can create training session linked to event
- [ ] Session includes:
  - Event ID (FK to ZeroDB events collection)
  - Start time, estimated duration
  - Capacity limit
  - Recording enabled/disabled
  - Chat enabled/disabled
- [ ] Cloudflare Calls room created automatically
- [ ] Room ID stored in ZeroDB training_sessions collection
- [ ] Session visible on event detail page
- [ ] Countdown timer shows time until start
- [ ] Join button appears 10 minutes before start

**Technical Notes:**
- Create `POST /api/training/sessions` endpoint
- Generate room via Cloudflare Calls API
- Store in ZeroDB training_sessions collection
- Create Python scheduler job to create rooms 1 hour before start

**Dependencies:** US-043, US-031 (event detail)

---

#### US-045: Join Live Session UI
**Priority:** 🔴 Critical | **Story Points:** 13 | **Sprint:** 6

**As a** member
**I want** to join a live training session
**So that** I can learn from instructors in real-time

**Acceptance Criteria:**
- [ ] "Join Session" button on event page (visible 10 min before start)
- [ ] Auth check (members only)
- [ ] Payment verification (if paid event)
- [ ] Terms acceptance modal
- [ ] Redirect to RTC interface
- [ ] RTC interface includes:
  - Instructor video (large)
  - Participant videos (grid, max 49 visible)
  - Audio/video toggle buttons
  - Screen share button (instructor only)
  - Chat panel (side or bottom)
  - Participant list with names
  - "Leave Session" button
  - Recording indicator (red dot)
  - Connection quality indicator
  - Reaction buttons (👍, 👏, ❤️)
- [ ] Keyboard shortcuts (space=mute, v=video, s=share)
- [ ] Mobile-responsive layout

**Technical Notes:**
- Create `/app/training/[sessionId]/live/page.tsx`
- Use WebRTC APIs (getUserMedia, RTCPeerConnection)
- Implement adaptive bitrate based on connection
- Use shadcn/ui Dialog for modals
- Store attendance in ZeroDB session_attendance collection

**Dependencies:** US-044

---

#### US-046: Live Session Recording
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 6

**As an** instructor
**I want** live sessions automatically recorded
**So that** members who missed it can watch later

**Acceptance Criteria:**
- [ ] Recording starts automatically when session starts
- [ ] Recording captures:
  - Instructor video and audio
  - Screen share content
  - Chat messages (as overlay or separate file)
- [ ] Recording stops when session ends
- [ ] Recording uploaded to Cloudflare Stream automatically
- [ ] Webhook received when upload complete
- [ ] VOD ID stored in ZeroDB training_sessions collection
- [ ] Recording available within 10 minutes of session end

**Technical Notes:**
- Use Cloudflare Calls Recording API
- Configure webhook: `POST /api/webhooks/cloudflare/recording`
- Handle recording failures gracefully
- Store recording duration and file size in ZeroDB

**Dependencies:** US-045

---

#### US-047: Cloudflare Stream Integration (VOD)
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 6

**As a** developer
**I want** Cloudflare Stream configured for VOD
**So that** I can store and serve training videos

**Acceptance Criteria:**
- [ ] Cloudflare Stream account configured
- [ ] API credentials stored
- [ ] Test video uploaded and played
- [ ] Signed URLs working for member-only videos
- [ ] Thumbnail generation enabled
- [ ] Captions/transcript support enabled
- [ ] Webhook for processing complete events

**Technical Notes:**
- Create `/backend/services/cloudflare_stream_service.py`
- Store credentials in environment variables
- Use TUS protocol for resumable uploads
- Configure webhook: `POST /api/webhooks/cloudflare/stream`
- Cloudflare Stream API: `https://api.cloudflare.com/client/v4/accounts/{account_id}/stream`

**Dependencies:** None (can start in parallel)

---

#### US-048: VOD Player with Access Control
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 7

**As a** member
**I want** to watch recorded training sessions
**So that** I can learn at my own pace

**Acceptance Criteria:**
- [ ] VOD accessible from event detail page
- [ ] Member-only gate (login required)
- [ ] Tier-based access (e.g., Premium+ only)
- [ ] Video player with controls:
  - Play/pause
  - Seek bar
  - Volume control
  - Playback speed (0.5x, 1x, 1.25x, 1.5x, 2x)
  - Quality selector (auto, 1080p, 720p, 480p)
  - Fullscreen toggle
  - Picture-in-picture
  - Keyboard shortcuts (space=play, f=fullscreen, j/l=skip)
- [ ] Transcript panel (toggleable, synced with video)
- [ ] Bookmarks (save timestamp notes)
- [ ] Watch progress saved in ZeroDB
- [ ] Related videos section

**Technical Notes:**
- Create `/app/training/[sessionId]/vod/page.tsx`
- Use Cloudflare Stream Player embed
- Generate signed URLs with 24-hour expiry for member-only videos
- Store watch progress in ZeroDB session_attendance collection
- Implement lazy loading for related videos

**Dependencies:** US-046, US-047

---

#### US-049: Training Session Analytics
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 7

**As an** instructor
**I want** to see analytics for my training sessions
**So that** I can understand engagement

**Acceptance Criteria:**
- [ ] Session detail page (admin view) shows:
  - Total registered vs attended
  - Peak concurrent viewers
  - Average watch time (for VOD)
  - Drop-off points (where people left)
  - Chat message count
  - Recording views (if VOD)
  - Feedback/ratings from attendees
- [ ] Export attendance report to CSV
- [ ] Compare sessions over time

**Technical Notes:**
- Query from ZeroDB session_attendance collection
- Use Cloudflare Stream analytics API for VOD metrics
- Create `/app/admin/training/[sessionId]/analytics/page.tsx`

**Dependencies:** US-045, US-048

---

#### US-050: Chat & Interaction Features
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 7

**As a** participant
**I want** to interact during live sessions
**So that** I can ask questions and engage

**Acceptance Criteria:**
- [ ] Chat panel in RTC interface
- [ ] Real-time message delivery (WebSocket or SSE)
- [ ] Emoji reactions (👍, 👏, ❤️, 🔥)
- [ ] Raise hand feature (notifies instructor)
- [ ] Private messages (instructor to participant)
- [ ] Chat moderation (instructor can delete messages, mute users)
- [ ] Chat export after session
- [ ] Typing indicators

**Technical Notes:**
- Use WebSocket for chat (consider Pusher or Ably for simplicity)
- Store messages in ZeroDB session_chat collection
- Implement rate limiting (max 5 messages/minute per user)

**Dependencies:** US-045

---

### Summary: Phase 3 Story Points
- **EP-06 (Search):** 55 points
- **EP-07 (RTC/VOD):** 55 points
- **Total:** 110 points
- **Duration:** 3 sprints (6 weeks)

---

## Phase 4: Content & Analytics (Weeks 6-8)

### EPIC-08: Admin Panel & Dashboards

**Epic Owner:** Full-stack Dev (Python + React)
**Business Value:** Operational efficiency and data-driven decisions
**Dependencies:** EP-03, EP-04, EP-05, EP-06, EP-07
**Total Story Points:** 34

---

#### US-051: Admin Dashboard Overview
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 4-5

**As an** administrator
**I want** a high-level dashboard
**So that** I can see key metrics at a glance

**Acceptance Criteria:**
- [ ] Dashboard shows KPI cards:
  - Total members (with % change vs last month)
  - Active subscriptions (with MRR)
  - Pending applications (with link to queue)
  - Upcoming events (with RSVP count)
  - Total searches this week
  - System health (API uptime, error rate)
- [ ] Charts:
  - Membership growth (line chart, 12 months)
  - MRR trend (line chart, 12 months)
  - Event RSVPs (bar chart, next 5 events)
  - Search volume (line chart, 30 days)
- [ ] Recent activity feed (last 20 actions from ZeroDB audit_logs)
- [ ] Quick actions (approve application, create event)

**Technical Notes:**
- Create `/app/admin/dashboard/page.tsx`
- Use Recharts for visualizations
- Query aggregations from ZeroDB collections
- Cache data with Redis (5-minute TTL)
- Use shadcn/ui Card components

**Dependencies:** Multiple (US-015, US-023, US-029, US-038)

---

#### US-052: Member Management Interface
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 4-5

**As an** administrator
**I want** to manage member accounts
**So that** I can handle support requests and moderation

**Acceptance Criteria:**
- [ ] Member directory (admin view)
- [ ] Searchable by name, email, discipline
- [ ] Filterable by role, tier, status
- [ ] Table columns: Name, Email, Tier, Status, Join Date, Actions
- [ ] Click row → member detail modal:
  - Full profile information (from ZeroDB profiles collection)
  - Subscription details (from ZeroDB subscriptions collection)
  - Payment history
  - RSVP history
  - Application history (if applicable)
  - Audit log (last 50 actions)
- [ ] Actions:
  - Edit profile
  - Change role (update in ZeroDB users collection)
  - Change tier (upgrade/downgrade)
  - Suspend account (temporary)
  - Delete account (GDPR-compliant, update in ZeroDB)
  - Send email
  - Impersonate user (for support)
- [ ] Bulk actions (email selected, export selected)
- [ ] Export all members to CSV

**Technical Notes:**
- Create `/app/admin/members/page.tsx`
- Implement server-side pagination (50 per page via ZeroDB query)
- Use debounced search
- Require confirmation for destructive actions
- Query multiple ZeroDB collections (users, profiles, subscriptions)

**Dependencies:** US-001, US-023

---

#### US-053: Integration Settings Management
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 5

**As an** administrator
**I want** to manage integration settings
**So that** I can configure third-party services

**Acceptance Criteria:**
- [ ] Settings page with sections:
  - ZeroDB (API key, project ID)
  - Stripe (API keys, webhook secret)
  - BeeHiiv (API key, list IDs)
  - Cloudflare (account ID, API token)
  - AINative AI Registry (API key)
  - Email (Postmark API key, sender domain)
  - Analytics (GA4 measurement ID)
- [ ] Test connection buttons for each integration
- [ ] Connection status indicators (green=connected, red=error)
- [ ] Masked API keys (show last 4 characters)
- [ ] Rotate API key buttons
- [ ] Save settings (encrypted in ZeroDB config collection)

**Technical Notes:**
- Create `/app/admin/settings/integrations/page.tsx`
- Store encrypted in ZeroDB (use Python `cryptography` library)
- Create `POST /api/admin/settings/integrations/test/:service` for testing
- Implement audit logging for settings changes in ZeroDB

**Dependencies:** None (can build anytime)

---

#### US-054: Audit Log Viewer
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 5

**As an** administrator
**I want** to view audit logs
**So that** I can track system changes and investigate issues

**Acceptance Criteria:**
- [ ] Audit log page with filterable table
- [ ] Columns: Timestamp, User, Action, Target Type, Target ID, Details
- [ ] Filters:
  - Date range
  - User (dropdown)
  - Action type (dropdown: create, update, delete, approve, reject, login, etc.)
  - Target type (application, subscription, event, etc.)
- [ ] Search by details (JSON field)
- [ ] Click row → expanded view with full JSON
- [ ] Export filtered results to CSV
- [ ] Pagination (100 per page)
- [ ] Real-time updates (poll every 30 seconds)

**Technical Notes:**
- Create `/app/admin/audit-logs/page.tsx`
- Query ZeroDB audit_logs collection
- Use shadcn/ui Table with sorting
- Implement JSON syntax highlighting for details

**Dependencies:** US-001 (audit_logs collection)

---

#### US-055: SEO Management Tools
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 5

**As an** administrator
**I want** SEO management tools
**So that** I can optimize search engine visibility

**Acceptance Criteria:**
- [ ] SEO dashboard with:
  - Sitemap status (last generated, URL count)
  - Robots.txt editor
  - Schema.org validator (checks all pages)
  - Broken link checker
  - Meta tag audit (missing titles, descriptions)
  - Open Graph preview
- [ ] Actions:
  - Regenerate sitemap
  - Resubmit sitemap to Google Search Console
  - Validate schema markup
  - Fix broken links (bulk find & replace)
- [ ] SEO health score (0-100)
- [ ] Link to Google Search Console
- [ ] Link to Google Analytics

**Technical Notes:**
- Create `/app/admin/seo/page.tsx`
- Use `next-sitemap` for sitemap generation
- Implement schema validator (check against schema.org specs)
- Use LinkChecker or similar for broken links

**Dependencies:** None (can build anytime)

---

#### US-056: System Health Monitoring
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 5

**As an** administrator
**I want** to monitor system health
**So that** I can identify and resolve issues proactively

**Acceptance Criteria:**
- [ ] Health dashboard shows:
  - API uptime (%)
  - Average response time (p50, p95, p99)
  - Error rate (last 24 hours)
  - ZeroDB connection status
  - Redis connection status
  - Background job queue depth
  - External service status (Stripe, Cloudflare, etc.)
- [ ] Alerts for:
  - API uptime < 99.5%
  - p95 response time > 1 second
  - Error rate > 5%
  - ZeroDB connection failures
- [ ] Link to full observability dashboard

**Technical Notes:**
- Create `/app/admin/system/health/page.tsx`
- Query from OpenTelemetry metrics
- Implement health check endpoints for dependencies
- Use WebSocket for real-time updates

**Dependencies:** US-083 (OpenTelemetry setup)

---

### EPIC-09: Newsletter & Content Integration

**Epic Owner:** Full-stack Dev (Python)
**Business Value:** Grow email list and automate content distribution
**Dependencies:** EP-01
**Total Story Points:** 21

---

#### US-057: BeeHiiv Account Setup
**Priority:** 🔴 Critical | **Story Points:** 2 | **Sprint:** 6

**As a** system administrator
**I want** BeeHiiv configured
**So that** we can send newsletters and sync content

**Acceptance Criteria:**
- [ ] BeeHiiv account created
- [ ] API key obtained
- [ ] Email lists created:
  - General (all subscribers)
  - Members Only
  - Instructors
- [ ] Email templates created (welcome, digest, event announcement)
- [ ] Custom domain configured (newsletter.wwmaa.com)
- [ ] DKIM/SPF records configured for deliverability

**Technical Notes:**
- Store API key in environment variables
- Document list IDs in `/docs/beehiiv.md`
- Test email deliverability with mail-tester.com

**Dependencies:** None (can start early)

---

#### US-058: Newsletter Subscription Backend
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 6

**As a** user
**I want** to subscribe to the newsletter
**So that** I can receive updates

**Acceptance Criteria:**
- [ ] `POST /api/newsletter/subscribe` endpoint
- [ ] Required field: email (validated)
- [ ] Optional fields: name, interests (checkboxes)
- [ ] Email added to BeeHiiv General list via API
- [ ] Double opt-in email sent (confirm subscription)
- [ ] Confirmation link redirects to thank you page
- [ ] Existing subscribers receive "already subscribed" message
- [ ] GDPR-compliant (consent checkbox, privacy policy link)

**Technical Notes:**
- Use BeeHiiv API for subscription
- Create endpoint in `/backend/routes/newsletter.py`
- Implement rate limiting (max 5 attempts per hour per IP)
- Send confirmation email via BeeHiiv

**Dependencies:** US-057

---

#### US-059: Member Auto-Subscribe
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 6

**As a** system
**I want** new members automatically subscribed to newsletter
**So that** they receive member communications

**Acceptance Criteria:**
- [ ] When application approved and subscription created:
  - Add email to BeeHiiv Members Only list via API
  - No double opt-in required (implied consent)
- [ ] When member upgrades to Instructor tier:
  - Add to Instructors list
- [ ] When subscription canceled:
  - Remove from Members Only list
  - Keep in General list (unless they unsubscribe)
- [ ] Sync member email changes to BeeHiiv

**Technical Notes:**
- Trigger from webhook handler (US-023)
- Create `/backend/services/beehiiv_service.py` utility
- Handle BeeHiiv API errors gracefully
- Query ZeroDB for user email

**Dependencies:** US-058, US-023

---

#### US-060: Blog Content Sync
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 6

**As an** administrator
**I want** blog posts from BeeHiiv synced to the website
**So that** content is consistent across platforms

**Acceptance Criteria:**
- [ ] BeeHiiv webhook configured for post.published events
- [ ] Webhook endpoint: `POST /api/webhooks/beehiiv/post`
- [ ] When post published in BeeHiiv:
  - Create/update blog post document in ZeroDB blog_posts collection
  - Extract metadata (title, excerpt, author, publish date)
  - Store content (HTML)
  - Generate slug from title
  - Set canonical URL (to BeeHiiv or our site, per SEO recommendation)
- [ ] Blog listing page shows synced posts from ZeroDB
- [ ] Blog detail pages render BeeHiiv content
- [ ] Images embedded correctly
- [ ] Links work properly

**Technical Notes:**
- Store posts in ZeroDB blog_posts collection
- Sanitize HTML content
- Create endpoint in `/backend/routes/webhooks.py`
- Handle duplicate posts (by BeeHiiv post ID)

**Dependencies:** US-057

---

#### US-061: Automated Email Campaigns
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 6

**As a** marketing manager
**I want** automated email campaigns
**So that** we can nurture leads and engage members

**Acceptance Criteria:**
- [ ] Email sequences created in BeeHiiv:
  - Welcome sequence (new subscribers, 3 emails over 7 days)
  - Onboarding sequence (new members, 5 emails over 30 days)
  - Event reminder (3 days before, 1 day before)
  - Weekly digest (every Monday, curated content)
- [ ] Trigger events configured:
  - Newsletter subscribe → Welcome sequence
  - Subscription created → Onboarding sequence
  - Event RSVP → Reminder sequence
- [ ] Unsubscribe link in all emails
- [ ] Email performance tracking (opens, clicks)

**Technical Notes:**
- Configure in BeeHiiv dashboard
- Use BeeHiiv automation features
- Track conversions in GA4

**Dependencies:** US-057

---

#### US-062: Newsletter Management (Admin)
**Priority:** 🟢 Medium | **Story Points:** 3 | **Sprint:** 6

**As an** administrator
**I want** to manage newsletter subscribers
**So that** I can segment and communicate effectively

**Acceptance Criteria:**
- [ ] Admin page shows:
  - Total subscribers per list
  - Subscriber growth chart (30 days)
  - Recent subscribers
  - Unsubscribe rate
- [ ] Actions:
  - View subscriber details
  - Manually add subscriber
  - Remove subscriber
  - Export subscriber list to CSV
  - Send one-off campaign
- [ ] Link to BeeHiiv dashboard

**Technical Notes:**
- Create `/app/admin/newsletter/page.tsx`
- Use BeeHiiv API to fetch subscriber data
- Cache results with Redis (10-minute TTL)

**Dependencies:** US-058

---

### EPIC-10: Analytics & Observability

**Epic Owner:** DevOps/Backend Lead (Python)
**Business Value:** Data-driven decision making and system reliability
**Dependencies:** All epics (cross-cutting concern)
**Total Story Points:** 21

---

#### US-063: Google Analytics 4 Setup
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 7

**As a** marketing manager
**I want** Google Analytics 4 configured
**So that** we can track user behavior and conversions

**Acceptance Criteria:**
- [ ] GA4 property created
- [ ] Measurement ID configured in Next.js
- [ ] Google Tag Manager (optional, recommended)
- [ ] Page view tracking automatic
- [ ] Enhanced measurement enabled (scroll, outbound links, site search, video engagement)
- [ ] Cross-domain tracking configured (if applicable)
- [ ] E-commerce tracking enabled
- [ ] Conversion events defined (sign up, subscribe, rsvp, purchase)

**Technical Notes:**
- Use `next/script` for GA4 tag
- Create `/lib/analytics/gtag.ts` helper (frontend TypeScript)
- Store measurement ID in environment variable
- Document event names in `/docs/analytics.md`

**Dependencies:** None (can start early)

---

#### US-064: Custom Event Tracking
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 7

**As a** product manager
**I want** custom events tracked in GA4
**So that** I can measure feature usage

**Acceptance Criteria:**
- [ ] Events tracked:
  - **Search**: search_started, search_result_viewed, search_feedback_submitted
  - **Membership**: application_submitted, application_approved, application_rejected
  - **Subscription**: checkout_started, subscription_created, subscription_canceled, payment_completed, payment_failed
  - **Events**: event_viewed, rsvp_submitted, rsvp_canceled, event_attended
  - **Training**: session_joined, session_left, vod_viewed, vod_completed
  - **Content**: blog_post_viewed, newsletter_subscribed
  - **Engagement**: profile_updated, belt_rank_updated
- [ ] Events include relevant parameters (event_id, user_id, amount, etc.)
- [ ] Events fire consistently across platform
- [ ] Events visible in GA4 DebugView (development)

**Technical Notes:**
- Create `/lib/analytics/events.ts` with typed event functions
- Call events from relevant components/API routes
- Use gtag.js or dataLayer.push
- Test in GA4 DebugView before production

**Dependencies:** US-063

---

#### US-065: OpenTelemetry Instrumentation
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 7

**As a** developer
**I want** OpenTelemetry tracing on all API endpoints
**So that** I can diagnose performance issues

**Acceptance Criteria:**
- [ ] OpenTelemetry SDK installed and configured in Python backend
- [ ] Auto-instrumentation for FastAPI/Flask routes
- [ ] Custom spans for:
  - ZeroDB queries
  - External API calls (Stripe, BeeHiiv, Cloudflare, AINative AI Registry)
  - Cache operations (Redis)
  - Search pipeline stages
- [ ] Traces include:
  - Trace ID, span ID
  - User ID, role
  - HTTP method, path, status code
  - Duration
  - Error status
- [ ] Traces exported to observability platform (Honeycomb, Jaeger, or Grafana Tempo)
- [ ] Sampling configured (100% in staging, 10% in production)

**Technical Notes:**
- Use `opentelemetry-api` and `opentelemetry-sdk`: `pip install opentelemetry-api opentelemetry-sdk`
- Create `/backend/observability/tracing.py`
- Instrument in backend application startup
- Export to OTLP endpoint (environment variable)

**Dependencies:** None (can build early)

---

#### US-066: Error Tracking & Alerting
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 7

**As a** developer
**I want** errors tracked and alerted
**So that** I can fix issues quickly

**Acceptance Criteria:**
- [ ] Error tracking tool configured (Sentry recommended)
- [ ] Automatic error capture for:
  - Unhandled exceptions (Python)
  - API errors (500s)
  - Client-side errors (React errors)
- [ ] Error context includes:
  - User ID, role
  - Request URL, method
  - Browser, OS (for frontend errors)
  - Stack trace
  - Breadcrumbs (recent actions)
- [ ] Alerts for:
  - Error rate > 5% (Slack notification)
  - Critical errors (payment failures, auth issues)
  - API downtime
- [ ] Errors grouped by fingerprint (deduplicated)

**Technical Notes:**
- Use Sentry: `pip install sentry-sdk`
- Create `/backend/observability/errors.py`
- Initialize Sentry in backend app startup
- Set up Slack integration

**Dependencies:** None

---

#### US-067: Performance Monitoring
**Priority:** 🟡 High | **Story Points:** 2 | **Sprint:** 7

**As a** developer
**I want** performance metrics tracked
**So that** I can ensure SLOs are met

**Acceptance Criteria:**
- [ ] Core Web Vitals tracked:
  - LCP (Largest Contentful Paint) < 2.5s
  - FID (First Input Delay) < 100ms
  - CLS (Cumulative Layout Shift) < 0.1
- [ ] API endpoint metrics:
  - p50, p95, p99 latency by endpoint
  - Throughput (requests per second)
  - Error rate
- [ ] ZeroDB query performance:
  - Slow query log (> 1 second)
- [ ] External service latency:
  - Stripe, BeeHiiv, Cloudflare, AINative AI Registry
- [ ] Alerts for SLO violations

**Technical Notes:**
- Use Next.js Analytics (built-in for frontend)
- Use OpenTelemetry metrics for backend
- Create Grafana dashboard for visualization
- Set up PagerDuty for alerts

**Dependencies:** US-065

---

### EPIC-11: Security & Compliance

**Epic Owner:** Backend Lead + Security Specialist (Python)
**Business Value:** Protect user data and meet regulatory requirements
**Dependencies:** EP-01, EP-02
**Total Story Points:** 34

---

#### US-068: Cloudflare WAF Configuration
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 7

**As a** system administrator
**I want** Cloudflare WAF protecting the application
**So that** we can prevent common attacks

**Acceptance Criteria:**
- [ ] Cloudflare account configured for wwmaa.com
- [ ] SSL/TLS certificate installed (Full Strict mode)
- [ ] WAF rules enabled:
  - OWASP Core Ruleset
  - Cloudflare Managed Ruleset
  - Rate limiting (100 req/min per IP)
  - Bot protection (challenge suspected bots)
  - DDoS protection enabled
- [ ] Custom rules:
  - Block known malicious IPs
  - Geo-block (if applicable)
  - Challenge on sensitive endpoints
- [ ] WAF logs forwarded to monitoring
- [ ] Weekly WAF report review

**Technical Notes:**
- Configure in Cloudflare Dashboard
- Test with penetration testing tools (OWASP ZAP)
- Document rules in `/docs/security/waf-rules.md`

**Dependencies:** None (can configure early)

---

#### US-069: Security Headers
**Priority:** 🔴 Critical | **Story Points:** 2 | **Sprint:** 7

**As a** developer
**I want** security headers on all responses
**So that** we mitigate common web vulnerabilities

**Acceptance Criteria:**
- [ ] Headers configured:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`
  - `Content-Security-Policy: (strict policy)`
- [ ] CSP allows:
  - Scripts: self, trusted CDNs (Stripe, GA, Cloudflare)
  - Styles: self, inline (with nonces)
  - Images: self, data:, ZeroDB Object Storage URLs
  - Media: Cloudflare Stream
  - Fonts: self, Google Fonts
- [ ] CSP tested and no violations in browser console

**Technical Notes:**
- Configure in `next.config.js` (headers array) for Next.js
- Configure in Python backend middleware for API responses
- Use CSP nonces for inline scripts
- Test with securityheaders.com

**Dependencies:** None

---

#### US-070: Input Validation & Sanitization
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 7

**As a** developer
**I want** all user input validated and sanitized
**So that** we prevent injection attacks

**Acceptance Criteria:**
- [ ] All API endpoints validate input with Pydantic schemas
- [ ] Validation errors return 400 with clear messages
- [ ] NoSQL injection prevented (sanitize ZeroDB query parameters)
- [ ] XSS prevented (React escaping + CSP)
- [ ] Path traversal prevented (file upload validation)
- [ ] Command injection prevented (no shell commands with user input)
- [ ] HTML sanitization for rich text fields (use bleach library)

**Technical Notes:**
- Create validation schemas in `/backend/models/validation/`
- Use Pydantic for all API input validation
- Use `bleach` library for sanitizing HTML: `pip install bleach`
- Never trust client-side validation alone

**Dependencies:** None

---

#### US-071: CSRF Protection
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 7

**As a** user
**I want** protection against CSRF attacks
**So that** my account cannot be compromised

**Acceptance Criteria:**
- [ ] CSRF tokens generated for all sessions
- [ ] Tokens validated on state-changing requests (POST, PUT, DELETE)
- [ ] Tokens rotated after login
- [ ] Tokens included in forms as hidden fields
- [ ] Tokens sent in custom header for AJAX requests
- [ ] Missing/invalid tokens return 403 Forbidden
- [ ] SameSite cookie attribute set to Strict

**Technical Notes:**
- Use Python CSRF library or implement custom middleware
- Create `/backend/middleware/csrf.py`
- Store tokens in httpOnly cookies
- Implement double-submit cookie pattern

**Dependencies:** US-009 (JWT tokens)

---

#### US-072: GDPR Compliance - Data Export
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 8

**As a** user
**I want** to export all my personal data
**So that** I can exercise my GDPR rights

**Acceptance Criteria:**
- [ ] "Export My Data" button in user settings
- [ ] Export includes:
  - Profile information (from ZeroDB profiles collection)
  - Application history
  - Subscription and payment history
  - Event RSVPs
  - Search queries
  - Training session attendance
  - Audit logs (user's actions)
- [ ] Export format: JSON (structured)
- [ ] Export generated asynchronously (background job)
- [ ] Email sent when export ready (24-hour link expiry)
- [ ] Export file stored temporarily in ZeroDB Object Storage
- [ ] Export includes cover letter explaining data

**Technical Notes:**
- Create `POST /api/privacy/export-data` endpoint
- Use Python background job queue (Celery or APScheduler)
- Store export files in ZeroDB Object Storage with 24-hour TTL
- Create `/backend/services/gdpr_service.py` utility

**Dependencies:** US-001

---

#### US-073: GDPR Compliance - Data Deletion
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 8

**As a** user
**I want** to delete my account and all data
**So that** I can exercise my right to be forgotten

**Acceptance Criteria:**
- [ ] "Delete My Account" button in user settings
- [ ] Confirmation modal with consequences:
  - All personal data deleted from ZeroDB
  - Subscription canceled immediately
  - Past RSVPs anonymized
  - Comments/posts anonymized (not deleted)
  - Cannot be undone
- [ ] Password confirmation required
- [ ] Account deletion processed asynchronously
- [ ] Data deleted from ZeroDB:
  - User document (soft delete, anonymize)
  - Profile data
  - Application history
  - Search queries (anonymize)
  - Training session attendance (anonymize)
- [ ] Data retained for legal purposes:
  - Payment records (7 years, anonymized)
  - Audit logs (1 year, anonymized)
- [ ] Confirmation email sent
- [ ] User logged out immediately

**Technical Notes:**
- Create `POST /api/privacy/delete-account` endpoint
- Use background job for deletion
- Anonymize by replacing with "Deleted User [hash]"
- Update documents in ZeroDB collections
- Create `/backend/services/gdpr_service.py` utility
- Document retention policy in privacy policy

**Dependencies:** US-001, US-023

---

#### US-074: Cookie Consent Banner
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 8

**As a** visitor
**I want** control over cookies
**So that** my privacy preferences are respected

**Acceptance Criteria:**
- [ ] Cookie banner appears on first visit
- [ ] Banner explains cookie usage (essential, functional, analytics, marketing)
- [ ] Options:
  - Accept All
  - Reject All (except essential)
  - Customize (checkboxes for each category)
- [ ] Consent stored in cookie (12-month expiry)
- [ ] User can update preferences in footer link
- [ ] Analytics/marketing cookies only load if consented
- [ ] GDPR/CCPA compliant

**Technical Notes:**
- Use `react-cookie-consent` or custom component
- Create `/components/cookie-consent.tsx`
- Store consent in localStorage and cookie
- Conditionally load GA4 script based on consent

**Dependencies:** None

---

#### US-075: Privacy Policy & Terms of Service
**Priority:** 🟡 High | **Story Points:** 3 | **Sprint:** 8

**As a** user
**I want** to read the privacy policy and terms
**So that** I understand how my data is used

**Acceptance Criteria:**
- [ ] Privacy Policy page created
- [ ] Terms of Service page created
- [ ] Pages include:
  - Last updated date
  - Table of contents
  - Plain language explanations
  - Contact information for privacy inquiries
- [ ] Privacy Policy covers:
  - What data is collected
  - How data is used (including ZeroDB storage)
  - Third-party services (Stripe, Cloudflare, AINative, etc.)
  - Data retention
  - GDPR/CCPA rights
  - Cookie policy
- [ ] Terms cover:
  - Account responsibilities
  - Payment terms
  - Refund policy
  - Content ownership
  - Liability limitations
- [ ] Links in footer
- [ ] Users must accept terms during registration

**Technical Notes:**
- Create `/app/privacy/page.tsx` and `/app/terms/page.tsx`
- Use legal templates (customize for WWMAA)
- Have legal counsel review before launch
- Version terms (store acceptance in ZeroDB)

**Dependencies:** None

---

### EPIC-12: Testing & Quality Assurance

**Epic Owner:** QA Lead + All Developers
**Business Value:** Ensure reliability and catch bugs before production
**Dependencies:** All epics (cross-cutting concern)
**Total Story Points:** Ongoing (not estimated in sprints)

---

#### US-076: Unit Testing Setup (Python)
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 1 (setup), Ongoing

**As a** developer
**I want** unit tests for business logic
**So that** I can refactor confidently

**Acceptance Criteria:**
- [ ] pytest configured for Python backend
- [ ] Test structure: `tests/` folder with test files
- [ ] Coverage reporting enabled (target: 80%)
- [ ] Tests for:
  - Approval workflow logic (two-approval quorum)
  - Role-based permission checks
  - Validation functions (Pydantic schemas)
  - Utility functions (date formatting, string manipulation)
  - Search query normalization
  - Payment calculation logic
- [ ] CI runs tests on every PR
- [ ] PRs blocked if tests fail or coverage drops

**Technical Notes:**
- Use pytest: `pip install pytest pytest-cov`
- Create `pytest.ini` or `pyproject.toml` config
- Add scripts: `pytest`, `pytest --cov=backend`
- Mock external APIs (Stripe, BeeHiiv, ZeroDB, etc.) using `pytest-mock`
- Create fixtures in `tests/conftest.py`

**Dependencies:** None

---

#### US-077: Integration Testing (Python API)
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 3 (setup), Ongoing

**As a** developer
**I want** integration tests for API endpoints
**So that** I can verify end-to-end functionality

**Acceptance Criteria:**
- [ ] Test client configured for API testing (FastAPI TestClient or Flask test_client)
- [ ] Test ZeroDB setup (separate test collections or mocked)
- [ ] Tests for critical flows:
  - Application submission → approval → subscription
  - Stripe webhook processing
  - Search query → ZeroDB → AI Registry
  - Event RSVP → payment
  - VOD access control
- [ ] Tests clean up after themselves
- [ ] CI runs integration tests on every PR
- [ ] Integration tests run against staging before deploy

**Technical Notes:**
- Use pytest with FastAPI TestClient or Flask test_client
- Create test fixtures in `/tests/fixtures/`
- Mock external APIs using `responses` or `httpretty` libraries
- Use test ZeroDB collections or mock ZeroDB client

**Dependencies:** US-001 (ZeroDB client)

---

#### US-078: End-to-End Testing (Frontend + Backend)
**Priority:** 🟡 High | **Story Points:** 13 | **Sprint:** 5 (setup), Ongoing

**As a** QA engineer
**I want** E2E tests for critical user flows
**So that** I can ensure the UI works correctly

**Acceptance Criteria:**
- [ ] Playwright or Cypress configured
- [ ] Tests for user journeys:
  - Registration → email verification → login
  - Membership application → approval → payment → access
  - Search → view result → feedback
  - Event browse → RSVP → payment → attendance
  - Live training join → participate → leave
  - VOD watch → progress save
  - Admin approve application → member created
- [ ] Tests run against local dev server
- [ ] Tests run against staging in CI
- [ ] Screenshots/videos captured on failure
- [ ] Parallel test execution (faster CI)

**Technical Notes:**
- Use Playwright (recommended): `npm install -D @playwright/test`
- Create `/e2e/` directory
- Use Page Object Model pattern
- Run in headless mode in CI
- Backend must be running (Python API)

**Dependencies:** Multiple (US-010, US-017, US-022, US-032, US-038, US-045, US-048)

---

#### US-079: Accessibility Testing
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 6 (setup), Ongoing

**As a** user with disabilities
**I want** the application to be accessible
**So that** I can use all features

**Acceptance Criteria:**
- [ ] jest-axe configured for automated a11y testing
- [ ] All pages tested for WCAG 2.2 AA compliance
- [ ] Manual testing with:
  - Screen reader (NVDA/JAWS)
  - Keyboard-only navigation
  - High contrast mode
  - Browser zoom (200%)
- [ ] Issues found and fixed:
  - Missing alt text
  - Low color contrast
  - Focus states missing
  - ARIA labels incorrect
  - Form errors not announced
- [ ] A11y checklist documented

**Technical Notes:**
- Use jest-axe for automated tests
- Use axe DevTools browser extension
- Use Lighthouse accessibility audit
- Create `/docs/accessibility.md` with guidelines

**Dependencies:** None

---

#### US-080: Load & Performance Testing
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 8 (before launch)

**As a** system administrator
**I want** to know the application can handle expected load
**So that** we don't crash on launch day

**Acceptance Criteria:**
- [ ] Load testing scenarios:
  - Search: 100 concurrent users, 1000 queries/min
  - RTC: 50 concurrent participants in one session
  - Stripe webhooks: 100 events/second burst
  - Event RSVP: 500 registrations in 10 minutes
  - Page load: 10,000 concurrent visitors
- [ ] Performance targets met:
  - p95 response time < 1.2s (search)
  - p95 response time < 300ms (API endpoints)
  - RTC drop rate < 1%
  - No errors under load
- [ ] Bottlenecks identified and fixed:
  - ZeroDB query optimization
  - Redis caching improvements
  - Connection pool sizing
- [ ] Load test report documented

**Technical Notes:**
- Use k6 or Locust for load testing (Python-friendly)
- Run against staging environment
- Create `/load-tests/` directory with scripts
- Monitor with OpenTelemetry during tests

**Dependencies:** US-065 (observability)

---

### EPIC-13: Deployment & CI/CD

**Epic Owner:** DevOps Lead
**Business Value:** Reliable, automated deployments
**Dependencies:** EP-01, EP-12
**Total Story Points:** 13

---

#### US-081: Railway Staging Environment
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 8

**As a** developer
**I want** a staging environment
**So that** I can test changes before production

**Acceptance Criteria:**
- [ ] Railway project created for staging
- [ ] Staging environment provisioned:
  - Python backend service (FastAPI/Flask)
  - Next.js frontend service
  - Redis instance
- [ ] Environment variables configured
- [ ] Staging URL: staging.wwmaa.com
- [ ] ZeroDB staging collections created
- [ ] Seed data loaded
- [ ] Connected to test instances of:
  - Stripe (test mode)
  - Cloudflare (test account)
  - BeeHiiv (test list)

**Technical Notes:**
- Create Railway project: wwmaa-staging
- Configure railway.json or railway.toml
- Use Railway environment variables
- Document staging URLs in `/docs/environments.md`

**Dependencies:** US-001, US-008

---

#### US-082: GitHub Actions CI Pipeline (Python)
**Priority:** 🔴 Critical | **Story Points:** 5 | **Sprint:** 8

**As a** developer
**I want** automated CI on every commit
**So that** issues are caught early

**Acceptance Criteria:**
- [ ] GitHub Actions workflow: `.github/workflows/ci.yml`
- [ ] Triggered on: push to main, pull request
- [ ] Pipeline steps:
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies (`pip install -r requirements.txt`)
  4. Lint (flake8, black, mypy)
  5. Run unit tests (pytest)
  6. Run integration tests
  7. Build Next.js app
  8. Run E2E tests (against preview deploy)
  9. Upload code coverage
  10. Publish test results
- [ ] PRs show check status (pass/fail)
- [ ] Merge blocked if checks fail
- [ ] Slack notification on failure

**Technical Notes:**
- Use Python 3.11 in GitHub Actions
- Cache pip dependencies for speed
- Parallelize tests where possible
- Use Railway CLI for preview deploys

**Dependencies:** US-076, US-077, US-078

---

#### US-083: Railway Production Deployment
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 9 (launch week)

**As a** system administrator
**I want** the application deployed to production
**So that** users can access it

**Acceptance Criteria:**
- [ ] Railway project created for production
- [ ] Production environment provisioned:
  - Python backend service
  - Next.js frontend service
  - Redis instance
- [ ] Custom domain configured: wwmaa.com (frontend), api.wwmaa.com (backend)
- [ ] SSL certificates configured (auto via Railway)
- [ ] Environment variables set (production values)
- [ ] ZeroDB production collections initialized
- [ ] Production data imported (if migrating from old system)
- [ ] Health check endpoint: `/api/health`
- [ ] Monitoring configured
- [ ] Backups enabled (daily via US-005)

**Technical Notes:**
- Create Railway project: wwmaa-production
- Use Railway's zero-downtime deployments
- Configure custom domain DNS (CNAME to Railway)
- Document deployment process in `/docs/deployment.md`

**Dependencies:** US-081, US-082

---

#### US-084: Continuous Deployment
**Priority:** 🟡 High | **Story Points:** 2 | **Sprint:** 9

**As a** developer
**I want** automatic deploys to staging and production
**So that** releases are fast and consistent

**Acceptance Criteria:**
- [ ] Staging deploys automatically on push to `main` branch
- [ ] Production deploys automatically on:
  - Git tag (e.g., `v1.0.0`)
  - Or manual approval in GitHub Actions
- [ ] Deployment notifications in Slack (#deploys channel)
- [ ] Rollback procedure documented
- [ ] Feature flags enabled for gradual rollouts

**Technical Notes:**
- Use Railway's GitHub integration
- Tag releases: `git tag -a v1.0.0 -m "Release 1.0.0"`
- Use Railway's rollback feature if needed
- Consider feature flags (LaunchDarkly or custom in ZeroDB)

**Dependencies:** US-083

---

## Phase 5: QA & Launch (Weeks 7-10)

### Pre-Launch Checklist (Sprint 9-10)

#### US-085: Security Audit
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 9

**As a** security professional
**I want** to audit the application for vulnerabilities
**So that** we launch securely

**Acceptance Criteria:**
- [ ] OWASP Top 10 checklist completed
- [ ] Dependency vulnerability scan (`pip-audit` or `safety`)
- [ ] Manual penetration testing (or hire third party)
- [ ] Secrets scanning (no API keys in git)
- [ ] Rate limiting tested (bypass attempts)
- [ ] NoSQL injection testing (ZeroDB queries)
- [ ] XSS testing
- [ ] CSRF testing
- [ ] Authentication bypass testing
- [ ] Authorization bypass testing
- [ ] Findings documented and fixed
- [ ] Retest after fixes

**Technical Notes:**
- Use OWASP ZAP or Burp Suite
- Run `pip-audit` or `safety check`
- Use Snyk for continuous monitoring
- Document findings in `/docs/security/audit-YYYY-MM-DD.md`

**Dependencies:** All security stories

---

#### US-086: Performance Optimization
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 9

**As a** user
**I want** the application to load quickly
**So that** I have a good experience

**Acceptance Criteria:**
- [ ] Lighthouse scores (all pages):
  - Performance: ≥90
  - Accessibility: 100
  - Best Practices: 100
  - SEO: 100
- [ ] Core Web Vitals pass:
  - LCP < 2.5s
  - FID < 100ms
  - CLS < 0.1
- [ ] Optimizations implemented:
  - Image optimization (next/image, serve from ZeroDB Object Storage)
  - Code splitting (dynamic imports)
  - Font optimization (preload, font-display)
  - Critical CSS inlined
  - JavaScript minification
  - Gzip/Brotli compression
  - CDN for static assets (Cloudflare)
- [ ] Bundle size analyzed (< 200KB first load JS)

**Technical Notes:**
- Use `@next/bundle-analyzer`
- Optimize images before uploading to ZeroDB Object Storage
- Use Cloudflare CDN
- Implement lazy loading
- Defer non-critical scripts

**Dependencies:** US-067 (performance monitoring)

---

#### US-087: Browser & Device Testing
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 9

**As a** QA engineer
**I want** the application tested on multiple browsers and devices
**So that** all users have a consistent experience

**Acceptance Criteria:**
- [ ] Tested on browsers:
  - Chrome (latest, -1 version)
  - Firefox (latest, -1 version)
  - Safari (latest, -1 version, iOS Safari)
  - Edge (latest)
- [ ] Tested on devices:
  - iPhone (iOS 16+)
  - Android phone (Android 12+)
  - iPad
  - Desktop (Mac, Windows, Linux)
- [ ] Responsive design works at all breakpoints
- [ ] Touch interactions work on mobile
- [ ] No console errors on any browser
- [ ] Visual bugs fixed

**Technical Notes:**
- Use BrowserStack or local devices
- Test at breakpoints: 320px, 375px, 768px, 1024px, 1440px
- Document browser support policy in `/docs/browser-support.md`

**Dependencies:** None

---

#### US-088: User Acceptance Testing (UAT)
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 9

**As a** stakeholder
**I want** to test the application with real users
**So that** I can validate it meets requirements

**Acceptance Criteria:**
- [ ] UAT plan created with test scenarios
- [ ] 10+ beta users recruited (mix of roles)
- [ ] Users complete test scenarios:
  - Register and apply for membership
  - Search for martial arts information
  - Register for an event
  - Join a live training session
  - Watch a recorded session
  - Update profile
  - Admin approves application
  - Admin creates event
- [ ] Feedback collected (survey)
- [ ] Issues triaged (critical, high, medium, low)
- [ ] Critical and high issues fixed before launch
- [ ] UAT sign-off obtained

**Technical Notes:**
- Use staging environment for UAT
- Create test accounts for each role in ZeroDB
- Use Google Forms or Typeform for feedback
- Document issues in GitHub Issues

**Dependencies:** All features complete

---

#### US-089: Documentation & Training
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 9-10

**As a** user or administrator
**I want** documentation and training materials
**So that** I can use the platform effectively

**Acceptance Criteria:**
- [ ] User documentation:
  - How to apply for membership
  - How to use search
  - How to register for events
  - How to join live sessions
  - How to update profile
  - FAQ page
- [ ] Admin documentation:
  - How to approve applications
  - How to create events
  - How to manage members
  - How to interpret analytics
  - How to configure integrations
- [ ] Developer documentation:
  - Architecture overview (Python + ZeroDB + Next.js)
  - API reference (auto-generated from Pydantic schemas)
  - ZeroDB schema documentation
  - Deployment procedures
  - Runbook (incident response)
- [ ] Video tutorials (optional):
  - Platform overview (5 minutes)
  - Admin training (15 minutes)

**Technical Notes:**
- Create `/docs/` directory with Markdown files
- Use MkDocs or Docusaurus for documentation site
- Host docs at docs.wwmaa.com
- Record screencasts with Loom

**Dependencies:** None

---

#### US-090: Launch Plan & Runbook
**Priority:** 🔴 Critical | **Story Points:** 3 | **Sprint:** 10

**As a** operations team
**I want** a launch plan and incident runbook
**So that** we can launch smoothly and handle issues

**Acceptance Criteria:**
- [ ] Launch plan includes:
  - Go-live date and time
  - Pre-launch checklist
  - Launch day checklist
  - Post-launch checklist
  - Rollback plan
  - Communication plan (email, social media)
- [ ] Runbook includes:
  - Incident response procedures
  - Common issues and fixes
  - Contact information (on-call rotation)
  - ZeroDB recovery procedures
  - Rollback procedures
  - Escalation matrix
- [ ] On-call rotation scheduled (30-day hypercare)
- [ ] Launch announcement drafted

**Technical Notes:**
- Store runbook in `/docs/runbook.md`
- Use PagerDuty or Opsgenie for on-call
- Schedule launch for low-traffic time (e.g., Tuesday 10 AM)
- Have rollback plan ready

**Dependencies:** All features complete

---

## Post-MVP Backlog

### EPIC-14: Internationalization (i18n)

**Priority:** 🟢 Medium | **Story Points:** 21 | **Target:** Post-MVP

---

#### US-091: i18n Infrastructure Setup
**Priority:** 🟢 Medium | **Story Points:** 5

**As a** developer
**I want** i18n infrastructure configured
**So that** we can support multiple languages

**Acceptance Criteria:**
- [ ] next-i18next or next-intl configured
- [ ] Locale detection (browser, URL, cookie)
- [ ] Translation files structure: `/locales/{lang}/{namespace}.json`
- [ ] Languages: en (English), es (Spanish), jp (Japanese)
- [ ] Language switcher in navigation
- [ ] URL routing: /en/, /es/, /jp/
- [ ] Fallback to English if translation missing

**Technical Notes:**
- Use next-intl (recommended for App Router)
- Store locale preference in cookie
- Create middleware for locale detection

**Dependencies:** None

---

#### US-092: Content Translation
**Priority:** 🟢 Medium | **Story Points:** 13

**As a** user
**I want** the interface in my language
**So that** I can understand and use the platform

**Acceptance Criteria:**
- [ ] UI translated (navigation, buttons, labels, errors)
- [ ] Static pages translated (About, FAQ, Privacy, Terms)
- [ ] Email templates translated
- [ ] SEO metadata translated (titles, descriptions)
- [ ] Blog posts remain in original language (English)
- [ ] Members can set preferred language in profile (store in ZeroDB)
- [ ] Language preference used for emails

**Technical Notes:**
- Hire professional translators (avoid machine translation)
- Use translation management tool (Crowdin, Lokalise)
- Store translations in JSON files
- Use interpolation for dynamic content

**Dependencies:** US-091

---

#### US-093: RTL Support
**Priority:** 🟢 Medium | **Story Points:** 3

**As a** user who reads right-to-left languages
**I want** proper RTL layout
**So that** the interface feels natural

**Acceptance Criteria:**
- [ ] CSS supports RTL (use logical properties)
- [ ] Layout flips for RTL languages (Arabic, Hebrew)
- [ ] Icons and images flip appropriately
- [ ] Text direction set correctly
- [ ] Tested with Arabic UI

**Technical Notes:**
- Use CSS logical properties (margin-inline-start vs margin-left)
- Use Tailwind RTL plugin
- Test with dir="rtl" attribute

**Dependencies:** US-091

---

### Technical Debt & Improvements

#### US-094: Migrate from Mock Data to ZeroDB
**Priority:** 🔴 Critical | **Story Points:** 8 | **Sprint:** 2

**As a** developer
**I want** to remove all mock data
**So that** the application uses real data from ZeroDB

**Acceptance Criteria:**
- [ ] Replace mock users with ZeroDB queries
- [ ] Replace mock events with ZeroDB queries
- [ ] Replace mock applications with ZeroDB queries
- [ ] Replace mock tiers with ZeroDB queries
- [ ] Remove `/lib/mock/db.ts`
- [ ] Remove mock mode from API layer
- [ ] All Python API endpoints query ZeroDB

**Technical Notes:**
- Update `/lib/api.ts` to remove MODE variable
- Replace mock functions with Python backend API calls
- Test all features after migration

**Dependencies:** US-001, US-004

---

#### US-095: API Response Caching Strategy
**Priority:** 🟡 High | **Story Points:** 5 | **Sprint:** 3

**As a** developer
**I want** a consistent caching strategy
**So that** API performance is optimized

**Acceptance Criteria:**
- [ ] Cache policy defined for each endpoint type:
  - Membership tiers: 1 hour
  - Events: 10 minutes
  - Search results: 5 minutes
  - User profile: 5 minutes
  - Blog posts: 30 minutes
- [ ] Cache invalidation on data updates in ZeroDB
- [ ] Cache headers set (Cache-Control, ETag)
- [ ] Redis cache implemented
- [ ] Cache hit/miss metrics tracked

**Technical Notes:**
- Use Redis
- Implement cache-aside pattern
- Create `/backend/utils/cache.py` utility
- Set cache headers in API responses

**Dependencies:** US-007 (caching layer)

---

#### US-096: ZeroDB Query Optimization
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 4

**As a** developer
**I want** optimized ZeroDB queries
**So that** API response times are fast

**Acceptance Criteria:**
- [ ] Slow query log analyzed (queries > 1 second)
- [ ] Query patterns optimized (minimize API calls)
- [ ] Batch queries where possible
- [ ] N+1 query problems fixed
- [ ] Query result pagination implemented (limit, offset)
- [ ] Connection pool sized appropriately

**Technical Notes:**
- Profile ZeroDB API calls
- Use batch queries for related data
- Implement pagination in Python endpoints
- Monitor with OpenTelemetry

**Dependencies:** US-001

---

#### US-097: Monitoring Dashboard (Grafana)
**Priority:** 🟡 High | **Story Points:** 8 | **Sprint:** 7

**As a** operations team
**I want** a unified monitoring dashboard
**So that** I can see system health at a glance

**Acceptance Criteria:**
- [ ] Grafana instance deployed
- [ ] Dashboards created:
  - System health (CPU, memory, disk)
  - API performance (latency, throughput, errors)
  - ZeroDB performance (query time, API calls)
  - Search performance (ZeroDB vector search, AI Registry)
  - Business metrics (signups, MRR, RSVPs)
- [ ] Alerts configured (PagerDuty integration)
- [ ] Dashboard accessible at monitoring.wwmaa.com
- [ ] Access restricted to operations team

**Technical Notes:**
- Deploy Grafana on Railway or separate VPS
- Use Prometheus or OpenTelemetry as data source
- Import community dashboards as starting point
- Create custom dashboards for business metrics

**Dependencies:** US-065 (OpenTelemetry)

---

#### US-098: Feature Flags System
**Priority:** 🟢 Medium | **Story Points:** 5 | **Sprint:** Post-MVP

**As a** product manager
**I want** feature flags
**So that** I can control rollout of new features

**Acceptance Criteria:**
- [ ] Feature flag system implemented (LaunchDarkly or custom in ZeroDB)
- [ ] Flags configurable per environment
- [ ] Flags configurable per user (target specific users)
- [ ] Flags configurable by percentage (gradual rollout)
- [ ] Flags accessible in code: `is_feature_enabled('feature_name')`
- [ ] Flags tracked in analytics (which users saw what)
- [ ] Admin UI for managing flags

**Technical Notes:**
- Use LaunchDarkly (easiest) or build custom with ZeroDB
- Store flags in ZeroDB config collection
- Create `/backend/services/feature_flags_service.py`
- Implement flag evaluation middleware

**Dependencies:** None

---

## Backlog Summary

### Story Point Totals by Epic

| Epic | Total Story Points | Sprints Required |
|------|-------------------|------------------|
| EP-01: ZeroDB & Infrastructure | 34 | 1 |
| EP-02: Authentication & Authorization | 21 | 1 |
| EP-03: Membership Application Workflow | 34 | 2 |
| EP-04: Payment Processing & Subscriptions | 55 | 2 |
| EP-05: Event Management System | 34 | 1 |
| EP-06: AI-Powered Semantic Search | 55 | 2 |
| EP-07: Live Training (RTC & VOD) | 55 | 2 |
| EP-08: Admin Panel & Dashboards | 34 | 1 |
| EP-09: Newsletter & Content Integration | 21 | 1 |
| EP-10: Analytics & Observability | 21 | 1 |
| EP-11: Security & Compliance | 34 | 2 |
| EP-12: Testing & QA | Ongoing | All sprints |
| EP-13: Deployment & CI/CD | 13 | 1 |
| EP-14: Internationalization (i18n) | 21 | Post-MVP |
| **Total (MVP)** | **411** | **~10 sprints** |

### Sprint Plan (2-week sprints, 40-50 points/sprint)

| Sprint | Focus Epics | Story Points | Key Deliverables |
|--------|------------|--------------|------------------|
| **Sprint 1** | EP-01, EP-02 | 55 | ZeroDB setup, Python backend, Authentication |
| **Sprint 2** | EP-03 | 34 | Membership applications, Two-board approval |
| **Sprint 3** | EP-04 (part 1) | 47 | Stripe integration, Subscriptions, Webhooks |
| **Sprint 4** | EP-04 (part 2), EP-05 | 42 | Payment flows, Events CRUD, RSVP |
| **Sprint 5** | EP-06 (part 1), EP-08 | 47 | AI Search setup, ZeroDB vector search, Admin panel |
| **Sprint 6** | EP-06 (part 2), EP-07 (part 1), EP-09 | 48 | Search UI, Cloudflare Calls, Newsletter |
| **Sprint 7** | EP-07 (part 2), EP-10, EP-11 (part 1) | 52 | VOD, Analytics, Security |
| **Sprint 8** | EP-11 (part 2), EP-13 | 37 | GDPR compliance, Railway deployment |
| **Sprint 9** | Launch Prep | 21 | Security audit, UAT, Performance testing |
| **Sprint 10** | Launch! | 8 | Final testing, Documentation, Go-live |
| **Post-MVP** | EP-14 | 21 | Internationalization |

---

## Technology Stack Summary

**Backend:** Python 3.11+ (FastAPI or Flask)
**Database:** AINative ZeroDB (Collections + Vector Search + Object Storage)
**Frontend:** Next.js 13+ (React + TypeScript + Tailwind)
**Video:** Cloudflare Calls (WebRTC) + Cloudflare Stream (VOD)
**Cache:** Redis (Upstash or Railway)
**Payments:** Stripe
**Newsletter:** BeeHiiv
**Email:** Postmark or SendGrid
**Hosting:** Railway (Python backend + Next.js frontend)
**CDN:** Cloudflare
**Analytics:** Google Analytics 4 + OpenTelemetry
**Monitoring:** Sentry + Grafana + PagerDuty

---

## Key Architecture Principles

1. **All structured data → ZeroDB Collections** (users, events, etc.)
2. **All file storage → ZeroDB Object Storage** (images, documents, backups)
3. **All semantic search → ZeroDB Vector Search** (embeddings)
4. **All videos → Cloudflare Stream** (VOD only)
5. **All live training → Cloudflare Calls** (WebRTC only)
6. **Python backend for ALL API logic** (NOT Node.js)
7. **Railway for hosting** (Python + Next.js + Redis)
8. **NO AWS, NO Supabase, NO PostgreSQL, NO Cloudflare R2**

---

**End of Backlog v2.0**

This backlog is aligned with the corrected architecture: Python backend, AINative ZeroDB for all data/object storage, Cloudflare for video only, and Railway for hosting.
