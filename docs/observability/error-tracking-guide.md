# Error Tracking & Alerting Guide (US-066)

## Overview

This guide covers the Sentry-based error tracking and alerting system implemented in Sprint 7. The system provides comprehensive error monitoring, automatic context capture, and intelligent alerting for production issues.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Error Capture](#error-capture)
- [User Context](#user-context)
- [Breadcrumbs](#breadcrumbs)
- [Domain-Specific Tracking](#domain-specific-tracking)
- [Middleware](#middleware)
- [Alerts](#alerts)
- [PII Filtering](#pii-filtering)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Dependencies

```bash
pip install sentry-sdk[fastapi]==1.40.0
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Required
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0

# Optional (with sensible defaults)
SENTRY_ENVIRONMENT=staging
SENTRY_RELEASE=wwmaa-backend@1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### 3. Initialize in Application

Sentry is automatically initialized in `backend/app.py`. No additional setup required!

### 4. Start Tracking Errors

```python
from backend.observability import capture_exception, add_breadcrumb

try:
    result = process_payment(amount=100)
except Exception as e:
    add_breadcrumb('payment', 'Payment processing started', {'amount': 100})
    capture_exception(e)
    raise
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | No | `""` | Sentry Data Source Name. Get from Sentry dashboard. |
| `SENTRY_ENVIRONMENT` | No | `PYTHON_ENV` | Environment name (development, staging, production) |
| `SENTRY_RELEASE` | No | Auto-detected | Release version. Auto-detected from git commit. |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `0.1` | Sample rate for performance monitoring (0.0-1.0) |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | `0.1` | Sample rate for profiling (0.0-1.0) |

### Sampling Strategy

The system uses dynamic sampling based on endpoint importance:

- **Critical endpoints** (payments, auth): 100% sampling
- **Health checks**: 1% sampling
- **Other endpoints**: 10% sampling (default)

To customize sampling, modify `traces_sampler()` in `backend/observability/errors.py`.

## Error Capture

### Automatic Error Capture

All unhandled exceptions are automatically captured thanks to global exception handlers in `app.py`:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Automatically captures to Sentry
    event_id = capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_id": event_id}
    )
```

### Manual Error Capture

For handled errors that you still want to track:

```python
from backend.observability import capture_exception

try:
    risky_operation()
except ValueError as e:
    # Capture but don't crash
    capture_exception(
        e,
        context={'operation': {'type': 'risky', 'param': value}},
        tags={'severity': 'high'},
        level='error'
    )
    # Handle gracefully
    return fallback_value
```

### Message Events

For non-exception events worth tracking:

```python
from backend.observability import capture_message

capture_message(
    "Subscription upgraded successfully",
    level="info",
    context={
        'user': {'id': user_id},
        'subscription': {'tier': 'premium'}
    },
    tags={'event': 'subscription_upgrade'}
)
```

## User Context

### Automatic User Context

The `ErrorTrackingMiddleware` automatically extracts user information from JWT tokens:

```python
# Add to app.py
from backend.middleware import ErrorTrackingMiddleware

app.add_middleware(ErrorTrackingMiddleware)
```

User context includes:
- User ID
- Email (hashed for privacy)
- Username
- Role
- Subscription tier

### Manual User Context

To set user context manually:

```python
from backend.observability import add_user_context

add_user_context(
    user_id="user_123",
    email="user@example.com",
    username="johndoe",
    role="member",
    tier="premium"
)
```

To clear user context (e.g., on logout):

```python
from backend.observability import clear_user_context

clear_user_context()
```

## Breadcrumbs

Breadcrumbs create a trail of events leading up to an error. They're essential for debugging.

### Adding Breadcrumbs

```python
from backend.observability import add_breadcrumb

# Basic breadcrumb
add_breadcrumb(
    'payment',
    'Payment initiated',
    {'amount': 100, 'currency': 'usd'}
)

# API call breadcrumb
add_breadcrumb(
    'api',
    'Stripe API called',
    {'endpoint': '/v1/subscriptions', 'method': 'POST'},
    level='info'
)
```

### Breadcrumb Categories

Standard categories:
- `auth` - Authentication events
- `payment` - Payment processing
- `subscription` - Subscription operations
- `database` - Database queries
- `cache` - Cache operations
- `api` - External API calls
- `http` - HTTP requests
- `navigation` - User navigation
- `user` - User actions
- `business_logic` - Business operations

### Middleware Breadcrumb Helpers

```python
from backend.middleware import (
    track_business_operation,
    track_external_api_call,
    track_database_operation,
    track_cache_operation
)

# Track business logic
track_business_operation(
    "payment_processed",
    {"amount": 100, "currency": "usd"}
)

# Track API calls
track_external_api_call(
    "stripe",
    "/v1/subscriptions",
    "POST",
    status_code=200,
    duration_ms=150.5
)

# Track database operations
track_database_operation(
    "INSERT",
    "subscriptions",
    duration_ms=25.3,
    records_affected=1
)

# Track cache operations
track_cache_operation(
    "GET",
    "user:123",
    hit=True,
    duration_ms=2.5
)
```

## Domain-Specific Tracking

### Payment Errors

```python
from backend.observability import track_payment_error

try:
    subscription = stripe.Subscription.create(...)
except stripe.error.StripeError as e:
    track_payment_error(
        e,
        customer_id="cus_123",
        amount=100.0,
        currency="usd",
        payment_method="card"
    )
    raise
```

### Authentication Errors

```python
from backend.observability import track_auth_error

try:
    authenticate_user(username, password)
except AuthenticationError as e:
    track_auth_error(
        e,
        username=username,
        auth_method="password",
        reason="invalid_credentials"
    )
    raise
```

### Subscription Errors

```python
from backend.observability import track_subscription_error

try:
    create_subscription(customer_id, tier)
except Exception as e:
    track_subscription_error(
        e,
        customer_id=customer_id,
        tier=tier,
        action="create"
    )
    raise
```

### API Errors

```python
from backend.observability import track_api_error

try:
    response = requests.post(api_url, data=payload)
    response.raise_for_status()
except requests.HTTPError as e:
    track_api_error(
        e,
        endpoint=api_url,
        method="POST",
        status_code=response.status_code
    )
    raise
```

### Database Errors

```python
from backend.observability import track_database_error

try:
    db.execute(query)
except DatabaseError as e:
    track_database_error(
        e,
        operation="INSERT",
        table="subscriptions"
    )
    raise
```

## Middleware

### ErrorTrackingMiddleware

Automatically adds request and user context to all errors.

**Installation:**

```python
# In app.py
from backend.middleware import ErrorTrackingMiddleware

app.add_middleware(ErrorTrackingMiddleware)
```

**Features:**
- Extracts user from JWT tokens
- Adds request context (URL, method, headers)
- Tracks request lifecycle breadcrumbs
- Cleans up context after request

**How it works:**

1. Request starts → adds request context
2. Extracts JWT token → adds user context
3. Adds "request started" breadcrumb
4. Processes request
5. Adds "request completed" breadcrumb
6. Cleans up user context

## Alerts

### Configuring Alerts in Sentry Dashboard

1. **Navigate to Alerts**
   - Go to your Sentry project
   - Click "Alerts" in the left sidebar
   - Click "Create Alert"

2. **High Error Rate Alert**
   ```
   WHEN: Error rate > 5% over 5 minutes
   THEN: Send notification to #backend-errors Slack channel

   Configuration:
   - Alert name: "High Error Rate"
   - Metric: Error rate
   - Threshold: > 5%
   - Time window: 5 minutes
   - Action: Slack notification
   ```

3. **Critical Error Alert**
   ```
   WHEN: Errors in payment OR auth flows
   THEN: Send immediate notification to Slack + PagerDuty

   Configuration:
   - Alert name: "Critical Error (Payment/Auth)"
   - Filter: error_type:payment OR error_type:authentication
   - Threshold: >= 1 error
   - Time window: 1 minute
   - Actions:
     * Slack notification (#backend-critical)
     * PagerDuty incident
   ```

4. **API Downtime Alert**
   ```
   WHEN: 10+ consecutive 500 errors
   THEN: Immediate alert

   Configuration:
   - Alert name: "API Downtime"
   - Filter: status_code:500
   - Threshold: >= 10 errors
   - Time window: 2 minutes
   - Actions:
     * Slack notification
     * PagerDuty incident
   ```

5. **New Error Type Alert**
   ```
   WHEN: New error fingerprint detected
   THEN: Slack notification

   Configuration:
   - Alert name: "New Error Type"
   - Metric: New issues
   - Threshold: >= 1
   - Action: Slack notification (#backend-errors)
   ```

### Slack Integration

1. Go to Sentry Settings → Integrations
2. Find and install "Slack"
3. Authorize Sentry to access your Slack workspace
4. Configure notification rules:
   - New issues → `#backend-errors`
   - Regressions → `#backend-errors`
   - High priority → `#backend-critical`

### PagerDuty Integration

1. Go to Sentry Settings → Integrations
2. Find and install "PagerDuty"
3. Connect your PagerDuty account
4. Configure:
   - Critical errors → Trigger incident
   - API downtime → Trigger incident

## PII Filtering

The system automatically filters sensitive data before sending to Sentry.

### Automatically Filtered

- Passwords (any field matching `password`)
- API keys (any field matching `api_key`, `api-key`)
- Tokens (any field matching `token`)
- Secrets (any field matching `secret`)
- Credit card numbers (16-digit card numbers)
- SSNs (XXX-XX-XXXX format)
- Authorization headers
- Cookie headers
- IP addresses (hashed)

### Custom PII Filtering

To add custom PII patterns, edit `backend/observability/errors.py`:

```python
PII_PATTERNS = {
    'password': re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.IGNORECASE),
    'custom_field': re.compile(r'your_pattern_here'),
    # Add more patterns...
}
```

### Verifying PII Filtering

1. Create a test error with PII
2. Check the Sentry event
3. Verify sensitive fields show `[REDACTED_*]`

## Performance Monitoring

### Transaction Tracking

Sentry automatically tracks endpoint performance:

```python
# Automatic - no code needed
# Every endpoint is tracked as a transaction
```

### Custom Transactions

For background jobs or complex operations:

```python
from backend.observability import start_transaction

with start_transaction('/background/email-send', 'background.task') as transaction:
    send_emails()
    transaction.set_tag('email_count', len(emails))
```

### Spans

Track individual operations within a transaction:

```python
from backend.observability import start_span

with start_span('db.query', 'Fetch user data'):
    user = db.query(User).filter_by(id=user_id).first()

with start_span('http.client', 'Call Stripe API'):
    response = stripe.Customer.create(...)
```

### Performance Budgets

Set performance budgets in Sentry Dashboard:
- P95 < 1 second
- P99 < 3 seconds
- Alert when exceeded

## Troubleshooting

### Errors Not Appearing in Sentry

**Check:**
1. Is `SENTRY_DSN` set?
   ```bash
   echo $SENTRY_DSN
   ```

2. Is Sentry initialized?
   ```
   Check logs for: "Sentry initialized for {environment} environment"
   ```

3. Is sampling excluding your errors?
   - Check `traces_sampler()` configuration
   - Critical endpoints should have 100% sampling

4. Is the error being caught before Sentry sees it?
   - Use `capture_exception()` in catch blocks

### Too Many Events

**Reduce noise:**

1. Adjust sampling rates:
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% instead of 10%
   ```

2. Filter out specific errors in Sentry Dashboard:
   - Settings → Inbound Filters
   - Add error messages or types to ignore

3. Use error grouping:
   - Sentry automatically groups similar errors
   - Adjust fingerprints if needed

### PII Leaking

**Steps:**

1. Check the `before_send` hook is working:
   ```python
   # Should see sanitization in logs
   logger.debug("Sanitizing event before send")
   ```

2. Add patterns to `PII_PATTERNS` for custom fields

3. Test with production-like data in staging

### Missing User Context

**Check:**

1. Is `ErrorTrackingMiddleware` installed?
   ```python
   # In app.py
   app.add_middleware(ErrorTrackingMiddleware)
   ```

2. Is JWT token valid?
   - Check token expiration
   - Verify JWT_SECRET matches

3. Is user context cleared prematurely?
   - Context is cleared after each request
   - Set context again if needed in async tasks

### Performance Impact

**Monitor:**

1. Check application latency:
   - Sentry adds ~1-5ms per request
   - Most overhead is in sampling

2. Reduce overhead:
   - Lower sample rates
   - Use async Sentry transport (default)
   - Disable profiling in high-traffic endpoints

3. Check Sentry SDK health:
   ```python
   import sentry_sdk
   print(sentry_sdk.Hub.current.client)
   ```

## Best Practices

### DO

✅ Use domain-specific tracking helpers (`track_payment_error`, etc.)
✅ Add breadcrumbs before critical operations
✅ Set meaningful tags for filtering
✅ Use fingerprints for custom error grouping
✅ Test error tracking in staging before production
✅ Monitor Sentry quota usage
✅ Set up Slack/PagerDuty integrations
✅ Configure alerts for critical flows

### DON'T

❌ Send PII to Sentry without filtering
❌ Capture every error (be selective)
❌ Set sampling rate to 100% in production
❌ Ignore Sentry alerts (tune them instead)
❌ Capture client-side errors in backend (use separate DSN)
❌ Log sensitive data in breadcrumbs
❌ Forget to test PII filtering

## Example: Complete Error Tracking Flow

```python
from backend.observability import (
    add_breadcrumb,
    track_payment_error,
    set_context
)
from backend.middleware import (
    track_business_operation,
    track_external_api_call
)

async def process_subscription(customer_id: str, tier: str):
    """Process subscription with comprehensive error tracking."""

    # Track business operation
    track_business_operation(
        "subscription_started",
        {"customer_id": customer_id, "tier": tier}
    )

    try:
        # Set context for debugging
        set_context("subscription", {
            "customer_id": customer_id,
            "tier": tier,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Add breadcrumb before Stripe call
        add_breadcrumb(
            "payment",
            "Creating Stripe subscription",
            {"tier": tier}
        )

        # Call Stripe
        import time
        start_time = time.time()

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": TIER_PRICES[tier]}],
        )

        duration_ms = (time.time() - start_time) * 1000

        # Track API call
        track_external_api_call(
            "stripe",
            "/v1/subscriptions",
            "POST",
            status_code=200,
            duration_ms=duration_ms
        )

        # Success breadcrumb
        add_breadcrumb(
            "payment",
            "Subscription created successfully",
            {"subscription_id": subscription.id}
        )

        return subscription

    except stripe.error.CardError as e:
        # Track payment error with context
        track_payment_error(
            e,
            customer_id=customer_id,
            amount=TIER_PRICES[tier],
            currency="usd",
            payment_method="card",
            tier=tier
        )
        raise

    except stripe.error.StripeError as e:
        # Track generic Stripe error
        track_payment_error(
            e,
            customer_id=customer_id,
            tier=tier
        )
        raise

    except Exception as e:
        # Catch-all for unexpected errors
        add_breadcrumb(
            "business_logic",
            "Unexpected error in subscription processing",
            {"error_type": type(e).__name__},
            level="error"
        )
        raise
```

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Alert Rules](https://docs.sentry.io/product/alerts/)

## Support

For issues with error tracking:
1. Check this guide
2. Review Sentry Dashboard for quota/errors
3. Check application logs for Sentry initialization
4. Contact team lead or DevOps

---

**Last Updated:** November 2025
**User Story:** US-066
**Sprint:** 7
