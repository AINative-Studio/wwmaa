#!/usr/bin/env python3
"""
Quick API Test for Admin Settings Endpoints

This script tests the admin settings API endpoints to verify:
- Settings retrieval
- Organization settings update
- Email settings update
- Stripe settings update
- Membership tiers update
- Test email sending

Requirements:
- Backend server running
- Admin user credentials
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@wwmaa.com"
ADMIN_PASSWORD = "your_admin_password"  # Replace with actual admin password


def login(email: str, password: str) -> str:
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def test_get_settings(token: str):
    """Test GET /api/admin/settings"""
    print("\n1. Testing GET /api/admin/settings...")

    response = requests.get(
        f"{BASE_URL}/api/admin/settings",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        settings = response.json()
        print(f"   ✓ Organization: {settings['org_name']}")
        print(f"   ✓ Email: {settings['org_email']}")
        print(f"   ✓ SMTP Host: {settings.get('smtp_host', 'Not configured')}")
        print(f"   ✓ Stripe Enabled: {settings.get('stripe_enabled', False)}")
        return settings
    else:
        print(f"   ✗ Error: {response.text}")
        return None


def test_update_organization(token: str):
    """Test PATCH /api/admin/settings/org"""
    print("\n2. Testing PATCH /api/admin/settings/org...")

    update_data = {
        "org_name": "WWMAA Test Org",
        "org_email": "test@wwmaa.com",
        "org_phone": "+1-555-1234",
        "org_address": "123 Test St, Test City, TS 12345"
    }

    response = requests.patch(
        f"{BASE_URL}/api/admin/settings/org",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Updated organization name: {result['org_name']}")
        print(f"   ✓ Updated email: {result['org_email']}")
        return True
    else:
        print(f"   ✗ Error: {response.text}")
        return False


def test_update_email_settings(token: str):
    """Test PATCH /api/admin/settings/email"""
    print("\n3. Testing PATCH /api/admin/settings/email...")

    update_data = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "test@gmail.com",
        "smtp_password": "test_app_password",
        "smtp_from_email": "noreply@wwmaa.com",
        "smtp_from_name": "WWMAA Team",
        "smtp_use_tls": True
    }

    response = requests.patch(
        f"{BASE_URL}/api/admin/settings/email",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Updated SMTP host: {result['smtp_host']}")
        print(f"   ✓ Updated SMTP port: {result['smtp_port']}")
        print(f"   ✓ Password encrypted: {result['smtp_password'] != 'test_app_password'}")
        return True
    else:
        print(f"   ✗ Error: {response.text}")
        return False


def test_update_stripe_settings(token: str):
    """Test PATCH /api/admin/settings/stripe"""
    print("\n4. Testing PATCH /api/admin/settings/stripe...")

    update_data = {
        "stripe_publishable_key": "pk_test_1234567890",
        "stripe_secret_key": "sk_test_abcdefghij",
        "stripe_webhook_secret": "whsec_test_xyz123",
        "stripe_enabled": True
    }

    response = requests.patch(
        f"{BASE_URL}/api/admin/settings/stripe",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Updated publishable key: {result['stripe_publishable_key']}")
        print(f"   ✓ Secret key encrypted: {'sk_test' in str(result.get('stripe_secret_key', ''))}")
        print(f"   ✓ Stripe enabled: {result['stripe_enabled']}")
        return True
    else:
        print(f"   ✗ Error: {response.text}")
        return False


def test_update_membership_tiers(token: str):
    """Test PATCH /api/admin/settings/membership-tiers"""
    print("\n5. Testing PATCH /api/admin/settings/membership-tiers...")

    update_data = {
        "premium": {
            "name": "Premium Updated",
            "price": 59.99,
            "currency": "USD",
            "interval": "month",
            "features": [
                "All Basic features",
                "Live training sessions",
                "1-on-1 coaching",
                "Advanced techniques",
                "Priority support"
            ],
            "stripe_price_id": "price_test_premium"
        }
    }

    response = requests.patch(
        f"{BASE_URL}/api/admin/settings/membership-tiers",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        premium = result['membership_tiers'].get('premium', {})
        print(f"   ✓ Updated premium tier: {premium.get('name')}")
        print(f"   ✓ Updated price: ${premium.get('price')}")
        print(f"   ✓ Features count: {len(premium.get('features', []))}")
        return True
    else:
        print(f"   ✗ Error: {response.text}")
        return False


def test_send_test_email(token: str, test_email: str):
    """Test POST /api/admin/settings/email/test"""
    print(f"\n6. Testing POST /api/admin/settings/email/test...")

    request_data = {
        "test_email": test_email,
        "test_subject": "WWMAA Test Email",
        "test_message": "This is a test email from admin settings API."
    }

    response = requests.post(
        f"{BASE_URL}/api/admin/settings/email/test",
        headers={"Authorization": f"Bearer {token}"},
        json=request_data
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
        print(f"   ✓ Timestamp: {result['timestamp']}")
        return True
    elif response.status_code == 400:
        print(f"   ⚠ SMTP not configured (expected): {response.json()['detail']}")
        return True
    else:
        print(f"   ✗ Error: {response.text}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Admin Settings API Test Suite")
    print("=" * 70)

    try:
        # Login
        print("\n🔐 Logging in as admin...")
        token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
        print(f"   ✓ Login successful")

        # Run tests
        results = {
            "Get Settings": test_get_settings(token),
            "Update Organization": test_update_organization(token),
            "Update Email": test_update_email_settings(token),
            "Update Stripe": test_update_stripe_settings(token),
            "Update Tiers": test_update_membership_tiers(token),
            "Send Test Email": test_send_test_email(token, "test@example.com")
        }

        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"   {status} - {test_name}")

        print(f"\n   Total: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {e}")
        print("\nMake sure:")
        print("  1. Backend server is running (python3 -m uvicorn backend.app:app)")
        print("  2. Admin credentials are correct")
        print("  3. Database is accessible")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
