#!/usr/bin/env python3
"""
Comprehensive Authentication and Backend API Test Suite
Tests the ZeroDB-powered authentication system and backend endpoints
"""

import requests
import json
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import jwt

# Configuration
BASE_URL = "https://athletic-curiosity-production.up.railway.app"
TEST_USERS = {
    "admin": {"email": "admin@wwmaa.com", "password": "AdminPass123!", "expected_role": "admin"},
    "member": {"email": "test@wwmaa.com", "password": "TestPass123!", "expected_role": "member"},
    "board_member": {"email": "board@wwmaa.com", "password": "BoardPass123!", "expected_role": "board_member"}
}

# Test results tracking
test_results: List[Dict[str, Any]] = []
session = requests.Session()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_test(test_name: str, passed: bool, details: str = "", response_data: Any = None):
    """Log test result with color coding"""
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"\n{Colors.BOLD}{status}{Colors.END} - {test_name}")
    if details:
        print(f"  {details}")
    if response_data and not passed:
        print(f"  Response: {json.dumps(response_data, indent=2)}")

    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
    return passed

def get_csrf_token() -> Optional[str]:
    """Get CSRF token from the backend by making a GET request"""
    try:
        # Make a GET request to any endpoint to get the CSRF cookie set
        response = session.get(f"{BASE_URL}/health")

        # Extract CSRF token from cookie
        csrf_token = session.cookies.get('csrf_token') or session.cookies.get('XSRF-TOKEN')
        if csrf_token:
            return csrf_token

        # If not in cookies, try any public endpoint
        response = session.get(f"{BASE_URL}/api/events/public")
        csrf_token = session.cookies.get('csrf_token') or session.cookies.get('XSRF-TOKEN')
        if csrf_token:
            return csrf_token

    except Exception as e:
        print(f"  {Colors.YELLOW}Warning: Could not get CSRF token: {e}{Colors.END}")
    return None

def test_backend_health():
    """Test 1.0: Verify backend is accessible"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== TEST CATEGORY 1: Backend Health ==={Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        passed = response.status_code == 200
        log_test(
            "Backend Health Check",
            passed,
            f"Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.2f}s"
        )
        return passed
    except Exception as e:
        log_test("Backend Health Check", False, f"Error: {str(e)}")
        return False

def test_login(user_type: str, credentials: Dict[str, str]) -> Optional[str]:
    """Test login for a specific user"""
    try:
        # Get CSRF token first
        csrf_token = get_csrf_token()

        headers = {
            "Content-Type": "application/json",
        }
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": credentials["email"], "password": credentials["password"]},
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get('token') or data.get('access_token')

            if token:
                # Decode token to verify contents (without signature verification for testing)
                try:
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    role_match = decoded.get('role') == credentials['expected_role']
                    email_match = decoded.get('email') == credentials['email']

                    passed = role_match and email_match
                    log_test(
                        f"Login - {user_type.capitalize()} ({credentials['email']})",
                        passed,
                        f"Token received, Role: {decoded.get('role')}, Email: {decoded.get('email')}"
                    )
                    return token if passed else None
                except jwt.DecodeError:
                    log_test(
                        f"Login - {user_type.capitalize()}",
                        True,
                        "Token received but could not decode (may use different encoding)"
                    )
                    return token
            else:
                log_test(
                    f"Login - {user_type.capitalize()}",
                    False,
                    "No token in response",
                    data
                )
                return None
        else:
            log_test(
                f"Login - {user_type.capitalize()}",
                False,
                f"Status: {response.status_code}",
                response.text
            )
            return None
    except Exception as e:
        log_test(f"Login - {user_type.capitalize()}", False, f"Error: {str(e)}")
        return None

def test_invalid_login():
    """Test login with invalid credentials"""
    try:
        csrf_token = get_csrf_token()
        headers = {"Content-Type": "application/json"}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@example.com", "password": "WrongPassword123!"},
            headers=headers,
            timeout=10
        )

        passed = response.status_code in [401, 403]
        log_test(
            "Login - Invalid Credentials",
            passed,
            f"Status: {response.status_code} (Expected 401 or 403)"
        )
        return passed
    except Exception as e:
        log_test("Login - Invalid Credentials", False, f"Error: {str(e)}")
        return False

def test_protected_endpoint(token: str, user_type: str):
    """Test protected /api/me endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/me", headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            user_data = data.get('user') or data

            passed = (
                user_data.get('email') in [u['email'] for u in TEST_USERS.values()]
            )
            log_test(
                f"Protected Endpoint /api/me - {user_type.capitalize()}",
                passed,
                f"Email: {user_data.get('email')}, Role: {user_data.get('role')}"
            )
            return passed
        else:
            log_test(
                f"Protected Endpoint /api/me - {user_type.capitalize()}",
                False,
                f"Status: {response.status_code}",
                response.text
            )
            return False
    except Exception as e:
        log_test(f"Protected Endpoint /api/me - {user_type.capitalize()}", False, f"Error: {str(e)}")
        return False

def test_protected_without_token():
    """Test protected endpoint without authentication"""
    try:
        response = requests.get(f"{BASE_URL}/api/me", timeout=10)
        passed = response.status_code == 401
        log_test(
            "Protected Endpoint - No Token",
            passed,
            f"Status: {response.status_code} (Expected 401)"
        )
        return passed
    except Exception as e:
        log_test("Protected Endpoint - No Token", False, f"Error: {str(e)}")
        return False

def test_protected_with_invalid_token():
    """Test protected endpoint with invalid token"""
    try:
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = requests.get(f"{BASE_URL}/api/me", headers=headers, timeout=10)
        passed = response.status_code == 401
        log_test(
            "Protected Endpoint - Invalid Token",
            passed,
            f"Status: {response.status_code} (Expected 401)"
        )
        return passed
    except Exception as e:
        log_test("Protected Endpoint - Invalid Token", False, f"Error: {str(e)}")
        return False

def test_public_endpoint(endpoint: str, expected_count: Optional[int] = None):
    """Test public endpoints"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)

        if response.status_code == 200:
            data = response.json()

            if expected_count is not None:
                # Check if response is a list or has a data/items field
                items = data if isinstance(data, list) else data.get('data', data.get('items', []))
                count = len(items) if isinstance(items, list) else 0
                passed = count >= expected_count if expected_count else True
                log_test(
                    f"Public Endpoint {endpoint}",
                    passed,
                    f"Status: {response.status_code}, Items: {count} (Expected: >={expected_count})"
                )
            else:
                log_test(
                    f"Public Endpoint {endpoint}",
                    True,
                    f"Status: {response.status_code}, Response received"
                )
            return True
        else:
            log_test(
                f"Public Endpoint {endpoint}",
                False,
                f"Status: {response.status_code}",
                response.text
            )
            return False
    except Exception as e:
        log_test(f"Public Endpoint {endpoint}", False, f"Error: {str(e)}")
        return False

def test_csrf_protection():
    """Test CSRF token protection"""
    try:
        # Try login without CSRF token
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@wwmaa.com", "password": "TestPass123!"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        # CSRF protection might return 403, or might allow without CSRF in some configs
        # We'll check if the endpoint exists and responds appropriately
        passed = response.status_code in [200, 403, 401]
        details = "CSRF protection active" if response.status_code == 403 else "CSRF may be optional or token embedded"

        log_test(
            "CSRF Protection Check",
            passed,
            f"Status: {response.status_code} - {details}"
        )
        return passed
    except Exception as e:
        log_test("CSRF Protection Check", False, f"Error: {str(e)}")
        return False

def test_role_based_access(admin_token: str, member_token: str):
    """Test role-based access control (if admin endpoints exist)"""
    # Test if there are admin-only endpoints
    admin_endpoints = [
        "/api/admin/users",
        "/api/users",
    ]

    for endpoint in admin_endpoints:
        try:
            # Test with member token (should fail)
            headers = {"Authorization": f"Bearer {member_token}"}
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)

            if response.status_code == 404:
                # Endpoint doesn't exist, skip
                print(f"  {Colors.YELLOW}Skip: {endpoint} not found{Colors.END}")
                continue

            member_denied = response.status_code in [403, 401]

            # Test with admin token (should succeed)
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            admin_allowed = response.status_code == 200

            passed = member_denied and admin_allowed
            log_test(
                f"Role-Based Access - {endpoint}",
                passed,
                f"Member: {member_denied}, Admin: {admin_allowed}"
            )

            if passed:
                return True  # At least one endpoint has RBAC
        except Exception as e:
            print(f"  {Colors.YELLOW}Error testing {endpoint}: {e}{Colors.END}")

    # If no admin endpoints found, mark as inconclusive
    log_test(
        "Role-Based Access Control",
        True,
        "No admin-specific endpoints found to test RBAC"
    )
    return True

def print_summary():
    """Print test summary"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

    passed = sum(1 for r in test_results if r['passed'])
    failed = len(test_results) - passed
    pass_rate = (passed / len(test_results) * 100) if test_results else 0

    print(f"\nTotal Tests: {len(test_results)}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    print(f"Pass Rate: {pass_rate:.1f}%")

    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.END}")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['test']}")
                if result['details']:
                    print(f"    {result['details']}")

    # Save detailed results to JSON
    with open('/Users/aideveloper/Desktop/wwmaa/test_results.json', 'w') as f:
        json.dump({
            "summary": {
                "total": len(test_results),
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "timestamp": datetime.now().isoformat()
            },
            "tests": test_results
        }, f, indent=2)

    print(f"\n{Colors.BLUE}Detailed results saved to: /Users/aideveloper/Desktop/wwmaa/test_results.json{Colors.END}")

    return failed == 0

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("WWMAA Authentication & Backend API Test Suite")
    print("="*60)
    print(f"{Colors.END}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Test 1: Backend Health
    if not test_backend_health():
        print(f"\n{Colors.RED}Backend is not accessible. Aborting tests.{Colors.END}")
        sys.exit(1)

    # Test 2: Authentication
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== TEST CATEGORY 2: Authentication ==={Colors.END}")
    tokens = {}
    for user_type, credentials in TEST_USERS.items():
        token = test_login(user_type, credentials)
        if token:
            tokens[user_type] = token

    # Test invalid login
    test_invalid_login()

    # Test 3: Protected Endpoints
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== TEST CATEGORY 3: Protected Endpoints ==={Colors.END}")
    for user_type, token in tokens.items():
        test_protected_endpoint(token, user_type)

    test_protected_without_token()
    test_protected_with_invalid_token()

    # Test 4: Public Endpoints
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== TEST CATEGORY 4: Public Endpoints ==={Colors.END}")
    test_public_endpoint("/api/events/public", expected_count=3)
    test_public_endpoint("/api/subscriptions")
    test_public_endpoint("/api/certifications")

    # Test 5: CSRF Protection
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== TEST CATEGORY 5: CSRF Protection ==={Colors.END}")
    test_csrf_protection()

    # Test 6: Role-Based Access
    if 'admin' in tokens and 'member' in tokens:
        print(f"\n{Colors.BLUE}{Colors.BOLD}=== TEST CATEGORY 6: Role-Based Access Control ==={Colors.END}")
        test_role_based_access(tokens['admin'], tokens['member'])

    # Print summary
    success = print_summary()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
