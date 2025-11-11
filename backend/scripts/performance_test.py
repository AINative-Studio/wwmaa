#!/usr/bin/env python3
"""
Performance Testing Script for WWMAA Backend

Tests key endpoints against SLO targets and generates performance reports.
Measures p50, p95, p99 latencies and compares against defined thresholds.

Usage:
    python backend/scripts/performance_test.py --base-url http://localhost:8000
    python backend/scripts/performance_test.py --base-url http://localhost:8000 --requests 1000
    python backend/scripts/performance_test.py --base-url http://localhost:8000 --endpoint /health
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx


class PerformanceTester:
    """Performance testing utility for API endpoints."""

    def __init__(self, base_url: str):
        """
        Initialize performance tester.

        Args:
            base_url: Base URL of the API to test
        """
        self.base_url = base_url.rstrip("/")
        self.results: Dict[str, List[float]] = {}

    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        num_requests: int = 100,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> List[float]:
        """
        Test an endpoint with multiple requests and measure latency.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Endpoint path
            num_requests: Number of requests to make
            headers: Optional headers to include
            json_data: Optional JSON data for POST requests

        Returns:
            List of response times in seconds
        """
        url = f"{self.base_url}{endpoint}"
        latencies = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\nTesting {method} {endpoint} with {num_requests} requests...")

            for i in range(num_requests):
                start_time = time.time()

                try:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=headers, json=json_data)
                    elif method.upper() == "PUT":
                        response = await client.put(url, headers=headers, json=json_data)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, headers=headers)
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    duration = time.time() - start_time
                    latencies.append(duration)

                    # Print progress every 10 requests
                    if (i + 1) % 10 == 0:
                        print(f"  Progress: {i + 1}/{num_requests} requests completed")

                    # Add small delay to avoid overwhelming the server
                    await asyncio.sleep(0.01)

                except Exception as e:
                    print(f"  Error on request {i + 1}: {e}")
                    continue

        self.results[f"{method} {endpoint}"] = latencies
        return latencies

    def calculate_percentiles(self, latencies: List[float]) -> Dict[str, float]:
        """
        Calculate latency percentiles.

        Args:
            latencies: List of latency measurements in seconds

        Returns:
            Dictionary with percentile values
        """
        if not latencies:
            return {"p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0, "avg": 0}

        sorted_latencies = sorted(latencies)
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": statistics.mean(latencies),
            "p50": statistics.quantiles(sorted_latencies, n=100)[49],
            "p95": statistics.quantiles(sorted_latencies, n=100)[94],
            "p99": statistics.quantiles(sorted_latencies, n=100)[98],
        }

    def check_slo_compliance(
        self, percentiles: Dict[str, float], slo_thresholds: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Check if performance meets SLO thresholds.

        Args:
            percentiles: Measured percentiles
            slo_thresholds: SLO threshold values

        Returns:
            Tuple of (compliant, violations) where violations is list of failure messages
        """
        violations = []

        for metric, threshold in slo_thresholds.items():
            if metric in percentiles and percentiles[metric] > threshold:
                violations.append(
                    f"  FAIL: {metric} = {percentiles[metric]:.3f}s "
                    f"(threshold: {threshold:.3f}s)"
                )

        return len(violations) == 0, violations

    def print_results(self, endpoint_key: str, latencies: List[float]):
        """
        Print formatted results for an endpoint.

        Args:
            endpoint_key: Endpoint identifier
            latencies: List of latency measurements
        """
        percentiles = self.calculate_percentiles(latencies)

        print(f"\n{'=' * 70}")
        print(f"Results for: {endpoint_key}")
        print(f"{'=' * 70}")
        print(f"Total Requests: {len(latencies)}")
        print(f"Min Latency:    {percentiles['min']*1000:.2f}ms")
        print(f"Max Latency:    {percentiles['max']*1000:.2f}ms")
        print(f"Avg Latency:    {percentiles['avg']*1000:.2f}ms")
        print(f"p50 Latency:    {percentiles['p50']*1000:.2f}ms")
        print(f"p95 Latency:    {percentiles['p95']*1000:.2f}ms")
        print(f"p99 Latency:    {percentiles['p99']*1000:.2f}ms")

    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Args:
            output_file: Optional file path to save JSON report

        Returns:
            Dictionary with complete report data
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "base_url": self.base_url,
            "endpoints": {},
            "summary": {"total_endpoints": len(self.results), "slo_compliant": 0},
        }

        # SLO thresholds for different endpoint categories
        slo_thresholds = {
            "public": {"p50": 0.2, "p95": 0.5, "p99": 1.0},
            "authenticated": {"p50": 0.3, "p95": 1.0, "p99": 2.0},
            "payment": {"p50": 0.5, "p95": 2.0, "p99": 5.0},
            "admin": {"p50": 0.5, "p95": 2.0, "p99": 5.0},
        }

        for endpoint_key, latencies in self.results.items():
            percentiles = self.calculate_percentiles(latencies)

            # Determine SLO category based on endpoint
            if "/admin" in endpoint_key:
                slo_category = "admin"
            elif any(
                path in endpoint_key for path in ["/payment", "/checkout", "/billing"]
            ):
                slo_category = "payment"
            elif any(path in endpoint_key for path in ["/api/", "/auth/"]):
                slo_category = "authenticated"
            else:
                slo_category = "public"

            thresholds = slo_thresholds[slo_category]
            compliant, violations = self.check_slo_compliance(percentiles, thresholds)

            if compliant:
                report["summary"]["slo_compliant"] += 1

            report["endpoints"][endpoint_key] = {
                "slo_category": slo_category,
                "total_requests": len(latencies),
                "percentiles": percentiles,
                "thresholds": thresholds,
                "compliant": compliant,
                "violations": violations,
            }

        # Calculate overall compliance percentage
        if report["summary"]["total_endpoints"] > 0:
            report["summary"]["compliance_percentage"] = (
                report["summary"]["slo_compliant"]
                / report["summary"]["total_endpoints"]
                * 100
            )
        else:
            report["summary"]["compliance_percentage"] = 0

        # Save to file if requested
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {output_file}")

        return report

    def print_summary_report(self):
        """Print summary of all test results."""
        print("\n" + "=" * 70)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 70)

        total_compliant = 0
        total_tests = len(self.results)

        for endpoint_key, latencies in self.results.items():
            self.print_results(endpoint_key, latencies)

            # Check SLO compliance
            percentiles = self.calculate_percentiles(latencies)

            # Simplified thresholds for summary
            if percentiles["p95"] <= 1.0:
                print("\n✓ SLO COMPLIANT")
                total_compliant += 1
            else:
                print("\n✗ SLO VIOLATION")

        print("\n" + "=" * 70)
        print(f"Overall Compliance: {total_compliant}/{total_tests} endpoints")
        print(
            f"Compliance Rate: {(total_compliant/total_tests*100) if total_tests > 0 else 0:.1f}%"
        )
        print("=" * 70)


async def main():
    """Main entry point for performance testing."""
    parser = argparse.ArgumentParser(
        description="Performance testing for WWMAA Backend API"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Number of requests per endpoint (default: 100)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Test specific endpoint only (e.g., /health)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for JSON report (e.g., performance_report.json)",
    )

    args = parser.parse_args()

    tester = PerformanceTester(args.base_url)

    print(f"Starting performance tests against: {args.base_url}")
    print(f"Requests per endpoint: {args.requests}")

    # Define endpoints to test
    endpoints_to_test = [
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/metrics/summary"),
    ]

    if args.endpoint:
        # Test specific endpoint only
        endpoints_to_test = [("GET", args.endpoint)]

    # Run tests
    for method, endpoint in endpoints_to_test:
        try:
            await tester.test_endpoint(method, endpoint, num_requests=args.requests)
        except Exception as e:
            print(f"\nError testing {method} {endpoint}: {e}")
            continue

    # Print results
    tester.print_summary_report()

    # Generate and save report
    report = tester.generate_report(output_file=args.output)

    # Exit with error code if not all endpoints are compliant
    if report["summary"]["compliance_percentage"] < 100:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
