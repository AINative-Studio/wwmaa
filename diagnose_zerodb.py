#!/usr/bin/env python3
"""
ZeroDB Diagnostic Script
Checks the actual state of the ZeroDB project
"""

import sys
import os
import requests
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from backend.config import settings

def diagnose_zerodb():
    """Diagnose ZeroDB project state"""
    print("="*60)
    print("ZeroDB Project Diagnostic")
    print("="*60)
    print()

    # Configuration
    base_url = str(settings.ZERODB_API_BASE_URL).rstrip("/")
    project_id = getattr(settings, 'ZERODB_PROJECT_ID', None)
    email = str(settings.ZERODB_EMAIL)
    password = str(settings.ZERODB_PASSWORD)

    print(f"Base URL: {base_url}")
    print(f"Project ID: {project_id}")
    print(f"Email: {email}")
    print()

    # Step 1: Authenticate
    print("Step 1: Authenticating...")
    auth_url = f"{base_url}/v1/public/auth/login-json"
    auth_data = {
        "username": email,
        "password": password
    }

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            result = response.json()
            token = result["access_token"]
            print(f"✅ Authentication successful")
            print(f"   Token: {token[:20]}...")
            print()
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: List tables
    print("Step 2: Listing tables in project...")
    tables_url = f"{base_url}/v1/projects/{project_id}/database/tables"

    try:
        response = requests.get(tables_url, headers=headers)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            tables = response.json()
            print(f"   ✅ Found {len(tables.get('tables', []))} tables")
            print()
            print("   Tables:")
            for table in tables.get('tables', []):
                table_name = table.get('table_name') or table.get('name')
                print(f"   - {table_name}")
            print()

            # If users table exists, check row count
            if any(t.get('table_name') == 'users' or t.get('name') == 'users' for t in tables.get('tables', [])):
                print("Step 3: Checking 'users' table...")
                users_url = f"{base_url}/v1/projects/{project_id}/database/tables/users/rows"
                response = requests.get(users_url, headers=headers, params={"limit": 10})

                if response.status_code == 200:
                    users_data = response.json()
                    rows = users_data.get('rows', [])
                    print(f"   ✅ Found {len(rows)} user(s) in users table")
                    print()

                    if rows:
                        print("   Sample Users:")
                        for row in rows:
                            row_data = row.get('row_data', {})
                            print(f"   - Email: {row_data.get('email')}, Role: {row_data.get('role')}")
                        print()
                    else:
                        print("   ⚠️  Users table exists but is empty!")
                        print("   Need to run seed script: python3 scripts/seed_zerodb.py")
                        print()
                else:
                    print(f"   ❌ Failed to query users table: {response.status_code}")
                    print(f"   Response: {response.text}")
                    print()
            else:
                print("⚠️  'users' table does not exist!")
                print("   Need to run seed script to create tables: python3 scripts/seed_zerodb.py")
                print()

            # Check events table
            if any(t.get('table_name') == 'events' or t.get('name') == 'events' for t in tables.get('tables', [])):
                print("Step 4: Checking 'events' table...")
                events_url = f"{base_url}/v1/projects/{project_id}/database/tables/events/rows"
                response = requests.get(events_url, headers=headers, params={"limit": 10})

                if response.status_code == 200:
                    events_data = response.json()
                    rows = events_data.get('rows', [])
                    print(f"   ✅ Found {len(rows)} event(s) in events table")
                    print()

                    if rows:
                        print("   Sample Events:")
                        for row in rows:
                            row_data = row.get('row_data', {})
                            print(f"   - Title: {row_data.get('title')}, Type: {row_data.get('event_type')}")
                        print()
                    else:
                        print("   ⚠️  Events table exists but is empty!")
                        print()
                else:
                    print(f"   ❌ Failed to query events table: {response.status_code}")
                    print()

        else:
            print(f"   ❌ Failed to list tables: {response.status_code}")
            print(f"   Response: {response.text}")
            print()

    except Exception as e:
        print(f"   ❌ Error listing tables: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("="*60)
    print("Diagnostic Complete")
    print("="*60)
    return True

if __name__ == "__main__":
    success = diagnose_zerodb()
    sys.exit(0 if success else 1)
