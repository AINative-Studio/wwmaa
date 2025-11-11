# WWMAA Load Testing Suite

Comprehensive load and performance testing suite for WWMAA platform before production launch.

## Overview

This suite tests all critical user journeys and system components under realistic production loads to ensure the platform can handle expected traffic patterns without degradation or failures.

## Prerequisites

### 1. Install k6

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Windows:**
```bash
choco install k6
```

### 2. Environment Setup

Create a `.env.load-tests` file with test configuration:

```env
# Target environment (staging recommended)
BASE_URL=https://staging.wwmaa.com
API_URL=https://staging.wwmaa.com/api

# Test user credentials
TEST_USER_EMAIL=loadtest@wwmaa.com
TEST_USER_PASSWORD=loadtest_password_123

# Test admin credentials (for admin operations)
TEST_ADMIN_EMAIL=admin@wwmaa.com
TEST_ADMIN_PASSWORD=admin_password_123

# Stripe webhook signing secret (for webhook tests)
STRIPE_WEBHOOK_SECRET=whsec_test_xxx

# Optional: Test data
TEST_EVENT_ID=evt_xxx
TEST_MEMBERSHIP_TIER_ID=tier_xxx
```

### 3. Staging Environment

These tests **must** run against a staging environment that mirrors production:
- Production-like data volume
- Same infrastructure configuration
- Isolated from production traffic
- Monitoring enabled (OpenTelemetry, Prometheus, Sentry)

See US-081 for staging environment setup.

## Test Scenarios

### 1. Search Load Test (`k6/search-load.js`)

**Scenario:** Primary use case - members searching for martial arts content

- **Load:** 100 concurrent users
- **Rate:** 1000 queries per minute
- **Duration:** 9 minutes (2m ramp-up, 5m sustained, 2m ramp-down)
- **Query Mix:**
  - 40% simple keyword searches ("kata", "kumite")
  - 30% filtered searches (by style, location, instructor)
  - 20% semantic searches (questions, natural language)
  - 10% complex multi-filter searches
- **Targets:**
  - p95 latency < 1.2s
  - p99 latency < 2s
  - Error rate < 0.1%

**Run:**
```bash
k6 run k6/search-load.js
```

### 2. RTC Load Test (`k6/rtc-load.js`)

**Scenario:** Live training session with video and chat

- **Load:** 50 concurrent participants in one session
- **Connections:** WebSocket (chat) + Cloudflare Calls (video)
- **Duration:** 10 minutes
- **Activities:**
  - Join session (authentication)
  - Establish WebSocket connection
  - Send chat messages (5 per minute per user)
  - Receive broadcast messages
  - Video connection health checks
- **Targets:**
  - WebSocket connection success rate > 99%
  - Message delivery rate > 99%
  - Connection drop rate < 1%
  - Chat message latency p95 < 500ms

**Run:**
```bash
k6 run k6/rtc-load.js
```

### 3. Stripe Webhooks Load Test (`k6/webhooks-load.js`)

**Scenario:** Burst traffic from Stripe webhooks during high-activity periods

- **Load:** 100 events/second burst
- **Duration:** 5 minutes
- **Event Mix:**
  - 40% `payment_intent.succeeded`
  - 30% `customer.subscription.updated`
  - 15% `invoice.payment_succeeded`
  - 10% `payment_intent.payment_failed`
  - 5% `customer.subscription.deleted`
- **Targets:**
  - p95 latency < 500ms
  - p99 latency < 1s
  - No dropped webhooks (100% processing)
  - No duplicate processing

**Run:**
```bash
k6 run k6/webhooks-load.js
```

### 4. Event RSVP Load Test (`k6/event-rsvp-load.js`)

**Scenario:** Flash traffic when popular event registration opens

- **Load:** 500 registrations in 10 minutes
- **Peak:** First 2 minutes (50% of traffic)
- **Activities:**
  - View event details
  - Submit RSVP form
  - Payment processing (if paid event)
  - Confirmation email trigger
- **Targets:**
  - p95 latency < 800ms
  - No failed registrations
  - No duplicate bookings
  - Proper capacity enforcement

**Run:**
```bash
k6 run k6/event-rsvp-load.js
```

### 5. Page Load Test (`k6/page-load.js`)

**Scenario:** General website traffic across all pages

- **Load:** 10,000 concurrent visitors
- **Duration:** 15 minutes
- **User Mix:**
  - 70% anonymous visitors
  - 30% authenticated members
- **Page Mix:**
  - 30% Homepage
  - 25% Event listings
  - 20% Instructor profiles
  - 15% Search results
  - 10% Member dashboard
- **Targets:**
  - p95 LCP < 2.5s
  - p95 API response < 300ms
  - Error rate < 0.1%
  - No 5xx errors

**Run:**
```bash
k6 run k6/page-load.js
```

## Running Tests

### Individual Tests

Run a specific test scenario:

```bash
# From load-tests directory
k6 run k6/search-load.js

# With custom configuration
k6 run --vus 200 --duration 10m k6/search-load.js

# Output results to file
k6 run --out json=results/search-load.json k6/search-load.js
```

### Full Test Suite

Run all tests sequentially with monitoring:

```bash
./scripts/run-all-tests.sh
```

This will:
1. Run baseline performance tests
2. Execute all load test scenarios
3. Collect metrics from monitoring systems
4. Generate comprehensive report

### CI/CD Integration

Run tests in CI/CD pipeline:

```bash
# Run with strict thresholds (fail fast)
k6 run --quiet --no-color k6/search-load.js

# Exit code 0 = all tests passed
# Exit code non-zero = some tests failed
```

## Monitoring During Tests

### Real-time Monitoring

While tests run, monitor these systems:

1. **k6 Output:**
   - Live metrics in terminal
   - HTTP request duration percentiles
   - Error rates
   - Virtual user count

2. **OpenTelemetry (Jaeger UI):**
   - Trace latency breakdown
   - Service dependencies
   - Error traces
   - Database query performance

3. **Prometheus/Grafana:**
   - CPU and memory usage
   - Request rates
   - Database connection pool
   - Cache hit rates
   - Error rates by endpoint

4. **Sentry:**
   - Real-time errors
   - Performance issues
   - Transaction traces

### Metrics to Watch

**Critical Alerts:**
- Error rate > 1%
- p95 latency exceeds targets
- Memory usage > 80%
- CPU usage > 90%
- Database connection pool exhausted
- Cache hit rate < 70%

## Performance Targets

All tests must meet these targets to pass:

| Metric | Target | Critical |
|--------|--------|----------|
| API endpoints p95 | < 300ms | < 500ms |
| Search queries p95 | < 1.2s | < 2s |
| Page load LCP p95 | < 2.5s | < 4s |
| Error rate | < 0.1% | < 1% |
| RTC drop rate | < 1% | < 5% |
| Database queries p95 | < 100ms | < 200ms |
| Webhook processing p95 | < 500ms | < 1s |

**Target:** All metrics meet "Target" column
**Critical:** System is unstable if any metric exceeds "Critical" column

## Interpreting Results

### k6 Metrics

Key metrics from k6 output:

```
http_req_duration..............: avg=245ms min=120ms med=230ms max=1.2s p(95)=450ms p(99)=800ms
http_req_failed................: 0.05%  (50 out of 100000)
iterations.....................: 100000 (1666.67/s)
vus............................: 100 min=0 max=100
```

- `http_req_duration p(95)`: 95th percentile latency - **primary metric**
- `http_req_failed`: Error rate - should be < 0.1%
- `iterations`: Total requests completed
- `vus`: Virtual users (concurrent connections)

### Pass/Fail Criteria

Tests automatically pass/fail based on thresholds defined in each script:

- ✅ **PASS:** All thresholds met
- ❌ **FAIL:** One or more thresholds exceeded

### Common Bottlenecks

If tests fail, investigate:

1. **High Latency (p95 > target):**
   - Slow database queries (check indexes)
   - Missing cache hits (check Redis)
   - Network latency (check service mesh)
   - CPU bottleneck (check profiling)

2. **High Error Rate:**
   - Connection pool exhaustion
   - Rate limiting triggered
   - Memory leaks
   - Unhandled exceptions

3. **Resource Exhaustion:**
   - Memory leaks (check heap dumps)
   - Connection leaks (check pool metrics)
   - File descriptor limits
   - Database connection limits

See `/docs/performance/OPTIMIZATION_GUIDE.md` for detailed troubleshooting.

## Optimization Workflow

1. **Baseline:** Run tests to establish current performance
2. **Identify:** Find bottlenecks from metrics and traces
3. **Optimize:** Apply targeted fixes (indexes, caching, etc.)
4. **Validate:** Re-run tests to measure improvement
5. **Document:** Record changes in load test report

## Test Data Setup

Before running tests, ensure staging has realistic data:

- 1,000+ member accounts
- 500+ events (past and upcoming)
- 200+ instructors with profiles
- 5,000+ searchable content items
- 100+ active subscriptions

**Script to seed test data:**
```bash
cd backend
python scripts/seed_load_test_data.py --environment=staging
```

## Troubleshooting

### Tests Fail to Start

```bash
# Check k6 installation
k6 version

# Verify staging environment is accessible
curl https://staging.wwmaa.com/health

# Check environment variables
cat .env.load-tests
```

### Connection Refused Errors

- Verify staging environment is running
- Check firewall rules allow test traffic
- Ensure load balancer can handle concurrent connections

### Inconsistent Results

- Run tests multiple times to establish baseline
- Ensure staging environment has stable load
- Check for background jobs or deployments during tests

### Memory Issues on Test Runner

- Reduce virtual users: `k6 run --vus 50`
- Run tests individually instead of all at once
- Use larger test runner instance

## Best Practices

1. **Always test against staging** - never production
2. **Run during off-hours** - minimize impact on staging users
3. **Monitor in real-time** - catch issues immediately
4. **Document everything** - record results and fixes
5. **Incremental load** - ramp up gradually to find breaking points
6. **Reproducible** - same test should give consistent results
7. **Version control** - commit test scripts and results

## Results and Reports

After running tests, generate report:

```bash
./scripts/generate-report.sh
```

Report location: `/docs/performance/LOAD_TEST_REPORT.md`

Includes:
- Test results (pass/fail)
- Performance metrics (all percentiles)
- Bottlenecks identified
- Optimizations applied
- Before/after comparisons
- Production readiness assessment

## Support

- **Load Testing Issues:** See `/docs/performance/OPTIMIZATION_GUIDE.md`
- **Environment Issues:** See US-081 staging setup
- **Monitoring Issues:** See US-065 OpenTelemetry setup
- **k6 Documentation:** https://k6.io/docs/

## Next Steps

After all tests pass:
1. Generate final load test report
2. Document optimizations in optimization guide
3. Mark US-080 as complete
4. Proceed with production deployment (US-082)

---

**Last Updated:** 2025-11-10
**Owner:** QA Team
**Related:** US-080, US-081, US-065, US-067
