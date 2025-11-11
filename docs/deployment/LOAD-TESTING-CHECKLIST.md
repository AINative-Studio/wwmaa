# Load Testing Pre-Production Checklist

Use this checklist before deploying to production to ensure all performance validation is complete.

## Pre-Testing Setup

### 1. Environment Preparation

- [ ] Staging environment deployed and mirrors production (US-081)
- [ ] Staging database contains realistic data volume
- [ ] Staging has same infrastructure as production
  - [ ] Same server specs (CPU, memory)
  - [ ] Same database configuration
  - [ ] Same Redis configuration
  - [ ] Same load balancer setup
- [ ] Staging is isolated from production traffic
- [ ] SSL certificates valid in staging

### 2. Monitoring Configuration

- [ ] OpenTelemetry configured and exporting traces (US-065)
- [ ] Prometheus collecting metrics (US-067)
- [ ] Grafana dashboards set up for load testing
- [ ] Sentry error tracking enabled (US-066)
- [ ] Database slow query logging enabled
- [ ] Application logging at INFO level (not DEBUG)

### 3. Test Data Preparation

- [ ] Test data seeded using `seed-load-test-data.py`
  - [ ] 1,000+ test users created
  - [ ] 500+ test events created
  - [ ] 200+ test instructors created
  - [ ] 5,000+ searchable content items
  - [ ] 100+ test subscriptions
- [ ] Dedicated load test event created (high capacity)
- [ ] Test user credentials documented in `.env.load-tests`

### 4. Load Testing Tool Setup

- [ ] k6 installed on test runner machine
- [ ] `.env.load-tests` configured with correct URLs
- [ ] Test scripts validated (dry run with 1 VU)
- [ ] Network connectivity from test runner to staging verified
- [ ] Firewall rules allow test traffic

---

## Test Execution

### 5. Pre-Flight Checks

- [ ] All monitoring systems healthy and collecting data
- [ ] No deployments scheduled during test window
- [ ] No other load tests running against staging
- [ ] Database has sufficient disk space
- [ ] Redis has sufficient memory
- [ ] Test team notified of test window

### 6. Baseline Tests

- [ ] Run baseline tests (single user, no load)
- [ ] Verify baseline performance is acceptable
- [ ] Document baseline metrics for comparison

### 7. Load Test Execution

Run all tests using: `./scripts/run-all-tests.sh`

- [ ] **Search Load Test** (9 min)
  - [ ] 100 concurrent users
  - [ ] 1000 queries/min sustained
  - [ ] p95 < 1.2s
  - [ ] Error rate < 0.1%

- [ ] **RTC Load Test** (12 min)
  - [ ] 50 concurrent participants
  - [ ] WebSocket connections stable
  - [ ] Drop rate < 1%
  - [ ] Message delivery > 99%

- [ ] **Webhooks Load Test** (5 min)
  - [ ] 100 events/sec burst
  - [ ] p95 < 500ms
  - [ ] All events processed
  - [ ] No duplicate processing

- [ ] **Event RSVP Load Test** (10 min)
  - [ ] 500 registrations in 10 min
  - [ ] Flash crowd handled
  - [ ] p95 < 800ms
  - [ ] Capacity enforcement working

- [ ] **Page Load Test** (15 min)
  - [ ] 10,000 concurrent visitors
  - [ ] p95 LCP < 2.5s
  - [ ] No 5xx errors
  - [ ] API p95 < 300ms

- [ ] **API Endpoints Test** (5 min)
  - [ ] Auth: 100 req/s
  - [ ] Events: 200 req/s
  - [ ] Subscriptions: 50 req/s
  - [ ] All p95 < 300ms

### 8. During Test Monitoring

Monitor these dashboards in real-time:

- [ ] k6 terminal output (live metrics)
- [ ] Grafana dashboards (CPU, memory, connections)
- [ ] Jaeger UI (distributed traces)
- [ ] Sentry (real-time errors)
- [ ] Application logs (for errors/warnings)

Alert if any of these occur:
- [ ] Error rate > 1%
- [ ] p95 latency exceeds critical threshold
- [ ] CPU > 90% sustained
- [ ] Memory > 85% sustained
- [ ] Database connection pool exhausted
- [ ] Redis connection pool exhausted

---

## Post-Testing Analysis

### 9. Results Review

- [ ] Generate load test report: `./scripts/generate-report.sh`
- [ ] Review all test summaries in `results/run_*/`
- [ ] Check all tests passed (green checkmarks)
- [ ] Verify all metrics within target thresholds
- [ ] No unexpected errors in logs

### 10. Performance Analysis

From OpenTelemetry (Jaeger UI):
- [ ] Review traces for high-latency requests
- [ ] Identify slow spans (database queries, API calls)
- [ ] Check service dependencies are correct
- [ ] No memory leaks detected

From Prometheus (Grafana):
- [ ] CPU usage peak < 70%
- [ ] Memory usage peak < 80%
- [ ] Database connection pool peak < 90%
- [ ] Cache hit rate > 70%
- [ ] No connection exhaustion

From Sentry:
- [ ] No new errors introduced during tests
- [ ] Error rate < 0.1%
- [ ] No performance regressions

### 11. Bottleneck Identification

If any test failed, identify bottlenecks:

- [ ] Slow database queries identified
- [ ] Missing indexes identified
- [ ] Cache miss patterns identified
- [ ] Connection pool sizing issues identified
- [ ] Network latency issues identified

### 12. Optimization Application

Apply optimizations from `/docs/performance/OPTIMIZATION_GUIDE.md`:

**Database:**
- [ ] Add missing indexes
- [ ] Optimize slow queries (N+1 queries, etc.)
- [ ] Adjust connection pool size
- [ ] Enable query result caching

**Caching:**
- [ ] Implement Redis caching layer
- [ ] Configure appropriate TTLs
- [ ] Set up cache warming
- [ ] Implement cache invalidation

**API:**
- [ ] Enable response compression
- [ ] Implement rate limiting
- [ ] Convert blocking endpoints to async
- [ ] Add request batching where applicable

**Static Assets:**
- [ ] Configure CDN
- [ ] Enable asset compression
- [ ] Implement lazy loading
- [ ] Optimize images (WebP)

**Connection Pools:**
- [ ] Tune PostgreSQL connection pool
- [ ] Tune Redis connection pool
- [ ] Configure pool timeouts
- [ ] Enable pool health checks

### 13. Re-Testing After Optimizations

If optimizations were applied:

- [ ] Re-run failed tests
- [ ] Verify improvements in metrics
- [ ] Confirm all tests now pass
- [ ] Update load test report with new results

---

## Production Readiness

### 14. Final Validation

- [ ] All load tests passing
- [ ] All metrics within target thresholds
- [ ] No critical bottlenecks remaining
- [ ] Error rate < 0.1% sustained
- [ ] Monitoring dashboards configured
- [ ] Alerting rules configured and tested
- [ ] On-call runbooks created
- [ ] Rollback procedure documented and tested

### 15. Capacity Planning

- [ ] Document maximum load tested
- [ ] Document headroom (% capacity remaining)
- [ ] Define scaling triggers (CPU, memory, latency)
- [ ] Configure auto-scaling policies
- [ ] Document scaling limits (max instances)
- [ ] Estimate cost at peak load

**Current Capacity (from tests):**
- Concurrent users: _____ (target: 10,000)
- Search queries/min: _____ (target: 1,000)
- RTC participants: _____ (target: 50/session)
- Webhook events/sec: _____ (target: 100)
- Event RSVPs/10min: _____ (target: 500)

**Headroom:** ___% remaining capacity before scaling needed

**Scaling Triggers:**
- CPU > __% for __ minutes → scale up
- Memory > __% for __ minutes → scale up
- API latency p95 > __ms for __ minutes → scale up
- Error rate > __% for __ minutes → alert

### 16. Documentation

- [ ] Load test report reviewed and approved
- [ ] Performance metrics documented
- [ ] Optimization history documented
- [ ] Capacity limits documented
- [ ] Scaling procedures documented
- [ ] Known limitations documented

### 17. Sign-Off

**Load Testing Sign-Off**

I certify that:
- All load tests have been executed successfully
- All performance targets have been met
- Critical optimizations have been applied
- Monitoring and alerting are in place
- The platform is ready for production deployment

**Signatures:**

- QA Engineer: _________________ Date: _______
- DevOps Engineer: _________________ Date: _______
- Technical Lead: _________________ Date: _______
- Product Manager: _________________ Date: _______

---

## Post-Production

### 18. Production Monitoring (First Week)

- [ ] Monitor actual traffic vs. predicted
- [ ] Verify performance targets met in production
- [ ] Check no unexpected errors
- [ ] Validate auto-scaling working correctly
- [ ] Review cost vs. estimates

### 19. Load Test Updates

- [ ] Update test scenarios based on real traffic patterns
- [ ] Adjust performance targets if needed
- [ ] Schedule monthly regression tests
- [ ] Maintain test data in staging

### 20. Continuous Improvement

- [ ] Document lessons learned
- [ ] Update optimization guide with findings
- [ ] Share results with team
- [ ] Plan for next round of optimization

---

## Quick Reference

### Critical Thresholds

| Metric | Target | Critical | Action |
|--------|--------|----------|--------|
| API latency p95 | < 300ms | > 500ms | Scale up |
| Search latency p95 | < 1.2s | > 2s | Optimize queries |
| Error rate | < 0.1% | > 1% | Investigate immediately |
| CPU usage | < 70% | > 90% | Scale up |
| Memory usage | < 80% | > 90% | Scale up |
| DB connections | < 80% | > 95% | Increase pool |
| Cache hit rate | > 70% | < 50% | Review cache strategy |

### Contact Information

- **Load Testing Issues:** #devops on Slack
- **On-Call Engineer:** Check PagerDuty
- **Escalation:** CTO / Engineering Manager

### Resources

- Load Testing Docs: `/load-tests/README.md`
- Optimization Guide: `/docs/performance/OPTIMIZATION_GUIDE.md`
- Monitoring Dashboards: [Grafana URL]
- Error Tracking: [Sentry URL]
- Traces: [Jaeger URL]

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Owner:** DevOps Team
