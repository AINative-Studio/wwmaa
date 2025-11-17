#!/usr/bin/env python3
"""
Debug the filtering logic
"""

import os
import sys
import requests

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
print("DEBUG: Client-Side Filtering Logic")
print("=" * 80)

filters = {"email": "admin@wwmaa.com"}

print(f"\nTotal rows fetched: {len(rows)}")
print(f"Filters: {filters}")
print()

filtered_rows = []
for i, row in enumerate(rows, 1):
    row_data = row.get("row_data", {})
    match = True

    print(f"\n--- Row #{i} ---")
    print(f"row_data type: {type(row_data)}")
    print(f"row_data: {row_data}")

    for key, value in filters.items():
        row_value = row_data.get(key)
        print(f"\nChecking filter: {key} = {value}")
        print(f"  row_data.get('{key}'): {repr(row_value)}")
        print(f"  Type: {type(row_value)}")
        print(f"  Match: {row_value == value}")

        if row_value != value:
            match = False
            print(f"  ❌ NO MATCH")
            break
        else:
            print(f"  ✅ MATCH")

    print(f"\nFinal match result: {match}")

    if match:
        filtered_rows.append(row)
        print("  ✅ ADDED TO FILTERED ROWS")
    else:
        print("  ❌ EXCLUDED")

print("\n" + "=" * 80)
print(f"RESULT: {len(filtered_rows)} rows matched")
print("=" * 80)

for row in filtered_rows:
    print(f"  - {row.get('row_data', {}).get('email')}")
