#!/usr/bin/env python3
"""
WWMAA Staging Environment Seed Data Script

This script populates the staging environment with realistic test data:
- 50 test user profiles (various tiers)
- 20 test events (past, upcoming, members-only)
- 100 test blog posts (for semantic search testing)
- 10 test training sessions
- Sample membership applications in various states
- Test payment and subscription records

Usage:
    python scripts/seed-staging-data.py

Environment:
    Requires staging environment variables to be set (ZERODB_API_KEY, etc.)
    See .env.staging.example for required configuration
"""

import os
import sys
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.zerodb_service import ZeroDBService
from backend.config import get_settings

# Ensure we're in staging environment
settings = get_settings()
if settings.python_env != 'staging':
    print(f"ERROR: Must run in staging environment (current: {settings.python_env})")
    print("Set PYTHON_ENV=staging before running this script")
    sys.exit(1)


class StagingSeedData:
    """Generate and insert seed data for staging environment."""

    def __init__(self):
        """Initialize ZeroDB service."""
        self.zerodb = ZeroDBService()
        self.created_users = []
        self.created_events = []
        self.created_blogs = []

    def generate_test_users(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate test user profiles with various tiers and statuses."""
        users = []
        tiers = ['basic', 'standard', 'premium']
        statuses = ['active', 'suspended', 'pending']

        for i in range(count):
            tier = tiers[i % 3]
            status = 'active' if i < 45 else random.choice(statuses)

            user = {
                'email': f'test.user{i:03d}@staging.wwmaa.com',
                'full_name': f'Test User {i:03d}',
                'tier': tier,
                'status': status,
                'bio': f'Test user profile for staging environment - Tier: {tier}',
                'phone': f'+1-555-{random.randint(1000, 9999)}',
                'company': f'Test Company {random.randint(1, 20)}',
                'job_title': random.choice([
                    'Software Engineer', 'Marketing Manager', 'Data Scientist',
                    'Product Manager', 'Designer', 'Consultant'
                ]),
                'linkedin_url': f'https://linkedin.com/in/testuser{i:03d}',
                'github_url': f'https://github.com/testuser{i:03d}' if tier == 'premium' else None,
                'location': random.choice([
                    'San Francisco, CA', 'New York, NY', 'Austin, TX',
                    'Seattle, WA', 'Boston, MA', 'Remote'
                ]),
                'interests': random.sample([
                    'AI/ML', 'Web Development', 'Mobile Development',
                    'DevOps', 'Cloud Computing', 'Data Science',
                    'Cybersecurity', 'Blockchain', 'IoT'
                ], k=random.randint(2, 5)),
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'is_seed_data': True,
                'seed_batch': 'staging-v1'
            }
            users.append(user)

        return users

    def generate_test_events(self, count: int = 20) -> List[Dict[str, Any]]:
        """Generate test events (past, upcoming, members-only)."""
        events = []
        event_types = ['workshop', 'networking', 'conference', 'training', 'social']
        access_types = ['public', 'members_only', 'premium_only']

        for i in range(count):
            # Mix of past and upcoming events
            is_past = i < 8
            days_offset = -random.randint(1, 90) if is_past else random.randint(1, 90)
            event_date = datetime.utcnow() + timedelta(days=days_offset)

            event_type = random.choice(event_types)
            access_type = access_types[i % 3]

            event = {
                'title': f'{event_type.title()} Event {i:03d}: {random.choice(["AI", "Web3", "Cloud", "Security", "Data"])} Session',
                'description': f'Test {event_type} event for staging environment. Access: {access_type}. This is a comprehensive event covering various topics in technology and innovation.',
                'event_type': event_type,
                'access_type': access_type,
                'event_date': event_date.isoformat(),
                'start_time': f'{random.randint(9, 18):02d}:00',
                'end_time': f'{random.randint(10, 20):02d}:00',
                'location': random.choice([
                    'Virtual (Zoom)', 'San Francisco Conference Center',
                    'New York Tech Hub', 'Austin Convention Center',
                    'Hybrid (Virtual + In-Person)'
                ]),
                'max_attendees': random.choice([50, 100, 200, None]),
                'current_attendees': random.randint(10, 50) if not is_past else random.randint(30, 100),
                'registration_deadline': (event_date - timedelta(days=3)).isoformat(),
                'organizer': random.choice(self.created_users)['email'] if self.created_users else 'admin@staging.wwmaa.com',
                'status': 'completed' if is_past else 'upcoming',
                'tags': random.sample([
                    'AI', 'Machine Learning', 'Cloud Computing', 'DevOps',
                    'Web Development', 'Mobile', 'Security', 'Networking'
                ], k=random.randint(2, 4)),
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'is_seed_data': True,
                'seed_batch': 'staging-v1'
            }
            events.append(event)

        return events

    def generate_test_blog_posts(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test blog posts for semantic search testing."""
        posts = []
        categories = ['Technology', 'AI/ML', 'Web Development', 'Career', 'Industry News']
        topics = [
            'Introduction to Machine Learning',
            'Building Scalable Web Applications',
            'Career Advice for Developers',
            'Latest Trends in Cloud Computing',
            'Getting Started with Python',
            'Advanced JavaScript Techniques',
            'Data Science Best Practices',
            'Mobile App Development Guide',
            'Cybersecurity Fundamentals',
            'DevOps and CI/CD Pipelines'
        ]

        for i in range(count):
            topic = random.choice(topics)
            category = random.choice(categories)

            post = {
                'title': f'{topic} - Part {random.randint(1, 5)}',
                'slug': f'{topic.lower().replace(" ", "-")}-part-{i}',
                'content': f'''
                    <h1>{topic}</h1>
                    <p>This is a comprehensive guide to {topic.lower()}. In this article, we'll explore various aspects and provide practical examples.</p>

                    <h2>Introduction</h2>
                    <p>Understanding {topic.lower()} is crucial for modern developers. This guide will help you master the fundamentals and advanced concepts.</p>

                    <h2>Key Concepts</h2>
                    <ul>
                        <li>Concept 1: Foundation and basics</li>
                        <li>Concept 2: Intermediate techniques</li>
                        <li>Concept 3: Advanced strategies</li>
                        <li>Concept 4: Best practices and optimization</li>
                    </ul>

                    <h2>Practical Applications</h2>
                    <p>Let's explore some real-world applications and use cases that demonstrate the power of {topic.lower()}.</p>

                    <h2>Conclusion</h2>
                    <p>By following this guide, you'll have a solid understanding of {topic.lower()} and be able to apply these concepts in your projects.</p>
                ''',
                'excerpt': f'A comprehensive guide to {topic.lower()} covering fundamentals, advanced concepts, and practical applications.',
                'category': category,
                'author': random.choice(self.created_users)['full_name'] if self.created_users else 'Test Author',
                'author_email': random.choice(self.created_users)['email'] if self.created_users else 'author@staging.wwmaa.com',
                'published_at': (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                'status': 'published' if i < 95 else 'draft',
                'tags': random.sample([
                    'programming', 'tutorial', 'guide', 'best-practices',
                    'beginners', 'advanced', 'tips', 'tools'
                ], k=random.randint(2, 5)),
                'views': random.randint(10, 5000),
                'likes': random.randint(0, 500),
                'reading_time_minutes': random.randint(3, 15),
                'featured_image': f'https://picsum.photos/seed/{i}/800/400',
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'is_seed_data': True,
                'seed_batch': 'staging-v1'
            }
            posts.append(post)

        return posts

    def generate_test_applications(self, count: int = 30) -> List[Dict[str, Any]]:
        """Generate test membership applications in various states."""
        applications = []
        statuses = ['pending', 'approved', 'rejected', 'under_review']
        tiers = ['basic', 'standard', 'premium']

        for i in range(count):
            user = random.choice(self.created_users) if self.created_users else None
            status = statuses[i % 4]
            tier = random.choice(tiers)

            application = {
                'applicant_email': user['email'] if user else f'applicant{i:03d}@staging.wwmaa.com',
                'applicant_name': user['full_name'] if user else f'Test Applicant {i:03d}',
                'requested_tier': tier,
                'status': status,
                'application_text': f'I am interested in joining WWMAA at the {tier} tier. I have experience in technology and would like to contribute to the community.',
                'linkedin_profile': f'https://linkedin.com/in/applicant{i:03d}',
                'company': f'Company {random.randint(1, 50)}',
                'job_title': random.choice(['Engineer', 'Manager', 'Director', 'VP', 'Consultant']),
                'years_experience': random.randint(1, 20),
                'referral_source': random.choice(['website', 'friend', 'social_media', 'event', 'search']),
                'reviewed_by': 'admin@staging.wwmaa.com' if status != 'pending' else None,
                'reviewed_at': datetime.utcnow().isoformat() if status != 'pending' else None,
                'review_notes': f'Test review notes for application {i}' if status != 'pending' else None,
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'is_seed_data': True,
                'seed_batch': 'staging-v1'
            }
            applications.append(application)

        return applications

    def generate_test_subscriptions(self, count: int = 40) -> List[Dict[str, Any]]:
        """Generate test subscription records."""
        subscriptions = []
        statuses = ['active', 'past_due', 'canceled', 'trialing']
        tiers = ['basic', 'standard', 'premium']

        for i in range(count):
            user = random.choice(self.created_users) if self.created_users else None
            tier = tiers[i % 3]
            status = statuses[i % 4]

            start_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))

            subscription = {
                'user_email': user['email'] if user else f'subscriber{i:03d}@staging.wwmaa.com',
                'stripe_subscription_id': f'sub_test_{i:08d}',
                'stripe_customer_id': f'cus_test_{i:08d}',
                'tier': tier,
                'status': status,
                'current_period_start': start_date.isoformat(),
                'current_period_end': (start_date + timedelta(days=30)).isoformat(),
                'cancel_at_period_end': status == 'canceled',
                'canceled_at': datetime.utcnow().isoformat() if status == 'canceled' else None,
                'trial_end': (start_date + timedelta(days=14)).isoformat() if status == 'trialing' else None,
                'created_at': start_date.isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'is_seed_data': True,
                'seed_batch': 'staging-v1'
            }
            subscriptions.append(subscription)

        return subscriptions

    async def seed_all_data(self):
        """Seed all test data into staging environment."""
        print("=" * 80)
        print("WWMAA Staging Environment Seed Data Script")
        print("=" * 80)
        print(f"Environment: {settings.python_env}")
        print(f"ZeroDB URL: {settings.zerodb_api_base_url}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print("=" * 80)

        try:
            # 1. Seed Users
            print("\n[1/6] Generating test users...")
            users = self.generate_test_users(50)
            print(f"  Generated {len(users)} test users")

            print("  Inserting users into staging_profiles collection...")
            for user in users:
                try:
                    result = self.zerodb.create_document('staging_profiles', user)
                    self.created_users.append(user)
                except Exception as e:
                    print(f"  Warning: Failed to insert user {user['email']}: {e}")

            print(f"  ✓ Inserted {len(self.created_users)} users successfully")

            # 2. Seed Events
            print("\n[2/6] Generating test events...")
            events = self.generate_test_events(20)
            print(f"  Generated {len(events)} test events")

            print("  Inserting events into staging_events collection...")
            for event in events:
                try:
                    result = self.zerodb.create_document('staging_events', event)
                    self.created_events.append(event)
                except Exception as e:
                    print(f"  Warning: Failed to insert event {event['title']}: {e}")

            print(f"  ✓ Inserted {len(self.created_events)} events successfully")

            # 3. Seed Blog Posts
            print("\n[3/6] Generating test blog posts...")
            blogs = self.generate_test_blog_posts(100)
            print(f"  Generated {len(blogs)} test blog posts")

            print("  Inserting blog posts into staging_blog_posts collection...")
            for blog in blogs:
                try:
                    result = self.zerodb.create_document('staging_blog_posts', blog)
                    self.created_blogs.append(blog)
                except Exception as e:
                    print(f"  Warning: Failed to insert blog {blog['title']}: {e}")

            print(f"  ✓ Inserted {len(self.created_blogs)} blog posts successfully")

            # 4. Seed Applications
            print("\n[4/6] Generating test applications...")
            applications = self.generate_test_applications(30)
            print(f"  Generated {len(applications)} test applications")

            print("  Inserting applications into staging_applications collection...")
            inserted_apps = 0
            for app in applications:
                try:
                    result = self.zerodb.create_document('staging_applications', app)
                    inserted_apps += 1
                except Exception as e:
                    print(f"  Warning: Failed to insert application: {e}")

            print(f"  ✓ Inserted {inserted_apps} applications successfully")

            # 5. Seed Subscriptions
            print("\n[5/6] Generating test subscriptions...")
            subscriptions = self.generate_test_subscriptions(40)
            print(f"  Generated {len(subscriptions)} test subscriptions")

            print("  Inserting subscriptions into staging_subscriptions collection...")
            inserted_subs = 0
            for sub in subscriptions:
                try:
                    result = self.zerodb.create_document('staging_subscriptions', sub)
                    inserted_subs += 1
                except Exception as e:
                    print(f"  Warning: Failed to insert subscription: {e}")

            print(f"  ✓ Inserted {inserted_subs} subscriptions successfully")

            # 6. Summary
            print("\n[6/6] Seed data summary:")
            print(f"  Users:         {len(self.created_users)}")
            print(f"  Events:        {len(self.created_events)}")
            print(f"  Blog Posts:    {len(self.created_blogs)}")
            print(f"  Applications:  {inserted_apps}")
            print(f"  Subscriptions: {inserted_subs}")

            print("\n" + "=" * 80)
            print("✓ Staging environment seeding completed successfully!")
            print("=" * 80)

            print("\nNext steps:")
            print("1. Verify data in ZeroDB dashboard")
            print("2. Test authentication with test users")
            print("3. Test event RSVP functionality")
            print("4. Test semantic search with blog posts")
            print("5. Test application approval workflow")

        except Exception as e:
            print(f"\n✗ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    seeder = StagingSeedData()
    asyncio.run(seeder.seed_all_data())


if __name__ == '__main__':
    main()
