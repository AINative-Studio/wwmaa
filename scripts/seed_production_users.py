#!/usr/bin/env python3
"""
Seed test users directly to production ZeroDB
This script ensures users are created in the PRODUCTION project
"""

import os
import sys
import requests
from passlib.context import CryptContext

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ZeroDB configuration from environment
ZERODB_EMAIL = os.getenv("ZERODB_EMAIL")
ZERODB_PASSWORD = os.getenv("ZERODB_PASSWORD")
ZERODB_API_BASE_URL = os.getenv("ZERODB_API_BASE_URL")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

print("=" * 60)
print("Production User Seeding Script")
print("=" * 60)
print(f"ZeroDB API: {ZERODB_API_BASE_URL}")
print(f"Project ID: {ZERODB_PROJECT_ID}")
print()

class ZeroDBClient:
    def __init__(self):
        self.base_url = ZERODB_API_BASE_URL.rstrip('/')
        self.project_id = ZERODB_PROJECT_ID
        self.token = None

    def authenticate(self):
        """Get JWT token"""
        url = f"{self.base_url}/v1/public/auth/login-json"
        response = requests.post(url, json={
            "username": ZERODB_EMAIL,
            "password": ZERODB_PASSWORD
        })

        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.text}")

        self.token = response.json()["access_token"]
        print("✅ Authenticated with ZeroDB")

    def get_headers(self):
        """Get auth headers"""
        return {"Authorization": f"Bearer {self.token}"}

    def list_rows(self, table_name):
        """List all rows in a table"""
        url = f"{self.base_url}/v1/projects/{self.project_id}/database/tables/{table_name}/rows"
        response = requests.get(url, headers=self.get_headers())

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return result
            return result.get("rows", [])
        return []

    def insert_row(self, table_name, row_data):
        """Insert a row into a table"""
        url = f"{self.base_url}/v1/projects/{self.project_id}/database/tables/{table_name}/rows"
        response = requests.post(url, headers=self.get_headers(), json={
            "row_data": row_data
        })

        if response.status_code != 200:
            raise Exception(f"Failed to insert row: {response.text}")

        return response.json().get("row_id")

    def delete_row(self, table_name, row_id):
        """Delete a row from a table"""
        url = f"{self.base_url}/v1/projects/{self.project_id}/database/tables/{table_name}/rows/{row_id}"
        response = requests.delete(url, headers=self.get_headers())
        return response.status_code == 200

def hash_password(password):
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def main():
    # Initialize client
    client = ZeroDBClient()
    client.authenticate()

    # Check existing users
    print("\n📋 Checking existing users...")
    existing_rows = client.list_rows("users")
    print(f"Found {len(existing_rows)} existing users")

    if len(existing_rows) > 0:
        print("\n⚠️  Existing users found:")
        for row in existing_rows:
            email = row.get("row_data", {}).get("email", "unknown")
            row_id = row.get("row_id", "unknown")
            print(f"   - {email} (ID: {row_id})")

        response = input("\nDelete existing users and recreate? (yes/no): ")
        if response.lower() == "yes":
            print("\n🗑️  Deleting existing users...")
            for row in existing_rows:
                row_id = row.get("row_id")
                if client.delete_row("users", row_id):
                    email = row.get("row_data", {}).get("email", "unknown")
                    print(f"   ✅ Deleted: {email}")
        else:
            print("\n❌ Cancelled - keeping existing users")
            return

    # Create test users
    print("\n👥 Creating test users...")
    users = [
        {
            "email": "admin@wwmaa.com",
            "password": "AdminPass123!",
            "first_name": "John",
            "last_name": "Admin",
            "role": "admin"
        },
        {
            "email": "test@wwmaa.com",
            "password": "TestPass123!",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": "member"
        },
        {
            "email": "board@wwmaa.com",
            "password": "BoardPass123!",
            "first_name": "Sarah",
            "last_name": "Board",
            "role": "board_member"
        }
    ]

    created_count = 0
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

            row_id = client.insert_row("users", user_row)

            print(f"✅ Created: {user_data['email']}")
            print(f"   Role: {user_data['role']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Row ID: {row_id}")
            print()

            created_count += 1

        except Exception as e:
            print(f"❌ Failed to create {user_data['email']}: {e}")
            print()

    # Verify
    print("=" * 60)
    print(f"✅ Created {created_count} users successfully")
    print("=" * 60)

    # List final users
    print("\n📋 Final user list:")
    final_rows = client.list_rows("users")
    for row in final_rows:
        row_data = row.get("row_data", {})
        print(f"   - {row_data.get('email')} ({row_data.get('role')})")

    print("\n" + "=" * 60)
    print("✅ Seeding Complete!")
    print("=" * 60)
    print("\nTest Credentials:")
    print("  admin@wwmaa.com / AdminPass123!")
    print("  test@wwmaa.com / TestPass123!")
    print("  board@wwmaa.com / BoardPass123!")
    print()

if __name__ == "__main__":
    main()
