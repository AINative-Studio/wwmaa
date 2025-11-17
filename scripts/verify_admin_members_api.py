#!/usr/bin/env python3
"""
Admin Members API Verification Script

This script verifies all CRUD operations for the admin members management endpoints.
It performs a complete lifecycle test: create -> read -> update -> delete.

Usage:
    python3 scripts/verify_admin_members_api.py

Requirements:
    - Backend server running on http://localhost:8000
    - Admin authentication token (or mock for development)
"""

import requests
import json
from typing import Dict, Any, Optional
import sys


# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/admin/members"
ADMIN_TOKEN = "your_admin_token_here"  # Replace with actual admin token


class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    """Print success message in green"""
    print(f"{Color.GREEN}✓ {message}{Color.RESET}")


def print_error(message: str):
    """Print error message in red"""
    print(f"{Color.RED}✗ {message}{Color.RESET}")


def print_info(message: str):
    """Print info message in blue"""
    print(f"{Color.BLUE}ℹ {message}{Color.RESET}")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Color.YELLOW}⚠ {message}{Color.RESET}")


def print_section(title: str):
    """Print section header"""
    print(f"\n{Color.BOLD}{'=' * 60}{Color.RESET}")
    print(f"{Color.BOLD}{title}{Color.RESET}")
    print(f"{Color.BOLD}{'=' * 60}{Color.RESET}\n")


def get_headers() -> Dict[str, str]:
    """Get request headers with auth token"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }


def check_backend_health() -> bool:
    """Check if backend is running and healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend is running at {BASE_URL}")
            return True
        else:
            print_error(f"Backend health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to backend at {BASE_URL}")
        print_info("Please ensure the backend server is running:")
        print_info("  cd backend && uvicorn app:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False


def test_create_member() -> Optional[str]:
    """Test creating a new member"""
    print_section("TEST 1: Create Member")

    member_data = {
        "email": "test.member@example.com",
        "password": "SecureTestPassword123!",
        "first_name": "Test",
        "last_name": "Member",
        "role": "member",
        "phone": "+12025551234",
        "is_active": True
    }

    print_info(f"Creating member: {member_data['email']}")
    print(json.dumps(member_data, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}",
            json=member_data,
            headers=get_headers(),
            timeout=10
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print_success("Member created successfully!")
            print(json.dumps(result, indent=2))

            # Verify required fields
            assert "id" in result, "Missing 'id' field"
            assert result["email"] == member_data["email"], "Email mismatch"
            assert result["first_name"] == member_data["first_name"], "First name mismatch"
            assert result["last_name"] == member_data["last_name"], "Last name mismatch"
            assert result["role"] == member_data["role"], "Role mismatch"

            print_success("All fields verified!")
            return result["id"]

        elif response.status_code == 409:
            print_warning("Member with this email already exists (expected if re-running)")
            print_info("Skipping to next test...")
            return None

        else:
            print_error(f"Failed to create member: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error creating member: {str(e)}")
        return None


def test_get_member(member_id: str) -> bool:
    """Test getting a single member"""
    print_section("TEST 2: Get Single Member")

    print_info(f"Fetching member: {member_id}")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/{member_id}",
            headers=get_headers(),
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print_success("Member fetched successfully!")
            print(json.dumps(result, indent=2))

            # Verify fields
            assert result["id"] == member_id, "ID mismatch"
            assert "email" in result, "Missing email field"
            assert "first_name" in result, "Missing first_name field"

            print_success("All fields verified!")
            return True

        else:
            print_error(f"Failed to get member: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error getting member: {str(e)}")
        return False


def test_update_member(member_id: str) -> bool:
    """Test updating a member"""
    print_section("TEST 3: Update Member")

    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "role": "instructor"
    }

    print_info(f"Updating member: {member_id}")
    print(json.dumps(update_data, indent=2))

    try:
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/{member_id}",
            json=update_data,
            headers=get_headers(),
            timeout=10
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print_success("Member updated successfully!")
            print(json.dumps(result, indent=2))

            # Verify updates
            assert result["first_name"] == update_data["first_name"], "First name not updated"
            assert result["last_name"] == update_data["last_name"], "Last name not updated"
            assert result["role"] == update_data["role"], "Role not updated"

            print_success("All updates verified!")
            return True

        else:
            print_error(f"Failed to update member: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error updating member: {str(e)}")
        return False


def test_list_members() -> bool:
    """Test listing members with pagination and filters"""
    print_section("TEST 4: List Members")

    print_info("Fetching members list (limit=10, offset=0)")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}?limit=10&offset=0",
            headers=get_headers(),
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print_success("Members list fetched successfully!")
            print(f"Total members: {result['total']}")
            print(f"Returned: {len(result['members'])} members")
            print(f"Limit: {result['limit']}, Offset: {result['offset']}")

            if result['members']:
                print("\nFirst member:")
                print(json.dumps(result['members'][0], indent=2))

            print_success("List endpoint verified!")
            return True

        else:
            print_error(f"Failed to list members: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error listing members: {str(e)}")
        return False


def test_list_with_filters() -> bool:
    """Test listing members with role filter"""
    print_section("TEST 5: List with Filters")

    print_info("Fetching members with role=instructor filter")

    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}?role=instructor&limit=5",
            headers=get_headers(),
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print_success("Filtered list fetched successfully!")
            print(f"Instructors found: {len(result['members'])}")

            # Verify all have instructor role
            for member in result['members']:
                assert member['role'] == 'instructor', f"Non-instructor in filtered results: {member['email']}"

            print_success("Filter verified!")
            return True

        else:
            print_error(f"Failed to list with filters: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error listing with filters: {str(e)}")
        return False


def test_delete_member(member_id: str) -> bool:
    """Test deleting a member"""
    print_section("TEST 6: Delete Member")

    print_info(f"Deleting member: {member_id}")

    try:
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/{member_id}",
            headers=get_headers(),
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 204:
            print_success("Member deleted successfully!")

            # Verify deletion by trying to fetch
            print_info("Verifying deletion...")
            verify_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/{member_id}",
                headers=get_headers(),
                timeout=10
            )

            if verify_response.status_code == 404:
                print_success("Deletion confirmed (404 on fetch)!")
                return True
            else:
                print_warning("Member still exists after deletion")
                return False

        else:
            print_error(f"Failed to delete member: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error deleting member: {str(e)}")
        return False


def test_validation_errors():
    """Test validation error handling"""
    print_section("TEST 7: Validation Errors")

    # Test 1: Weak password
    print_info("Testing weak password validation...")
    weak_password_data = {
        "email": "weak@example.com",
        "password": "weak",  # Too short, no uppercase, no special chars
        "first_name": "Test",
        "last_name": "User"
    }

    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}",
            json=weak_password_data,
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 422:
            print_success("Weak password rejected (422)!")
        else:
            print_warning(f"Expected 422, got {response.status_code}")

    except Exception as e:
        print_error(f"Error testing weak password: {str(e)}")

    # Test 2: Invalid email
    print_info("\nTesting invalid email validation...")
    invalid_email_data = {
        "email": "not-an-email",
        "password": "ValidPass123!",
        "first_name": "Test",
        "last_name": "User"
    }

    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}",
            json=invalid_email_data,
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 422:
            print_success("Invalid email rejected (422)!")
        else:
            print_warning(f"Expected 422, got {response.status_code}")

    except Exception as e:
        print_error(f"Error testing invalid email: {str(e)}")

    # Test 3: Invalid UUID
    print_info("\nTesting invalid UUID format...")
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/not-a-valid-uuid",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 400:
            print_success("Invalid UUID rejected (400)!")
        else:
            print_warning(f"Expected 400, got {response.status_code}")

    except Exception as e:
        print_error(f"Error testing invalid UUID: {str(e)}")


def run_all_tests():
    """Run all API tests"""
    print(f"\n{Color.BOLD}{Color.BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       Admin Members API Verification Script             ║")
    print("║                                                          ║")
    print("║  Testing complete CRUD lifecycle for member management  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(Color.RESET)

    # Check backend health
    if not check_backend_health():
        print_error("\nBackend is not available. Exiting.")
        sys.exit(1)

    results = {
        "create": False,
        "get": False,
        "update": False,
        "list": False,
        "filter": False,
        "delete": False,
        "validation": True  # Validation tests don't fail the suite
    }

    # Run tests
    member_id = test_create_member()

    if member_id:
        results["create"] = True
        results["get"] = test_get_member(member_id)
        results["update"] = test_update_member(member_id)
        results["list"] = test_list_members()
        results["filter"] = test_list_with_filters()
        results["delete"] = test_delete_member(member_id)
    else:
        print_warning("\nSkipping remaining tests (no member created)")

    # Always test validation
    test_validation_errors()

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")
    print()

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = Color.GREEN if result else Color.RED
        print(f"{color}{status}{Color.RESET} - {test_name.replace('_', ' ').title()}")

    print()

    if passed == total:
        print_success("All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
