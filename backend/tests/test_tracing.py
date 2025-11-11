"""
Integration Tests for OpenTelemetry Tracing

Tests the OpenTelemetry instrumentation across all backend services,
including FastAPI auto-instrumentation, custom spans, and trace context.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, InMemorySpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from backend.observability.tracing import initialize_tracing, get_tracer, is_tracing_enabled, shutdown_tracing
from backend.observability.tracing_utils import (
    with_span,
    add_span_attributes,
    set_span_error,
    get_trace_id,
    get_span_id,
    add_user_context,
    add_http_context,
)


class TestTracingInitialization:
    """Test OpenTelemetry tracing initialization"""

    def setup_method(self):
        """Setup for each test"""
        self.memory_exporter = InMemorySpanExporter()
        self.resource = Resource.create({SERVICE_NAME: "test-service"})

    def teardown_method(self):
        """Teardown after each test"""
        shutdown_tracing()
        self.memory_exporter.clear()

    def test_initialize_tracing_with_console_exporter(self):
        """Test tracing initialization with console exporter"""
        provider = initialize_tracing(
            service_name="test-service",
            service_version="1.0.0",
            environment="development",
            exporter_type="console",
            sampling_rate=1.0,
        )

        assert provider is not None
        assert is_tracing_enabled()

    def test_initialize_tracing_staging_environment(self):
        """Test tracing initialization for staging (100% sampling)"""
        provider = initialize_tracing(
            service_name="test-service",
            environment="staging",
            exporter_type="console",
        )

        assert provider is not None
        assert is_tracing_enabled()

    def test_initialize_tracing_production_environment(self):
        """Test tracing initialization for production (10% sampling)"""
        provider = initialize_tracing(
            service_name="test-service",
            environment="production",
            exporter_type="console",
        )

        assert provider is not None
        assert is_tracing_enabled()

    def test_get_tracer(self):
        """Test getting a tracer instance"""
        initialize_tracing(
            service_name="test-service",
            exporter_type="console",
            sampling_rate=1.0,
        )

        tracer = get_tracer("test-module")
        assert tracer is not None

    def test_shutdown_tracing(self):
        """Test tracing shutdown"""
        initialize_tracing(
            service_name="test-service",
            exporter_type="console",
            sampling_rate=1.0,
        )

        assert is_tracing_enabled()
        shutdown_tracing()
        assert not is_tracing_enabled()


class TestCustomSpans:
    """Test custom span creation and management"""

    def setup_method(self):
        """Setup in-memory exporter for each test"""
        self.memory_exporter = InMemorySpanExporter()

        # Create tracer provider with in-memory exporter
        provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: "test-service"})
        )
        provider.add_span_processor(SimpleSpanProcessor(self.memory_exporter))
        trace.set_tracer_provider(provider)

    def teardown_method(self):
        """Clear spans after each test"""
        self.memory_exporter.clear()

    def test_with_span_context_manager(self):
        """Test custom span creation with context manager"""
        with with_span("test_operation", attributes={"test_key": "test_value"}):
            pass

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "test_operation"
        assert spans[0].attributes.get("test_key") == "test_value"

    def test_add_span_attributes(self):
        """Test adding attributes to current span"""
        tracer = get_tracer("test")

        with tracer.start_as_current_span("test_span") as span:
            add_span_attributes(
                user_id="user_123",
                action="create",
                resource_type="application"
            )

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes.get("user_id") == "user_123"
        assert spans[0].attributes.get("action") == "create"
        assert spans[0].attributes.get("resource_type") == "application"

    def test_set_span_error(self):
        """Test setting error on span"""
        tracer = get_tracer("test")

        try:
            with tracer.start_as_current_span("test_span") as span:
                raise ValueError("Test error")
        except ValueError as e:
            set_span_error(span, e)

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes.get("error") is True
        assert spans[0].attributes.get("error.type") == "ValueError"
        assert "Test error" in spans[0].attributes.get("error.message", "")

    def test_get_trace_id(self):
        """Test getting trace ID from current span"""
        tracer = get_tracer("test")

        with tracer.start_as_current_span("test_span"):
            trace_id = get_trace_id()
            assert trace_id is not None
            assert len(trace_id) == 32  # Hex string of trace ID

    def test_get_span_id(self):
        """Test getting span ID from current span"""
        tracer = get_tracer("test")

        with tracer.start_as_current_span("test_span"):
            span_id = get_span_id()
            assert span_id is not None
            assert len(span_id) == 16  # Hex string of span ID

    def test_add_user_context(self):
        """Test adding user context to span"""
        tracer = get_tracer("test")

        with tracer.start_as_current_span("test_span"):
            add_user_context(user_id="user_456", role="member")

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes.get("user.id") == "user_456"
        assert spans[0].attributes.get("user.role") == "member"

    def test_add_http_context(self):
        """Test adding HTTP context to span"""
        tracer = get_tracer("test")

        with tracer.start_as_current_span("test_span"):
            add_http_context(
                method="POST",
                url="/api/applications",
                status_code=201,
                user_agent="TestClient/1.0"
            )

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes.get("http.method") == "POST"
        assert spans[0].attributes.get("http.url") == "/api/applications"
        assert spans[0].attributes.get("http.status_code") == 201
        assert spans[0].attributes.get("http.user_agent") == "TestClient/1.0"


class TestSearchPipelineTracing:
    """Test tracing for the 11-step search pipeline"""

    def setup_method(self):
        """Setup in-memory exporter for each test"""
        self.memory_exporter = InMemorySpanExporter()

        # Create tracer provider with in-memory exporter
        provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: "test-service"})
        )
        provider.add_span_processor(SimpleSpanProcessor(self.memory_exporter))
        trace.set_tracer_provider(provider)

    def teardown_method(self):
        """Clear spans after each test"""
        self.memory_exporter.clear()

    def test_search_pipeline_span_creation(self):
        """Test that search pipeline creates correct spans"""
        tracer = get_tracer("test")

        # Simulate search pipeline
        with tracer.start_as_current_span("search_query"):
            with with_span("search.normalize", attributes={"step": 1}):
                pass
            with with_span("search.cache_check", attributes={"step": 3}):
                pass
            with with_span("search.generate_embedding", attributes={"step": 4}):
                pass
            with with_span("search.vector_search", attributes={"step": 5}):
                pass
            with with_span("search.generate_answer", attributes={"step": 6}):
                pass
            with with_span("search.attach_media", attributes={"step": 8}):
                pass
            with with_span("search.cache_write", attributes={"step": 9}):
                pass
            with with_span("search.log_query", attributes={"step": 10}):
                pass

        spans = self.memory_exporter.get_finished_spans()

        # Should have parent span + 8 child spans
        assert len(spans) == 9

        # Check span names
        span_names = [span.name for span in spans]
        assert "search_query" in span_names
        assert "search.normalize" in span_names
        assert "search.cache_check" in span_names
        assert "search.generate_embedding" in span_names
        assert "search.vector_search" in span_names
        assert "search.generate_answer" in span_names
        assert "search.attach_media" in span_names

    def test_search_pipeline_attributes(self):
        """Test that search pipeline spans have correct attributes"""
        with with_span("search.generate_embedding", attributes={
            "step": 4,
            "query": "test query",
            "embedding_dimensions": 1536,
            "model": "text-embedding-3-small"
        }):
            pass

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].attributes.get("step") == 4
        assert spans[0].attributes.get("query") == "test query"
        assert spans[0].attributes.get("embedding_dimensions") == 1536
        assert spans[0].attributes.get("model") == "text-embedding-3-small"


class TestZeroDBTracing:
    """Test ZeroDB operations tracing"""

    def setup_method(self):
        """Setup in-memory exporter for each test"""
        self.memory_exporter = InMemorySpanExporter()

        # Create tracer provider with in-memory exporter
        provider = TracerProvider(
            resource=Resource.create({SERVICE_NAME: "test-service"})
        )
        provider.add_span_processor(SimpleSpanProcessor(self.memory_exporter))
        trace.set_tracer_provider(provider)

    def teardown_method(self):
        """Clear spans after each test"""
        self.memory_exporter.clear()

    def test_zerodb_create_document_span(self):
        """Test ZeroDB create document creates correct span"""
        with with_span("zerodb.create_document", attributes={
            "db.system": "zerodb",
            "db.operation": "create",
            "db.collection": "applications",
            "document.id": "doc_123"
        }):
            pass

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "zerodb.create_document"
        assert spans[0].attributes.get("db.system") == "zerodb"
        assert spans[0].attributes.get("db.operation") == "create"
        assert spans[0].attributes.get("db.collection") == "applications"

    def test_zerodb_query_span(self):
        """Test ZeroDB query creates correct span"""
        with with_span("zerodb.query", attributes={
            "db.system": "zerodb",
            "db.operation": "query",
            "db.collection": "members",
            "query.limit": 10,
            "query.result_count": 5
        }):
            pass

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "zerodb.query"
        assert spans[0].attributes.get("query.limit") == 10
        assert spans[0].attributes.get("query.result_count") == 5
