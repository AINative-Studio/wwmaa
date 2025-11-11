# OpenTelemetry Tracing Guide

## Overview

WWMAA Backend uses OpenTelemetry for distributed tracing across all API endpoints, database operations, external API calls, and caching operations. This guide covers setup, configuration, and usage of the tracing infrastructure.

## Features

- **Auto-instrumentation**: Automatic tracing for FastAPI routes, Redis operations, and HTTP requests
- **Custom spans**: Manual instrumentation for ZeroDB queries, search pipeline steps, and business logic
- **Sampling strategies**: Environment-based sampling (100% staging, 10% production)
- **Multiple exporters**: Support for Honeycomb, Jaeger, Grafana Tempo, and console output
- **Rich context**: Traces include user ID, role, HTTP context, database operations, and error details
- **Search pipeline**: All 11 steps of the query search pipeline are traced with detailed attributes

## Architecture

### Automatic Instrumentation

The following libraries are automatically instrumented:

- **FastAPI**: All routes and middleware
- **Requests**: External API calls (Stripe, BeeHiiv, Cloudflare, AI Registry)
- **Redis**: Cache operations

### Custom Instrumentation

Custom spans are created for:

- **ZeroDB operations**: `zerodb.{operation}` (create_document, query, vector_search, etc.)
- **Search pipeline steps**: `search.{step}` (normalize, cache_check, generate_embedding, vector_search, generate_answer, attach_media, cache_write, log_query)
- **Business logic**: Any critical operation requiring detailed observability

## Configuration

### Environment Variables

Configure OpenTelemetry using the following environment variables:

```bash
# Required: OTLP endpoint (e.g., Honeycomb, Jaeger, Grafana Tempo)
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io

# Required: API key or authentication headers
OTEL_EXPORTER_OTLP_HEADERS=x-honeycomb-team=your_api_key_here

# Service name (defaults to "wwmaa-backend")
OTEL_SERVICE_NAME=wwmaa-backend

# Deployment environment (uses PYTHON_ENV if not set)
OTEL_DEPLOYMENT_ENVIRONMENT=staging

# Exporter type: grpc (default), http, or console
OTEL_EXPORTER_TYPE=grpc

# Sampling rate (0.0-1.0) - overrides environment-based sampling
OTEL_TRACES_SAMPLER_ARG=0.1
```

### Honeycomb Configuration

For Honeycomb (recommended):

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
OTEL_EXPORTER_OTLP_HEADERS=x-honeycomb-team=YOUR_API_KEY_HERE
OTEL_SERVICE_NAME=wwmaa-backend
OTEL_DEPLOYMENT_ENVIRONMENT=staging
OTEL_EXPORTER_TYPE=grpc
```

### Jaeger Configuration

For Jaeger (local development):

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=wwmaa-backend
OTEL_DEPLOYMENT_ENVIRONMENT=development
OTEL_EXPORTER_TYPE=grpc
```

### Grafana Tempo Configuration

For Grafana Tempo:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://tempo-prod-us-central1.grafana.net:443
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic YOUR_BASE64_CREDENTIALS
OTEL_SERVICE_NAME=wwmaa-backend
OTEL_DEPLOYMENT_ENVIRONMENT=production
OTEL_EXPORTER_TYPE=grpc
```

## Sampling Strategy

Sampling is configured automatically based on the environment:

- **Development**: 100% sampling (all traces collected)
- **Staging**: 100% sampling (all traces collected)
- **Production**: 10% sampling (one in ten traces collected)

You can override this with the `OTEL_TRACES_SAMPLER_ARG` environment variable.

### Always-Sampled Operations

The following operations are always sampled, regardless of the sampling rate:

- Error traces (any operation that raises an exception)
- Admin endpoints
- Payment operations

## Usage

### Creating Custom Spans

Use the `with_span` context manager to create custom spans:

```python
from backend.observability.tracing_utils import with_span, add_span_attributes

def process_application(application_id: str):
    with with_span("process_application", attributes={
        "application.id": application_id,
        "operation": "process"
    }) as span:
        # Your code here
        result = perform_processing()
        
        # Add additional attributes
        add_span_attributes(
            status="approved",
            processing_time_ms=100
        )
        
        return result
```

### Adding User Context

Add user information to traces for better debugging:

```python
from backend.observability.tracing_utils import add_user_context

def my_endpoint(current_user: User):
    add_user_context(user_id=current_user.id, role=current_user.role)
    # Your code here
```

### Adding HTTP Context

Add HTTP request details to traces:

```python
from backend.observability.tracing_utils import add_http_context

@app.post("/api/resource")
async def create_resource(request: Request):
    add_http_context(
        method=request.method,
        url=str(request.url),
        status_code=201
    )
    # Your code here
```

### Handling Errors

Set error status on spans when exceptions occur:

```python
from backend.observability.tracing_utils import with_span, set_span_error

def risky_operation():
    with with_span("risky_operation") as span:
        try:
            # Your code that might fail
            perform_risky_task()
        except Exception as e:
            set_span_error(span, e)
            raise
```

### Using Decorators

Use the `@trace_function` decorator for automatic span creation:

```python
from backend.observability.tracing_utils import trace_function

@trace_function(span_name="calculate_metrics", attributes={"type": "analytics"})
def calculate_metrics(data):
    # Function is automatically wrapped in a span
    return process(data)
```

## Search Pipeline Tracing

The 11-step search query pipeline is fully instrumented with the following spans:

1. **search.normalize** (Step 1): Query normalization
   - Attributes: `query_length`, `normalized_query_length`

2. **search.cache_check** (Step 3): Redis cache lookup
   - Attributes: `cache_hit` (true/false)

3. **search.generate_embedding** (Step 4): OpenAI embedding generation
   - Attributes: `query`, `embedding_dimensions`, `model`

4. **search.vector_search** (Step 5): ZeroDB vector similarity search
   - Attributes: `top_k`, `embedding_dimension`, `result_count`

5. **search.generate_answer** (Step 6): AI Registry answer generation
   - Attributes: `model`, `context_count`, `tokens_used`, `answer_length`

6. **search.attach_media** (Step 8): Media attachment
   - Attributes: `videos_count`, `images_count`

7. **search.cache_write** (Step 9): Cache result storage
   - Attributes: None

8. **search.log_query** (Step 10): Query logging to ZeroDB
   - Attributes: `latency_ms`, `cached`

Each span includes the `step` attribute indicating its position in the pipeline.

## ZeroDB Operation Tracing

All ZeroDB operations are traced with spans following the pattern `zerodb.{operation}`:

- **zerodb.create_document**: Document creation
- **zerodb.query**: Document queries
- **zerodb.vector_search**: Vector similarity search
- **zerodb.update_document**: Document updates
- **zerodb.delete_document**: Document deletion

Example attributes:
```
db.system: "zerodb"
db.operation: "create" | "query" | "search" | "update" | "delete"
db.collection: "applications" | "members" | "events" | etc.
document.id: "doc_123"
query.limit: 10
query.result_count: 5
```

## Viewing Traces

### Honeycomb

1. Log in to [Honeycomb](https://ui.honeycomb.io)
2. Select the "wwmaa-backend" dataset
3. Use the query builder to filter traces:
   - By endpoint: `http.url = "/api/search"`
   - By user: `user.id = "user_123"`
   - By error: `error = true`
   - By duration: `duration_ms > 1000`

### Jaeger

1. Open Jaeger UI at `http://localhost:16686`
2. Select "wwmaa-backend" service
3. Use filters to find specific traces
4. Click on a trace to see the waterfall view

### Grafana Tempo

1. Open Grafana
2. Navigate to Explore
3. Select Tempo as the data source
4. Use TraceQL to query traces:
   ```
   { service.name = "wwmaa-backend" && http.status_code >= 500 }
   ```

## Troubleshooting

### Tracing Not Working

Check the health endpoint to verify tracing status:

```bash
curl http://localhost:8000/health
```

Response should include:
```json
{
  "status": "healthy",
  "tracing": {
    "enabled": true,
    "service_name": "wwmaa-backend",
    "exporter_type": "grpc"
  }
}
```

### No Spans Appearing

1. Verify environment variables are set correctly
2. Check logs for OpenTelemetry errors:
   ```bash
   grep "OpenTelemetry" logs/app.log
   ```
3. Ensure the OTLP endpoint is reachable
4. Verify sampling is not filtering out all traces

### High Cardinality Warnings

If you see warnings about high cardinality attributes:

1. Avoid using unique IDs as attribute values (use as tags instead)
2. Limit the number of unique values for attributes
3. Use aggregation for metrics instead of individual traces

### Performance Impact

Tracing has minimal performance impact (<1-2% overhead). If you experience issues:

1. Reduce sampling rate in production
2. Use batch span processor (default)
3. Adjust exporter timeout settings

## Best Practices

1. **Use semantic naming**: Follow the pattern `{namespace}.{operation}` for span names
   - Good: `search.generate_embedding`, `zerodb.query`, `payment.process`
   - Bad: `step1`, `db_call`, `function_x`

2. **Add context**: Include relevant attributes for debugging
   - User ID, operation type, resource IDs
   - Avoid sensitive data (passwords, API keys, PII)

3. **Handle errors properly**: Always mark spans with errors
   ```python
   except Exception as e:
       set_span_error(span, e)
       raise
   ```

4. **Keep spans focused**: One span per logical operation
   - Too broad: Single span for entire request
   - Too narrow: Span for each line of code
   - Just right: Span for each service call or logical step

5. **Use parent-child relationships**: Nested spans show operation flow
   ```python
   with with_span("parent_operation"):
       with with_span("child_operation_1"):
           pass
       with with_span("child_operation_2"):
           pass
   ```

## Performance Metrics

Expected span counts per operation:

- **Simple API request**: 3-5 spans (FastAPI, database query, cache)
- **Search query**: 15-20 spans (11 pipeline steps + sub-operations)
- **Application submission**: 10-15 spans (validation, database, email, webhook)
- **Payment processing**: 8-12 spans (Stripe API, database, notifications)

## Support

For issues or questions:

1. Check application logs: `logs/app.log`
2. Review Honeycomb/Jaeger for trace details
3. Contact the DevOps team with trace IDs

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Honeycomb Documentation](https://docs.honeycomb.io/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Grafana Tempo Documentation](https://grafana.com/docs/tempo/)
