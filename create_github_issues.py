#!/usr/bin/env python3
"""
Script to parse BACKLOG.md and create GitHub issues for all Epics and User Stories.
"""

import re
import subprocess
import json
from typing import List, Dict

def read_backlog_file(file_path: str) -> str:
    """Read the entire backlog file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_epics(content: str) -> List[Dict]:
    """Parse all Epic sections from the backlog."""
    epics = []

    # Pattern to match Epic headers
    epic_pattern = r'### (EPIC-\d+): (.+?)\n\n\*\*Epic Owner:\*\* (.+?)\n\*\*Business Value:\*\* (.+?)\n\*\*Dependencies:\*\* (.+?)\n\*\*Total Story Points:\*\* (.+?)(?:\n|$)'

    matches = re.finditer(epic_pattern, content, re.MULTILINE)

    for match in matches:
        epic_id = match.group(1)
        title = match.group(2)
        owner = match.group(3)
        business_value = match.group(4)
        dependencies = match.group(5)
        story_points = match.group(6)

        epic_body = f"""**Epic Owner:** {owner}
**Business Value:** {business_value}
**Dependencies:** {dependencies}
**Total Story Points:** {story_points}

This epic tracks all user stories related to {title.lower()}.
"""

        epics.append({
            'id': epic_id,
            'title': f"{epic_id}: {title}",
            'body': epic_body,
            'labels': ['epic']
        })

    return epics

def parse_user_stories(content: str) -> List[Dict]:
    """Parse all User Story sections from the backlog."""
    user_stories = []

    # Split content by user story headers
    us_sections = re.split(r'#### (US-\d+): (.+?)\n', content)

    # Process in groups of 3 (text before, US-ID, US-Title, US-Content)
    for i in range(1, len(us_sections), 3):
        if i + 2 > len(us_sections):
            break

        us_id = us_sections[i]
        us_title = us_sections[i + 1]
        us_content = us_sections[i + 2]

        # Extract priority and story points
        priority_match = re.search(r'\*\*Priority:\*\* ([^|]+) \| \*\*Story Points:\*\* (\d+) \| \*\*Sprint:\*\* (.+?)(?:\n|$)', us_content)

        if not priority_match:
            continue

        priority_text = priority_match.group(1).strip()
        story_points = priority_match.group(2)
        sprint = priority_match.group(3).strip()

        # Map priority emoji to label
        priority_map = {
            '🔴 Critical': 'priority-critical',
            '🟡 High': 'priority-high',
            '🟢 Medium': 'priority-medium',
            '🔵 Low': 'priority-low'
        }
        priority_label = priority_map.get(priority_text, 'priority-medium')

        # Extract the full user story content (everything after the priority line)
        # Stop at the next user story or epic
        content_start = priority_match.end()
        next_section = re.search(r'(?:---\n\n#### US-|\n### EPIC-)', us_content[content_start:])
        if next_section:
            story_content = us_content[content_start:content_start + next_section.start()].strip()
        else:
            story_content = us_content[content_start:].strip()

        # Build the issue body
        issue_body = f"""**Priority:** {priority_text}
**Story Points:** {story_points}
**Sprint:** {sprint}

{story_content}
"""

        # Determine labels
        labels = ['user-story', priority_label]

        # Add sprint label if specified
        if sprint and sprint != 'TBD':
            sprint_label = f"sprint-{sprint.lower().replace(' ', '-').replace(',', '')}"
            labels.append(sprint_label)

        user_stories.append({
            'id': us_id,
            'title': f"{us_id}: {us_title}",
            'body': issue_body,
            'labels': labels,
            'story_points': story_points
        })

    return user_stories

def create_github_issue(title: str, body: str, labels: List[str], assignee: str = "urbantech") -> str:
    """Create a GitHub issue using gh CLI."""

    # Build the gh command
    cmd = ['gh', 'issue', 'create', '--title', title, '--body', body, '--assignee', assignee]

    # Add labels
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

def main():
    backlog_file = '/Users/aideveloper/Desktop/wwmaa/BACKLOG.md'

    print("=" * 80)
    print("WWMAA GitHub Issue Creator")
    print("=" * 80)
    print()

    # Read the backlog file
    print("Reading BACKLOG.md...")
    content = read_backlog_file(backlog_file)
    print(f"✓ File loaded ({len(content)} characters)")
    print()

    # Parse Epics
    print("Parsing Epics...")
    epics = parse_epics(content)
    print(f"✓ Found {len(epics)} Epics")
    print()

    # Parse User Stories
    print("Parsing User Stories...")
    user_stories = parse_user_stories(content)
    print(f"✓ Found {len(user_stories)} User Stories")
    print()

    # Create Epic issues
    print("=" * 80)
    print("Creating Epic Issues (14 total)")
    print("=" * 80)
    print()

    epic_urls = {}
    for epic in epics:
        url = create_github_issue(
            title=epic['title'],
            body=epic['body'],
            labels=epic['labels']
        )
        if url:
            epic_urls[epic['id']] = url
        print()

    print(f"✓ Created {len(epic_urls)} Epic issues")
    print()

    # Create User Story issues
    print("=" * 80)
    print("Creating User Story Issues (98 total)")
    print("=" * 80)
    print()

    us_count = 0
    for us in user_stories:
        url = create_github_issue(
            title=us['title'],
            body=us['body'],
            labels=us['labels']
        )
        if url:
            us_count += 1

        # Add a small delay to avoid rate limiting
        if us_count % 10 == 0:
            print(f"Progress: {us_count}/{len(user_stories)} user stories created")
            print()

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✓ Created {len(epic_urls)} Epic issues")
    print(f"✓ Created {us_count} User Story issues")
    print(f"✓ Total: {len(epic_urls) + us_count} issues created")
    print()
    print("All issues have been assigned to: urbantech")
    print()

if __name__ == '__main__':
    main()
