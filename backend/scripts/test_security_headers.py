#!/usr/bin/env python3
"""
Security Headers Testing Script

This script tests the security headers configuration of the WWMAA backend API.
It verifies that all required security headers are present and have correct values.

Usage:
    python scripts/test_security_headers.py [--url URL] [--verbose]

Arguments:
    --url URL        Backend URL to test (default: http://localhost:8000)
    --verbose        Show detailed output

Features:
- Tests all required security headers
- Validates header values
- Checks CSP policy directives
- Provides security grade
- Generates recommendations

Example:
    # Test local development server
    python scripts/test_security_headers.py

    # Test staging environment
    python scripts/test_security_headers.py --url https://staging-api.wwmaa.com

    # Test with verbose output
    python scripts/test_security_headers.py --verbose
"""

import sys
import argparse
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class SecurityGrade(Enum):
    """Security grade enum."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class HeaderCheck:
    """Result of a security header check."""
    name: str
    present: bool
    value: str
    expected: str
    passed: bool
    message: str


@dataclass
class TestResult:
    """Overall test result."""
    url: str
    grade: SecurityGrade
    checks: List[HeaderCheck]
    warnings: List[str]
    recommendations: List[str]


class SecurityHeadersTester:
    """Test security headers configuration."""

    def __init__(self, url: str, verbose: bool = False):
        """
        Initialize the tester.

        Args:
            url: Backend URL to test
            verbose: Enable verbose output
        """
        self.url = url.rstrip("/")
        self.verbose = verbose
        self.checks: List[HeaderCheck] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def run_tests(self) -> TestResult:
        """
        Run all security header tests.

        Returns:
            TestResult with all check results
        """
        print(f"\n🔒 Testing Security Headers for: {self.url}\n")

        try:
            # Make request to test endpoint
            response = requests.get(f"{self.url}/health", timeout=10)

            if self.verbose:
                print(f"Status Code: {response.status_code}")
                print(f"Response Time: {response.elapsed.total_seconds():.3f}s\n")

            # Run all header checks
            self._check_hsts(response.headers)
            self._check_x_frame_options(response.headers)
            self._check_x_content_type_options(response.headers)
            self._check_referrer_policy(response.headers)
            self._check_permissions_policy(response.headers)
            self._check_csp(response.headers)
            self._check_x_xss_protection(response.headers)
            self._check_x_dns_prefetch_control(response.headers)

            # Calculate grade
            grade = self._calculate_grade()

            return TestResult(
                url=self.url,
                grade=grade,
                checks=self.checks,
                warnings=self.warnings,
                recommendations=self.recommendations
            )

        except requests.exceptions.ConnectionError:
            print(f"❌ ERROR: Could not connect to {self.url}")
            print("   Make sure the backend server is running.")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print(f"❌ ERROR: Request to {self.url} timed out")
            sys.exit(1)
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            sys.exit(1)

    def _check_hsts(self, headers: Dict[str, str]) -> None:
        """Check Strict-Transport-Security header."""
        header_name = "Strict-Transport-Security"
        value = headers.get(header_name, "")

        if not value:
            self.checks.append(HeaderCheck(
                name=header_name,
                present=False,
                value="",
                expected="max-age=31536000; includeSubDomains; preload",
                passed=False,
                message="HSTS header is missing"
            ))
            self.warnings.append("HSTS not configured - connections not forced to HTTPS")
            return

        # Check for required directives
        has_max_age = "max-age=" in value
        has_subdomains = "includeSubDomains" in value
        has_preload = "preload" in value

        # Extract max-age value
        max_age = None
        if has_max_age:
            try:
                max_age_str = value.split("max-age=")[1].split(";")[0].strip()
                max_age = int(max_age_str)
            except (IndexError, ValueError):
                pass

        passed = has_max_age and has_subdomains and has_preload and (max_age and max_age >= 31536000)

        message = "HSTS configured correctly" if passed else "HSTS configuration incomplete"
        if not has_preload:
            message += " (missing preload)"
        if max_age and max_age < 31536000:
            message += f" (max-age too short: {max_age})"

        self.checks.append(HeaderCheck(
            name=header_name,
            present=True,
            value=value,
            expected="max-age=31536000; includeSubDomains; preload",
            passed=passed,
            message=message
        ))

        if not passed:
            self.recommendations.append("Increase HSTS max-age to 31536000 (1 year) and add preload")

    def _check_x_frame_options(self, headers: Dict[str, str]) -> None:
        """Check X-Frame-Options header."""
        header_name = "X-Frame-Options"
        value = headers.get(header_name, "")
        expected = "DENY"

        passed = value == expected

        self.checks.append(HeaderCheck(
            name=header_name,
            present=bool(value),
            value=value,
            expected=expected,
            passed=passed,
            message="Clickjacking protection enabled" if passed else "Weak or missing clickjacking protection"
        ))

        if not passed:
            self.warnings.append("X-Frame-Options not set to DENY - vulnerable to clickjacking")

    def _check_x_content_type_options(self, headers: Dict[str, str]) -> None:
        """Check X-Content-Type-Options header."""
        header_name = "X-Content-Type-Options"
        value = headers.get(header_name, "")
        expected = "nosniff"

        passed = value == expected

        self.checks.append(HeaderCheck(
            name=header_name,
            present=bool(value),
            value=value,
            expected=expected,
            passed=passed,
            message="MIME sniffing disabled" if passed else "MIME sniffing not disabled"
        ))

        if not passed:
            self.warnings.append("MIME sniffing not disabled - potential security risk")

    def _check_referrer_policy(self, headers: Dict[str, str]) -> None:
        """Check Referrer-Policy header."""
        header_name = "Referrer-Policy"
        value = headers.get(header_name, "")
        expected = "strict-origin-when-cross-origin"

        passed = value == expected

        self.checks.append(HeaderCheck(
            name=header_name,
            present=bool(value),
            value=value,
            expected=expected,
            passed=passed,
            message="Referrer policy configured" if passed else "Referrer policy not configured"
        ))

        if not value:
            self.recommendations.append("Configure Referrer-Policy to control information leakage")

    def _check_permissions_policy(self, headers: Dict[str, str]) -> None:
        """Check Permissions-Policy header."""
        header_name = "Permissions-Policy"
        value = headers.get(header_name, "")

        if not value:
            self.checks.append(HeaderCheck(
                name=header_name,
                present=False,
                value="",
                expected="geolocation=(), microphone=(), camera=()...",
                passed=False,
                message="Permissions policy not configured"
            ))
            self.recommendations.append("Configure Permissions-Policy to restrict browser features")
            return

        # Check for important restrictions
        has_geolocation = "geolocation=()" in value
        has_microphone = "microphone=()" in value
        has_camera = "camera=()" in value

        passed = has_geolocation and has_microphone and has_camera

        self.checks.append(HeaderCheck(
            name=header_name,
            present=True,
            value=value[:100] + "..." if len(value) > 100 else value,
            expected="geolocation=(), microphone=(), camera=()...",
            passed=passed,
            message="Permissions policy configured" if passed else "Permissions policy incomplete"
        ))

    def _check_csp(self, headers: Dict[str, str]) -> None:
        """Check Content-Security-Policy header."""
        header_name = "Content-Security-Policy"
        value = headers.get(header_name, "")

        if not value:
            self.checks.append(HeaderCheck(
                name=header_name,
                present=False,
                value="",
                expected="default-src 'self'; script-src 'self'...",
                passed=False,
                message="CSP not configured - vulnerable to XSS"
            ))
            self.warnings.append("Content Security Policy not configured - HIGH RISK")
            return

        # Check for important directives
        has_default_src = "default-src" in value
        has_script_src = "script-src" in value
        has_object_src = "object-src" in value
        has_frame_ancestors = "frame-ancestors" in value

        # Check for unsafe directives (warnings, not failures)
        has_unsafe_inline = "'unsafe-inline'" in value
        has_unsafe_eval = "'unsafe-eval'" in value

        passed = has_default_src and has_script_src and has_object_src and has_frame_ancestors

        message = "CSP configured"
        if has_unsafe_inline:
            message += " (has unsafe-inline)"
            self.recommendations.append("Remove 'unsafe-inline' and use nonces for better security")
        if has_unsafe_eval:
            message += " (has unsafe-eval)"
            self.recommendations.append("Remove 'unsafe-eval' if possible")

        self.checks.append(HeaderCheck(
            name=header_name,
            present=True,
            value=value[:100] + "..." if len(value) > 100 else value,
            expected="default-src 'self'; script-src 'self'...",
            passed=passed,
            message=message
        ))

        if self.verbose:
            print(f"CSP Policy:\n{value}\n")

    def _check_x_xss_protection(self, headers: Dict[str, str]) -> None:
        """Check X-XSS-Protection header (legacy)."""
        header_name = "X-XSS-Protection"
        value = headers.get(header_name, "")
        expected = "1; mode=block"

        passed = value == expected

        self.checks.append(HeaderCheck(
            name=header_name,
            present=bool(value),
            value=value,
            expected=expected,
            passed=passed,
            message="Legacy XSS protection enabled" if passed else "Legacy XSS protection not configured"
        ))

    def _check_x_dns_prefetch_control(self, headers: Dict[str, str]) -> None:
        """Check X-DNS-Prefetch-Control header."""
        header_name = "X-DNS-Prefetch-Control"
        value = headers.get(header_name, "")
        expected = "off"

        passed = value == expected

        self.checks.append(HeaderCheck(
            name=header_name,
            present=bool(value),
            value=value,
            expected=expected,
            passed=passed,
            message="DNS prefetch disabled" if passed else "DNS prefetch not disabled"
        ))

    def _calculate_grade(self) -> SecurityGrade:
        """
        Calculate security grade based on checks.

        Returns:
            SecurityGrade enum value
        """
        total_checks = len(self.checks)
        passed_checks = sum(1 for check in self.checks if check.passed)
        critical_checks = ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options"]
        critical_passed = sum(1 for check in self.checks if check.name in critical_checks and check.passed)

        if total_checks == 0:
            return SecurityGrade.F

        pass_rate = passed_checks / total_checks

        # All critical checks must pass for A grade
        if critical_passed < len(critical_checks):
            if critical_passed == 0:
                return SecurityGrade.F
            elif pass_rate >= 0.7:
                return SecurityGrade.C
            else:
                return SecurityGrade.D

        # Grade based on pass rate
        if pass_rate >= 0.95:
            return SecurityGrade.A_PLUS
        elif pass_rate >= 0.85:
            return SecurityGrade.A
        elif pass_rate >= 0.75:
            return SecurityGrade.B
        elif pass_rate >= 0.65:
            return SecurityGrade.C
        elif pass_rate >= 0.50:
            return SecurityGrade.D
        else:
            return SecurityGrade.F

    def print_results(self, result: TestResult) -> None:
        """
        Print test results in a formatted way.

        Args:
            result: TestResult to print
        """
        print("\n" + "=" * 80)
        print(f"Security Headers Test Results - Grade: {result.grade.value}")
        print("=" * 80 + "\n")

        # Print checks
        passed = sum(1 for check in result.checks if check.passed)
        total = len(result.checks)

        print(f"Checks: {passed}/{total} passed\n")

        for check in result.checks:
            status = "✅" if check.passed else "❌"
            print(f"{status} {check.name}")
            if self.verbose or not check.passed:
                print(f"   Present: {'Yes' if check.present else 'No'}")
                if check.present:
                    print(f"   Value: {check.value}")
                print(f"   Expected: {check.expected}")
                print(f"   Message: {check.message}")
            print()

        # Print warnings
        if result.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in result.warnings:
                print(f"   - {warning}")

        # Print recommendations
        if result.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in result.recommendations:
                print(f"   - {rec}")

        # Print external testing tools
        print("\n🔍 EXTERNAL SECURITY TESTING TOOLS:")
        print(f"   - https://securityheaders.com/?q={result.url}")
        print(f"   - https://observatory.mozilla.org/analyze/{result.url.replace('http://', '').replace('https://', '')}")

        print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test security headers configuration of WWMAA backend"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend URL to test (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    # Create tester and run tests
    tester = SecurityHeadersTester(args.url, args.verbose)
    result = tester.run_tests()
    tester.print_results(result)

    # Exit with error code if grade is not A or A+
    if result.grade not in [SecurityGrade.A_PLUS, SecurityGrade.A]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
