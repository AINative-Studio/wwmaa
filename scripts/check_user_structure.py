#!/usr/bin/env python3
"""
Check the exact structure of users in production ZeroDB
"""

import os
import sys
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

ZERODB_EMAIL = os.getenv("ZERODB_EMAIL")
ZERODB_PASSWORD = os.getenv("ZERODB_PASSWORD")
ZERODB_API_BASE_URL = os.getenv("ZERODB_API_BASE_URL")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

# Get JWT token
url = f"{ZERODB_API_BASE_URL}/v1/public/auth/login-json"
response = requests.post(url, json={
    "username": ZERODB_EMAIL,
    "password": ZERODB_PASSWORD
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get users
url = f"{ZERODB_API_BASE_URL}/v1/projects/{ZERODB_PROJECT_ID}/database/tables/users/rows"
response = requests.get(url, headers=headers)
result = response.json()

if isinstance(result, list):
    rows = result
else:
    rows = result.get("rows", [])

print("=" * 80)
print("USER DATA STRUCTURE IN PRODUCTION")
print("=" * 80)
print(f"\nTotal users found: {len(rows)}")
print()

for i, row in enumerate(rows, 1):
    print(f"\n{'=' * 80}")
    print(f"USER #{i}")
    print(f"{'=' * 80}")
    print(json.dumps(row, indent=2))

print("\n" + "=" * 80)
print("BACKEND QUERY FORMAT")
print("=" * 80)
print("""
The backend queries with:
  filters={'email': 'admin@wwmaa.com'}

It expects to match against row_data.email
""")
