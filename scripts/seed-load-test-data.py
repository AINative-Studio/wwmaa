#!/usr/bin/env python3
"""
WWMAA Load Test Data Seeding Script

Seeds staging environment with realistic test data for load testing.

Usage:
    python scripts/seed-load-test-data.py --environment=staging [--clean]

Options:
    --environment ENV    Target environment (staging only)
    --clean             Clean existing test data before seeding
    --users N           Number of test users to create (default: 1000)
    --events N          Number of test events to create (default: 500)
    --instructors N     Number of test instructors (default: 200)
    --content N         Number of searchable content items (default: 5000)
    --help              Show this help message
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta
from faker import Faker
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Faker for realistic test data
fake = Faker()

# Color codes for output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def log(message):
    print(f"{Colors.BLUE}[{datetime.now().strftime('%H:%M:%S')}]{Colors.END} {message}")

def log_success(message):
    print(f"{Colors.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ✓ {message}{Colors.END}")

def log_error(message):
    print(f"{Colors.RED}[{datetime.now().strftime('%H:%M:%S')}] ✗ {message}{Colors.END}")

def log_warn(message):
    print(f"{Colors.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⚠ {message}{Colors.END}")

class LoadTestDataSeeder:
    def __init__(self, environment, clean=False):
        self.environment = environment
        self.clean = clean
        self.conn = None
        self.cursor = None

        # Validate environment
        if environment != 'staging':
            raise ValueError("This script can only run against staging environment")

        # Database connection
        self.db_url = os.getenv('STAGING_DATABASE_URL')
        if not self.db_url:
            raise ValueError("STAGING_DATABASE_URL not set in environment")

    def connect(self):
        """Connect to database."""
        log(f"Connecting to {self.environment} database...")
        self.conn = psycopg2.connect(self.db_url)
        self.cursor = self.conn.cursor()
        log_success("Database connected")

    def disconnect(self):
        """Disconnect from database."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        log_success("Database disconnected")

    def clean_test_data(self):
        """Clean existing test data."""
        if not self.clean:
            return

        log_warn("Cleaning existing test data...")

        # Delete test data (marked by email/name containing 'loadtest')
        queries = [
            "DELETE FROM event_rsvps WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%loadtest%')",
            "DELETE FROM events WHERE title LIKE '%Load Test%'",
            "DELETE FROM users WHERE email LIKE '%loadtest%'",
            "DELETE FROM instructors WHERE email LIKE '%loadtest%'",
            "DELETE FROM content WHERE title LIKE '%Load Test%'",
        ]

        for query in queries:
            try:
                self.cursor.execute(query)
                self.conn.commit()
            except Exception as e:
                log_warn(f"Clean query failed (may not exist): {str(e)}")

        log_success("Test data cleaned")

    def seed_users(self, count=1000):
        """Seed test users."""
        log(f"Seeding {count} test users...")

        users = []
        for i in range(count):
            users.append({
                'email': f'loadtest_user_{i}@wwmaa.com',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewnWuE/5U7Vxd0sG',  # 'test_password_123'
                'status': 'active',
                'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
            })

        # Batch insert
        insert_query = """
            INSERT INTO users (email, first_name, last_name, password_hash, status, created_at)
            VALUES (%(email)s, %(first_name)s, %(last_name)s, %(password_hash)s, %(status)s, %(created_at)s)
            ON CONFLICT (email) DO NOTHING
        """

        execute_batch(self.cursor, insert_query, users, page_size=100)
        self.conn.commit()

        log_success(f"{count} test users seeded")

    def seed_instructors(self, count=200):
        """Seed test instructors."""
        log(f"Seeding {count} test instructors...")

        martial_arts_styles = [
            'Karate', 'Judo', 'Aikido', 'Taekwondo', 'Brazilian Jiu-Jitsu',
            'Muay Thai', 'Kendo', 'Wing Chun', 'Kyokushin', 'Shotokan',
            'Goju-Ryu', 'Wado-Ryu', 'Hapkido', 'Krav Maga', 'Capoeira'
        ]

        belt_ranks = [
            'Black Belt 1st Dan', 'Black Belt 2nd Dan', 'Black Belt 3rd Dan',
            'Black Belt 4th Dan', 'Black Belt 5th Dan', 'Master Instructor'
        ]

        instructors = []
        for i in range(count):
            style = random.choice(martial_arts_styles)
            instructors.append({
                'email': f'loadtest_instructor_{i}@wwmaa.com',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'style': style,
                'rank': random.choice(belt_ranks),
                'bio': fake.text(max_nb_chars=500),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'years_experience': random.randint(5, 40),
                'created_at': fake.date_time_between(start_date='-5y', end_date='now'),
            })

        insert_query = """
            INSERT INTO instructors (email, first_name, last_name, style, rank, bio, city, state, years_experience, created_at)
            VALUES (%(email)s, %(first_name)s, %(last_name)s, %(style)s, %(rank)s, %(bio)s, %(city)s, %(state)s, %(years_experience)s, %(created_at)s)
            ON CONFLICT (email) DO NOTHING
        """

        execute_batch(self.cursor, insert_query, instructors, page_size=100)
        self.conn.commit()

        log_success(f"{count} test instructors seeded")

    def seed_events(self, count=500):
        """Seed test events."""
        log(f"Seeding {count} test events...")

        event_types = [
            'Training Session', 'Tournament', 'Seminar', 'Workshop',
            'Demonstration', 'Belt Test', 'Sparring Practice', 'Kata Practice'
        ]

        martial_arts_styles = [
            'Karate', 'Judo', 'Aikido', 'Taekwondo', 'Brazilian Jiu-Jitsu',
            'Muay Thai', 'Kendo', 'Wing Chun'
        ]

        # Get instructor IDs
        self.cursor.execute("SELECT id FROM instructors WHERE email LIKE '%loadtest%'")
        instructor_ids = [row[0] for row in self.cursor.fetchall()]

        if not instructor_ids:
            log_warn("No instructors found, creating events without instructors")
            instructor_ids = [None]

        events = []
        for i in range(count):
            start_date = fake.date_time_between(start_date='now', end_date='+1y')
            end_date = start_date + timedelta(hours=random.randint(1, 4))

            events.append({
                'title': f"{random.choice(event_types)} - {random.choice(martial_arts_styles)} (Load Test {i})",
                'description': fake.text(max_nb_chars=1000),
                'start_date': start_date,
                'end_date': end_date,
                'location_name': fake.company(),
                'location_address': fake.street_address(),
                'location_city': fake.city(),
                'location_state': fake.state_abbr(),
                'location_zip': fake.zipcode(),
                'capacity': random.randint(20, 200),
                'price': random.choice([0, 25, 50, 75, 100, 150]),
                'instructor_id': random.choice(instructor_ids),
                'status': random.choice(['active', 'active', 'active', 'draft']),  # 75% active
                'created_at': fake.date_time_between(start_date='-6m', end_date='now'),
            })

        insert_query = """
            INSERT INTO events (title, description, start_date, end_date, location_name, location_address,
                               location_city, location_state, location_zip, capacity, price, instructor_id, status, created_at)
            VALUES (%(title)s, %(description)s, %(start_date)s, %(end_date)s, %(location_name)s, %(location_address)s,
                    %(location_city)s, %(location_state)s, %(location_zip)s, %(capacity)s, %(price)s, %(instructor_id)s, %(status)s, %(created_at)s)
        """

        execute_batch(self.cursor, insert_query, events, page_size=100)
        self.conn.commit()

        log_success(f"{count} test events seeded")

    def seed_content(self, count=5000):
        """Seed searchable content."""
        log(f"Seeding {count} searchable content items...")

        content_types = ['article', 'video', 'tutorial', 'guide', 'technique']

        martial_arts_topics = [
            'kata techniques', 'kumite strategies', 'belt progression',
            'training methods', 'martial arts philosophy', 'self-defense',
            'competition preparation', 'injury prevention', 'warm-up exercises',
            'flexibility training', 'strength training', 'meditation practices'
        ]

        content_items = []
        for i in range(count):
            topic = random.choice(martial_arts_topics)
            content_items.append({
                'title': f"{topic.title()} - Load Test Content {i}",
                'content': fake.text(max_nb_chars=2000),
                'type': random.choice(content_types),
                'author': fake.name(),
                'tags': random.sample(martial_arts_topics, k=random.randint(2, 5)),
                'published_at': fake.date_time_between(start_date='-2y', end_date='now'),
                'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
            })

        insert_query = """
            INSERT INTO content (title, content, type, author, tags, published_at, created_at)
            VALUES (%(title)s, %(content)s, %(type)s, %(author)s, %(tags)s, %(published_at)s, %(created_at)s)
        """

        execute_batch(self.cursor, insert_query, content_items, page_size=100)
        self.conn.commit()

        log_success(f"{count} content items seeded")

    def seed_subscriptions(self, count=100):
        """Seed test subscriptions."""
        log(f"Seeding {count} test subscriptions...")

        # Get user IDs
        self.cursor.execute("SELECT id FROM users WHERE email LIKE '%loadtest%' LIMIT 100")
        user_ids = [row[0] for row in self.cursor.fetchall()]

        if not user_ids:
            log_warn("No users found, skipping subscriptions")
            return

        subscription_tiers = ['basic', 'premium', 'elite']
        subscription_statuses = ['active', 'active', 'active', 'canceled']  # 75% active

        subscriptions = []
        for user_id in user_ids[:count]:
            tier = random.choice(subscription_tiers)
            status = random.choice(subscription_statuses)
            start_date = fake.date_time_between(start_date='-1y', end_date='now')
            end_date = start_date + timedelta(days=365) if status == 'active' else start_date + timedelta(days=random.randint(30, 300))

            subscriptions.append({
                'user_id': user_id,
                'tier': tier,
                'status': status,
                'stripe_subscription_id': f'sub_loadtest_{fake.uuid4()}',
                'start_date': start_date,
                'end_date': end_date if status == 'canceled' else None,
                'created_at': start_date,
            })

        insert_query = """
            INSERT INTO subscriptions (user_id, tier, status, stripe_subscription_id, start_date, end_date, created_at)
            VALUES (%(user_id)s, %(tier)s, %(status)s, %(stripe_subscription_id)s, %(start_date)s, %(end_date)s, %(created_at)s)
            ON CONFLICT (user_id) DO NOTHING
        """

        execute_batch(self.cursor, insert_query, subscriptions, page_size=100)
        self.conn.commit()

        log_success(f"{count} test subscriptions seeded")

    def create_load_test_event(self):
        """Create special event for load testing (with known ID)."""
        log("Creating dedicated load test event...")

        event = {
            'title': 'Load Test Event - High Capacity Tournament',
            'description': 'Special event for load testing RSVP functionality. This event has high capacity to test flash crowd scenarios.',
            'start_date': datetime.now() + timedelta(days=30),
            'end_date': datetime.now() + timedelta(days=30, hours=6),
            'location_name': 'Load Test Arena',
            'location_address': '123 Test Street',
            'location_city': 'Test City',
            'location_state': 'CA',
            'location_zip': '12345',
            'capacity': 1000,  # High capacity for load testing
            'price': 0,  # Free event
            'status': 'active',
            'created_at': datetime.now(),
        }

        insert_query = """
            INSERT INTO events (title, description, start_date, end_date, location_name, location_address,
                               location_city, location_state, location_zip, capacity, price, status, created_at)
            VALUES (%(title)s, %(description)s, %(start_date)s, %(end_date)s, %(location_name)s, %(location_address)s,
                    %(location_city)s, %(location_state)s, %(location_zip)s, %(capacity)s, %(price)s, %(status)s, %(created_at)s)
            ON CONFLICT (title) DO NOTHING
            RETURNING id
        """

        self.cursor.execute(insert_query, event)
        result = self.cursor.fetchone()
        self.conn.commit()

        if result:
            event_id = result[0]
            log_success(f"Load test event created with ID: {event_id}")
            log(f"Use TEST_EVENT_ID={event_id} in load test configuration")
        else:
            log_warn("Load test event already exists")

    def verify_data(self):
        """Verify seeded data."""
        log("Verifying seeded data...")

        queries = {
            'Users': "SELECT COUNT(*) FROM users WHERE email LIKE '%loadtest%'",
            'Instructors': "SELECT COUNT(*) FROM instructors WHERE email LIKE '%loadtest%'",
            'Events': "SELECT COUNT(*) FROM events WHERE title LIKE '%Load Test%'",
            'Content': "SELECT COUNT(*) FROM content WHERE title LIKE '%Load Test%'",
            'Subscriptions': "SELECT COUNT(*) FROM subscriptions WHERE stripe_subscription_id LIKE '%loadtest%'",
        }

        for name, query in queries.items():
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            log(f"  {name}: {count}")

        log_success("Data verification complete")

    def run(self, users=1000, events=500, instructors=200, content=5000):
        """Run the full seeding process."""
        try:
            self.connect()

            if self.clean:
                self.clean_test_data()

            # Seed data
            self.seed_users(users)
            self.seed_instructors(instructors)
            self.seed_events(events)
            self.seed_content(content)
            self.seed_subscriptions(min(100, users))
            self.create_load_test_event()

            # Verify
            self.verify_data()

            log_success("✓ Load test data seeding complete!")
            log("")
            log("Next steps:")
            log("1. Update .env.load-tests with test user credentials")
            log("2. Note the TEST_EVENT_ID from output above")
            log("3. Run load tests: ./scripts/run-all-tests.sh")

        except Exception as e:
            log_error(f"Seeding failed: {str(e)}")
            self.conn.rollback()
            raise
        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(
        description='Seed staging environment with load test data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--environment', default='staging', help='Target environment (staging only)')
    parser.add_argument('--clean', action='store_true', help='Clean existing test data')
    parser.add_argument('--users', type=int, default=1000, help='Number of test users')
    parser.add_argument('--events', type=int, default=500, help='Number of test events')
    parser.add_argument('--instructors', type=int, default=200, help='Number of test instructors')
    parser.add_argument('--content', type=int, default=5000, help='Number of content items')

    args = parser.parse_args()

    # Safety check
    if args.environment != 'staging':
        log_error("This script can only run against staging environment!")
        sys.exit(1)

    log("=" * 60)
    log("WWMAA Load Test Data Seeding")
    log("=" * 60)
    log(f"Environment: {args.environment}")
    log(f"Clean existing data: {args.clean}")
    log(f"Users: {args.users}")
    log(f"Events: {args.events}")
    log(f"Instructors: {args.instructors}")
    log(f"Content: {args.content}")
    log("=" * 60)
    log("")

    # Confirm
    if not args.clean:
        confirm = input("Proceed with seeding? (yes/no): ")
        if confirm.lower() != 'yes':
            log("Seeding canceled")
            sys.exit(0)

    # Run seeding
    seeder = LoadTestDataSeeder(args.environment, args.clean)
    seeder.run(
        users=args.users,
        events=args.events,
        instructors=args.instructors,
        content=args.content
    )

if __name__ == '__main__':
    main()
