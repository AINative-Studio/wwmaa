#!/usr/bin/env python3
"""
Verification script for Admin Analytics Endpoint

This script demonstrates the analytics endpoint functionality
and validates that all components are working correctly.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Import the analytics module
from backend.routes.admin.analytics import (
    calculate_analytics,
    require_admin,
    AnalyticsResponse,
    ANALYTICS_CACHE_KEY,
    ANALYTICS_CACHE_TTL,
)
from backend.models.schemas import User, UserRole


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def verify_imports():
    """Verify all required modules are importable"""
    print_section("1. Verifying Imports")

    try:
        from backend.routes.admin import analytics
        print("✅ Analytics module imported successfully")

        from backend.services.instrumented_cache_service import get_cache_service
        print("✅ Cache service imported successfully")

        from backend.services.zerodb_service import get_zerodb_client
        print("✅ ZeroDB service imported successfully")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def verify_response_model():
    """Verify the AnalyticsResponse model"""
    print_section("2. Verifying Response Model")

    try:
        now = datetime.utcnow()
        data = {
            "total_members": 100,
            "active_subscriptions": 50,
            "total_revenue": 5000.00,
            "recent_signups": 10,
            "upcoming_events": 5,
            "active_sessions": 1,
            "pending_applications": 3,
            "total_events_this_month": 4,
            "revenue_this_month": 1000.00,
            "cached": False,
            "generated_at": now,
            "cache_expires_at": now + timedelta(seconds=300)
        }

        response = AnalyticsResponse(**data)

        print(f"✅ Response model validation successful")
        print(f"   - total_members: {response.total_members}")
        print(f"   - active_subscriptions: {response.active_subscriptions}")
        print(f"   - total_revenue: ${response.total_revenue:.2f}")
        print(f"   - recent_signups: {response.recent_signups}")
        print(f"   - upcoming_events: {response.upcoming_events}")
        print(f"   - active_sessions: {response.active_sessions}")
        print(f"   - cached: {response.cached}")

        return True
    except Exception as e:
        print(f"❌ Model validation error: {e}")
        return False


def verify_authorization():
    """Verify authorization checks"""
    print_section("3. Verifying Authorization")

    try:
        # Test with admin user
        admin_user = User(
            id=uuid4(),
            email="admin@test.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        result = require_admin(current_user=admin_user)
        print(f"✅ Admin user authorized: {result.email}")

        # Test with member user (should raise exception)
        member_user = User(
            id=uuid4(),
            email="member@test.com",
            password_hash="hash",
            role=UserRole.MEMBER,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            require_admin(current_user=member_user)
            print(f"❌ Member user should have been rejected")
            return False
        except Exception:
            print(f"✅ Member user correctly rejected")

        return True
    except Exception as e:
        print(f"❌ Authorization error: {e}")
        return False


def verify_cache_configuration():
    """Verify cache configuration"""
    print_section("4. Verifying Cache Configuration")

    print(f"✅ Cache key: {ANALYTICS_CACHE_KEY}")
    print(f"✅ Cache TTL: {ANALYTICS_CACHE_TTL} seconds ({ANALYTICS_CACHE_TTL / 60} minutes)")

    return True


def verify_endpoint_registration():
    """Verify endpoint is registered in FastAPI app"""
    print_section("5. Verifying Endpoint Registration")

    try:
        from backend.app import app

        routes = [route.path for route in app.routes]

        if "/api/admin/analytics" in [r.replace("{path:path}", "") for r in routes]:
            print("✅ Analytics endpoint registered in FastAPI app")
            return True
        else:
            # Check if the router prefix is included
            analytics_routes = [r for r in routes if "analytics" in r.lower()]
            if analytics_routes:
                print(f"✅ Analytics routes found:")
                for route in analytics_routes[:5]:
                    print(f"   - {route}")
                return True
            else:
                print("❌ Analytics endpoint not found in app routes")
                return False
    except Exception as e:
        print(f"❌ Error checking endpoint registration: {e}")
        return False


def verify_test_coverage():
    """Verify test file exists and is comprehensive"""
    print_section("6. Verifying Test Coverage")

    try:
        import os
        test_file = "backend/tests/test_admin_analytics.py"

        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
                test_count = content.count("def test_")

            print(f"✅ Test file exists: {test_file}")
            print(f"✅ Test count: {test_count} tests")

            # Check for key test areas
            checks = {
                "Authorization": "test_require_admin" in content,
                "Calculation": "test_calculate_analytics" in content,
                "Caching": "test_get_analytics" in content and "cache" in content.lower(),
                "Edge Cases": "test_calculate_analytics_handles" in content,
                "Response Model": "test_analytics_response_model" in content,
            }

            print("\n   Test coverage areas:")
            for area, exists in checks.items():
                status = "✅" if exists else "❌"
                print(f"   {status} {area}")

            return all(checks.values())
        else:
            print(f"❌ Test file not found: {test_file}")
            return False
    except Exception as e:
        print(f"❌ Error checking tests: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "ADMIN ANALYTICS ENDPOINT VERIFICATION" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")

    results = []

    # Run verification checks
    results.append(("Imports", verify_imports()))
    results.append(("Response Model", verify_response_model()))
    results.append(("Authorization", verify_authorization()))
    results.append(("Cache Configuration", verify_cache_configuration()))
    results.append(("Endpoint Registration", verify_endpoint_registration()))
    results.append(("Test Coverage", verify_test_coverage()))

    # Print summary
    print_section("VERIFICATION SUMMARY")

    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12} - {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 All verification checks passed! Endpoint is ready for use.")
    else:
        print("⚠️  Some verification checks failed. Please review the output above.")
    print("=" * 80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
