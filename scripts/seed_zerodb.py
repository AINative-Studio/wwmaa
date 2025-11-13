#!/usr/bin/env python3
"""
Seed ZeroDB with test data for development and testing

This script creates:
- Test users with different roles
- Sample events
"""
import sys
import os
import requests
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.utils.security import hash_password
from backend.config import settings

# Load ZERODB_PROJECT_ID from environment
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")
if not ZERODB_PROJECT_ID:
    # Try loading from .env file
    from pathlib import Path
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("ZERODB_PROJECT_ID="):
                    ZERODB_PROJECT_ID = line.split("=", 1)[1].strip()
                    break

if not ZERODB_PROJECT_ID:
    raise ValueError("ZERODB_PROJECT_ID not found in environment or .env file")

class ZeroDBSeeder:
    """Handles seeding ZeroDB with test data"""

    def __init__(self):
        self.base_url = str(settings.ZERODB_API_BASE_URL).rstrip("/")
        self.project_id = ZERODB_PROJECT_ID
        self.email = str(settings.ZERODB_EMAIL)
        self.password = str(settings.ZERODB_PASSWORD)
        self.token = None

    def login(self):
        """Authenticate and get JWT token"""
        url = f"{self.base_url}/v1/public/auth/login-json"
        data = {
            "username": self.email,
            "password": self.password
        }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            print("✅ Authenticated successfully\n")
        else:
            raise Exception(f"Authentication failed: {response.text}")

    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}

    def create_table(self, table_name, schema):
        """Create a table in ZeroDB project"""
        url = f"{self.base_url}/v1/projects/{self.project_id}/database/tables"
        data = {
            "table_name": table_name,
            "schema": schema
        }

        response = requests.post(url, headers=self.get_headers(), json=data)
        if response.status_code == 200:
            print(f"✅ Table '{table_name}' created")
            return True
        elif "already exists" in response.text.lower():
            print(f"ℹ️  Table '{table_name}' already exists")
            return True
        else:
            print(f"⚠️  Failed to create table '{table_name}': {response.text}")
            return False

    def insert_row(self, table_name, row_data):
        """Insert a row into a table"""
        url = f"{self.base_url}/v1/projects/{self.project_id}/database/tables/{table_name}/rows"
        data = {"row_data": row_data}

        response = requests.post(url, headers=self.get_headers(), json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get("row_id")
        else:
            raise Exception(f"Failed to insert row: {response.text}")

    def list_rows(self, table_name):
        """List all rows in a table"""
        url = f"{self.base_url}/v1/projects/{self.project_id}/database/tables/{table_name}/rows"
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            result = response.json()
            # Handle both list response and dict response
            if isinstance(result, list):
                return result
            return result.get("rows", [])
        return []

    def create_tables(self):
        """Create required tables"""
        print("📦 Creating Tables...")
        print()

        # Users table
        users_schema = {
            "email": "string",
            "password_hash": "string",
            "first_name": "string",
            "last_name": "string",
            "role": "string",
            "is_active": "boolean",
            "is_verified": "boolean"
        }
        self.create_table("users", users_schema)

        # Profiles table
        profiles_schema = {
            "user_id": "string",
            "bio": "string",
            "phone": "string",
            "country": "string",
            "locale": "string",
            "ranks": "json",
            "schools_affiliated": "json"
        }
        self.create_table("profiles", profiles_schema)

        # Events table
        events_schema = {
            "title": "string",
            "description": "string",
            "event_type": "string",
            "visibility": "string",
            "status": "string",
            "is_published": "boolean",
            "start_date": "string",
            "end_date": "string",
            "location": "string",
            "is_online": "boolean",
            "price": "number",
            "currency": "string",
            "capacity": "number",
            "registered_count": "number",
            "created_by": "string"
        }
        self.create_table("events", events_schema)

        print()

    def create_test_users(self):
        """Create test users with different roles"""
        print("📝 Creating Test Users...")
        print()

        # Check if users already exist
        existing_users = self.list_rows("users")
        if existing_users:
            print(f"⚠️  {len(existing_users)} users already exist, skipping user creation")
            # Return existing users with mock passwords for display
            return [{
                "id": user["row_id"],
                "email": user["row_data"]["email"],
                "password": "[Existing]",
                "role": user["row_data"]["role"]
            } for user in existing_users]

        users = [
            {
                "email": "test@wwmaa.com",
                "password": "TestPass123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "role": "member"
            },
            {
                "email": "admin@wwmaa.com",
                "password": "AdminPass123!",
                "first_name": "John",
                "last_name": "Admin",
                "role": "admin"
            },
            {
                "email": "board@wwmaa.com",
                "password": "BoardPass123!",
                "first_name": "Sarah",
                "last_name": "Board",
                "role": "board_member"
            }
        ]

        created_users = []

        for user_data in users:
            try:
                # Hash password
                password_hash = hash_password(user_data["password"])

                # Create user row
                user_row = {
                    "email": user_data["email"],
                    "password_hash": password_hash,
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "role": user_data["role"],
                    "is_active": True,
                    "is_verified": True
                }

                user_id = self.insert_row("users", user_row)

                print(f"✅ Created user: {user_data['email']}")
                print(f"   ID: {user_id}")
                print(f"   Role: {user_data['role']}")
                print(f"   Password: {user_data['password']}")

                # Create profile
                profile_row = {
                    "user_id": user_id,
                    "bio": f"{user_data['first_name']} {user_data['last_name']} - Test User",
                    "phone": "+1-555-0100",
                    "country": "USA",
                    "locale": "en-US",
                    "ranks": {"karate": "Black Belt (1st Dan)"},
                    "schools_affiliated": ["WWMAA Test Dojo"]
                }

                self.insert_row("profiles", profile_row)
                print(f"   ✅ Profile created")
                print()

                created_users.append({
                    "id": user_id,
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "role": user_data["role"]
                })

            except Exception as e:
                print(f"❌ Failed to create user {user_data['email']}: {e}")
                print()

        return created_users

    def create_sample_events(self, admin_user_id):
        """Create sample events for testing"""
        print("📅 Creating Sample Events...")
        print()

        # Check if events already exist
        existing_events = self.list_rows("events")
        if existing_events:
            print(f"⚠️  {len(existing_events)} events already exist, skipping event creation")
            print()
            return []

        if not admin_user_id:
            print("⚠️  No admin user found, skipping event creation")
            return []

        events = [
            {
                "title": "Karate Workshop - Advanced Techniques",
                "description": "Join us for an intensive workshop covering advanced Karate techniques including kata and kumite strategies.",
                "event_type": "workshop",
                "visibility": "public",
                "status": "published",
                "is_published": True,
                "start_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=30, hours=3)).isoformat(),
                "location": "WWMAA Headquarters",
                "is_online": False,
                "price": 50.00,
                "currency": "USD",
                "capacity": 30,
                "registered_count": 5,
                "created_by": admin_user_id
            },
            {
                "title": "Women's Self-Defense Seminar",
                "description": "Empowerment through martial arts. Learn practical self-defense techniques in a supportive environment.",
                "event_type": "seminar",
                "visibility": "public",
                "status": "published",
                "is_published": True,
                "start_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=45, hours=4)).isoformat(),
                "location": "Online via Zoom",
                "is_online": True,
                "price": 0.00,
                "currency": "USD",
                "capacity": 100,
                "registered_count": 23,
                "created_by": admin_user_id
            },
            {
                "title": "Annual WWMAA Championship",
                "description": "The premier martial arts competition featuring practitioners from across the nation.",
                "event_type": "competition",
                "visibility": "public",
                "status": "published",
                "is_published": True,
                "start_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=92)).isoformat(),
                "location": "National Sports Center",
                "is_online": False,
                "price": 75.00,
                "currency": "USD",
                "capacity": 200,
                "registered_count": 87,
                "created_by": admin_user_id
            }
        ]

        created_events = []

        for event_data in events:
            try:
                event_id = self.insert_row("events", event_data)

                print(f"✅ Created event: {event_data['title']}")
                print(f"   ID: {event_id}")
                print(f"   Type: {event_data['event_type']}")
                print(f"   Date: {event_data['start_date'][:10]}")
                print()

                created_events.append(event_id)

            except Exception as e:
                print(f"❌ Failed to create event {event_data['title']}: {e}")
                print()

        return created_events

    def run(self):
        """Main seeding function"""
        print("=" * 60)
        print("ZeroDB Data Seeding Script")
        print("=" * 60)
        print()

        # Authenticate
        self.login()

        # Create tables
        self.create_tables()

        # Create users
        users = self.create_test_users()

        if not users:
            print("❌ No users created. Exiting.")
            return

        # Find admin user
        admin_user = next((u for u in users if u["role"] == "admin"), None)
        admin_user_id = admin_user["id"] if admin_user else None

        # Create events
        if admin_user_id:
            events = self.create_sample_events(admin_user_id)
            print(f"✅ Created {len(events)} events")
        else:
            print("⚠️  No admin user found, skipping event creation")

        # Print summary
        print()
        print("=" * 60)
        print("✅ Seeding Complete!")
        print("=" * 60)
        print()
        print("Test User Credentials:")
        print()
        for user in users:
            if user["password"] != "[Existing]":
                print(f"Email: {user['email']}")
                print(f"Password: {user['password']}")
                print(f"Role: {user['role']}")
                print()

if __name__ == "__main__":
    seeder = ZeroDBSeeder()
    seeder.run()
