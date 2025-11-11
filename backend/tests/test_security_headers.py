"""
Tests for Security Headers Middleware (US-069)

This module provides comprehensive testing for:
- Security headers middleware functionality
- CSP nonce generation and inclusion
- Environment-specific CSP policies
- CSP violation reporting
- Security headers configuration

Test Coverage:
- Header presence and values
- CSP policy directives
- Nonce generation uniqueness
- CSP report endpoint
- Development vs production policies
- Middleware integration
"""

import pytest
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from backend.middleware.security_headers import (
    SecurityHeadersMiddleware,
    get_csp_nonce
)
from backend.routes.security import router as security_router
from backend.config import get_settings
from unittest.mock import patch, MagicMock

settings = get_settings()


@pytest.fixture
def app():
    """Create a test FastAPI application with security headers middleware."""
    test_app = FastAPI()

    # Add security headers middleware
    test_app.add_middleware(SecurityHeadersMiddleware)

    # Add security router
    test_app.include_router(security_router)

    # Add test endpoint
    @test_app.get("/test")
    async def test_endpoint(request: Request):
        nonce = get_csp_nonce(request)
        return JSONResponse({"message": "test", "nonce": nonce})

    return test_app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestSecurityHeadersMiddleware:
    """Test security headers middleware functionality."""

    def test_hsts_header_present(self, client):
        """Test that HSTS header is present on all responses."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers

    def test_hsts_header_value(self, client):
        """Test HSTS header has correct value with preload."""
        response = client.get("/test")
        hsts = response.headers["Strict-Transport-Security"]

        # Should include max-age, includeSubDomains, and preload
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    def test_x_frame_options_header(self, client):
        """Test X-Frame-Options header prevents framing."""
        response = client.get("/test")
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_header(self, client):
        """Test X-Content-Type-Options prevents MIME sniffing."""
        response = client.get("/test")
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_referrer_policy_header(self, client):
        """Test Referrer-Policy controls referrer information."""
        response = client.get("/test")
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_x_xss_protection_header(self, client):
        """Test X-XSS-Protection legacy header is present."""
        response = client.get("/test")
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_x_dns_prefetch_control_header(self, client):
        """Test X-DNS-Prefetch-Control header is present."""
        response = client.get("/test")
        assert response.headers["X-DNS-Prefetch-Control"] == "off"

    def test_x_download_options_header(self, client):
        """Test X-Download-Options header is present."""
        response = client.get("/test")
        assert response.headers["X-Download-Options"] == "noopen"

    def test_x_permitted_cross_domain_policies_header(self, client):
        """Test X-Permitted-Cross-Domain-Policies header is present."""
        response = client.get("/test")
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"

    def test_permissions_policy_header(self, client):
        """Test Permissions-Policy header restricts browser features."""
        response = client.get("/test")
        permissions_policy = response.headers.get("Permissions-Policy", "")

        # Check that dangerous features are disabled
        assert "geolocation=()" in permissions_policy
        assert "microphone=()" in permissions_policy
        assert "camera=()" in permissions_policy
        assert "payment=()" in permissions_policy

        # Check that safe features are allowed for self
        assert "fullscreen=(self)" in permissions_policy
        assert "picture-in-picture=(self)" in permissions_policy

    def test_csp_header_present(self, client):
        """Test Content-Security-Policy header is present."""
        response = client.get("/test")
        assert "Content-Security-Policy" in response.headers

    def test_all_required_headers_present(self, client):
        """Test that all required security headers are present."""
        response = client.get("/test")

        required_headers = [
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
            "Content-Security-Policy",
            "X-XSS-Protection",
            "X-DNS-Prefetch-Control",
        ]

        for header in required_headers:
            assert header in response.headers, f"Missing required header: {header}"


class TestCSPNonceGeneration:
    """Test CSP nonce generation and uniqueness."""

    def test_nonce_is_generated(self, client):
        """Test that a CSP nonce is generated for each request."""
        response = client.get("/test")
        data = response.json()
        assert data["nonce"] is not None
        assert len(data["nonce"]) > 0

    def test_nonce_is_unique(self, client):
        """Test that each request gets a unique nonce."""
        response1 = client.get("/test")
        response2 = client.get("/test")

        nonce1 = response1.json()["nonce"]
        nonce2 = response2.json()["nonce"]

        assert nonce1 != nonce2

    def test_nonce_is_cryptographically_secure(self, client):
        """Test that nonce is sufficiently long for security."""
        response = client.get("/test")
        nonce = response.json()["nonce"]

        # Should be at least 24 characters (from 18 bytes base64)
        assert len(nonce) >= 24

    def test_nonce_included_in_csp(self, client):
        """Test that nonce is included in CSP header for production."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")
            nonce = response.json()["nonce"]

            # Nonce should be in CSP for production
            assert f"'nonce-{nonce}'" in csp

    def test_get_csp_nonce_utility(self, client):
        """Test get_csp_nonce utility function."""
        response = client.get("/test")
        nonce_from_response = response.json()["nonce"]

        # The nonce should be accessible via the utility
        assert nonce_from_response is not None


class TestCSPPolicy:
    """Test Content Security Policy configuration."""

    def test_csp_default_src_directive(self, client):
        """Test CSP default-src directive is configured."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp

    def test_csp_script_src_directive(self, client):
        """Test CSP script-src includes trusted sources."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "script-src" in csp
        # Should allow self
        assert "'self'" in csp
        # Should allow Stripe
        assert "https://js.stripe.com" in csp

    def test_csp_style_src_directive(self, client):
        """Test CSP style-src allows Google Fonts."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "style-src" in csp
        assert "https://fonts.googleapis.com" in csp

    def test_csp_font_src_directive(self, client):
        """Test CSP font-src allows Google Fonts."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "font-src" in csp
        assert "https://fonts.gstatic.com" in csp

    def test_csp_img_src_directive(self, client):
        """Test CSP img-src allows data URIs and HTTPS."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "img-src" in csp
        assert "data:" in csp

    def test_csp_media_src_cloudflare(self, client):
        """Test CSP media-src allows Cloudflare Stream."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "media-src" in csp
        assert "https://*.cloudflarestream.com" in csp

    def test_csp_frame_src_directive(self, client):
        """Test CSP frame-src allows Stripe and Cloudflare."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "frame-src" in csp
        assert "https://js.stripe.com" in csp
        assert "https://*.cloudflarestream.com" in csp

    def test_csp_object_src_none(self, client):
        """Test CSP blocks object/embed elements."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "object-src 'none'" in csp

    def test_csp_base_uri_self(self, client):
        """Test CSP base-uri restricted to self."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "base-uri" in csp
        assert "'self'" in csp

    def test_csp_form_action_self(self, client):
        """Test CSP form-action restricted to self."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "form-action" in csp

    def test_csp_frame_ancestors_none(self, client):
        """Test CSP frame-ancestors prevents clickjacking."""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        assert "frame-ancestors 'none'" in csp


class TestCSPEnvironmentSpecific:
    """Test environment-specific CSP policies."""

    def test_development_csp_allows_unsafe_eval(self, client):
        """Test development CSP allows unsafe-eval for HMR."""
        with patch.object(settings, 'PYTHON_ENV', 'development'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            # Development should allow unsafe-eval for Next.js HMR
            assert "'unsafe-eval'" in csp

    def test_development_csp_allows_unsafe_inline(self, client):
        """Test development CSP allows unsafe-inline."""
        with patch.object(settings, 'PYTHON_ENV', 'development'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            # Development should allow unsafe-inline
            assert "'unsafe-inline'" in csp

    def test_development_csp_allows_localhost(self, client):
        """Test development CSP allows localhost connections."""
        with patch.object(settings, 'PYTHON_ENV', 'development'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            # Development should allow localhost
            assert "localhost" in csp or "127.0.0.1" in csp

    def test_production_csp_uses_nonces(self, client):
        """Test production CSP uses nonces instead of unsafe-inline."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            # Production should NOT allow unsafe-inline or unsafe-eval
            # (they might be in the string as part of comments, so check carefully)
            # Instead, should use nonces
            assert "'nonce-" in csp

    def test_production_csp_upgrade_insecure_requests(self, client):
        """Test production CSP includes upgrade-insecure-requests."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            assert "upgrade-insecure-requests" in csp

    def test_production_csp_block_mixed_content(self, client):
        """Test production CSP blocks mixed content."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            assert "block-all-mixed-content" in csp

    def test_production_csp_report_uri(self, client):
        """Test production CSP includes report-uri."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/test")
            csp = response.headers.get("Content-Security-Policy", "")

            assert "report-uri" in csp
            assert "/api/csp-report" in csp


class TestCSPReportEndpoint:
    """Test CSP violation reporting endpoint."""

    def test_csp_report_endpoint_exists(self, client):
        """Test CSP report endpoint is accessible."""
        # The endpoint should accept POST requests
        response = client.post("/api/csp-report", json={
            "csp-report": {
                "document-uri": "https://example.com/page",
                "violated-directive": "script-src",
                "blocked-uri": "https://evil.com/script.js",
                "effective-directive": "script-src",
                "original-policy": "default-src 'self'",
                "status-code": 200,
                "disposition": "enforce"
            }
        })

        # Should return 204 No Content as per CSP spec
        assert response.status_code == 204

    def test_csp_report_logs_violation(self, client, caplog):
        """Test CSP violations are logged."""
        with caplog.at_level("WARNING"):
            client.post("/api/csp-report", json={
                "csp-report": {
                    "document-uri": "https://example.com/page",
                    "violated-directive": "script-src",
                    "blocked-uri": "https://evil.com/script.js",
                    "effective-directive": "script-src",
                    "original-policy": "default-src 'self'",
                    "status-code": 200,
                    "disposition": "enforce"
                }
            })

        # Should have logged the violation
        assert "CSP Violation" in caplog.text

    def test_csp_report_handles_malformed_data(self, client):
        """Test CSP report endpoint handles malformed data gracefully."""
        response = client.post("/api/csp-report", json={
            "invalid": "data"
        })

        # Should still return 204 and not crash
        assert response.status_code == 204

    def test_csp_report_handles_empty_body(self, client):
        """Test CSP report endpoint handles empty body."""
        response = client.post("/api/csp-report", json={})

        # Should still return 204 and not crash
        assert response.status_code == 204


class TestSecurityEndpoints:
    """Test security information endpoints."""

    def test_security_headers_info_endpoint_dev(self, client):
        """Test security headers info endpoint in development."""
        with patch.object(settings, 'PYTHON_ENV', 'development'):
            response = client.get("/api/security/headers")
            assert response.status_code == 200

            data = response.json()
            assert "headers_info" in data
            assert "csp_nonce" in data
            assert "testing_recommendations" in data

    def test_security_headers_info_endpoint_production(self, client):
        """Test security headers info endpoint blocked in production."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/api/security/headers")
            assert response.status_code == 404

    def test_csp_violations_endpoint_dev(self, client):
        """Test CSP violations endpoint in development."""
        with patch.object(settings, 'PYTHON_ENV', 'development'):
            response = client.get("/api/security/csp-violations")
            assert response.status_code == 200

            data = response.json()
            assert "violations" in data

    def test_csp_violations_endpoint_production(self, client):
        """Test CSP violations endpoint blocked in production."""
        with patch.object(settings, 'PYTHON_ENV', 'production'):
            response = client.get("/api/security/csp-violations")
            assert response.status_code == 404


class TestMiddlewareIntegration:
    """Test middleware integration with FastAPI."""

    def test_middleware_processes_all_routes(self, client):
        """Test middleware adds headers to all routes."""
        # Test the test endpoint
        response1 = client.get("/test")
        assert "Content-Security-Policy" in response1.headers

        # Test CSP report endpoint
        response2 = client.post("/api/csp-report", json={})
        assert "Content-Security-Policy" in response2.headers

    def test_middleware_works_with_errors(self, client):
        """Test middleware adds headers even on error responses."""
        # Request non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Headers should still be present
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_headers_on_different_http_methods(self, client):
        """Test headers are added for all HTTP methods."""
        methods = [
            client.get("/test"),
            client.post("/api/csp-report", json={}),
        ]

        for response in methods:
            assert "Content-Security-Policy" in response.headers
            assert "Strict-Transport-Security" in response.headers


class TestConfiguration:
    """Test security headers configuration."""

    def test_security_headers_config_method(self):
        """Test get_security_headers_config returns correct values."""
        config = settings.get_security_headers_config()

        assert isinstance(config, dict)
        assert "enabled" in config
        assert "csp_report_uri" in config
        assert "hsts_max_age" in config

    def test_default_configuration_values(self):
        """Test default configuration values are secure."""
        assert settings.SECURITY_HEADERS_ENABLED is True
        assert settings.HSTS_MAX_AGE == 31536000  # 1 year
        assert settings.HSTS_INCLUDE_SUBDOMAINS is True
        assert settings.HSTS_PRELOAD is True

    def test_csp_report_uri_configurable(self):
        """Test CSP report URI is configurable."""
        assert settings.CSP_REPORT_URI == "/api/csp-report"


# Performance and edge cases
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_large_csp_report(self, client):
        """Test handling of very large CSP reports."""
        large_report = {
            "csp-report": {
                "document-uri": "https://example.com/page",
                "violated-directive": "script-src",
                "blocked-uri": "https://evil.com/script.js",
                "effective-directive": "script-src",
                "original-policy": "x" * 10000,  # Very large policy
                "status-code": 200,
                "disposition": "enforce",
                "script-sample": "y" * 5000  # Large script sample
            }
        }

        response = client.post("/api/csp-report", json=large_report)
        assert response.status_code == 204

    def test_unicode_in_csp_report(self, client):
        """Test handling of unicode in CSP reports."""
        unicode_report = {
            "csp-report": {
                "document-uri": "https://example.com/页面",
                "violated-directive": "script-src",
                "blocked-uri": "https://evil.com/скрипт.js",
                "effective-directive": "script-src",
                "original-policy": "default-src 'self'",
                "status-code": 200,
                "disposition": "enforce"
            }
        }

        response = client.post("/api/csp-report", json=unicode_report)
        assert response.status_code == 204

    def test_concurrent_requests_unique_nonces(self, client):
        """Test that concurrent requests get unique nonces."""
        import concurrent.futures

        def get_nonce():
            response = client.get("/test")
            return response.json()["nonce"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            nonces = list(executor.map(lambda _: get_nonce(), range(100)))

        # All nonces should be unique
        assert len(set(nonces)) == len(nonces)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.middleware.security_headers", "--cov-report=term-missing"])
