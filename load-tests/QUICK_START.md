# WWMAA Load Testing - Quick Start Guide

Get started with load testing in 5 minutes.

## Prerequisites

1. **Install k6:**
   ```bash
   # macOS
   brew install k6

   # Linux
   curl -s https://dl.k6.io/key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/k6-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   ```

2. **Configure environment:**
   ```bash
   cd load-tests
   cp .env.load-tests.example .env.load-tests
   # Edit .env.load-tests with your staging URLs
   ```

3. **Seed test data (staging only):**
   ```bash
   cd ..
   python scripts/seed-load-test-data.py --environment=staging
   ```

## Running Tests

### Run All Tests (Recommended)

```bash
cd load-tests
./scripts/run-all-tests.sh
```

This runs all 5 test scenarios:
- Search load test (9 min)
- RTC load test (12 min)
- Webhooks load test (5 min)
- Event RSVP load test (10 min)
- Page load test (15 min)

**Total time:** ~60 minutes including stabilization periods

### Run Individual Tests

```bash
# Search load test
k6 run k6/search-load.js

# RTC load test
k6 run k6/rtc-load.js

# Webhooks load test
k6 run k6/webhooks-load.js

# Event RSVP load test
k6 run k6/event-rsvp-load.js

# Page load test
k6 run k6/page-load.js

# API endpoints test
k6 run k6/api-load.js
```

### Run Quick Tests (Reduced Duration)

```bash
# 2-minute quick test
k6 run --vus 10 --duration 2m k6/search-load.js

# Custom configuration
k6 run --vus 50 --duration 5m k6/page-load.js
```

## Interpreting Results

### k6 Output

```
✓ status is 200
✓ response time < 1.2s

checks.........................: 99.5% ✓ 9950      ✗ 50
http_req_duration..............: avg=245ms min=120ms med=230ms max=1.2s p(95)=450ms p(99)=800ms
http_req_failed................: 0.05% ✓ 50        ✗ 9950
iterations.....................: 10000 (166.67/s)
vus............................: 100   min=0       max=100
```

**Key Metrics:**
- `checks`: Pass/fail rate (should be > 99%)
- `http_req_duration p(95)`: 95th percentile response time (PRIMARY METRIC)
- `http_req_failed`: Error rate (should be < 1%)
- `iterations`: Total requests completed
- `vus`: Virtual users (concurrent load)

### Pass/Fail

- ✅ **PASS**: All thresholds met (green checkmarks)
- ❌ **FAIL**: One or more thresholds exceeded (red X's)

## What to Do If Tests Fail

1. **Check the logs:**
   ```bash
   cat results/run_*/test_run.log
   ```

2. **Review individual test summaries:**
   ```bash
   cat results/run_*/*_summary.txt
   ```

3. **Check monitoring systems:**
   - OpenTelemetry traces (Jaeger UI)
   - Prometheus metrics (Grafana)
   - Sentry errors

4. **Apply optimizations:**
   - See `/docs/performance/OPTIMIZATION_GUIDE.md`
   - Common fixes: add indexes, enable caching, increase pool sizes

5. **Re-run failed tests:**
   ```bash
   k6 run k6/search-load.js  # Re-run specific test
   ```

## Generate Report

After running tests:

```bash
./scripts/generate-report.sh
```

This creates a comprehensive report:
- `results/run_*/LOAD_TEST_REPORT.md`

## Monitoring During Tests

### 1. k6 Real-Time Output

Watch the terminal output during test execution.

### 2. OpenTelemetry (Jaeger UI)

```
http://localhost:16686
```

- View traces in real-time
- Identify slow spans
- Find error patterns

### 3. Prometheus/Grafana

```
http://localhost:3000
```

- Monitor CPU, memory, database connections
- View request rates and latency
- Check cache hit rates

### 4. Sentry

```
https://sentry.io/organizations/wwmaa/
```

- Real-time error tracking
- Performance issues
- Transaction traces

## Common Issues

### Connection Refused

**Problem:** Can't connect to staging environment

**Solution:**
```bash
# Verify staging is running
curl https://staging.wwmaa.com/health

# Check firewall rules
# Verify VPN connection if required
```

### Rate Limiting

**Problem:** Tests fail with 429 errors

**Solution:**
- Reduce virtual users: `k6 run --vus 50 k6/search-load.js`
- Increase rate limits in staging configuration
- Use load balancer to distribute requests

### Out of Memory

**Problem:** Test runner runs out of memory

**Solution:**
- Reduce virtual users
- Run tests individually instead of all at once
- Use larger test runner instance
- Disable JSON output: Remove `--out json=...`

### Inconsistent Results

**Problem:** Results vary between runs

**Solution:**
- Run tests multiple times to establish baseline
- Ensure staging is not running other workloads
- Check for background jobs or deployments
- Wait longer between test runs (5 minutes)

## Performance Targets

| Test | Metric | Target | Critical |
|------|--------|--------|----------|
| Search | p95 | < 1.2s | < 2s |
| API | p95 | < 300ms | < 500ms |
| RTC | Drop rate | < 1% | < 5% |
| Webhooks | p95 | < 500ms | < 1s |
| Page Load | p95 LCP | < 2.5s | < 4s |

**Target:** All metrics meet "Target" column
**Critical:** System is unstable if any metric exceeds "Critical"

## Next Steps

After all tests pass:

1. ✅ Generate final load test report
2. ✅ Document any optimizations applied
3. ✅ Mark US-080 as complete
4. ✅ Proceed with production deployment (US-082)

## Help & Support

- **Load Testing Issues:** See `/docs/performance/OPTIMIZATION_GUIDE.md`
- **k6 Documentation:** https://k6.io/docs/
- **Staging Environment:** See US-081
- **Monitoring Setup:** See US-065 (OpenTelemetry), US-067 (Prometheus)

---

**Quick Links:**
- [Full README](./README.md)
- [Optimization Guide](../docs/performance/OPTIMIZATION_GUIDE.md)
- [Test Scripts](./k6/)
- [Results Directory](./results/)
