# Performance Monitoring Setup Guide

## Overview

WWMAA Backend implements comprehensive performance monitoring using Prometheus, Grafana, and custom metrics collection. This guide explains how to set up and use the monitoring infrastructure.

## Components

### 1. Prometheus Metrics (`/backend/observability/metrics.py`)

Exports metrics for:
- HTTP request latency and throughput
- ZeroDB query performance
- External API call latency (Stripe, BeeHiiv, Cloudflare, AI Registry)
- Redis cache hit/miss rates
- Background job execution times

### 2. Slow Query Logger (`/backend/observability/slow_query_logger.py`)

Logs queries exceeding performance thresholds:
- Default threshold: 1 second
- Critical threshold: 5 seconds
- Logs to: `/var/log/wwmaa/slow_queries.log`
- Automatic log rotation (10MB per file, 5 backups)

### 3. Request ID Tracing (`/backend/middleware/metrics_middleware.py`)

Adds unique request IDs to all requests:
- Generates UUID for each request
- Adds `X-Request-ID` header to responses
- Enables request correlation across services

### 4. Instrumented Services

- **ZeroDB Client**: `/backend/services/instrumented_zerodb_client.py`
- **Cache Service**: `/backend/services/instrumented_cache_service.py`
- **External API Tracker**: `/backend/observability/external_api_tracker.py`

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key packages:
- `prometheus-client==0.19.0`
- `prometheus-fastapi-instrumentator==6.1.0`

### 2. Configure Environment Variables

Add to `.env`:

```bash
# Performance Monitoring
PROMETHEUS_ENABLED=true
METRICS_ENDPOINT=/metrics
SLOW_QUERY_THRESHOLD_SECONDS=1.0
SLOW_QUERY_LOG_FILE=/var/log/wwmaa/slow_queries.log
```

### 3. Create Log Directory

```bash
sudo mkdir -p /var/log/wwmaa
sudo chown $USER:$USER /var/log/wwmaa
```

Or for development (logs to `./logs`):
```bash
mkdir -p ./logs
```

## Usage

### Access Metrics

Start the backend and access metrics:

```bash
# Start backend
cd backend
uvicorn app:app --reload

# Access Prometheus metrics
curl http://localhost:8000/metrics

# Access metrics summary (development only)
curl http://localhost:8000/metrics/summary
```

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'wwmaa-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

Run Prometheus:

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### Grafana Dashboard

1. Start Grafana:

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

2. Access Grafana at `http://localhost:3000` (default credentials: admin/admin)

3. Add Prometheus data source:
   - Configuration > Data Sources > Add data source
   - Select Prometheus
   - URL: `http://prometheus:9090` (or `http://localhost:9090` for local)

4. Import dashboard:
   - Dashboards > Import
   - Upload `/docs/observability/grafana-dashboard.json`

### Alert Manager

Configure AlertManager to use the rules in `/docs/observability/prometheus-alerts.yml`:

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'team-email'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@wwmaa.com'
        from: 'alerts@wwmaa.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alerts@wwmaa.com'
        auth_password: 'password'
```

## Instrumentation

### HTTP Endpoints (Automatic)

HTTP endpoints are automatically instrumented via middleware. No changes needed.

### ZeroDB Queries

Use the instrumented client:

```python
from backend.services.instrumented_zerodb_client import get_instrumented_zerodb_client

client = get_instrumented_zerodb_client()
result = client.query_documents("users", filters={"status": "active"})
```

### External API Calls

Use context managers or decorators:

```python
from backend.observability.external_api_tracker import track_stripe, ExternalAPITracker

# Using decorator
@track_stripe("create_payment")
def create_payment(amount: int):
    return stripe.PaymentIntent.create(amount=amount)

# Using context manager
with ExternalAPITracker.track_stripe_call("create_payment"):
    stripe.PaymentIntent.create(amount=1000)
```

### Cache Operations

Use the instrumented cache service:

```python
from backend.services.instrumented_cache_service import get_cache_service

cache = get_cache_service()
value = cache.get("my_key")  # Automatically tracked
cache.set("my_key", "value", expiration=300)  # Automatically tracked
```

### Background Jobs

Track background jobs:

```python
from backend.observability.metrics import track_background_job

with track_background_job("dunning_reminder"):
    send_dunning_emails()
```

## Performance Testing

Run performance tests:

```bash
cd backend

# Test all endpoints
python scripts/performance_test.py --base-url http://localhost:8000 --requests 100

# Test specific endpoint
python scripts/performance_test.py --base-url http://localhost:8000 --endpoint /health

# Generate JSON report
python scripts/performance_test.py --output performance_report.json
```

## Monitoring Best Practices

### 1. Set Appropriate SLOs

See `/docs/observability/slos.md` for defined Service Level Objectives.

### 2. Review Metrics Regularly

- **Daily**: Check dashboard for anomalies
- **Weekly**: Review SLO compliance
- **Monthly**: Analyze trends and optimize

### 3. Slow Query Investigation

Check slow query logs:

```bash
# View recent slow queries
tail -n 100 /var/log/wwmaa/slow_queries.log

# Search for specific collection
grep "collection.*users" /var/log/wwmaa/slow_queries.log

# Count slow queries by collection
grep -o '"collection":"[^"]*"' /var/log/wwmaa/slow_queries.log | sort | uniq -c
```

### 4. Alert Response

When alerts fire:

1. Check Grafana dashboard for context
2. Review slow query logs if database-related
3. Check external service status (Stripe, BeeHiiv, etc.)
4. Review application logs for errors
5. Correlate with request IDs for specific failures

## Troubleshooting

### Metrics Not Appearing

1. Verify Prometheus is enabled:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Check environment variable:
   ```bash
   echo $PROMETHEUS_ENABLED
   ```

3. Restart the backend

### High Memory Usage

Prometheus metrics can consume memory. To reduce:

1. Decrease metric retention in Prometheus
2. Reduce scrape frequency
3. Use metric relabeling to drop unused metrics

### Slow Query Logs Not Created

1. Check directory permissions:
   ```bash
   ls -la /var/log/wwmaa/
   ```

2. Create directory if missing:
   ```bash
   mkdir -p /var/log/wwmaa
   chmod 755 /var/log/wwmaa
   ```

3. Check threshold configuration in `.env`

### Request IDs Not in Logs

Ensure middleware is added to FastAPI app:

```python
from backend.middleware.metrics_middleware import MetricsMiddleware

app.add_middleware(MetricsMiddleware)
```

## Production Deployment

### Docker Compose

Example `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PROMETHEUS_ENABLED=true
    volumes:
      - ./logs:/var/log/wwmaa

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./docs/observability/prometheus-alerts.yml:/etc/prometheus/alerts.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

volumes:
  grafana-storage:
```

### Kubernetes

See `/docs/deployment/kubernetes/` for Kubernetes manifests.

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [SLO Documentation](./slos.md)
- [Alert Rules](./prometheus-alerts.yml)
- [Dashboard Configuration](./grafana-dashboard.json)

## Support

For issues or questions:
- Check troubleshooting section above
- Review application logs
- Contact: backend-team@wwmaa.com
