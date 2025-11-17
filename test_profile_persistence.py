#!/usr/bin/env python3
"""
Manual test script to verify profile persistence
Tests the PATCH /api/me/profile endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEST_EMAIL = "test-profile@example.com"
TEST_PASSWORD = "TestPassword123!"

def test_profile_persistence():
    """Test profile update persistence"""

    print("=" * 60)
    print("Profile Persistence Test")
    print("=" * 60)

    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "first_name": "Test",
            "last_name": "User"
        }
    )

    if register_response.status_code == 201:
        print("   ✓ User registered successfully")
    elif register_response.status_code == 400 and "already exists" in register_response.text:
        print("   ℹ User already exists, continuing with login...")
    else:
        print(f"   ✗ Registration failed: {register_response.status_code}")
        print(f"   Response: {register_response.text}")
        return False

    # Step 2: Login to get token
    print("\n2. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )

    if login_response.status_code != 200:
        print(f"   ✗ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✓ Login successful")

    # Step 3: Get current profile
    print("\n3. Getting current profile...")
    profile_response = requests.get(
        f"{BASE_URL}/api/me",
        headers=headers
    )

    if profile_response.status_code != 200:
        print(f"   ✗ Failed to get profile: {profile_response.status_code}")
        print(f"   Response: {profile_response.text}")
        return False

    current_profile = profile_response.json()
    print("   ✓ Current profile retrieved")
    print(f"   Name: {current_profile.get('name')}")
    print(f"   Email: {current_profile.get('email')}")

    # Step 4: Update profile
    print("\n4. Updating profile...")
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "phone": "+12025551234",
        "city": "Seattle",
        "state": "WA",
        "country": "USA",
        "bio": "This is my updated bio",
        "emergency_contact": {
            "name": "Emergency Contact",
            "relationship": "Spouse",
            "phone": "+12025555678",
            "email": "emergency@example.com"
        }
    }

    update_response = requests.patch(
        f"{BASE_URL}/api/me/profile",
        headers=headers,
        json=update_data
    )

    if update_response.status_code != 200:
        print(f"   ✗ Profile update failed: {update_response.status_code}")
        print(f"   Response: {update_response.text}")
        return False

    update_result = update_response.json()
    print("   ✓ Profile updated successfully")
    print(f"   Message: {update_result.get('message')}")

    # Step 5: Verify the update persisted
    print("\n5. Verifying persistence...")
    verify_response = requests.get(
        f"{BASE_URL}/api/me",
        headers=headers
    )

    if verify_response.status_code != 200:
        print(f"   ✗ Failed to verify profile: {verify_response.status_code}")
        return False

    verified_profile = verify_response.json()

    # Check if updates persisted
    checks = [
        ("Name", verified_profile.get('name'), "Updated Name"),
        ("Email", verified_profile.get('email'), TEST_EMAIL),
    ]

    all_passed = True
    for field_name, actual, expected in checks:
        if actual == expected:
            print(f"   ✓ {field_name}: {actual}")
        else:
            print(f"   ✗ {field_name}: Expected '{expected}', got '{actual}'")
            all_passed = False

    # Step 6: Test photo upload (if endpoint exists)
    print("\n6. Testing photo upload...")

    # Create a small fake image
    fake_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'

    files = {
        'file': ('test-profile.png', fake_image, 'image/png')
    }

    photo_response = requests.post(
        f"{BASE_URL}/api/me/profile/photo",
        headers=headers,
        files=files
    )

    if photo_response.status_code == 200:
        photo_result = photo_response.json()
        print("   ✓ Photo uploaded successfully")
        print(f"   Photo URL: {photo_result.get('photo_url')}")
    elif photo_response.status_code == 404:
        print("   ℹ Photo upload endpoint not implemented")
    else:
        print(f"   ⚠ Photo upload returned: {photo_response.status_code}")
        print(f"   Response: {photo_response.text}")

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Profile updates are persisting correctly!")
    else:
        print("✗ SOME TESTS FAILED - Profile updates may not be persisting")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    try:
        success = test_profile_persistence()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
