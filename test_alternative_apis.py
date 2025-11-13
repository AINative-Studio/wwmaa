#!/usr/bin/env python3
"""
Test Alternative ZeroDB API Endpoints
Tries different API paths to find what works
"""

import sys
import os
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from backend.config import settings

def test_alternative_apis():
    """Test various ZeroDB API endpoints to find what works"""
    print("="*60)
    print("Testing Alternative ZeroDB API Endpoints")
    print("="*60)
    print()

    # Configuration
    base_url = str(settings.ZERODB_API_BASE_URL).rstrip("/")
    project_id = getattr(settings, 'ZERODB_PROJECT_ID', None)
    email = str(settings.ZERODB_EMAIL)
    password = str(settings.ZERODB_PASSWORD)

    # Authenticate
    print("Authenticating...")
    auth_url = f"{base_url}/v1/public/auth/login-json"
    auth_data = {"username": email, "password": password}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return False

        token = response.json()["access_token"]
        print("✅ Authenticated")
        print()
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # Test different API endpoints
    test_endpoints = [
        # Tables API (current - known to fail)
        {
            "name": "Tables API - List Tables",
            "url": f"{base_url}/v1/projects/{project_id}/database/tables",
            "method": "GET"
        },
        {
            "name": "Tables API - Users Table",
            "url": f"{base_url}/v1/projects/{project_id}/database/tables/users/rows",
            "method": "GET",
            "params": {"limit": 1}
        },

        # Collections API (alternative)
        {
            "name": "Collections API - List Collections",
            "url": f"{base_url}/v1/projects/{project_id}/collections",
            "method": "GET"
        },
        {
            "name": "Collections API - Users Collection",
            "url": f"{base_url}/v1/projects/{project_id}/collections/users/documents",
            "method": "GET",
            "params": {"limit": 1}
        },

        # Database API (alternative)
        {
            "name": "Database API - Query",
            "url": f"{base_url}/v1/projects/{project_id}/database/query",
            "method": "POST",
            "json": {"table": "users", "limit": 1}
        },
        {
            "name": "Database API - Search",
            "url": f"{base_url}/v1/projects/{project_id}/database/search",
            "method": "POST",
            "json": {"collection": "users", "query": {}}
        },

        # Project API
        {
            "name": "Project Info",
            "url": f"{base_url}/v1/projects/{project_id}",
            "method": "GET"
        },
        {
            "name": "Project Schema",
            "url": f"{base_url}/v1/projects/{project_id}/schema",
            "method": "GET"
        },

        # Data API (alternative)
        {
            "name": "Data API - Users",
            "url": f"{base_url}/v1/data/projects/{project_id}/users",
            "method": "GET"
        },

        # Storage API (alternative)
        {
            "name": "Storage API - List",
            "url": f"{base_url}/v1/projects/{project_id}/storage",
            "method": "GET"
        },
    ]

    working_endpoints = []
    failed_endpoints = []

    for test in test_endpoints:
        print(f"Testing: {test['name']}")
        print(f"  URL: {test['url']}")

        try:
            if test['method'] == 'GET':
                response = requests.get(
                    test['url'],
                    headers=headers,
                    params=test.get('params', {}),
                    timeout=10
                )
            elif test['method'] == 'POST':
                response = requests.post(
                    test['url'],
                    headers=headers,
                    json=test.get('json', {}),
                    timeout=10
                )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"  Response keys: {list(data.keys())}")
                    working_endpoints.append({
                        "name": test['name'],
                        "url": test['url'],
                        "response": data
                    })
                except:
                    print(f"  Response: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"  ⚠️  Not Found (endpoint may not exist)")
                failed_endpoints.append({
                    "name": test['name'],
                    "status": 404,
                    "reason": "Not Found"
                })
            elif response.status_code == 500:
                print(f"  ❌ Server Error: {response.text[:100]}")
                failed_endpoints.append({
                    "name": test['name'],
                    "status": 500,
                    "reason": response.text[:100]
                })
            else:
                print(f"  ⚠️  Status: {response.status_code}")
                print(f"  Response: {response.text[:100]}")
                failed_endpoints.append({
                    "name": test['name'],
                    "status": response.status_code,
                    "reason": response.text[:100]
                })

        except requests.exceptions.Timeout:
            print(f"  ⏱️  Timeout")
            failed_endpoints.append({
                "name": test['name'],
                "status": "timeout",
                "reason": "Request timeout"
            })
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed_endpoints.append({
                "name": test['name'],
                "status": "error",
                "reason": str(e)
            })

        print()

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print()

    if working_endpoints:
        print(f"✅ Found {len(working_endpoints)} working endpoint(s):")
        print()
        for endpoint in working_endpoints:
            print(f"  ✅ {endpoint['name']}")
            print(f"     URL: {endpoint['url']}")
            print(f"     Response: {list(endpoint['response'].keys())}")
            print()

        print("="*60)
        print("RECOMMENDATION")
        print("="*60)
        print()
        print("Update ZeroDB service to use the working endpoint(s) above.")
        print()

    else:
        print("❌ No working endpoints found!")
        print()
        print("Possible issues:")
        print("  1. ZeroDB API version mismatch")
        print("  2. Project not properly initialized")
        print("  3. ZeroDB API has breaking bugs")
        print()
        print("Recommendation: Contact ZeroDB support")

    return len(working_endpoints) > 0

if __name__ == "__main__":
    success = test_alternative_apis()
    sys.exit(0 if success else 1)
