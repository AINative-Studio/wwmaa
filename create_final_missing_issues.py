#!/usr/bin/env python3
"""
Script to create the final missing User Story issues.
"""

import subprocess

def create_github_issue(title: str, body: str, labels: list, assignee: str = "urbantech"):
    """Create a GitHub issue using gh CLI."""
    cmd = ['gh', 'issue', 'create', '--title', title, '--body', body, '--assignee', assignee]

    for label in labels:
        cmd.extend(['--label', label])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd='/Users/aideveloper/Desktop/wwmaa')
        issue_url = result.stdout.strip()
        print(f"✓ Created: {title}")
        print(f"  URL: {issue_url}")
        return issue_url
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create: {title}")
        print(f"  Error: {e.stderr}")
        return None

# Define the final missing user stories
missing_stories = [
    {
        'title': 'US-051: Admin Dashboard Overview',
        'labels': ['user-story', 'priority-critical', 'sprint-4-5'],
        'body': '''**Priority:** 🔴 Critical
**Story Points:** 8
**Sprint:** 4-5

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

**Dependencies:** Multiple (US-015, US-023, US-029, US-038)'''
    },
    {
        'title': 'US-052: Member Management Interface',
        'labels': ['user-story', 'priority-critical', 'sprint-4-5'],
        'body': '''**Priority:** 🔴 Critical
**Story Points:** 8
**Sprint:** 4-5

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

**Dependencies:** US-001, US-023'''
    },
    {
        'title': 'US-076: Unit Testing Setup (Python)',
        'labels': ['user-story', 'priority-high', 'sprint-1'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 5
**Sprint:** 1 (setup), Ongoing

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

**Dependencies:** None'''
    },
    {
        'title': 'US-077: Integration Testing (Python API)',
        'labels': ['user-story', 'priority-high', 'sprint-3'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 8
**Sprint:** 3 (setup), Ongoing

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

**Dependencies:** US-001 (ZeroDB client)'''
    },
    {
        'title': 'US-078: End-to-End Testing (Frontend + Backend)',
        'labels': ['user-story', 'priority-high', 'sprint-5'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 13
**Sprint:** 5 (setup), Ongoing

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

**Dependencies:** Multiple (US-010, US-017, US-022, US-032, US-038, US-045, US-048)'''
    },
    {
        'title': 'US-079: Accessibility Testing',
        'labels': ['user-story', 'priority-high', 'sprint-6'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 5
**Sprint:** 6 (setup), Ongoing

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

**Dependencies:** None'''
    },
    {
        'title': 'US-080: Load & Performance Testing',
        'labels': ['user-story', 'priority-high', 'sprint-8'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 8
**Sprint:** 8 (before launch)

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

**Dependencies:** US-065 (observability)'''
    }
]

# Need to create sprint-4-5 label first
print("Creating sprint-4-5 label...")
result = subprocess.run(
    ['gh', 'label', 'create', 'sprint-4-5', '--description', 'Sprint 4-5', '--color', 'BFD4F2'],
    capture_output=True,
    text=True,
    cwd='/Users/aideveloper/Desktop/wwmaa'
)
if result.returncode == 0:
    print("✓ Created sprint-4-5 label")
else:
    print("Note: sprint-4-5 label may already exist")
print()

print("=" * 80)
print("Creating Final Missing User Story Issues")
print("=" * 80)
print()

success_count = 0
for story in missing_stories:
    url = create_github_issue(
        title=story['title'],
        body=story['body'],
        labels=story['labels']
    )
    if url:
        success_count += 1
    print()

print("=" * 80)
print(f"✓ Created {success_count}/{len(missing_stories)} final missing issues")
print("=" * 80)
