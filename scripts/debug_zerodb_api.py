#!/usr/bin/env python3
"""
Debug ZeroDB API Access

Tests the ZeroDB API endpoints to diagnose 403 errors.
"""

import sys
import os
import requests
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import get_settings

def main():
    print("=" * 70)
    print("ZeroDB API Debug")
    print("=" * 70)

    settings = get_settings()

    print(f"\n📋 Configuration:")
    print(f"API URL: https://api.ainative.studio")
    print(f"Project ID: {settings.ZERODB_PROJECT_ID}")
    print(f"JWT Token: {settings.ZERODB_JWT_TOKEN[:30]}...")

    # Test 1: List projects to see what we have access to
    print("\n" + "=" * 70)
    print("Test 1: List Available Projects")
    print("=" * 70)

    try:
        response = requests.get(
            "https://api.ainative.studio/v1/projects",
            headers={"Authorization": f"Bearer {settings.ZERODB_JWT_TOKEN}"},
            timeout=10
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} projects:")
            for i, project in enumerate(projects, 1):
                proj_id = project.get('id', 'N/A')
                proj_name = project.get('name', 'N/A')
                print(f"  {i}. {proj_name} (ID: {proj_id})")

                if proj_id == settings.ZERODB_PROJECT_ID:
                    print(f"     ✅ This is the configured project!")
        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test 2: Get specific project details
    print("\n" + "=" * 70)
    print("Test 2: Get Project Details")
    print("=" * 70)

    try:
        response = requests.get(
            f"https://api.ainative.studio/v1/projects/{settings.ZERODB_PROJECT_ID}",
            headers={"Authorization": f"Bearer {settings.ZERODB_JWT_TOKEN}"},
            timeout=10
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            project = response.json()
            print(f"✅ Project details:")
            print(json.dumps(project, indent=2))
        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test 3: Try embedding generation with detailed error
    print("\n" + "=" * 70)
    print("Test 3: Test Embedding Generation Endpoint")
    print("=" * 70)

    try:
        response = requests.post(
            f"https://api.ainative.studio/v1/projects/{settings.ZERODB_PROJECT_ID}/embeddings/generate",
            headers={
                "Authorization": f"Bearer {settings.ZERODB_JWT_TOKEN}",
                "Content-Type": "application/json"
            },
            json={"texts": ["test"]},
            timeout=10
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            print("✅ Embedding generation works!")
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Possible issues:")
            print("   - JWT token doesn't have permission for this project")
            print("   - Embedding feature not enabled for this project")
            print("   - JWT token expired or invalid")
        else:
            print(f"❌ Unexpected error")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test 4: Check API documentation endpoint
    print("\n" + "=" * 70)
    print("Test 4: Check Available Endpoints")
    print("=" * 70)

    try:
        response = requests.get(
            "https://api.ainative.studio/docs",
            timeout=10
        )

        print(f"Status: {response.status_code}")
        print(f"API docs available at: https://api.ainative.studio/docs")

    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    main()
