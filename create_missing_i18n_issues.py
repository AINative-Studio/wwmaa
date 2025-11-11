#!/usr/bin/env python3
"""
Script to create the missing i18n User Story issues.
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

# First check if EPIC-14 exists
print("Checking for EPIC-14...")
result = subprocess.run(
    ['gh', 'issue', 'list', '--search', 'EPIC-14 in:title', '--json', 'number,title'],
    capture_output=True,
    text=True,
    cwd='/Users/aideveloper/Desktop/wwmaa'
)

import json
existing_issues = json.loads(result.stdout)
epic_14_exists = any('EPIC-14' in issue['title'] for issue in existing_issues)

if not epic_14_exists:
    print("EPIC-14 not found, creating it...")
    epic_14_body = """**Epic Owner:** Full-stack Dev
**Business Value:** Enable global reach with multi-language support
**Dependencies:** None (can be done post-MVP)
**Total Story Points:** 21

This epic tracks all user stories related to internationalization (i18n) and localization support, enabling the platform to serve users in multiple languages.
"""
    create_github_issue(
        title="EPIC-14: Internationalization (i18n)",
        body=epic_14_body,
        labels=['epic']
    )
    print()
else:
    print("✓ EPIC-14 already exists")
    print()

# Define the missing user stories
missing_stories = [
    {
        'title': 'US-091: i18n Infrastructure Setup',
        'labels': ['user-story', 'priority-medium', 'sprint-post-mvp'],
        'body': '''**Priority:** 🟢 Medium
**Story Points:** 5
**Sprint:** Post-MVP

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

**Dependencies:** None'''
    },
    {
        'title': 'US-092: Content Translation',
        'labels': ['user-story', 'priority-medium', 'sprint-post-mvp'],
        'body': '''**Priority:** 🟢 Medium
**Story Points:** 13
**Sprint:** Post-MVP

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

**Dependencies:** US-091'''
    },
    {
        'title': 'US-093: RTL Support',
        'labels': ['user-story', 'priority-medium', 'sprint-post-mvp'],
        'body': '''**Priority:** 🟢 Medium
**Story Points:** 3
**Sprint:** Post-MVP

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

**Dependencies:** US-091'''
    }
]

print("=" * 80)
print("Creating Missing i18n User Story Issues")
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
print(f"✓ Created {success_count}/{len(missing_stories)} missing i18n issues")
print("=" * 80)
