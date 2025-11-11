# Error Tracking Quick Reference

Quick reference card for Sentry error tracking in WWMAA backend.

## Setup

```bash
# .env
SENTRY_DSN=https://your-key@o0.ingest.sentry.io/0
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.1
```

## Basic Usage

### Capture Exception

```python
from backend.observability import capture_exception

try:
    risky_operation()
except Exception as e:
    capture_exception(e)
    raise
```

### Add Breadcrumb

```python
from backend.observability import add_breadcrumb

add_breadcrumb('payment', 'Payment started', {'amount': 100})
```

### Set User Context

```python
from backend.observability import add_user_context

add_user_context(
    user_id="user_123",
    email="user@example.com",
    role="member"
)
```

## Domain-Specific Helpers

### Payment Errors

```python
from backend.observability import track_payment_error

try:
    stripe.Subscription.create(...)
except stripe.error.StripeError as e:
    track_payment_error(
        e,
        customer_id="cus_123",
        amount=100.0,
        currency="usd"
    )
    raise
```

### Auth Errors

```python
from backend.observability import track_auth_error

track_auth_error(
    error,
    username="user",
    auth_method="password",
    reason="invalid_credentials"
)
```

### API Errors

```python
from backend.observability import track_api_error

track_api_error(
    error,
    endpoint="/api/test",
    method="POST",
    status_code=500
)
```

### Database Errors

```python
from backend.observability import track_database_error

track_database_error(
    error,
    operation="INSERT",
    table="subscriptions"
)
```

## Middleware Helpers

### Track Business Operations

```python
from backend.middleware import track_business_operation

track_business_operation(
    "payment_processed",
    {"amount": 100, "customer_id": "cus_123"}
)
```

### Track External API Calls

```python
from backend.middleware import track_external_api_call

track_external_api_call(
    "stripe",
    "/v1/subscriptions",
    "POST",
    status_code=200,
    duration_ms=150.5
)
```

### Track Database Operations

```python
from backend.middleware import track_database_operation

track_database_operation(
    "INSERT",
    "subscriptions",
    duration_ms=25.3,
    records_affected=1
)
```

### Track Cache Operations

```python
from backend.middleware import track_cache_operation

track_cache_operation(
    "GET",
    "user:123",
    hit=True,
    duration_ms=2.5
)
```

## Performance Monitoring

### Transactions

```python
from backend.observability import start_transaction

with start_transaction('/api/payments', 'http.server'):
    process_payment()
```

### Spans

```python
from backend.observability import start_span

with start_span('db.query', 'Fetch user'):
    user = db.query(User).first()
```

## Breadcrumb Categories

- `auth` - Authentication
- `payment` - Payments
- `subscription` - Subscriptions
- `database` - Database
- `cache` - Cache
- `api` - External APIs
- `http` - HTTP requests
- `business_logic` - Business operations

## Tags & Context

### Set Tag

```python
from backend.observability import set_tag

set_tag('payment_method', 'stripe')
```

### Set Context

```python
from backend.observability import set_context

set_context('payment', {
    'amount': 100,
    'currency': 'usd'
})
```

## Common Patterns

### Payment Processing

```python
from backend.observability import add_breadcrumb, track_payment_error
from backend.middleware import track_external_api_call

# Start
add_breadcrumb('payment', 'Payment initiated', {'amount': 100})

try:
    # Call Stripe
    result = stripe.Subscription.create(...)

    # Track API call
    track_external_api_call('stripe', '/v1/subscriptions', 'POST', 200)

    # Success
    add_breadcrumb('payment', 'Payment successful', {'id': result.id})

except stripe.error.StripeError as e:
    # Error
    track_payment_error(e, customer_id='cus_123', amount=100.0)
    raise
```

### Authentication Flow

```python
from backend.observability import add_breadcrumb, track_auth_error

add_breadcrumb('auth', 'Login attempt', {'username': username})

try:
    user = authenticate(username, password)
    add_breadcrumb('auth', 'Login successful', {'user_id': user.id})
except AuthError as e:
    track_auth_error(e, username=username, auth_method='password')
    raise
```

### Database Operations

```python
from backend.middleware import track_database_operation

track_database_operation('INSERT', 'subscriptions', 25.3, 1)
result = db.execute(query)
```

## Troubleshooting

### Not Seeing Errors?

1. Check `SENTRY_DSN` is set
2. Check logs for "Sentry initialized"
3. Verify sampling rate
4. Ensure error reaches Sentry (not caught silently)

### Too Many Events?

1. Lower `SENTRY_TRACES_SAMPLE_RATE`
2. Add filters in Sentry dashboard
3. Use error grouping

### Missing Context?

1. Verify middleware installed
2. Check JWT token valid
3. Add context before error occurs

## Best Practices

✅ **DO**
- Use domain helpers (`track_payment_error`, etc.)
- Add breadcrumbs before critical ops
- Set meaningful tags
- Test in staging first

❌ **DON'T**
- Send PII without filtering
- Capture every error (be selective)
- Set 100% sampling in production
- Log sensitive data in breadcrumbs

## Links

- [Full Guide](/docs/observability/error-tracking-guide.md)
- [Sentry Docs](https://docs.sentry.io/)
- [Implementation Summary](/docs/US-066-IMPLEMENTATION-SUMMARY.md)

---

**Quick Help:** For issues, check the [Troubleshooting Guide](/docs/observability/error-tracking-guide.md#troubleshooting)
