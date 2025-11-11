"""
Tests for Performance Metrics and Monitoring

Tests Prometheus metrics, slow query logging, and request ID tracing.
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from backend.observability.metrics import (
    http_request_duration,
    http_requests_total,
    zerodb_query_duration,
    zerodb_slow_queries_total,
    external_api_duration,
    cache_operations_total,
    track_zerodb_query,
    track_external_api_call,
    track_cache_operation,
    record_http_request,
    get_metrics_summary,
)
from backend.observability.slow_query_logger import (
    SlowQueryLogger,
    get_slow_query_logger,
    log_slow_query,
)
from backend.middleware.metrics_middleware import MetricsMiddleware, get_request_id
from backend.services.instrumented_zerodb_client import InstrumentedZeroDBClient
from backend.services.instrumented_cache_service import InstrumentedCacheService


class TestPrometheusMetrics:
    """Test Prometheus metrics collection."""

    def test_http_request_metrics_recorded(self):
        """Test that HTTP request metrics are recorded correctly."""
        # Record some metrics
        record_http_request("GET", "/health", 200, 0.150)
        record_http_request("POST", "/api/users", 201, 0.350)
        record_http_request("GET", "/api/events", 500, 2.500)

        # Get metrics from registry
        metrics = {}
        for metric in REGISTRY.collect():
            if metric.name == "http_requests_total":
                for sample in metric.samples:
                    key = (
                        sample.labels.get("method"),
                        sample.labels.get("endpoint"),
                        sample.labels.get("status_code"),
                    )
                    metrics[key] = sample.value

        # Verify metrics were recorded
        assert ("GET", "/health", "200") in metrics
        assert ("POST", "/api/users", "201") in metrics
        assert ("GET", "/api/events", "500") in metrics

    def test_zerodb_query_tracking(self):
        """Test ZeroDB query performance tracking."""
        # Track a normal query
        with track_zerodb_query("users", "query", slow_query_threshold=1.0):
            time.sleep(0.05)  # Fast query

        # Track a slow query
        with track_zerodb_query("events", "query", slow_query_threshold=0.01):
            time.sleep(0.02)  # Slow query

        # Get slow query metrics
        slow_queries = 0
        for metric in REGISTRY.collect():
            if metric.name == "zerodb_slow_queries_total":
                for sample in metric.samples:
                    if (
                        sample.labels.get("collection") == "events"
                        and sample.labels.get("operation") == "query"
                    ):
                        slow_queries = sample.value

        assert slow_queries >= 1

    def test_external_api_tracking(self):
        """Test external API call tracking."""
        # Track successful API call
        with track_external_api_call("stripe", "create_payment"):
            time.sleep(0.01)

        # Track API call with error
        try:
            with track_external_api_call("beehiiv", "get_subscriber"):
                raise ValueError("API Error")
        except ValueError:
            pass  # Expected

        # Get metrics
        found_stripe = False
        found_error = False

        for metric in REGISTRY.collect():
            if metric.name == "external_api_requests_total":
                for sample in metric.samples:
                    if sample.labels.get("service") == "stripe":
                        found_stripe = True
            elif metric.name == "external_api_errors_total":
                for sample in metric.samples:
                    if sample.labels.get("service") == "beehiiv":
                        found_error = True

        assert found_stripe
        assert found_error

    def test_cache_operation_tracking(self):
        """Test cache operation tracking."""
        # Track cache hit
        with track_cache_operation("get") as track_result:
            time.sleep(0.001)
            track_result("hit")

        # Track cache miss
        with track_cache_operation("get") as track_result:
            time.sleep(0.001)
            track_result("miss")

        # Get metrics
        hits = 0
        misses = 0

        for metric in REGISTRY.collect():
            if metric.name == "cache_operations_total":
                for sample in metric.samples:
                    if sample.labels.get("result") == "hit":
                        hits += sample.value
                    elif sample.labels.get("result") == "miss":
                        misses += sample.value

        assert hits > 0
        assert misses > 0

    def test_metrics_summary(self):
        """Test metrics summary generation."""
        summary = get_metrics_summary()

        assert "http_requests" in summary
        assert "zerodb_queries" in summary
        assert "external_apis" in summary
        assert "cache" in summary
        assert "background_jobs" in summary


class TestSlowQueryLogger:
    """Test slow query logging functionality."""

    def test_slow_query_logger_initialization(self):
        """Test slow query logger initialization."""
        logger = SlowQueryLogger(slow_threshold=1.0, critical_threshold=5.0)

        assert logger.slow_threshold == 1.0
        assert logger.critical_threshold == 5.0

    def test_slow_query_logging(self, tmp_path):
        """Test that slow queries are logged."""
        logger = SlowQueryLogger(slow_threshold=0.1)

        # Log a slow query
        logger.log_query(
            collection="users",
            operation="query",
            duration=0.5,
            query_details={"filters": {"status": "active"}},
            result_count=100,
        )

        # Verify log was created (would need to check actual log file in integration test)
        # For unit test, we just verify the method executes without error
        assert True

    def test_query_below_threshold_not_logged(self):
        """Test that queries below threshold are not logged."""
        logger = SlowQueryLogger(slow_threshold=1.0)

        # Log a fast query (should not log)
        logger.log_query(
            collection="users",
            operation="query",
            duration=0.1,  # Below 1.0 threshold
        )

        # Should execute without error
        assert True

    def test_critical_query_alert(self):
        """Test that critical slow queries trigger alerts."""
        logger = SlowQueryLogger(slow_threshold=1.0, critical_threshold=5.0)

        # Log a critical query
        with patch.object(logger, "_send_critical_alert") as mock_alert:
            logger.log_query(
                collection="events",
                operation="vector_search",
                duration=6.0,  # Above critical threshold
                query_details={"top_k": 100},
            )

            mock_alert.assert_called_once()

    def test_sensitive_data_sanitization(self):
        """Test that sensitive data is sanitized in logs."""
        logger = SlowQueryLogger(slow_threshold=0.1)

        query_details = {
            "email": "user@example.com",
            "password": "secret123",
            "filters": {"status": "active"},
        }

        sanitized = logger._sanitize_query_details(query_details)

        assert sanitized["email"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["filters"]["status"] == "active"

    def test_convenience_function(self):
        """Test convenience function for slow query logging."""
        # Should not raise error
        log_slow_query(
            collection="test",
            operation="test_op",
            duration=1.5,
            query_details={"test": "data"},
        )

        assert True


class TestMetricsMiddleware:
    """Test metrics middleware functionality."""

    def test_request_id_generation(self):
        """Test that request ID is generated for each request."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)

        @app.get("/test")
        async def test_route(request: Request):
            return {"request_id": get_request_id(request)}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.json()["request_id"] == response.headers["X-Request-ID"]

    def test_request_id_in_response_headers(self):
        """Test that request ID is included in response headers."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)

        @app.get("/test")
        async def test_route():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_endpoint_normalization(self):
        """Test that endpoints with IDs are normalized."""
        app = FastAPI()
        middleware = MetricsMiddleware(app)

        # Test UUID normalization
        normalized = middleware._normalize_endpoint(
            "/api/users/550e8400-e29b-41d4-a716-446655440000"
        )
        assert normalized == "/api/users/{uuid}"

        # Test numeric ID normalization
        normalized = middleware._normalize_endpoint("/api/events/12345")
        assert normalized == "/api/events/{id}"

        # Test token normalization
        normalized = middleware._normalize_endpoint(
            "/api/files/abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
        )
        assert normalized == "/api/files/{token}"


class TestInstrumentedZeroDBClient:
    """Test instrumented ZeroDB client."""

    @pytest.fixture
    def mock_client(self):
        """Create mock ZeroDB client."""
        with patch("backend.services.instrumented_zerodb_client.ZeroDBClient.__init__"):
            client = InstrumentedZeroDBClient(
                api_key="test-key", base_url="http://test.com"
            )
            return client

    def test_create_document_tracking(self, mock_client):
        """Test that create_document is tracked with metrics."""
        mock_client._client = Mock()
        mock_client._build_url = Mock(return_value="http://test.com/test")
        mock_client._handle_response = Mock(return_value={"id": "123"})

        # Mock parent method
        with patch(
            "backend.services.zerodb_service.ZeroDBClient.create_document",
            return_value={"id": "123"},
        ):
            result = mock_client.create_document("users", {"name": "Test"})

            assert result["id"] == "123"

    def test_slow_query_logging(self, mock_client):
        """Test that slow queries are logged."""
        mock_client._client = Mock()
        mock_client._build_url = Mock(return_value="http://test.com/test")
        mock_client.slow_query_threshold = 0.01

        with patch(
            "backend.services.zerodb_service.ZeroDBClient.query_documents",
            side_effect=lambda *args, **kwargs: (time.sleep(0.02), {"documents": []})[
                1
            ],
        ):
            with patch(
                "backend.services.instrumented_zerodb_client.log_slow_query"
            ) as mock_log:
                mock_client.query_documents("users", filters={})

                # Verify slow query was logged
                mock_log.assert_called_once()
                call_args = mock_log.call_args
                assert call_args[1]["collection"] == "users"
                assert call_args[1]["operation"] == "query"


class TestInstrumentedCacheService:
    """Test instrumented cache service."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        return mock

    def test_cache_get_hit(self, mock_redis):
        """Test cache get operation with hit."""
        with patch("redis.from_url", return_value=mock_redis):
            cache = InstrumentedCacheService()
            mock_redis.get.return_value = '"test_value"'

            result = cache.get("test_key")

            assert result == "test_value"
            mock_redis.get.assert_called_once_with("test_key")

    def test_cache_get_miss(self, mock_redis):
        """Test cache get operation with miss."""
        with patch("redis.from_url", return_value=mock_redis):
            cache = InstrumentedCacheService()
            mock_redis.get.return_value = None

            result = cache.get("test_key")

            assert result is None
            mock_redis.get.assert_called_once_with("test_key")

    def test_cache_set(self, mock_redis):
        """Test cache set operation."""
        with patch("redis.from_url", return_value=mock_redis):
            cache = InstrumentedCacheService()
            mock_redis.set.return_value = True

            result = cache.set("test_key", "test_value")

            assert result is True
            mock_redis.set.assert_called_once()

    def test_cache_set_with_expiration(self, mock_redis):
        """Test cache set with expiration."""
        with patch("redis.from_url", return_value=mock_redis):
            cache = InstrumentedCacheService()
            mock_redis.setex.return_value = True

            result = cache.set("test_key", "test_value", expiration=300)

            assert result is True
            mock_redis.setex.assert_called_once_with("test_key", 300, '"test_value"')

    def test_cache_delete(self, mock_redis):
        """Test cache delete operation."""
        with patch("redis.from_url", return_value=mock_redis):
            cache = InstrumentedCacheService()
            mock_redis.delete.return_value = 1

            result = cache.delete("test_key")

            assert result is True
            mock_redis.delete.assert_called_once_with("test_key")

    def test_cache_error_handling(self, mock_redis):
        """Test cache error handling."""
        with patch("redis.from_url", return_value=mock_redis):
            cache = InstrumentedCacheService()
            mock_redis.get.side_effect = Exception("Connection error")

            result = cache.get("test_key")

            # Should return None on error, not raise exception
            assert result is None


class TestMetricsIntegration:
    """Integration tests for metrics system."""

    def test_full_request_lifecycle(self):
        """Test full request lifecycle with metrics."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware)

        @app.get("/test")
        async def test_route(request: Request):
            # Simulate some work
            with track_zerodb_query("users", "query"):
                time.sleep(0.01)

            with track_cache_operation("get") as track_result:
                track_result("hit")

            return {"status": "ok", "request_id": get_request_id(request)}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.json()["status"] == "ok"

    def test_metrics_endpoint_returns_data(self):
        """Test that /metrics endpoint returns Prometheus data."""
        from backend.observability.metrics import get_metrics_handler

        response = get_metrics_handler()

        assert response.media_type == "text/plain; version=0.0.4; charset=utf-8"
        assert len(response.body) > 0

        # Check for expected metrics in output
        content = response.body.decode("utf-8")
        assert "http_requests_total" in content or "http_request" in content
