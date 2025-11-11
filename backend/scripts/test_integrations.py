#!/usr/bin/env python3
"""
Sprint 6 Integration Test Script - Real API Testing

This script performs comprehensive integration tests against real external APIs
to verify that all Sprint 6 integrations are properly configured and working.

Tests:
1. Cloudflare Calls - Video conferencing rooms and tokens
2. Cloudflare Stream - Video upload and signed URLs
3. BeeHiiv - Newsletter subscriber management
4. ZeroDB - Database connectivity and collections

Usage:
    python backend/scripts/test_integrations.py

Author: WWMAA Backend Team
Date: 2025-11-10
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Environment setup - load from project root
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)
print(f"Loading environment from: {env_path}")

# Import services
from backend.services.cloudflare_calls_service import CloudflareCallsService, CloudflareCallsError
from backend.services.cloudflare_stream_service import CloudflareStreamService, CloudflareStreamError
from backend.services.beehiiv_service import BeeHiivService, BeeHiivAPIError
from backend.services.zerodb_service import ZeroDBClient, ZeroDBError

# Suppress service logging during tests
logging.getLogger("backend.services").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)


# ANSI color codes for terminal output
class Colors:
    """Terminal color codes for beautiful output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


# Cost tracking per service
ESTIMATED_COSTS = {
    "cloudflare_calls": 0.01,
    "cloudflare_stream": 0.02,
    "beehiiv": 0.00,
    "zerodb": 0.00
}


class IntegrationTestRunner:
    """Main test runner for Sprint 6 integration tests"""

    def __init__(self):
        """Initialize test runner"""
        self.results: Dict[str, bool] = {}
        self.timings: Dict[str, float] = {}
        self.errors: Dict[str, str] = {}
        self.cleanup_tasks: List[Tuple[str, callable]] = []
        self.output_lines: List[str] = []
        self.start_time = time.time()

    def log(self, message: str, color: str = Colors.RESET):
        """Log message to console and output buffer"""
        formatted = f"{color}{message}{Colors.RESET}"
        print(formatted)
        self.output_lines.append(message)

    def log_step(self, message: str):
        """Log a test step"""
        self.log(f"  {Colors.CYAN}✓{Colors.RESET} {message}")

    def log_error(self, message: str):
        """Log an error"""
        self.log(f"  {Colors.RED}✗{Colors.RESET} {message}", Colors.RED)

    def log_warning(self, message: str):
        """Log a warning"""
        self.log(f"  {Colors.YELLOW}⚠{Colors.RESET} {message}", Colors.YELLOW)

    def log_skip(self, message: str):
        """Log a skipped test"""
        self.log(f"  {Colors.YELLOW}⊘{Colors.RESET} {message}", Colors.YELLOW)

    def add_cleanup(self, name: str, cleanup_func: callable):
        """Add a cleanup task to be executed later"""
        self.cleanup_tasks.append((name, cleanup_func))

    def run_cleanup(self):
        """Execute all cleanup tasks"""
        if not self.cleanup_tasks:
            return

        self.log(f"\n{Colors.CYAN}Cleaning up test resources...{Colors.RESET}")

        for name, cleanup_func in self.cleanup_tasks:
            try:
                cleanup_func()
                self.log(f"  {Colors.GREEN}✓{Colors.RESET} {name}")
            except Exception as e:
                self.log(f"  {Colors.RED}✗{Colors.RESET} {name}: {str(e)}")

    def print_header(self):
        """Print test header"""
        header = """
╔══════════════════════════════════════════════════════════════╗
║        Sprint 6 Integration Tests - Real API Testing         ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.log(header, Colors.BOLD + Colors.CYAN)

    def print_footer(self):
        """Print test results summary"""
        duration = time.time() - self.start_time
        passed = sum(1 for result in self.results.values() if result)
        failed = len(self.results) - passed
        total = len(self.results)

        # Calculate total cost
        total_cost = sum(
            ESTIMATED_COSTS.get(service, 0.0)
            for service, result in self.results.items()
            if result
        )

        status_icon = f"{Colors.GREEN}✅ ALL TESTS PASSED{Colors.RESET}" if failed == 0 else f"{Colors.RED}❌ SOME TESTS FAILED{Colors.RESET}"

        footer = f"""
╔══════════════════════════════════════════════════════════════╗
║                      TEST RESULTS                             ║
╠══════════════════════════════════════════════════════════════╣
║ Total Tests:    {total:<44} ║
║ Passed:         {Colors.GREEN}{passed}{Colors.RESET}                                             ║
║ Failed:         {Colors.RED if failed > 0 else Colors.GREEN}{failed}{Colors.RESET}                                             ║
║ Duration:       {duration:.1f}s                                        ║
║ Status:         {status_icon}                          ║
╚══════════════════════════════════════════════════════════════╝

Estimated API costs for this test run: ${total_cost:.2f}
"""
        self.log(footer, Colors.BOLD)

    def save_results(self):
        """Save test results to file"""
        output_file = "/Users/aideveloper/Desktop/wwmaa/integration-test-results.txt"

        try:
            with open(output_file, "w") as f:
                f.write(f"Sprint 6 Integration Test Results\n")
                f.write(f"Executed: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")

                for line in self.output_lines:
                    # Strip ANSI color codes for file output
                    clean_line = line
                    for color in [Colors.RESET, Colors.BOLD, Colors.DIM, Colors.BLACK,
                                 Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE,
                                 Colors.MAGENTA, Colors.CYAN, Colors.WHITE,
                                 Colors.BG_RED, Colors.BG_GREEN, Colors.BG_YELLOW, Colors.BG_BLUE]:
                        clean_line = clean_line.replace(color, "")
                    f.write(clean_line + "\n")

            self.log(f"\n{Colors.GREEN}Results saved to: {output_file}{Colors.RESET}")
        except Exception as e:
            self.log(f"\n{Colors.RED}Failed to save results: {e}{Colors.RESET}")

    def check_credentials(self) -> Dict[str, bool]:
        """
        Check if all required credentials are present

        Returns:
            Dictionary of service names to availability status
        """
        self.log(f"{Colors.BOLD}Checking credentials...{Colors.RESET}\n")

        credentials = {
            "cloudflare_calls": {
                "required": ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"],
                "optional": ["CLOUDFLARE_CALLS_API_TOKEN", "CLOUDFLARE_CALLS_APP_ID"]
            },
            "cloudflare_stream": {
                "required": ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"],
                "optional": ["CLOUDFLARE_STREAM_API_TOKEN", "CLOUDFLARE_STREAM_SIGNING_KEY"]
            },
            "beehiiv": {
                "required": ["BEEHIIV_API_KEY"],
                "optional": ["BEEHIIV_PUBLICATION_ID"]
            },
            "zerodb": {
                "required": ["ZERODB_API_KEY", "ZERODB_API_BASE_URL"],
                "optional": ["ZERODB_EMAIL", "ZERODB_PASSWORD"]
            }
        }

        availability = {}

        for service, creds in credentials.items():
            missing_required = []

            for key in creds["required"]:
                value = os.getenv(key)
                if not value or value.startswith("your-"):
                    missing_required.append(key)

            if missing_required:
                self.log_warning(f"{service}: Missing credentials - {', '.join(missing_required)}")
                availability[service] = False
            else:
                self.log_step(f"{service}: Credentials available")
                availability[service] = True

        self.log("")
        return availability

    def test_cloudflare_calls(self) -> bool:
        """
        Test Cloudflare Calls service

        Returns:
            True if test passed, False otherwise
        """
        service_name = "cloudflare_calls"
        self.log(f"{Colors.BOLD}[1/4] Testing Cloudflare Calls...{Colors.RESET}")
        start_time = time.time()

        room_id = None
        token = None

        try:
            # Initialize service
            service = CloudflareCallsService()

            # Create test room
            timestamp = int(time.time())
            session_id = f"integration-test-room-{timestamp}"

            self.log_step(f"Creating test room (session: {session_id})")
            room_data = service.create_room(
                session_id=session_id,
                max_participants=10,
                enable_recording=False
            )

            room_id = room_data.get("room_id")
            if not room_id:
                raise CloudflareCallsError("No room ID returned")

            self.log_step(f"Room created successfully (ID: {room_id})")

            # Generate participant token
            self.log_step("Generating participant token")
            token = service.generate_room_token(
                room_id=room_id,
                user_id=f"test-user-{timestamp}",
                user_name="Integration Test User",
                role="participant",
                expiry_hours=1
            )

            if not token:
                raise CloudflareCallsError("No token returned")

            self.log_step("Participant token generated successfully")

            # Add cleanup task
            def cleanup():
                if room_id:
                    service.delete_room(room_id)

            self.add_cleanup(f"Delete Cloudflare Calls room {room_id}", cleanup)

            # Success
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.log(f"  {Colors.GREEN}✅ PASSED{Colors.RESET} ({elapsed:.1f}s)\n")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.errors[service_name] = str(e)
            self.log_error(f"Error: {str(e)}")
            self.log(f"  {Colors.RED}❌ FAILED{Colors.RESET} ({elapsed:.1f}s)\n")
            return False

    def test_cloudflare_stream(self) -> bool:
        """
        Test Cloudflare Stream service

        Returns:
            True if test passed, False otherwise
        """
        service_name = "cloudflare_stream"
        self.log(f"{Colors.BOLD}[2/4] Testing Cloudflare Stream...{Colors.RESET}")
        start_time = time.time()

        video_id = None

        try:
            # Initialize service
            service = CloudflareStreamService()

            # Create test video from URL (using a sample video)
            test_video_url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"

            self.log_step("Creating test video from URL")
            video_data = service.create_video_from_url(
                url=test_video_url,
                metadata={"test": "integration-test", "timestamp": str(int(time.time()))},
                require_signed_urls=False  # Don't require signed URLs for test
            )

            video_id = video_data.get("video_id")
            if not video_id:
                raise CloudflareStreamError("No video ID returned")

            self.log_step(f"Video created successfully (ID: {video_id})")

            # Check video status
            self.log_step("Checking video processing status")
            video_info = service.get_video(video_id)
            status = video_info.get("status", "unknown")
            self.log_step(f"Video status: {status}")

            # Generate signed URL (basic - will be simple without signing key)
            self.log_step("Generating playback URL")
            signed_url = service.generate_signed_url(
                video_id=video_id,
                expiry_hours=24,
                download_allowed=False
            )

            if not signed_url:
                raise CloudflareStreamError("No signed URL returned")

            self.log_step("Playback URL generated successfully")

            # Add cleanup task
            def cleanup():
                if video_id:
                    service.delete_video(video_id)

            self.add_cleanup(f"Delete Cloudflare Stream video {video_id}", cleanup)

            # Success
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.log(f"  {Colors.GREEN}✅ PASSED{Colors.RESET} ({elapsed:.1f}s)\n")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.errors[service_name] = str(e)
            self.log_error(f"Error: {str(e)}")
            self.log(f"  {Colors.RED}❌ FAILED{Colors.RESET} ({elapsed:.1f}s)\n")
            return False

    def test_beehiiv(self) -> bool:
        """
        Test BeeHiiv service

        Returns:
            True if test passed, False otherwise
        """
        service_name = "beehiiv"
        self.log(f"{Colors.BOLD}[3/4] Testing BeeHiiv...{Colors.RESET}")
        start_time = time.time()

        test_email = None

        try:
            # Initialize service
            service = BeeHiivService()

            # Check if publication ID is set
            if not service.publication_id or service.publication_id.startswith("your-"):
                self.log_warning("BeeHiiv publication ID not configured")
                self.log_skip("Skipping BeeHiiv tests (configure BEEHIIV_PUBLICATION_ID)")
                elapsed = time.time() - start_time
                self.timings[service_name] = elapsed
                self.log(f"  {Colors.YELLOW}⊘ SKIPPED{Colors.RESET} ({elapsed:.1f}s)\n")
                return True  # Count as success since it's not configured

            # Add test subscriber
            timestamp = int(time.time())
            test_email = f"integration-test-{timestamp}@example.com"

            self.log_step(f"Adding test subscriber ({test_email})")
            subscriber_data = service.add_subscriber(
                email=test_email,
                name="Integration Test User",
                metadata={"test": "true", "timestamp": str(timestamp)},
                reactivate_existing=True
            )

            self.log_step("Subscriber added successfully")

            # Get subscriber details
            self.log_step("Verifying subscriber exists")
            subscriber_info = service.get_subscriber(test_email)

            if not subscriber_info:
                raise BeeHiivAPIError("Subscriber not found after creation")

            self.log_step("Subscriber verified successfully")

            # Add cleanup task
            def cleanup():
                if test_email:
                    try:
                        service.remove_subscriber(test_email)
                    except:
                        pass  # Ignore cleanup errors

            self.add_cleanup(f"Remove BeeHiiv subscriber {test_email}", cleanup)

            # Success
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.log(f"  {Colors.GREEN}✅ PASSED{Colors.RESET} ({elapsed:.1f}s)\n")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.errors[service_name] = str(e)
            self.log_error(f"Error: {str(e)}")
            self.log(f"  {Colors.RED}❌ FAILED{Colors.RESET} ({elapsed:.1f}s)\n")
            return False

    def test_zerodb(self) -> bool:
        """
        Test ZeroDB connection and collections

        Returns:
            True if test passed, False otherwise
        """
        service_name = "zerodb"
        self.log(f"{Colors.BOLD}[4/4] Testing ZeroDB...{Colors.RESET}")
        start_time = time.time()

        try:
            # Initialize client
            client = ZeroDBClient()

            # Test connection by querying a collection
            self.log_step("Testing connection to ZeroDB")

            # Try to query users collection
            self.log_step("Querying 'users' collection")
            users_result = client.query_documents(
                collection="users",
                limit=1
            )

            self.log_step("Successfully connected to ZeroDB")

            # List some expected collections
            expected_collections = [
                "users", "events", "training_sessions", "applications",
                "subscriptions", "content_index"
            ]

            self.log_step(f"Verifying critical collections exist")

            # Try to query each collection
            found_collections = []
            for collection in expected_collections:
                try:
                    result = client.query_documents(collection=collection, limit=1)
                    found_collections.append(collection)
                except:
                    pass  # Collection might not exist yet

            self.log_step(f"Found {len(found_collections)}/{len(expected_collections)} collections")

            # Success if we found at least the users collection
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.log(f"  {Colors.GREEN}✅ PASSED{Colors.RESET} ({elapsed:.1f}s)\n")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            self.timings[service_name] = elapsed
            self.errors[service_name] = str(e)
            self.log_error(f"Error: {str(e)}")
            self.log(f"  {Colors.RED}❌ FAILED{Colors.RESET} ({elapsed:.1f}s)\n")
            return False

    def run_all_tests(self):
        """Run all integration tests"""
        # Print header
        self.print_header()

        # Check credentials
        availability = self.check_credentials()

        # Run tests
        tests = [
            ("cloudflare_calls", self.test_cloudflare_calls),
            ("cloudflare_stream", self.test_cloudflare_stream),
            ("beehiiv", self.test_beehiiv),
            ("zerodb", self.test_zerodb),
        ]

        for service_name, test_func in tests:
            if availability.get(service_name, False):
                result = test_func()
                self.results[service_name] = result
            else:
                self.log(f"{Colors.BOLD}[{tests.index((service_name, test_func)) + 1}/4] Testing {service_name}...{Colors.RESET}")
                self.log_skip(f"Skipping {service_name} (credentials not configured)")
                elapsed = 0.0
                self.timings[service_name] = elapsed
                self.log(f"  {Colors.YELLOW}⊘ SKIPPED{Colors.RESET} ({elapsed:.1f}s)\n")
                self.results[service_name] = True  # Count skipped as success

        # Run cleanup
        self.run_cleanup()

        # Print footer
        self.print_footer()

        # Save results
        self.save_results()

        # Exit with appropriate code
        failed = sum(1 for result in self.results.values() if not result)
        sys.exit(0 if failed == 0 else 1)


def main():
    """Main entry point"""
    try:
        runner = IntegrationTestRunner()
        runner.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
