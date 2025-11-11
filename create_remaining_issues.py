#!/usr/bin/env python3
"""
Script to create the remaining failed User Story issues.
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

# Define the remaining user stories
remaining_stories = [
    {
        'title': 'US-083: Railway Production Deployment',
        'labels': ['user-story', 'priority-critical', 'sprint-9-(launch-week)'],
        'body': '''**Priority:** 🔴 Critical
**Story Points:** 5
**Sprint:** 9 (Launch Week)

**As a** team
**I want** a production Railway environment deployed
**So that** we can serve real users

**Acceptance Criteria:**
- [ ] Production Railway project created
- [ ] Environment variables configured (production values)
- [ ] Domain configured (wwmaa.com)
- [ ] SSL certificate configured
- [ ] Database migrations run
- [ ] Production data seeded (membership tiers, initial content)
- [ ] Service health checks configured
- [ ] Deployment documented in runbook

**Technical Notes:**
- Use Railway production plan
- Configure auto-scaling if needed
- Set up proper resource limits
- Document deployment checklist

**Dependencies:** US-081'''
    },
    {
        'title': 'US-084: Continuous Deployment',
        'labels': ['user-story', 'priority-high', 'sprint-9'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 3
**Sprint:** 9

**As a** developer
**I want** continuous deployment to staging and production
**So that** changes are automatically deployed

**Acceptance Criteria:**
- [ ] CD workflow triggers on merge to main (staging)
- [ ] CD workflow triggers on tag push (production)
- [ ] Automatic Railway deployments configured
- [ ] Deployment notifications sent (Slack/Discord)
- [ ] Rollback procedure documented
- [ ] Deployment status visible in GitHub

**Technical Notes:**
- Use GitHub Actions for CD
- Implement blue-green deployments if possible
- Add deployment approval gates for production
- Document rollback procedure

**Dependencies:** US-082, US-083'''
    },
    {
        'title': 'US-085: Security Audit',
        'labels': ['user-story', 'priority-critical', 'sprint-9'],
        'body': '''**Priority:** 🔴 Critical
**Story Points:** 8
**Sprint:** 9

**As a** system administrator
**I want** a comprehensive security audit performed
**So that** we launch with minimal vulnerabilities

**Acceptance Criteria:**
- [ ] OWASP Top 10 checklist completed
- [ ] Dependency vulnerability scan (Snyk, npm audit)
- [ ] Penetration testing performed
- [ ] Security headers verified (CSP, HSTS, etc.)
- [ ] Authentication flow tested (session hijacking, CSRF)
- [ ] Input validation tested (XSS, SQL injection)
- [ ] Secrets audit (no hardcoded keys, proper env vars)
- [ ] Security findings documented and prioritized
- [ ] Critical vulnerabilities fixed before launch

**Technical Notes:**
- Use automated tools: OWASP ZAP, Burp Suite
- Test authentication flows manually
- Review all API endpoints for authorization issues
- Check for exposed sensitive data in responses

**Dependencies:** US-068, US-069, US-070, US-071'''
    },
    {
        'title': 'US-086: Performance Optimization',
        'labels': ['user-story', 'priority-high', 'sprint-9'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 8
**Sprint:** 9

**As a** user
**I want** fast page load times and responsive interactions
**So that** I have a good user experience

**Acceptance Criteria:**
- [ ] Lighthouse score > 90 on all key pages
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Core Web Vitals all "Good" (LCP, FID, CLS)
- [ ] Images optimized and lazy-loaded
- [ ] JavaScript bundles minimized
- [ ] API response times < 200ms (p95)
- [ ] Database query optimization completed

**Technical Notes:**
- Use Next.js Image optimization
- Implement code splitting
- Enable Redis caching for expensive queries
- Optimize database indexes
- Use CDN for static assets (Cloudflare)
- Minify CSS and JavaScript

**Dependencies:** US-095, US-096'''
    },
    {
        'title': 'US-087: Browser & Device Testing',
        'labels': ['user-story', 'priority-high', 'sprint-9'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 5
**Sprint:** 9

**As a** user
**I want** the application to work on different browsers and devices
**So that** I can access it from any platform

**Acceptance Criteria:**
- [ ] Tested on Chrome, Firefox, Safari, Edge (latest versions)
- [ ] Tested on mobile devices (iOS Safari, Android Chrome)
- [ ] Tested on tablets
- [ ] Responsive design verified at all breakpoints
- [ ] Touch interactions tested on mobile
- [ ] Browser compatibility issues documented and fixed
- [ ] Testing matrix documented

**Technical Notes:**
- Use BrowserStack or CrossBrowserTesting
- Test critical user flows on each platform
- Document any browser-specific issues
- Ensure graceful degradation for older browsers

**Dependencies:** US-078'''
    },
    {
        'title': 'US-088: User Acceptance Testing (UAT)',
        'labels': ['user-story', 'priority-critical', 'sprint-9'],
        'body': '''**Priority:** 🔴 Critical
**Story Points:** 13
**Sprint:** 9

**As a** product owner
**I want** real users to test the application
**So that** we can identify issues before launch

**Acceptance Criteria:**
- [ ] UAT plan created with test scenarios
- [ ] 10+ beta testers recruited from WWMAA community
- [ ] UAT environment prepared (staging)
- [ ] Test accounts created for beta testers
- [ ] Feedback collection process established
- [ ] UAT sessions conducted (guided and exploratory)
- [ ] Bugs triaged and prioritized
- [ ] Critical bugs fixed before launch
- [ ] UAT sign-off obtained from stakeholders

**Technical Notes:**
- Create UAT test scenarios covering all key user flows
- Use staging environment for testing
- Collect feedback via forms, interviews, session recordings
- Document all issues in GitHub
- Prioritize fixes based on severity and impact

**Dependencies:** US-083, US-087'''
    },
    {
        'title': 'US-089: Documentation & Training',
        'labels': ['user-story', 'priority-high', 'sprint-9-10'],
        'body': '''**Priority:** 🟡 High
**Story Points:** 8
**Sprint:** 9-10

**As a** stakeholder
**I want** comprehensive documentation and training materials
**So that** users and administrators know how to use the system

**Acceptance Criteria:**
- [ ] User guide created (member onboarding, features)
- [ ] Admin guide created (dashboard, member management)
- [ ] Video tutorials recorded (3-5 key features)
- [ ] FAQ section populated
- [ ] Help center integrated into application
- [ ] Developer documentation complete (API, architecture)
- [ ] Training session conducted for WWMAA board members
- [ ] Support process documented

**Technical Notes:**
- Use Loom or similar for video tutorials
- Create searchable documentation site
- Document API endpoints with examples
- Include troubleshooting guides

**Dependencies:** US-088'''
    },
    {
        'title': 'US-090: Launch Plan & Runbook',
        'labels': ['user-story', 'priority-critical', 'sprint-10'],
        'body': '''**Priority:** 🔴 Critical
**Story Points:** 5
**Sprint:** 10

**As a** team
**I want** a detailed launch plan and operational runbook
**So that** we can execute a smooth launch and handle incidents

**Acceptance Criteria:**
- [ ] Launch checklist created (pre-launch, launch day, post-launch)
- [ ] Rollback procedure documented
- [ ] Incident response runbook created
- [ ] Launch communication plan (emails, social media)
- [ ] Monitoring alerts configured
- [ ] On-call schedule established
- [ ] Launch retrospective scheduled
- [ ] Success metrics defined (KPIs, SLAs)

**Technical Notes:**
- Document all operational procedures
- Create incident response playbook
- Set up monitoring dashboards
- Prepare launch announcements
- Plan for traffic spikes

**Dependencies:** US-083, US-088'''
    },
    {
        'title': 'US-098: Feature Flags System',
        'labels': ['user-story', 'priority-medium', 'sprint-post-mvp'],
        'body': '''**Priority:** 🟢 Medium
**Story Points:** 5
**Sprint:** Post-MVP

**As a** developer
**I want** a feature flag system
**So that** we can enable/disable features without redeployment

**Acceptance Criteria:**
- [ ] Feature flag service configured (LaunchDarkly, Unleash, or custom)
- [ ] Feature flags implemented for key features
- [ ] Admin UI for managing flags
- [ ] Environment-specific flag configurations
- [ ] User targeting capabilities (enable for specific users/segments)
- [ ] Feature flag documentation

**Technical Notes:**
- Consider using LaunchDarkly, Unleash, or custom solution
- Implement feature flag checks in code
- Create admin interface for flag management
- Document flag usage and best practices

**Dependencies:** None (Post-MVP feature)'''
    }
]

print("=" * 80)
print("Creating Remaining User Story Issues")
print("=" * 80)
print()

success_count = 0
for story in remaining_stories:
    url = create_github_issue(
        title=story['title'],
        body=story['body'],
        labels=story['labels']
    )
    if url:
        success_count += 1
    print()

print("=" * 80)
print(f"✓ Created {success_count}/{len(remaining_stories)} remaining issues")
print("=" * 80)
