#!/usr/bin/env python3
"""
WWMAA Staging ZeroDB Setup Script

This script creates and configures ZeroDB collections for the staging environment.
It sets up the database schema with appropriate indexes and constraints.

Collections created:
- staging_profiles: User profiles with authentication data
- staging_events: Events and workshops
- staging_rsvps: Event RSVP records
- staging_applications: Membership applications
- staging_subscriptions: Stripe subscription records
- staging_blog_posts: Blog content for semantic search
- staging_newsletter_subscribers: Newsletter subscription records
- staging_training_sessions: Live training session records
- staging_chat_messages: Training chat messages
- staging_search_analytics: Search analytics data

Usage:
    python scripts/setup-staging-db.py

Environment:
    Requires ZERODB_API_KEY and PYTHON_ENV=staging
    See .env.staging.example for required configuration
"""

import os
import sys
import requests
from datetime import datetime
from typing import Dict, List, Any

# Ensure we're in staging environment
if os.getenv('PYTHON_ENV') != 'staging':
    print("ERROR: Must run in staging environment")
    print("Set PYTHON_ENV=staging before running this script")
    sys.exit(1)

# ZeroDB Configuration
ZERODB_API_KEY = os.getenv('ZERODB_API_KEY')
ZERODB_API_BASE_URL = os.getenv('ZERODB_API_BASE_URL', 'https://api.zerodb.io/v1')

if not ZERODB_API_KEY:
    print("ERROR: ZERODB_API_KEY not set")
    print("Please set ZERODB_API_KEY environment variable")
    sys.exit(1)


class ZeroDBStagingSetup:
    """Setup ZeroDB collections for staging environment."""

    def __init__(self):
        """Initialize ZeroDB API client."""
        self.api_key = ZERODB_API_KEY
        self.base_url = ZERODB_API_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def create_collection(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """
        Create a ZeroDB collection with schema.

        Args:
            collection_name: Name of the collection
            schema: Collection schema definition

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nCreating collection: {collection_name}")

            # Create collection
            response = requests.post(
                f'{self.base_url}/collections',
                headers=self.headers,
                json={
                    'name': collection_name,
                    'schema': schema
                }
            )

            if response.status_code in [200, 201]:
                print(f"  ✓ Collection created: {collection_name}")
                return True
            elif response.status_code == 409:
                print(f"  ℹ Collection already exists: {collection_name}")
                return True
            else:
                print(f"  ✗ Failed to create collection: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

        except Exception as e:
            print(f"  ✗ Error creating collection: {e}")
            return False

    def create_index(self, collection_name: str, index_name: str, fields: List[str]) -> bool:
        """
        Create an index on a collection.

        Args:
            collection_name: Name of the collection
            index_name: Name of the index
            fields: List of fields to index

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"  Creating index '{index_name}' on {fields}")

            response = requests.post(
                f'{self.base_url}/collections/{collection_name}/indexes',
                headers=self.headers,
                json={
                    'name': index_name,
                    'fields': fields
                }
            )

            if response.status_code in [200, 201]:
                print(f"    ✓ Index created: {index_name}")
                return True
            elif response.status_code == 409:
                print(f"    ℹ Index already exists: {index_name}")
                return True
            else:
                print(f"    ✗ Failed to create index: {response.status_code}")
                return False

        except Exception as e:
            print(f"    ✗ Error creating index: {e}")
            return False

    def setup_profiles_collection(self):
        """Create staging_profiles collection for user data."""
        schema = {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'full_name': {'type': 'string'},
                'hashed_password': {'type': 'string'},
                'tier': {'type': 'string', 'enum': ['basic', 'standard', 'premium']},
                'status': {'type': 'string', 'enum': ['active', 'suspended', 'pending']},
                'bio': {'type': 'string'},
                'phone': {'type': 'string'},
                'company': {'type': 'string'},
                'job_title': {'type': 'string'},
                'linkedin_url': {'type': 'string'},
                'github_url': {'type': 'string'},
                'location': {'type': 'string'},
                'interests': {'type': 'array', 'items': {'type': 'string'}},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['email', 'full_name', 'tier', 'status']
        }

        success = self.create_collection('staging_profiles', schema)
        if success:
            self.create_index('staging_profiles', 'email_idx', ['email'])
            self.create_index('staging_profiles', 'tier_idx', ['tier'])
            self.create_index('staging_profiles', 'status_idx', ['status'])

        return success

    def setup_events_collection(self):
        """Create staging_events collection."""
        schema = {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'event_type': {'type': 'string'},
                'access_type': {'type': 'string', 'enum': ['public', 'members_only', 'premium_only']},
                'event_date': {'type': 'string', 'format': 'date-time'},
                'start_time': {'type': 'string'},
                'end_time': {'type': 'string'},
                'location': {'type': 'string'},
                'max_attendees': {'type': 'integer'},
                'current_attendees': {'type': 'integer'},
                'status': {'type': 'string'},
                'tags': {'type': 'array', 'items': {'type': 'string'}},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['title', 'event_type', 'event_date', 'status']
        }

        success = self.create_collection('staging_events', schema)
        if success:
            self.create_index('staging_events', 'event_date_idx', ['event_date'])
            self.create_index('staging_events', 'status_idx', ['status'])
            self.create_index('staging_events', 'access_type_idx', ['access_type'])

        return success

    def setup_rsvps_collection(self):
        """Create staging_rsvps collection."""
        schema = {
            'type': 'object',
            'properties': {
                'event_id': {'type': 'string'},
                'user_email': {'type': 'string', 'format': 'email'},
                'status': {'type': 'string', 'enum': ['confirmed', 'cancelled', 'waitlist']},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['event_id', 'user_email', 'status']
        }

        success = self.create_collection('staging_rsvps', schema)
        if success:
            self.create_index('staging_rsvps', 'event_idx', ['event_id'])
            self.create_index('staging_rsvps', 'user_idx', ['user_email'])

        return success

    def setup_applications_collection(self):
        """Create staging_applications collection."""
        schema = {
            'type': 'object',
            'properties': {
                'applicant_email': {'type': 'string', 'format': 'email'},
                'applicant_name': {'type': 'string'},
                'requested_tier': {'type': 'string', 'enum': ['basic', 'standard', 'premium']},
                'status': {'type': 'string', 'enum': ['pending', 'approved', 'rejected', 'under_review']},
                'application_text': {'type': 'string'},
                'linkedin_profile': {'type': 'string'},
                'company': {'type': 'string'},
                'job_title': {'type': 'string'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['applicant_email', 'applicant_name', 'requested_tier', 'status']
        }

        success = self.create_collection('staging_applications', schema)
        if success:
            self.create_index('staging_applications', 'email_idx', ['applicant_email'])
            self.create_index('staging_applications', 'status_idx', ['status'])

        return success

    def setup_subscriptions_collection(self):
        """Create staging_subscriptions collection."""
        schema = {
            'type': 'object',
            'properties': {
                'user_email': {'type': 'string', 'format': 'email'},
                'stripe_subscription_id': {'type': 'string'},
                'stripe_customer_id': {'type': 'string'},
                'tier': {'type': 'string', 'enum': ['basic', 'standard', 'premium']},
                'status': {'type': 'string'},
                'current_period_start': {'type': 'string', 'format': 'date-time'},
                'current_period_end': {'type': 'string', 'format': 'date-time'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['user_email', 'stripe_subscription_id', 'tier', 'status']
        }

        success = self.create_collection('staging_subscriptions', schema)
        if success:
            self.create_index('staging_subscriptions', 'user_idx', ['user_email'])
            self.create_index('staging_subscriptions', 'stripe_sub_idx', ['stripe_subscription_id'])

        return success

    def setup_blog_posts_collection(self):
        """Create staging_blog_posts collection."""
        schema = {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'slug': {'type': 'string'},
                'content': {'type': 'string'},
                'excerpt': {'type': 'string'},
                'category': {'type': 'string'},
                'author': {'type': 'string'},
                'author_email': {'type': 'string', 'format': 'email'},
                'published_at': {'type': 'string', 'format': 'date-time'},
                'status': {'type': 'string', 'enum': ['draft', 'published', 'archived']},
                'tags': {'type': 'array', 'items': {'type': 'string'}},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['title', 'slug', 'content', 'status']
        }

        success = self.create_collection('staging_blog_posts', schema)
        if success:
            self.create_index('staging_blog_posts', 'slug_idx', ['slug'])
            self.create_index('staging_blog_posts', 'status_idx', ['status'])

        return success

    def setup_newsletter_collection(self):
        """Create staging_newsletter_subscribers collection."""
        schema = {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'status': {'type': 'string', 'enum': ['subscribed', 'unsubscribed', 'bounced']},
                'beehiiv_subscriber_id': {'type': 'string'},
                'subscribed_at': {'type': 'string', 'format': 'date-time'},
                'unsubscribed_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['email', 'status']
        }

        success = self.create_collection('staging_newsletter_subscribers', schema)
        if success:
            self.create_index('staging_newsletter_subscribers', 'email_idx', ['email'])

        return success

    def setup_training_sessions_collection(self):
        """Create staging_training_sessions collection."""
        schema = {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'instructor': {'type': 'string'},
                'scheduled_at': {'type': 'string', 'format': 'date-time'},
                'duration_minutes': {'type': 'integer'},
                'cloudflare_room_id': {'type': 'string'},
                'recording_url': {'type': 'string'},
                'status': {'type': 'string'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['title', 'instructor', 'scheduled_at', 'status']
        }

        success = self.create_collection('staging_training_sessions', schema)
        if success:
            self.create_index('staging_training_sessions', 'scheduled_idx', ['scheduled_at'])
            self.create_index('staging_training_sessions', 'status_idx', ['status'])

        return success

    def setup_all_collections(self):
        """Set up all staging collections."""
        print("=" * 80)
        print("WWMAA Staging ZeroDB Setup")
        print("=" * 80)
        print(f"Environment: staging")
        print(f"ZeroDB URL: {self.base_url}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print("=" * 80)

        collections = [
            ("User Profiles", self.setup_profiles_collection),
            ("Events", self.setup_events_collection),
            ("RSVPs", self.setup_rsvps_collection),
            ("Applications", self.setup_applications_collection),
            ("Subscriptions", self.setup_subscriptions_collection),
            ("Blog Posts", self.setup_blog_posts_collection),
            ("Newsletter Subscribers", self.setup_newsletter_collection),
            ("Training Sessions", self.setup_training_sessions_collection),
        ]

        results = []
        for name, setup_func in collections:
            print(f"\n[{len(results) + 1}/{len(collections)}] Setting up {name}...")
            success = setup_func()
            results.append((name, success))

        # Summary
        print("\n" + "=" * 80)
        print("Setup Summary")
        print("=" * 80)

        successful = sum(1 for _, success in results if success)
        failed = len(results) - successful

        for name, success in results:
            status = "✓" if success else "✗"
            print(f"  {status} {name}")

        print("\n" + "=" * 80)
        print(f"Total: {len(results)} collections")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print("=" * 80)

        if failed > 0:
            print("\n⚠ Some collections failed to create. Check logs above.")
            print("You may need to create them manually in the ZeroDB dashboard.")
            sys.exit(1)
        else:
            print("\n✓ All staging collections created successfully!")
            print("\nNext steps:")
            print("  1. Verify collections in ZeroDB dashboard")
            print("  2. Run seed data script: python scripts/seed-staging-data.py")
            print("  3. Test application with staging database")


def main():
    """Main entry point."""
    setup = ZeroDBStagingSetup()
    setup.setup_all_collections()


if __name__ == '__main__':
    main()
