#!/usr/bin/env python3
"""
ZeroDB Seed Data Script for WWMAA Development

This script generates realistic test data for development using the Faker library.
It populates all ZeroDB collections with comprehensive seed data.

Usage:
    python backend/scripts/seed_data.py
    python backend/scripts/seed_data.py --clear  # Clear existing data first
    python backend/scripts/seed_data.py --count 50  # Generate 50 users instead of 20
    python backend/scripts/seed_data.py --collections users,events  # Seed specific collections

Collections seeded:
    - users (20+ with different roles)
    - profiles (linked to users)
    - applications (15+ in various states)
    - approvals (linked to applications)
    - subscriptions (for members)
    - payments (transaction history)
    - events (10+ public, members-only, invite-only)
    - rsvps (event registrations)
    - training_sessions (5+ with VOD references)
    - session_attendance (attendance records)
    - search_queries (20+ logged queries)
    - content_index (searchable content with embeddings)
    - media_assets (file metadata)
    - audit_logs (system activity)
"""

import argparse
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from faker import Faker

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import (
    Application,
    ApplicationStatus,
    Approval,
    ApprovalStatus,
    AttendanceStatus,
    AuditAction,
    AuditLog,
    ContentIndex,
    Event,
    EventType,
    EventVisibility,
    MediaAsset,
    MediaType,
    Payment,
    PaymentStatus,
    Profile,
    RSVP,
    RSVPStatus,
    SearchQuery,
    SessionAttendance,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    TrainingSession,
    User,
    UserRole,
)
from services.zerodb_service import ZeroDBClient, ZeroDBError
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """
    Check that script is only run in development or staging environments

    Raises:
        RuntimeError: If run in production environment
    """
    if settings.is_production:
        raise RuntimeError(
            "SAFETY CHECK: Cannot run seed data script in PRODUCTION environment!\n"
            "This script should only be run in development or staging.\n"
            f"Current environment: {settings.PYTHON_ENV}"
        )
    logger.info(f"Environment check passed: {settings.PYTHON_ENV}")


def clear_all_data(client: ZeroDBClient, collections: Optional[List[str]] = None):
    """
    Clear all data from ZeroDB collections - USE WITH CAUTION!

    This function is designed for testing and development purposes.
    It will delete all documents from the specified collections.

    Args:
        client: ZeroDBClient instance
        collections: List of collection names to clear (default: all)

    Raises:
        RuntimeError: If attempted in production environment
    """
    # Safety check
    if settings.is_production:
        raise RuntimeError(
            "SAFETY CHECK: Cannot clear data in PRODUCTION environment!"
        )

    default_collections = [
        'users', 'profiles', 'applications', 'approvals',
        'subscriptions', 'payments', 'events', 'rsvps',
        'training_sessions', 'session_attendance',
        'search_queries', 'content_index',
        'media_assets', 'audit_logs'
    ]

    collections_to_clear = collections or default_collections

    logger.warning(f"Clearing {len(collections_to_clear)} collections...")

    for collection in collections_to_clear:
        try:
            logger.info(f"Querying all documents in '{collection}'...")
            result = client.query_documents(
                collection=collection,
                filters={},
                limit=1000  # Adjust if you have more records
            )

            docs = result.get('documents', [])
            if not docs:
                logger.info(f"Collection '{collection}' is already empty")
                continue

            logger.info(f"Deleting {len(docs)} documents from '{collection}'...")
            deleted_count = 0

            for doc in docs:
                try:
                    doc_id = doc.get('id')
                    if doc_id:
                        client.delete_document(collection, doc_id)
                        deleted_count += 1
                except ZeroDBError as e:
                    logger.warning(f"Failed to delete document {doc_id}: {e}")

            logger.info(f"Deleted {deleted_count} documents from '{collection}'")

        except ZeroDBError as e:
            logger.warning(f"Failed to clear collection '{collection}': {e}")

    logger.info("Data clearing complete!")

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducible data
random.seed(42)


class ProgressTracker:
    """Simple progress tracker for CLI output"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description

    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        bar_length = 40
        filled = int(bar_length * self.current / self.total) if self.total > 0 else 0
        bar = '=' * filled + '-' * (bar_length - filled)
        print(f'\r{self.description}: [{bar}] {self.current}/{self.total} ({percentage:.1f}%)', end='', flush=True)

    def complete(self):
        """Mark as complete"""
        print()  # New line


class SeedDataGenerator:
    """Generates seed data for all ZeroDB collections"""

    def __init__(self, zerodb_client: ZeroDBClient):
        self.client = zerodb_client
        self.collections = {
            'users': [],
            'profiles': [],
            'applications': [],
            'approvals': [],
            'subscriptions': [],
            'payments': [],
            'events': [],
            'rsvps': [],
            'training_sessions': [],
            'session_attendance': [],
            'search_queries': [],
            'content_index': [],
            'media_assets': [],
            'audit_logs': [],
        }

    def generate_users(self, count: int = 65) -> List[UUID]:
        """
        Generate users with different roles
        Default distribution: 5 admin, 10 board members, 20 members, 30 public

        Args:
            count: Number of users to generate (default: 65)

        Returns:
            List of user IDs
        """
        logger.info(f"Generating {count} users...")
        progress = ProgressTracker(count, "Users")

        user_ids = []

        # Define role distribution based on requirements
        # US-003: 5 admin, 10 board members, 20 members, 30 public users
        if count == 65:
            # Use exact distribution from requirements
            role_distribution = [
                (UserRole.ADMIN, 5),
                (UserRole.BOARD_MEMBER, 10),
                (UserRole.MEMBER, 20),
                (UserRole.PUBLIC, 30),
            ]
        else:
            # Use percentage-based distribution for custom counts
            role_distribution = [
                (UserRole.PUBLIC, int(count * 0.46)),  # ~46% public
                (UserRole.MEMBER, int(count * 0.31)),  # ~31% members
                (UserRole.BOARD_MEMBER, int(count * 0.15)),  # ~15% board members
                (UserRole.ADMIN, max(1, int(count * 0.08))),  # ~8% admins (min 1)
            ]

        users_to_create = []
        for role, role_count in role_distribution:
            for _ in range(role_count):
                user_data = {
                    'id': str(uuid4()),
                    'email': fake.unique.email(),
                    'password_hash': fake.sha256(),
                    'role': role,
                    'is_active': random.choice([True] * 9 + [False]),  # 90% active
                    'is_verified': random.choice([True] * 8 + [False] * 2),  # 80% verified
                    'last_login': fake.date_time_between(start_date='-30d', end_date='now') if random.random() > 0.2 else None,
                    'created_at': fake.date_time_between(start_date='-2y', end_date='-1d').isoformat(),
                    'updated_at': fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
                }
                users_to_create.append(user_data)
                user_ids.append(UUID(user_data['id']))

        # Create users in batches
        for user_data in users_to_create:
            try:
                self.client.create_document('users', user_data, document_id=user_data['id'])
                self.collections['users'].append(user_data)
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create user {user_data['email']}: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['users'])} users")
        return user_ids

    def generate_profiles(self, user_ids: List[UUID]) -> List[UUID]:
        """
        Generate user profiles linked to users

        Args:
            user_ids: List of user IDs to create profiles for

        Returns:
            List of profile IDs
        """
        logger.info(f"Generating {len(user_ids)} profiles...")
        progress = ProgressTracker(len(user_ids), "Profiles")

        profile_ids = []
        disciplines = ['Karate', 'Taekwondo', 'Judo', 'Brazilian Jiu-Jitsu', 'Muay Thai',
                       'Kung Fu', 'Aikido', 'Krav Maga', 'Boxing', 'Wrestling']

        for user_id in user_ids:
            profile_data = {
                'id': str(uuid4()),
                'user_id': str(user_id),
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'display_name': fake.user_name() if random.random() > 0.5 else None,
                'bio': fake.text(max_nb_chars=500) if random.random() > 0.3 else None,
                'avatar_url': fake.image_url() if random.random() > 0.6 else None,
                'phone': fake.phone_number() if random.random() > 0.4 else None,
                'website': fake.url() if random.random() > 0.7 else None,
                'city': fake.city(),
                'state': fake.state_abbr(),
                'country': 'USA',
                'disciplines': random.sample(disciplines, k=random.randint(1, 3)),
                'ranks': {discipline: f"{random.choice(['White', 'Yellow', 'Orange', 'Green', 'Blue', 'Purple', 'Brown', 'Black'])} Belt"
                          for discipline in random.sample(disciplines, k=random.randint(1, 2))},
                'instructor_certifications': [f"{discipline} Instructor" for discipline in random.sample(disciplines, k=random.randint(0, 2))],
                'schools_affiliated': [fake.company() for _ in range(random.randint(0, 2))],
                'newsletter_subscribed': random.choice([True, False]),
                'public_profile': random.choice([True] * 7 + [False] * 3),  # 70% public
                'event_notifications': random.choice([True] * 8 + [False] * 2),  # 80% enabled
                'social_links': {
                    'twitter': f"@{fake.user_name()}" if random.random() > 0.5 else None,
                    'instagram': f"@{fake.user_name()}" if random.random() > 0.6 else None,
                    'facebook': fake.url() if random.random() > 0.7 else None,
                },
                'member_since': fake.date_time_between(start_date='-5y', end_date='-1d').isoformat(),
                'last_activity': fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
                'created_at': fake.date_time_between(start_date='-2y', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('profiles', profile_data, document_id=profile_data['id'])
                self.collections['profiles'].append(profile_data)
                profile_ids.append(UUID(profile_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create profile for user {user_id}: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['profiles'])} profiles")
        return profile_ids

    def generate_applications(self, user_ids: List[UUID], count: int = 15) -> List[UUID]:
        """
        Generate membership applications in various states

        Args:
            user_ids: List of user IDs
            count: Number of applications to generate

        Returns:
            List of application IDs
        """
        logger.info(f"Generating {count} applications...")
        progress = ProgressTracker(count, "Applications")

        application_ids = []
        statuses = [ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED,
                    ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED,
                    ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]
        disciplines = ['Karate', 'Taekwondo', 'Judo', 'Brazilian Jiu-Jitsu', 'Muay Thai']

        for _ in range(count):
            user_id = random.choice(user_ids)
            status = random.choice(statuses)

            application_data = {
                'id': str(uuid4()),
                'user_id': str(user_id),
                'status': status,
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': fake.email(),
                'phone': fake.phone_number() if random.random() > 0.3 else None,
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=70).isoformat() if random.random() > 0.2 else None,
                'address_line1': fake.street_address() if random.random() > 0.2 else None,
                'address_line2': fake.secondary_address() if random.random() > 0.8 else None,
                'city': fake.city() if random.random() > 0.2 else None,
                'state': fake.state_abbr() if random.random() > 0.2 else None,
                'zip_code': fake.zipcode() if random.random() > 0.2 else None,
                'country': 'USA',
                'disciplines': random.sample(disciplines, k=random.randint(1, 3)),
                'experience_years': random.randint(0, 30) if random.random() > 0.2 else None,
                'current_rank': f"{random.choice(['White', 'Yellow', 'Green', 'Blue', 'Brown', 'Black'])} Belt" if random.random() > 0.3 else None,
                'school_affiliation': fake.company() if random.random() > 0.5 else None,
                'instructor_name': fake.name() if random.random() > 0.4 else None,
                'motivation': fake.text(max_nb_chars=500) if random.random() > 0.3 else None,
                'goals': fake.text(max_nb_chars=500) if random.random() > 0.3 else None,
                'referral_source': random.choice(['Google', 'Facebook', 'Friend', 'Event', 'Other']) if random.random() > 0.3 else None,
                'submitted_at': fake.date_time_between(start_date='-90d', end_date='now').isoformat() if status != ApplicationStatus.DRAFT else None,
                'reviewed_at': fake.date_time_between(start_date='-60d', end_date='now').isoformat() if status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED] else None,
                'reviewed_by': str(random.choice(user_ids)) if status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED] else None,
                'decision_notes': fake.sentence() if status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED] else None,
                'subscription_tier': random.choice([SubscriptionTier.FREE, SubscriptionTier.BASIC, SubscriptionTier.PREMIUM]),
                'certificate_url': fake.url() if status == ApplicationStatus.APPROVED else None,
                'created_at': fake.date_time_between(start_date='-120d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('applications', application_data, document_id=application_data['id'])
                self.collections['applications'].append(application_data)
                application_ids.append(UUID(application_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create application: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['applications'])} applications")
        return application_ids

    def generate_approvals(self, application_ids: List[UUID], user_ids: List[UUID]) -> List[UUID]:
        """
        Generate approvals for applications

        Args:
            application_ids: List of application IDs
            user_ids: List of user IDs (board members)

        Returns:
            List of approval IDs
        """
        # Only create approvals for a subset of applications
        apps_to_approve = random.sample(application_ids, k=min(10, len(application_ids)))
        logger.info(f"Generating {len(apps_to_approve)} approvals...")
        progress = ProgressTracker(len(apps_to_approve), "Approvals")

        approval_ids = []

        for app_id in apps_to_approve:
            approval_data = {
                'id': str(uuid4()),
                'application_id': str(app_id),
                'approver_id': str(random.choice(user_ids)),
                'status': random.choice([ApprovalStatus.PENDING, ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]),
                'notes': fake.sentence() if random.random() > 0.5 else None,
                'approved_at': fake.date_time_between(start_date='-60d', end_date='now').isoformat() if random.random() > 0.3 else None,
                'conditions': [fake.sentence() for _ in range(random.randint(0, 2))],
                'priority': random.randint(0, 10),
                'created_at': fake.date_time_between(start_date='-90d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('approvals', approval_data, document_id=approval_data['id'])
                self.collections['approvals'].append(approval_data)
                approval_ids.append(UUID(approval_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create approval: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['approvals'])} approvals")
        return approval_ids

    def generate_subscriptions(self, user_ids: List[UUID], count: int = 15) -> List[UUID]:
        """
        Generate subscriptions for members

        Args:
            user_ids: List of user IDs
            count: Number of subscriptions to generate

        Returns:
            List of subscription IDs
        """
        logger.info(f"Generating {count} subscriptions...")
        progress = ProgressTracker(count, "Subscriptions")

        subscription_ids = []
        tiers_pricing = {
            SubscriptionTier.FREE: 0.0,
            SubscriptionTier.BASIC: 29.99,
            SubscriptionTier.PREMIUM: 99.99,
            SubscriptionTier.LIFETIME: 999.99,
        }

        for _ in range(count):
            tier = random.choice([SubscriptionTier.FREE, SubscriptionTier.BASIC,
                                  SubscriptionTier.PREMIUM, SubscriptionTier.LIFETIME])
            start_date = fake.date_time_between(start_date='-2y', end_date='now')

            subscription_data = {
                'id': str(uuid4()),
                'user_id': str(random.choice(user_ids)),
                'tier': tier,
                'status': random.choice([SubscriptionStatus.ACTIVE] * 7 + [SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED, SubscriptionStatus.PAST_DUE]),
                'stripe_subscription_id': f"sub_{fake.uuid4()}" if tier != SubscriptionTier.FREE else None,
                'stripe_customer_id': f"cus_{fake.uuid4()}" if tier != SubscriptionTier.FREE else None,
                'start_date': start_date.isoformat(),
                'end_date': (start_date + timedelta(days=365)).isoformat() if tier != SubscriptionTier.LIFETIME else None,
                'trial_end_date': (start_date + timedelta(days=30)).isoformat() if random.random() > 0.7 else None,
                'canceled_at': fake.date_time_between(start_date=start_date, end_date='now').isoformat() if random.random() > 0.8 else None,
                'amount': tiers_pricing[tier],
                'currency': 'USD',
                'interval': 'month' if tier in [SubscriptionTier.BASIC, SubscriptionTier.PREMIUM] else 'lifetime',
                'features': {
                    'event_access': tier in [SubscriptionTier.BASIC, SubscriptionTier.PREMIUM, SubscriptionTier.LIFETIME],
                    'vod_access': tier in [SubscriptionTier.PREMIUM, SubscriptionTier.LIFETIME],
                    'discount': tier == SubscriptionTier.PREMIUM,
                },
                'metadata': {'source': random.choice(['web', 'mobile', 'event'])},
                'created_at': start_date.isoformat(),
                'updated_at': fake.date_time_between(start_date=start_date, end_date='now').isoformat(),
            }

            try:
                self.client.create_document('subscriptions', subscription_data, document_id=subscription_data['id'])
                self.collections['subscriptions'].append(subscription_data)
                subscription_ids.append(UUID(subscription_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create subscription: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['subscriptions'])} subscriptions")
        return subscription_ids

    def generate_payments(self, user_ids: List[UUID], subscription_ids: List[UUID], count: int = 20) -> List[UUID]:
        """
        Generate payment transactions

        Args:
            user_ids: List of user IDs
            subscription_ids: List of subscription IDs
            count: Number of payments to generate

        Returns:
            List of payment IDs
        """
        logger.info(f"Generating {count} payments...")
        progress = ProgressTracker(count, "Payments")

        payment_ids = []
        amounts = [29.99, 99.99, 999.99, 19.99, 49.99]

        for _ in range(count):
            amount = random.choice(amounts)
            status = random.choice([PaymentStatus.SUCCEEDED] * 8 + [PaymentStatus.FAILED, PaymentStatus.REFUNDED])

            payment_data = {
                'id': str(uuid4()),
                'user_id': str(random.choice(user_ids)),
                'subscription_id': str(random.choice(subscription_ids)) if random.random() > 0.3 else None,
                'amount': amount,
                'currency': 'USD',
                'status': status,
                'stripe_payment_intent_id': f"pi_{fake.uuid4()}",
                'stripe_charge_id': f"ch_{fake.uuid4()}" if status == PaymentStatus.SUCCEEDED else None,
                'payment_method': random.choice(['card', 'bank_account', 'paypal']),
                'description': fake.sentence(),
                'receipt_url': fake.url() if status == PaymentStatus.SUCCEEDED else None,
                'refunded_amount': amount if status == PaymentStatus.REFUNDED else 0.0,
                'refunded_at': fake.date_time_between(start_date='-60d', end_date='now').isoformat() if status == PaymentStatus.REFUNDED else None,
                'refund_reason': fake.sentence() if status == PaymentStatus.REFUNDED else None,
                'metadata': {'invoice_id': fake.uuid4()},
                'processed_at': fake.date_time_between(start_date='-180d', end_date='now').isoformat(),
                'created_at': fake.date_time_between(start_date='-180d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('payments', payment_data, document_id=payment_data['id'])
                self.collections['payments'].append(payment_data)
                payment_ids.append(UUID(payment_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create payment: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['payments'])} payments")
        return payment_ids

    def generate_events(self, user_ids: List[UUID], count: int = 10) -> List[UUID]:
        """
        Generate events with various visibility levels

        Args:
            user_ids: List of user IDs (organizers)
            count: Number of events to generate

        Returns:
            List of event IDs
        """
        logger.info(f"Generating {count} events...")
        progress = ProgressTracker(count, "Events")

        event_ids = []
        event_types = [EventType.TRAINING, EventType.SEMINAR, EventType.COMPETITION, EventType.SOCIAL, EventType.MEETING]
        visibilities = [EventVisibility.PUBLIC, EventVisibility.MEMBERS_ONLY, EventVisibility.INVITE_ONLY]

        for _ in range(count):
            start_datetime = fake.date_time_between(start_date='-60d', end_date='+90d')
            duration_hours = random.randint(1, 4)

            event_data = {
                'id': str(uuid4()),
                'title': f"{random.choice(['Advanced', 'Beginner', 'Intermediate', 'Special'])} {random.choice(['Karate', 'Taekwondo', 'Judo', 'BJJ'])} {random.choice(['Training', 'Workshop', 'Seminar', 'Competition'])}",
                'description': fake.text(max_nb_chars=500),
                'event_type': random.choice(event_types),
                'visibility': random.choice(visibilities),
                'start_datetime': start_datetime.isoformat(),
                'end_datetime': (start_datetime + timedelta(hours=duration_hours)).isoformat(),
                'timezone': 'America/Los_Angeles',
                'is_all_day': False,
                'location_name': fake.company() if random.random() > 0.3 else None,
                'address': fake.address() if random.random() > 0.3 else None,
                'city': fake.city() if random.random() > 0.3 else None,
                'state': fake.state_abbr() if random.random() > 0.3 else None,
                'virtual_url': fake.url() if random.random() > 0.5 else None,
                'is_virtual': random.choice([True, False]),
                'max_attendees': random.choice([None, 20, 30, 50, 100]),
                'current_attendees': random.randint(0, 25),
                'waitlist_enabled': random.choice([True, False]),
                'organizer_id': str(random.choice(user_ids)),
                'instructors': [str(random.choice(user_ids)) for _ in range(random.randint(1, 3))],
                'featured_image_url': fake.image_url() if random.random() > 0.5 else None,
                'gallery_urls': [fake.image_url() for _ in range(random.randint(0, 3))],
                'registration_required': random.choice([True] * 7 + [False] * 3),
                'registration_deadline': (start_datetime - timedelta(days=7)).isoformat() if random.random() > 0.5 else None,
                'registration_fee': random.choice([0.0, 25.0, 50.0, 100.0]) if random.random() > 0.5 else None,
                'is_published': random.choice([True] * 8 + [False] * 2),
                'is_canceled': random.choice([True] + [False] * 19),  # 5% canceled
                'canceled_reason': fake.sentence() if random.random() > 0.95 else None,
                'tags': random.sample(['karate', 'bjj', 'seminar', 'competition', 'beginner', 'advanced'], k=random.randint(1, 3)),
                'metadata': {'capacity': random.randint(20, 100)},
                'created_at': fake.date_time_between(start_date='-90d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('events', event_data, document_id=event_data['id'])
                self.collections['events'].append(event_data)
                event_ids.append(UUID(event_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create event: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['events'])} events")
        return event_ids

    def generate_rsvps(self, event_ids: List[UUID], user_ids: List[UUID], count: int = 30) -> List[UUID]:
        """
        Generate event RSVPs

        Args:
            event_ids: List of event IDs
            user_ids: List of user IDs
            count: Number of RSVPs to generate

        Returns:
            List of RSVP IDs
        """
        logger.info(f"Generating {count} RSVPs...")
        progress = ProgressTracker(count, "RSVPs")

        rsvp_ids = []

        for _ in range(count):
            rsvp_data = {
                'id': str(uuid4()),
                'event_id': str(random.choice(event_ids)),
                'user_id': str(random.choice(user_ids)),
                'status': random.choice([RSVPStatus.CONFIRMED] * 7 + [RSVPStatus.DECLINED, RSVPStatus.WAITLIST, RSVPStatus.CANCELED]),
                'guests_count': random.randint(0, 3),
                'notes': fake.sentence() if random.random() > 0.7 else None,
                'responded_at': fake.date_time_between(start_date='-60d', end_date='now').isoformat(),
                'checked_in_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat() if random.random() > 0.5 else None,
                'reminder_sent': random.choice([True, False]),
                'confirmation_sent': random.choice([True] * 8 + [False] * 2),
                'created_at': fake.date_time_between(start_date='-90d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('rsvps', rsvp_data, document_id=rsvp_data['id'])
                self.collections['rsvps'].append(rsvp_data)
                rsvp_ids.append(UUID(rsvp_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create RSVP: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['rsvps'])} RSVPs")
        return rsvp_ids

    def generate_training_sessions(self, event_ids: List[UUID], user_ids: List[UUID], count: int = 5) -> List[UUID]:
        """
        Generate training sessions with VOD references

        Args:
            event_ids: List of event IDs
            user_ids: List of user IDs (instructors)
            count: Number of training sessions to generate

        Returns:
            List of training session IDs
        """
        logger.info(f"Generating {count} training sessions...")
        progress = ProgressTracker(count, "Training Sessions")

        session_ids = []
        disciplines = ['Karate', 'Taekwondo', 'Judo', 'Brazilian Jiu-Jitsu', 'Muay Thai']
        skill_levels = ['beginner', 'intermediate', 'advanced']

        for _ in range(count):
            session_date = fake.date_time_between(start_date='-90d', end_date='now')

            session_data = {
                'id': str(uuid4()),
                'event_id': str(random.choice(event_ids)) if random.random() > 0.5 else None,
                'title': f"{random.choice(['Fundamentals', 'Advanced Techniques', 'Sparring', 'Forms'])} - {random.choice(disciplines)}",
                'description': fake.text(max_nb_chars=500),
                'instructor_id': str(random.choice(user_ids)),
                'assistant_instructors': [str(random.choice(user_ids)) for _ in range(random.randint(0, 2))],
                'session_date': session_date.isoformat(),
                'duration_minutes': random.choice([60, 90, 120, 180]),
                'discipline': random.choice(disciplines),
                'topics': random.sample(['kata', 'kumite', 'bunkai', 'kihon', 'randori', 'drills'], k=random.randint(2, 4)),
                'skill_level': random.choice(skill_levels),
                'cloudflare_stream_id': fake.uuid4() if random.random() > 0.3 else None,
                'video_url': fake.url() if random.random() > 0.3 else None,
                'video_duration_seconds': random.randint(3600, 7200) if random.random() > 0.3 else None,
                'recording_status': random.choice(['recorded', 'processing', 'not_recorded', 'available']),
                'is_public': random.choice([True] + [False] * 4),  # 20% public
                'members_only': True,
                'attendance_count': random.randint(5, 30),
                'tags': random.sample(['technique', 'sparring', 'fundamentals', 'advanced'], k=random.randint(1, 3)),
                'created_at': session_date.isoformat(),
                'updated_at': fake.date_time_between(start_date=session_date, end_date='now').isoformat(),
            }

            try:
                self.client.create_document('training_sessions', session_data, document_id=session_data['id'])
                self.collections['training_sessions'].append(session_data)
                session_ids.append(UUID(session_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create training session: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['training_sessions'])} training sessions")
        return session_ids

    def generate_session_attendance(self, session_ids: List[UUID], user_ids: List[UUID], count: int = 25) -> List[UUID]:
        """
        Generate session attendance records

        Args:
            session_ids: List of training session IDs
            user_ids: List of user IDs
            count: Number of attendance records to generate

        Returns:
            List of attendance IDs
        """
        logger.info(f"Generating {count} attendance records...")
        progress = ProgressTracker(count, "Attendance Records")

        attendance_ids = []

        for _ in range(count):
            attendance_data = {
                'id': str(uuid4()),
                'training_session_id': str(random.choice(session_ids)),
                'user_id': str(random.choice(user_ids)),
                'status': random.choice([AttendanceStatus.PRESENT] * 8 + [AttendanceStatus.ABSENT, AttendanceStatus.LATE]),
                'checked_in_at': fake.date_time_between(start_date='-90d', end_date='now').isoformat() if random.random() > 0.2 else None,
                'checked_out_at': fake.date_time_between(start_date='-90d', end_date='now').isoformat() if random.random() > 0.3 else None,
                'notes': fake.sentence() if random.random() > 0.8 else None,
                'participation_score': random.randint(70, 100) if random.random() > 0.5 else None,
                'video_watch_percentage': random.uniform(50.0, 100.0) if random.random() > 0.4 else None,
                'last_watched_position': random.randint(0, 7200) if random.random() > 0.4 else None,
                'created_at': fake.date_time_between(start_date='-90d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('session_attendance', attendance_data, document_id=attendance_data['id'])
                self.collections['session_attendance'].append(attendance_data)
                attendance_ids.append(UUID(attendance_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create attendance record: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['session_attendance'])} attendance records")
        return attendance_ids

    def generate_search_queries(self, user_ids: List[UUID], count: int = 20) -> List[UUID]:
        """
        Generate search query logs

        Args:
            user_ids: List of user IDs
            count: Number of search queries to generate

        Returns:
            List of search query IDs
        """
        logger.info(f"Generating {count} search queries...")
        progress = ProgressTracker(count, "Search Queries")

        query_ids = []
        search_terms = [
            'karate training near me', 'bjj techniques', 'upcoming tournaments',
            'how to tie belt', 'black belt requirements', 'self defense classes',
            'kids martial arts', 'mma training', 'tai chi benefits', 'kickboxing workouts'
        ]

        for _ in range(count):
            query_data = {
                'id': str(uuid4()),
                'user_id': str(random.choice(user_ids)) if random.random() > 0.3 else None,  # 30% anonymous
                'query_text': random.choice(search_terms),
                'embedding_vector': [random.uniform(-1, 1) for _ in range(1536)] if random.random() > 0.2 else None,
                'intent': random.choice(['informational', 'navigational', 'transactional']) if random.random() > 0.4 else None,
                'results_count': random.randint(0, 50),
                'top_result_ids': [str(uuid4()) for _ in range(random.randint(0, 5))],
                'response_time_ms': random.randint(50, 500),
                'clicked_result_ids': [str(uuid4()) for _ in range(random.randint(0, 3))],
                'click_through_rate': random.uniform(0.1, 0.8) if random.random() > 0.3 else None,
                'session_id': fake.uuid4(),
                'user_agent': fake.user_agent(),
                'ip_address': fake.ipv4(),
                'created_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                'updated_at': fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('search_queries', query_data, document_id=query_data['id'])
                self.collections['search_queries'].append(query_data)
                query_ids.append(UUID(query_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create search query: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['search_queries'])} search queries")
        return query_ids

    def generate_content_index(self, user_ids: List[UUID], count: int = 15) -> List[UUID]:
        """
        Generate searchable content with embeddings

        Args:
            user_ids: List of user IDs
            count: Number of content entries to generate

        Returns:
            List of content index IDs
        """
        logger.info(f"Generating {count} content index entries...")
        progress = ProgressTracker(count, "Content Index")

        content_ids = []
        content_types = ['event', 'article', 'profile', 'training', 'news']
        categories = ['training', 'events', 'news', 'community', 'education']

        for _ in range(count):
            content_data = {
                'id': str(uuid4()),
                'content_type': random.choice(content_types),
                'content_id': str(uuid4()),
                'title': fake.sentence(),
                'body': fake.text(max_nb_chars=2000),
                'summary': fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
                'embedding_vector': [random.uniform(-1, 1) for _ in range(1536)],
                'embedding_model': 'text-embedding-ada-002',
                'author_id': str(random.choice(user_ids)) if random.random() > 0.3 else None,
                'tags': random.sample(['martial-arts', 'training', 'technique', 'event', 'community'], k=random.randint(1, 3)),
                'category': random.choice(categories) if random.random() > 0.3 else None,
                'visibility': random.choice(['public', 'members', 'private']),
                'keywords': random.sample(['karate', 'judo', 'bjj', 'training', 'seminar', 'competition'], k=random.randint(2, 4)),
                'search_weight': random.uniform(0.5, 5.0),
                'published_at': fake.date_time_between(start_date='-180d', end_date='now').isoformat() if random.random() > 0.2 else None,
                'is_active': random.choice([True] * 9 + [False]),
                'created_at': fake.date_time_between(start_date='-180d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('content_index', content_data, document_id=content_data['id'])
                self.collections['content_index'].append(content_data)
                content_ids.append(UUID(content_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create content index: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['content_index'])} content index entries")
        return content_ids

    def generate_media_assets(self, user_ids: List[UUID], count: int = 10) -> List[UUID]:
        """
        Generate media asset metadata

        Args:
            user_ids: List of user IDs
            count: Number of media assets to generate

        Returns:
            List of media asset IDs
        """
        logger.info(f"Generating {count} media assets...")
        progress = ProgressTracker(count, "Media Assets")

        asset_ids = []

        for _ in range(count):
            media_type = random.choice([MediaType.IMAGE, MediaType.VIDEO, MediaType.DOCUMENT, MediaType.CERTIFICATE])

            asset_data = {
                'id': str(uuid4()),
                'media_type': media_type,
                'filename': fake.file_name(),
                'file_size_bytes': random.randint(1024, 10485760),  # 1KB to 10MB
                'mime_type': random.choice(['image/jpeg', 'image/png', 'video/mp4', 'application/pdf']),
                'storage_provider': random.choice(['zerodb', 'cloudflare']),
                'object_id': fake.uuid4(),
                'url': fake.url(),
                'width': random.randint(640, 1920) if media_type == MediaType.IMAGE else None,
                'height': random.randint(480, 1080) if media_type == MediaType.IMAGE else None,
                'duration_seconds': random.randint(60, 3600) if media_type == MediaType.VIDEO else None,
                'cloudflare_stream_id': fake.uuid4() if media_type == MediaType.VIDEO else None,
                'uploaded_by': str(random.choice(user_ids)),
                'entity_type': random.choice(['event', 'profile', 'training']) if random.random() > 0.3 else None,
                'entity_id': str(uuid4()) if random.random() > 0.3 else None,
                'alt_text': fake.sentence() if random.random() > 0.5 else None,
                'caption': fake.sentence() if random.random() > 0.6 else None,
                'tags': random.sample(['event', 'training', 'certificate', 'profile'], k=random.randint(1, 2)),
                'is_public': random.choice([True, False]),
                'access_roles': random.sample([UserRole.PUBLIC, UserRole.MEMBER, UserRole.INSTRUCTOR], k=random.randint(1, 2)),
                'created_at': fake.date_time_between(start_date='-180d', end_date='-1d').isoformat(),
                'updated_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('media_assets', asset_data, document_id=asset_data['id'])
                self.collections['media_assets'].append(asset_data)
                asset_ids.append(UUID(asset_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create media asset: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['media_assets'])} media assets")
        return asset_ids

    def generate_audit_logs(self, user_ids: List[UUID], count: int = 30) -> List[UUID]:
        """
        Generate audit log entries

        Args:
            user_ids: List of user IDs
            count: Number of audit logs to generate

        Returns:
            List of audit log IDs
        """
        logger.info(f"Generating {count} audit logs...")
        progress = ProgressTracker(count, "Audit Logs")

        log_ids = []
        actions = [AuditAction.CREATE, AuditAction.READ, AuditAction.UPDATE,
                   AuditAction.DELETE, AuditAction.LOGIN, AuditAction.LOGOUT,
                   AuditAction.APPROVE, AuditAction.REJECT, AuditAction.PAYMENT]
        resource_types = ['users', 'applications', 'events', 'payments', 'subscriptions']

        for _ in range(count):
            log_data = {
                'id': str(uuid4()),
                'user_id': str(random.choice(user_ids)) if random.random() > 0.1 else None,  # 10% system actions
                'action': random.choice(actions),
                'resource_type': random.choice(resource_types),
                'resource_id': str(uuid4()) if random.random() > 0.2 else None,
                'description': fake.sentence(),
                'changes': {
                    'before': {'status': random.choice(['draft', 'pending', 'active'])},
                    'after': {'status': random.choice(['approved', 'completed', 'inactive'])}
                } if random.random() > 0.5 else {},
                'ip_address': fake.ipv4(),
                'user_agent': fake.user_agent(),
                'session_id': fake.uuid4(),
                'success': random.choice([True] * 19 + [False]),  # 95% success
                'error_message': fake.sentence() if random.random() > 0.95 else None,
                'severity': random.choice(['info'] * 15 + ['warning'] * 4 + ['error']),
                'tags': random.sample(['security', 'user-action', 'system', 'payment'], k=random.randint(1, 2)),
                'metadata': {'ip_location': fake.city()},
                'created_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                'updated_at': fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
            }

            try:
                self.client.create_document('audit_logs', log_data, document_id=log_data['id'])
                self.collections['audit_logs'].append(log_data)
                log_ids.append(UUID(log_data['id']))
                progress.update()
            except ZeroDBError as e:
                logger.warning(f"Failed to create audit log: {e}")

        progress.complete()
        logger.info(f"Created {len(self.collections['audit_logs'])} audit logs")
        return log_ids

    def clear_collections(self, collection_names: Optional[List[str]] = None):
        """
        Clear all data from specified collections (delegates to clear_all_data)

        Args:
            collection_names: List of collection names to clear (default: all)
        """
        clear_all_data(self.client, collection_names)

    def seed_all(self, user_count: int = 65, application_count: int = 15,
                 event_count: int = 10, training_session_count: int = 5,
                 collection_filter: Optional[List[str]] = None):
        """
        Seed all collections with data

        Args:
            user_count: Number of users to generate
            application_count: Number of applications to generate
            event_count: Number of events to generate
            training_session_count: Number of training sessions to generate
            collection_filter: Only seed specific collections
        """
        logger.info("=" * 60)
        logger.info("Starting ZeroDB seed data generation")
        logger.info("=" * 60)

        # Generate users and profiles first (foundational data)
        if not collection_filter or 'users' in collection_filter:
            user_ids = self.generate_users(count=user_count)
        else:
            user_ids = [uuid4() for _ in range(user_count)]

        if not collection_filter or 'profiles' in collection_filter:
            profile_ids = self.generate_profiles(user_ids)

        # Generate applications and approvals
        if not collection_filter or 'applications' in collection_filter:
            application_ids = self.generate_applications(user_ids, count=application_count)
        else:
            application_ids = [uuid4() for _ in range(application_count)]

        if not collection_filter or 'approvals' in collection_filter:
            approval_ids = self.generate_approvals(application_ids, user_ids)

        # Generate subscriptions and payments
        if not collection_filter or 'subscriptions' in collection_filter:
            subscription_ids = self.generate_subscriptions(user_ids, count=min(15, user_count))
        else:
            subscription_ids = [uuid4() for _ in range(15)]

        if not collection_filter or 'payments' in collection_filter:
            payment_ids = self.generate_payments(user_ids, subscription_ids, count=20)

        # Generate events and RSVPs
        if not collection_filter or 'events' in collection_filter:
            event_ids = self.generate_events(user_ids, count=event_count)
        else:
            event_ids = [uuid4() for _ in range(event_count)]

        if not collection_filter or 'rsvps' in collection_filter:
            rsvp_ids = self.generate_rsvps(event_ids, user_ids, count=min(30, user_count * 2))

        # Generate training sessions and attendance
        if not collection_filter or 'training_sessions' in collection_filter:
            session_ids = self.generate_training_sessions(event_ids, user_ids, count=training_session_count)
        else:
            session_ids = [uuid4() for _ in range(training_session_count)]

        if not collection_filter or 'session_attendance' in collection_filter:
            attendance_ids = self.generate_session_attendance(session_ids, user_ids, count=min(25, user_count))

        # Generate search and content data
        if not collection_filter or 'search_queries' in collection_filter:
            query_ids = self.generate_search_queries(user_ids, count=20)

        if not collection_filter or 'content_index' in collection_filter:
            content_ids = self.generate_content_index(user_ids, count=15)

        if not collection_filter or 'media_assets' in collection_filter:
            asset_ids = self.generate_media_assets(user_ids, count=10)

        if not collection_filter or 'audit_logs' in collection_filter:
            log_ids = self.generate_audit_logs(user_ids, count=30)

        logger.info("=" * 60)
        logger.info("Seed data generation complete!")
        logger.info("=" * 60)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print summary of generated data"""
        logger.info("\nData Summary:")
        logger.info("-" * 60)
        for collection, data in self.collections.items():
            if data:
                logger.info(f"  {collection.ljust(25)}: {len(data)} records")
        logger.info("-" * 60)
        total = sum(len(data) for data in self.collections.values())
        logger.info(f"  {'TOTAL'.ljust(25)}: {total} records")
        logger.info("=" * 60)


def main():
    """Main entry point for seed data script"""
    parser = argparse.ArgumentParser(
        description='Seed ZeroDB with realistic test data for WWMAA development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/scripts/seed_data.py
  python backend/scripts/seed_data.py --clear
  python backend/scripts/seed_data.py --count 100
  python backend/scripts/seed_data.py --collections users,events

SAFETY: This script includes environment checks and will NOT run in production.
        """
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data before seeding'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=65,
        help='Number of users to generate (default: 65 - includes 5 admin, 10 board, 20 members, 30 public)'
    )
    parser.add_argument(
        '--applications',
        type=int,
        default=15,
        help='Number of applications to generate (default: 15)'
    )
    parser.add_argument(
        '--events',
        type=int,
        default=10,
        help='Number of events to generate (default: 10)'
    )
    parser.add_argument(
        '--training-sessions',
        type=int,
        default=5,
        help='Number of training sessions to generate (default: 5)'
    )
    parser.add_argument(
        '--collections',
        type=str,
        help='Comma-separated list of collections to seed (default: all)'
    )

    args = parser.parse_args()

    try:
        # Environment safety check
        logger.info("Performing environment safety check...")
        check_environment()

        # Initialize ZeroDB client
        logger.info("Initializing ZeroDB client...")
        client = ZeroDBClient()

        # Initialize seed generator
        generator = SeedDataGenerator(client)

        # Clear data if requested
        if args.clear:
            collection_filter = args.collections.split(',') if args.collections else None
            generator.clear_collections(collection_filter)

        # Parse collection filter
        collection_filter = args.collections.split(',') if args.collections else None

        # Generate seed data
        generator.seed_all(
            user_count=args.count,
            application_count=args.applications,
            event_count=args.events,
            training_session_count=args.training_sessions,
            collection_filter=collection_filter
        )

        logger.info("\nSeed data generation completed successfully!")
        return 0

    except ZeroDBError as e:
        logger.error(f"ZeroDB error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 2
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    sys.exit(main())
