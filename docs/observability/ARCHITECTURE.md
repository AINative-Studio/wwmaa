# Performance Monitoring Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WWMAA Backend API                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Application                       │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │        Prometheus Instrumentator Middleware           │ │ │
│  │  │  • Auto-instruments all endpoints                     │ │ │
│  │  │  • Histogram buckets: [0.01...10.0]s                  │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │          MetricsMiddleware                             │ │ │
│  │  │  • Generates X-Request-ID                             │ │ │
│  │  │  • Tracks active requests                             │ │ │
│  │  │  • Normalizes endpoint paths                          │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │                                                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │ │
│  │  │   Routes     │  │  Services    │  │   External APIs │  │ │
│  │  │              │  │              │  │                 │  │ │
│  │  │ • Auth       │  │ • ZeroDB     │  │ • Stripe        │  │ │
│  │  │ • Payments   │  │ • Cache      │  │ • BeeHiiv       │  │ │
│  │  │ • Events     │  │ • Email      │  │ • Cloudflare    │  │ │
│  │  │ • Search     │  │ • AI         │  │ • AI Registry   │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘  │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Observability Components                        │ │
│  │                                                              │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │ │
│  │  │ Metrics Module │  │ Slow Query Log │  │ API Tracker   │ │ │
│  │  │                │  │                │  │               │ │ │
│  │  │ • HTTP metrics │  │ • JSON logs    │  │ • Stripe      │ │ │
│  │  │ • DB metrics   │  │ • Rotation     │  │ • BeeHiiv     │ │ │
│  │  │ • Cache metrics│  │ • Thresholds   │  │ • Cloudflare  │ │ │
│  │  │ • Job metrics  │  │ • Alerts       │  │ • AI Registry │ │ │
│  │  └────────────────┘  └────────────────┘  └───────────────┘ │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │        Instrumented Services                           │ │ │
│  │  │                                                        │ │ │
│  │  │  • InstrumentedZeroDBClient                           │ │ │
│  │  │    - Wraps all DB operations                          │ │ │
│  │  │    - Tracks query duration                            │ │ │
│  │  │    - Logs slow queries                                │ │ │
│  │  │                                                        │ │ │
│  │  │  • InstrumentedCacheService                           │ │ │
│  │  │    - Wraps Redis operations                           │ │ │
│  │  │    - Tracks hit/miss rates                            │ │ │
│  │  │    - Measures latency                                 │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Metrics Endpoints                               │ │
│  │                                                              │ │
│  │  GET /metrics        → Prometheus text format               │ │
│  │  GET /metrics/summary → JSON summary (dev only)             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP Scrape (15s interval)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Prometheus Server                          │
│                                                                     │
│  • Metrics Collection (TSDB)                                       │
│  • Alert Evaluation (30s interval)                                │
│  • 22 Alert Rules                                                  │
│  • 30-day Retention                                                │
│                                                                     │
│  Metrics Stored:                                                   │
│  ├─ http_request_duration_seconds (histogram)                     │
│  ├─ http_requests_total (counter)                                 │
│  ├─ zerodb_query_duration_seconds (histogram)                     │
│  ├─ zerodb_slow_queries_total (counter)                           │
│  ├─ external_api_duration_seconds (histogram)                     │
│  ├─ cache_operations_total (counter)                              │
│  ├─ cache_hit_ratio (gauge)                                       │
│  └─ background_job_duration_seconds (histogram)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                      │                          │
                      │                          │ Alert Trigger
                      │                          ▼
                      │                    ┌─────────────────┐
                      │                    │ AlertManager    │
                      │                    │                 │
                      │                    │ • Route alerts  │
                      │ Query (PromQL)     │ • Deduplication │
                      │                    │ • Grouping      │
                      ▼                    │ • Silencing     │
┌─────────────────────────────────────┐   └─────────────────┘
│        Grafana Dashboard            │             │
│                                     │             │ Notify
│  12 Panels:                         │             ▼
│  1. API Request Rate                │   ┌─────────────────────┐
│  2. API Latency (p50/p95/p99)       │   │   PagerDuty        │
│  3. API Error Rate                  │   │   • Critical alerts │
│  4. Active Requests                 │   │   • On-call rotation│
│  5. ZeroDB Query Latency            │   └─────────────────────┘
│  6. Slow ZeroDB Queries             │
│  7. External API Latency            │   ┌─────────────────────┐
│  8. External API Errors             │   │   Email / Slack     │
│  9. Cache Hit Ratio                 │   │   • Warning alerts  │
│ 10. Cache Operations                │   │   • Team notifications│
│ 11. Background Job Duration         │   └─────────────────────┘
│ 12. Background Job Errors           │
│                                     │
│  • 30s Auto-refresh                 │
│  • Alert Annotations                │
│  • Custom Time Ranges               │
└─────────────────────────────────────┘
```

## Data Flow

### 1. Request Processing Flow

```
Client Request
    │
    ▼
[MetricsMiddleware]
    │ • Generate Request ID
    │ • Start timer
    │ • Increment active_requests
    │
    ▼
[Prometheus Instrumentator]
    │ • Track request start
    │
    ▼
[Route Handler]
    │
    ├─► [InstrumentedZeroDBClient]
    │       │ • Track query start
    │       │ • Execute query
    │       │ • Record duration
    │       └─► Log if slow (> 1s)
    │
    ├─► [InstrumentedCacheService]
    │       │ • Track operation start
    │       │ • Execute operation
    │       │ • Record hit/miss
    │       └─► Update hit ratio
    │
    └─► [External API Tracker]
            │ • Track API call start
            │ • Execute request
            │ • Record duration/status
            └─► Track errors
    │
    ▼
[Response]
    │ • Add X-Request-ID header
    │ • Record total duration
    │ • Decrement active_requests
    │
    ▼
Client Response
```

### 2. Metrics Collection Flow

```
Application Metrics
    │
    ├─► [Prometheus Client]
    │       │ • Store in memory
    │       │ • Update counters/histograms
    │       └─► Expose at /metrics
    │
    ├─► [Slow Query Logger]
    │       │ • Check duration threshold
    │       │ • Format as JSON
    │       └─► Write to log file
    │
    └─► [Alert Evaluation]
            │ • Check thresholds
            │ • Track duration
            └─► Trigger if violated
```

### 3. Monitoring Stack Flow

```
/metrics endpoint
    │ (scrape every 15s)
    ▼
Prometheus Server
    │
    ├─► [Storage]
    │       └─► Time-series database (30 days)
    │
    ├─► [Alert Rules]
    │       │ • Evaluate every 30s
    │       │ • Check 22 alert conditions
    │       └─► Fire alerts
    │
    └─► [Query API]
            │ (PromQL)
            ▼
        Grafana Dashboard
            │
            └─► Visualize metrics
                (refresh every 30s)
```

## Component Dependencies

```
┌────────────────────────────────────────────────────────┐
│                   Application Layer                    │
│                                                        │
│  FastAPI App → MetricsMiddleware → Instrumentator     │
│                                                        │
└────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                Observability Layer                     │
│                                                        │
│  Metrics Module ← Instrumented Services ← API Tracker │
│         ↓                 ↓                    ↓       │
│  Prometheus Client   Slow Logger         Error Track  │
│                                                        │
└────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                   │
│                                                        │
│  Prometheus ← AlertManager → PagerDuty/Slack          │
│      ↓                                                 │
│  Grafana                                               │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Metric Types

### HTTP Metrics
- **Type:** Histogram + Counter
- **Labels:** method, endpoint, status_code
- **Buckets:** [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
- **Purpose:** Track API performance

### Database Metrics
- **Type:** Histogram + Counter
- **Labels:** collection, operation
- **Buckets:** [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
- **Purpose:** Track query performance

### External API Metrics
- **Type:** Histogram + Counter
- **Labels:** service, operation, status_code
- **Buckets:** [0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
- **Purpose:** Track external service latency

### Cache Metrics
- **Type:** Counter + Gauge
- **Labels:** operation, result
- **Buckets:** [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
- **Purpose:** Track cache performance

## Alert Hierarchy

```
Critical Alerts (Page Immediately)
    │
    ├─ CriticalAPILatency (p95 > 5s)
    ├─ CriticalAPIErrorRate (> 5%)
    ├─ StripeAPIErrors (any errors)
    ├─ CriticalExternalAPILatency (p95 > 10s)
    ├─ MetricsNotReported (service down)
    └─ CriticalCacheHitRatio (< 50%)

Warning Alerts (Notify Team)
    │
    ├─ HighAPILatency (p95 > 1s)
    ├─ HighAPIErrorRate (> 1%)
    ├─ SlowZeroDBQueries (p95 > 100ms)
    ├─ HighSlowQueryRate (> 0.1/s)
    ├─ SlowExternalAPI (p95 > 3s)
    ├─ HighExternalAPIErrorRate (> 0.1/s)
    ├─ LowCacheHitRatio (< 70%)
    ├─ BackgroundJobFailures (any failures)
    └─ LongRunningBackgroundJob (p95 > 300s)

Informational
    │
    ├─ APIThroughputDrop (50% decrease)
    ├─ HighActiveRequests (> 100)
    └─ HighZeroDBErrorRate (> 0.05/s)
```

## Performance Impact

### Latency Overhead
```
Component                    Overhead
────────────────────────────────────────
MetricsMiddleware           < 1ms
Prometheus Instrumentator   < 0.5ms
ZeroDB Instrumentation      < 0.5ms
Cache Instrumentation       < 0.1ms
External API Tracking       < 0.2ms
────────────────────────────────────────
Total per request           < 2.3ms
```

### Memory Usage
```
Component                    Memory
────────────────────────────────────────
Prometheus Metrics          5-10 MB
Slow Query Logs            ~1 MB/day
Request ID Storage         Negligible
────────────────────────────────────────
Total overhead             ~15 MB
```

### CPU Usage
```
Component                    CPU
────────────────────────────────────────
Metrics Collection          < 1%
Log Rotation               Negligible
Alert Evaluation           Negligible
────────────────────────────────────────
Total overhead             < 1%
```

## Scalability Considerations

### High Traffic (> 10,000 req/s)
- Use metric sampling (sample 10% of requests)
- Increase Prometheus scrape interval to 30s
- Use remote write to external storage
- Implement metric aggregation

### Large Dataset (> 1TB metrics)
- Use Prometheus federation
- Implement data retention policies
- Use downsampling for old data
- Consider Thanos for long-term storage

### Multiple Regions
- Deploy Prometheus per region
- Aggregate with Grafana data sources
- Use global AlertManager
- Implement regional dashboards

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Maintained By:** Backend Engineering Team
