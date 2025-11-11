#!/bin/bash

###############################################################################
# WWMAA Load Testing Suite - Orchestration Script
#
# Runs all load tests sequentially with monitoring and reporting
#
# Usage:
#   ./scripts/run-all-tests.sh [--skip-baseline] [--output-dir <dir>]
#
# Options:
#   --skip-baseline    Skip baseline performance tests
#   --output-dir DIR   Output directory for results (default: results/)
#   --quick            Run quick tests (reduced duration)
#   --help             Show this help message
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOAD_TESTS_DIR="$PROJECT_ROOT/load-tests"
K6_DIR="$LOAD_TESTS_DIR/k6"
RESULTS_DIR="$LOAD_TESTS_DIR/results"
BASELINE_DIR="$RESULTS_DIR/baseline"

# Default options
SKIP_BASELINE=false
QUICK_MODE=false
OUTPUT_DIR="$RESULTS_DIR"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-baseline)
      SKIP_BASELINE=true
      shift
      ;;
    --quick)
      QUICK_MODE=true
      shift
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --help)
      grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# //'
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$BASELINE_DIR"

# Timestamp for this test run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="$OUTPUT_DIR/run_$TIMESTAMP"
mkdir -p "$RUN_DIR"

# Log file
LOG_FILE="$RUN_DIR/test_run.log"

# Helper functions
log() {
  echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ $1${NC}" | tee -a "$LOG_FILE"
}

log_warn() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ $1${NC}" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
  log "Checking prerequisites..."

  # Check k6 installation
  if ! command -v k6 &> /dev/null; then
    log_error "k6 is not installed. Please install k6 first."
    echo "Visit: https://k6.io/docs/getting-started/installation/"
    exit 1
  fi

  log_success "k6 is installed: $(k6 version)"

  # Check environment file
  if [ ! -f "$LOAD_TESTS_DIR/.env.load-tests" ]; then
    log_warn ".env.load-tests not found. Using default values."
    log_warn "Create .env.load-tests for custom configuration."
  else
    log_success ".env.load-tests found"
    # Load environment variables
    set -a
    source "$LOAD_TESTS_DIR/.env.load-tests"
    set +a
  fi

  # Check staging environment is accessible
  BASE_URL=${BASE_URL:-"https://staging.wwmaa.com"}
  log "Checking staging environment: $BASE_URL"

  if curl -s --head "$BASE_URL/health" | head -n 1 | grep "200" > /dev/null; then
    log_success "Staging environment is accessible"
  else
    log_error "Staging environment is not accessible: $BASE_URL"
    log_error "Please ensure staging environment is running (see US-081)"
    exit 1
  fi
}

# Run baseline tests (single user, no load)
run_baseline_tests() {
  if [ "$SKIP_BASELINE" = true ]; then
    log_warn "Skipping baseline tests"
    return 0
  fi

  log "Running baseline performance tests (single user, no load)..."

  # Search baseline
  log "Baseline: Search API"
  k6 run --vus 1 --duration 1m --quiet \
    --out "json=$BASELINE_DIR/search_baseline.json" \
    "$K6_DIR/search-load.js" 2>&1 | tee -a "$LOG_FILE"

  # Events API baseline
  log "Baseline: Events API"
  k6 run --vus 1 --duration 1m --quiet \
    --out "json=$BASELINE_DIR/events_baseline.json" \
    -e BASE_URL="$BASE_URL" \
    "$K6_DIR/event-rsvp-load.js" 2>&1 | tee -a "$LOG_FILE"

  # Page load baseline
  log "Baseline: Page Load"
  k6 run --vus 1 --duration 1m --quiet \
    --out "json=$BASELINE_DIR/page_baseline.json" \
    "$K6_DIR/page-load.js" 2>&1 | tee -a "$LOG_FILE"

  log_success "Baseline tests completed"
}

# Run individual load test
run_load_test() {
  local test_name=$1
  local test_file=$2
  local description=$3

  log ""
  log "========================================"
  log "Running: $test_name"
  log "Description: $description"
  log "========================================"

  local test_start=$(date +%s)
  local output_file="$RUN_DIR/${test_name}.json"
  local summary_file="$RUN_DIR/${test_name}_summary.txt"

  # Run test with k6
  if k6 run --out "json=$output_file" "$test_file" 2>&1 | tee "$summary_file" >> "$LOG_FILE"; then
    local test_end=$(date +%s)
    local duration=$((test_end - test_start))
    log_success "$test_name completed in ${duration}s"
    return 0
  else
    local test_end=$(date +%s)
    local duration=$((test_end - test_start))
    log_error "$test_name failed after ${duration}s"
    return 1
  fi
}

# Main test execution
run_load_tests() {
  log "Starting load test suite..."
  log "Output directory: $RUN_DIR"

  local total_tests=5
  local passed_tests=0
  local failed_tests=0

  # Test 1: Search Load
  if run_load_test \
    "search-load" \
    "$K6_DIR/search-load.js" \
    "100 concurrent users, 1000 queries/min, mixed query types"; then
    ((passed_tests++))
  else
    ((failed_tests++))
  fi

  # Wait between tests to allow system to stabilize
  log "Waiting 30s for system to stabilize..."
  sleep 30

  # Test 2: RTC Load
  if run_load_test \
    "rtc-load" \
    "$K6_DIR/rtc-load.js" \
    "50 concurrent participants, WebSocket + video"; then
    ((passed_tests++))
  else
    ((failed_tests++))
  fi

  log "Waiting 30s for system to stabilize..."
  sleep 30

  # Test 3: Stripe Webhooks
  if run_load_test \
    "webhooks-load" \
    "$K6_DIR/webhooks-load.js" \
    "100 events/sec burst, Stripe webhook processing"; then
    ((passed_tests++))
  else
    ((failed_tests++))
  fi

  log "Waiting 30s for system to stabilize..."
  sleep 30

  # Test 4: Event RSVP
  if run_load_test \
    "event-rsvp-load" \
    "$K6_DIR/event-rsvp-load.js" \
    "500 registrations in 10 min, flash crowd simulation"; then
    ((passed_tests++))
  else
    ((failed_tests++))
  fi

  log "Waiting 30s for system to stabilize..."
  sleep 30

  # Test 5: Page Load
  if run_load_test \
    "page-load" \
    "$K6_DIR/page-load.js" \
    "10,000 concurrent visitors, mixed page types"; then
    ((passed_tests++))
  else
    ((failed_tests++))
  fi

  # Summary
  log ""
  log "========================================"
  log "Load Test Suite Summary"
  log "========================================"
  log "Total Tests: $total_tests"
  log_success "Passed: $passed_tests"
  if [ $failed_tests -gt 0 ]; then
    log_error "Failed: $failed_tests"
  else
    log "Failed: $failed_tests"
  fi
  log "Results: $RUN_DIR"
  log ""

  # Return status
  if [ $failed_tests -gt 0 ]; then
    return 1
  else
    return 0
  fi
}

# Collect monitoring data
collect_monitoring_data() {
  log "Collecting monitoring data..."

  # This would integrate with your monitoring systems
  # For now, we'll create placeholders

  # OpenTelemetry traces
  log "Note: Manually export OpenTelemetry traces from Jaeger UI for this time period"

  # Prometheus metrics
  log "Note: Manually export Prometheus metrics from Grafana for this time period"

  # Sentry errors
  log "Note: Check Sentry for errors during test period: $TIMESTAMP"

  # Create monitoring notes file
  cat > "$RUN_DIR/monitoring_notes.txt" <<EOF
Monitoring Data Collection Notes
=================================

Test Run: $TIMESTAMP
Period: $(date)

Required Manual Steps:
1. Export OpenTelemetry traces from Jaeger UI
   - Time range: Test run period
   - Services: All WWMAA services
   - Focus on high-latency traces and errors

2. Export Prometheus metrics from Grafana
   - Time range: Test run period
   - Metrics:
     - CPU usage
     - Memory usage
     - Request rates
     - Database connection pool
     - Cache hit rates
     - Error rates

3. Check Sentry for errors
   - Time range: Test run period
   - Look for:
     - New errors introduced
     - Error rate spikes
     - Performance degradation

4. Database metrics
   - Query performance
   - Connection pool usage
   - Slow query log

Results Location: $RUN_DIR
EOF

  log_success "Monitoring notes created: $RUN_DIR/monitoring_notes.txt"
}

# Generate summary report
generate_summary_report() {
  log "Generating summary report..."

  local report_file="$RUN_DIR/SUMMARY_REPORT.md"

  cat > "$report_file" <<EOF
# WWMAA Load Test Summary Report

**Test Run:** $TIMESTAMP
**Date:** $(date)
**Environment:** ${BASE_URL:-"staging"}

## Test Results

### 1. Search Load Test
- **Status:** See \`search-load_summary.txt\`
- **Target:** 100 concurrent users, 1000 queries/min
- **Results:** See \`search-load.json\` for detailed metrics

### 2. RTC Load Test
- **Status:** See \`rtc-load_summary.txt\`
- **Target:** 50 concurrent participants with WebSocket + video
- **Results:** See \`rtc-load.json\` for detailed metrics

### 3. Stripe Webhooks Load Test
- **Status:** See \`webhooks-load_summary.txt\`
- **Target:** 100 events/sec burst
- **Results:** See \`webhooks-load.json\` for detailed metrics

### 4. Event RSVP Load Test
- **Status:** See \`event-rsvp-load_summary.txt\`
- **Target:** 500 registrations in 10 min with flash crowd
- **Results:** See \`event-rsvp-load.json\` for detailed metrics

### 5. Page Load Test
- **Status:** See \`page-load_summary.txt\`
- **Target:** 10,000 concurrent visitors
- **Results:** See \`page-load.json\` for detailed metrics

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| API endpoints p95 | < 300ms | See individual tests |
| Search queries p95 | < 1.2s | See search-load test |
| Page load LCP p95 | < 2.5s | See page-load test |
| Error rate | < 0.1% | See individual tests |
| RTC drop rate | < 1% | See rtc-load test |
| Database queries p95 | < 100ms | Check monitoring data |

## Next Steps

1. Review individual test summaries for pass/fail status
2. Analyze detailed metrics in JSON output files
3. Collect monitoring data (see \`monitoring_notes.txt\`)
4. Identify bottlenecks from traces and metrics
5. Apply optimizations (see \`/docs/performance/OPTIMIZATION_GUIDE.md\`)
6. Re-run failed tests to validate fixes
7. Generate final load test report

## Files

- Individual test summaries: \`*_summary.txt\`
- Detailed metrics: \`*.json\`
- Test execution log: \`test_run.log\`
- Monitoring notes: \`monitoring_notes.txt\`

## Production Readiness

Based on test results:
- [ ] All tests passed with metrics within targets
- [ ] No critical bottlenecks identified
- [ ] Monitoring shows healthy resource usage
- [ ] Error rates within acceptable limits
- [ ] System can handle expected production load

**Recommendation:** [PASS/FAIL - Update after reviewing all results]

---

**Generated by:** WWMAA Load Testing Suite
**Location:** \`$RUN_DIR\`
EOF

  log_success "Summary report generated: $report_file"
}

# Main execution
main() {
  log "========================================"
  log "WWMAA Load Testing Suite"
  log "========================================"
  log "Start time: $(date)"
  log ""

  # Check prerequisites
  check_prerequisites

  # Run baseline tests
  run_baseline_tests

  # Run load tests
  if run_load_tests; then
    log_success "All load tests passed!"
    test_status="PASSED"
  else
    log_error "Some load tests failed. Review results for details."
    test_status="FAILED"
  fi

  # Collect monitoring data
  collect_monitoring_data

  # Generate summary report
  generate_summary_report

  log ""
  log "========================================"
  log "Test Run Complete"
  log "========================================"
  log "Status: $test_status"
  log "Results: $RUN_DIR"
  log "Summary: $RUN_DIR/SUMMARY_REPORT.md"
  log "End time: $(date)"
  log ""

  if [ "$test_status" = "FAILED" ]; then
    exit 1
  fi
}

# Run main function
main
