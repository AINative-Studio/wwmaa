#!/usr/bin/env python3
"""
Test the exact same query the backend makes
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.services.zerodb_service import get_zerodb_client

print("=" * 80)
print("TESTING BACKEND QUERY LOGIC")
print("=" * 80)

# Get the same client the backend uses
db_client = get_zerodb_client()

print("\n1. Testing query for admin@wwmaa.com...")
users = db_client.query_documents(
    collection="users",
    filters={"email": "admin@wwmaa.com"},
    limit=1
)

print(f"\nResult: {users}")
print(f"Documents found: {len(users.get('documents', []))}")

if users.get("documents"):
    print("\n✅ Found user!")
    user = users["documents"][0]
    print(f"User ID: {user.get('id')}")
    print(f"Email: {user.get('data', {}).get('email')}")
    print(f"Role: {user.get('data', {}).get('role')}")
else:
    print("\n❌ No user found!")
    print("This matches what the backend sees")

print("\n2. Testing query for ALL users (no filter)...")
all_users = db_client.query_documents(
    collection="users",
    limit=10
)

print(f"\nAll users found: {len(all_users.get('documents', []))}")
for user in all_users.get("documents", []):
    print(f"  - {user.get('data', {}).get('email')}")
