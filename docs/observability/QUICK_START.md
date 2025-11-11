# Performance Monitoring Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
cd backend
pip install prometheus-client==0.19.0 prometheus-fastapi-instrumentator==6.1.0
```

### 2. Configure Environment
Add to `.env`:
```bash
PROMETHEUS_ENABLED=true
METRICS_ENDPOINT=/metrics
SLOW_QUERY_THRESHOLD_SECONDS=1.0
```

### 3. Create Log Directory
```bash
mkdir -p ./logs
```

### 4. Start Backend
```bash
uvicorn app:app --reload
```

### 5. Verify Metrics
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Check metrics summary
curl http://localhost:8000/metrics/summary
```

## Quick Usage

### Track ZeroDB Queries
```python
from backend.services.instrumented_zerodb_client import get_instrumented_zerodb_client

client = get_instrumented_zerodb_client()
users = client.query_documents("users", filters={"active": True})
```

### Track Cache Operations
```python
from backend.services.instrumented_cache_service import get_cache_service

cache = get_cache_service()
value = cache.get("my_key")
cache.set("my_key", "value", expiration=300)
```

### Track External API Calls
```python
from backend.observability.external_api_tracker import ExternalAPITracker

with ExternalAPITracker.track_stripe_call("create_payment"):
    stripe.PaymentIntent.create(amount=1000)
```

### Get Request ID
```python
from fastapi import Request
from backend.middleware.metrics_middleware import get_request_id

@app.get("/api/example")
async def example(request: Request):
    request_id = get_request_id(request)
    return {"request_id": request_id}
```

## Quick Prometheus Setup

### 1. Create `prometheus.yml`
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'wwmaa-backend'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

### 2. Start Prometheus
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 3. Access Prometheus
Open http://localhost:9090

## Quick Grafana Setup

### 1. Start Grafana
```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

### 2. Add Data Source
1. Open http://localhost:3000 (admin/admin)
2. Configuration → Data Sources → Add Prometheus
3. URL: `http://host.docker.internal:9090`
4. Save & Test

### 3. Import Dashboard
1. Dashboards → Import
2. Upload `/docs/observability/grafana-dashboard.json`
3. Select Prometheus data source
4. Import

## Quick Performance Test

```bash
# Test all endpoints
python backend/scripts/performance_test.py --base-url http://localhost:8000

# Test with more requests
python backend/scripts/performance_test.py --requests 1000

# Generate report
python backend/scripts/performance_test.py --output report.json
```

## Key Metrics to Monitor

### API Performance
```promql
# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])
```

### Database Performance
```promql
# p95 query latency
histogram_quantile(0.95, rate(zerodb_query_duration_seconds_bucket[5m]))

# Slow query rate
rate(zerodb_slow_queries_total[5m])
```

### Cache Performance
```promql
# Hit ratio
cache_hit_ratio

# Operations per second
rate(cache_operations_total[5m])
```

## Troubleshooting

### Metrics Not Showing?
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if metrics are enabled
curl http://localhost:8000/metrics

# Check environment
echo $PROMETHEUS_ENABLED
```

### Can't Access Prometheus?
```bash
# Check if container is running
docker ps | grep prometheus

# Check logs
docker logs prometheus

# Restart container
docker restart prometheus
```

### Slow Queries Not Logged?
```bash
# Check log directory
ls -la ./logs/

# Create if missing
mkdir -p ./logs

# Check threshold
grep SLOW_QUERY_THRESHOLD .env

# View recent logs
tail -f ./logs/slow_queries.log
```

## Next Steps

1. Review [Full Documentation](./README.md)
2. Check [SLO Definitions](./slos.md)
3. Set up [Alert Rules](./prometheus-alerts.yml)
4. Configure production monitoring

## Support

- Documentation: `/docs/observability/`
- Implementation: `/backend/US-067-IMPLEMENTATION-SUMMARY.md`
- Tests: `/backend/tests/test_metrics.py`
