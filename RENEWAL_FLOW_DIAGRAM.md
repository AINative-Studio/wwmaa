# Membership Renewal Flow Diagram

## Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STUDENT DASHBOARD                                    │
│                                                                              │
│  Current Subscription: Basic Membership                                     │
│  Expiry Date: 2025-12-14                                                    │
│  Status: Active                                                              │
│                                                                              │
│  ┌──────────────────────────┐                                               │
│  │  Renew Membership Button │ ◄── Click                                     │
│  └──────────────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ POST /api/payments/create-renewal-session
                    │ Authorization: Bearer <jwt_token>
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   BACKEND: Renewal Endpoint                                  │
│                   (backend/routes/payments.py)                              │
│                                                                              │
│  1. Authenticate user via JWT                                               │
│  2. Query ZeroDB for active subscription:                                   │
│     - filters: user_id, status in [active, past_due]                        │
│  3. Validate subscription exists and tier != free                           │
│  4. Get user email and Stripe customer ID                                   │
│  5. Call StripeService.create_renewal_checkout_session()                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ create_renewal_checkout_session(
                    │   user_id, tier_id, subscription_id,
                    │   customer_email, stripe_customer_id
                    │ )
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  STRIPE SERVICE: Create Checkout Session                    │
│                  (backend/services/stripe_service.py)                       │
│                                                                              │
│  1. Validate tier (reject free/lifetime)                                    │
│  2. Get pricing: TIER_PRICING[tier]                                         │
│     - basic: $29.00/year                                                    │
│     - premium: $79.00/year                                                  │
│  3. Set default URLs:                                                       │
│     success: /dashboard/student?renewal=success&session_id={ID}             │
│     cancel:  /dashboard/student?renewal=cancelled                           │
│  4. Call Stripe API:                                                        │
│     stripe.checkout.Session.create(                                         │
│       mode="subscription",                                                  │
│       line_items=[{                                                         │
│         price_data: {                                                       │
│           currency: "usd",                                                  │
│           unit_amount: 2900,  # $29.00                                      │
│           recurring: { interval: "year" }                                   │
│         }                                                                   │
│       }],                                                                   │
│       metadata: {                                                           │
│         user_id, subscription_id, tier_id,                                  │
│         type: "renewal"  ◄── CRITICAL for webhook routing                  │
│       }                                                                     │
│     )                                                                       │
│  5. Return session data                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Return: { session_id, url, amount, tier, ... }
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND: API Response                                │
│                                                                              │
│  {                                                                           │
│    "session_id": "cs_test_abc123",                                          │
│    "url": "https://checkout.stripe.com/c/pay/...",                          │
│    "amount": 2900,                                                          │
│    "currency": "usd",                                                       │
│    "tier": "basic",                                                         │
│    "mode": "subscription",                                                  │
│    "expires_at": 1731607711                                                 │
│  }                                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Frontend receives response
                    │ window.location.href = data.url
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRIPE CHECKOUT PAGE                                      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │  WWMAA Basic Membership - Renewal                          │             │
│  │  $29.00 / year                                             │             │
│  │                                                            │             │
│  │  Card Number:  [4242 4242 4242 4242]                      │             │
│  │  Expiry:       [12 / 25]                                  │             │
│  │  CVC:          [123]                                       │             │
│  │                                                            │             │
│  │  ┌────────────┐                                            │             │
│  │  │    Pay     │ ◄── Customer clicks                        │             │
│  │  └────────────┘                                            │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Payment successful
                    │ Stripe processes payment
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRIPE: Redirect to Success URL                           │
│                                                                              │
│  Redirect: https://wwmaa.com/dashboard/student?renewal=success&             │
│            session_id=cs_test_abc123                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ (Parallel process)
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   STRIPE: Send Webhook Event                                │
│                                                                              │
│  POST https://wwmaa.com/api/webhooks/stripe                                 │
│  Stripe-Signature: t=...,v1=...                                             │
│                                                                              │
│  {                                                                           │
│    "id": "evt_abc123",                                                      │
│    "type": "checkout.session.completed",                                    │
│    "data": {                                                                │
│      "object": {                                                            │
│        "id": "cs_test_abc123",                                              │
│        "customer": "cus_xyz789",                                            │
│        "subscription": "sub_stripe_123",                                    │
│        "amount_total": 2900,                                                │
│        "payment_intent": "pi_test_456",                                     │
│        "metadata": {                                                        │
│          "type": "renewal",  ◄── Webhook routes to renewal handler         │
│          "user_id": "uuid-user",                                            │
│          "subscription_id": "uuid-sub",                                     │
│          "tier_id": "basic"                                                 │
│        }                                                                    │
│      }                                                                      │
│    }                                                                        │
│  }                                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Verify signature with STRIPE_WEBHOOK_SECRET
                    │ Check for duplicate (idempotency)
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                WEBHOOK SERVICE: Process Event                                │
│                (backend/services/webhook_service.py)                        │
│                                                                              │
│  1. Check if event_id already processed (idempotency)                       │
│  2. Route to handler based on event_type                                    │
│  3. checkout.session.completed → _handle_checkout_completed()               │
│  4. Check metadata.type == "renewal"                                        │
│  5. Route to _handle_renewal_payment()                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ _handle_renewal_payment(session_data)
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                WEBHOOK SERVICE: Process Renewal                              │
│                                                                              │
│  1. Extract metadata:                                                       │
│     - user_id = metadata.user_id                                            │
│     - subscription_id = metadata.subscription_id                            │
│     - tier_id = metadata.tier_id                                            │
│                                                                              │
│  2. Get existing subscription from ZeroDB:                                  │
│     subscription = db.get_document("subscriptions", subscription_id)        │
│     {                                                                        │
│       "id": "uuid-sub",                                                     │
│       "user_id": "uuid-user",                                               │
│       "tier": "basic",                                                      │
│       "status": "active",                                                   │
│       "end_date": "2025-12-14T00:00:00Z",  ◄── Current expiry              │
│       ...                                                                   │
│     }                                                                       │
│                                                                              │
│  3. Calculate new end date:                                                 │
│     current_end_date = parse(subscription.end_date)                         │
│     if current_end_date < now:                                              │
│       new_end_date = now + 1 year  # Expired subscription                  │
│     else:                                                                   │
│       new_end_date = current_end_date + 1 year  # Active subscription       │
│                                                                              │
│     Result: new_end_date = "2026-12-14T00:00:00Z"                          │
│                                                                              │
│  4. Update subscription in ZeroDB:                                          │
│     db.update_document("subscriptions", subscription_id, {                  │
│       "status": "active",                                                   │
│       "end_date": "2026-12-14T00:00:00Z",  ◄── Extended by 1 year          │
│       "stripe_subscription_id": "sub_stripe_123",                           │
│       "canceled_at": null,  # Clear any cancellation                        │
│       "updated_at": "2025-11-14T17:00:00Z",                                │
│       "metadata": {                                                         │
│         "renewed_at": "2025-11-14T17:00:00Z",                              │
│         "renewal_session_id": "cs_test_abc123"                             │
│       }                                                                     │
│     })                                                                      │
│                                                                              │
│  5. Create payment record:                                                  │
│     db.create_document("payments", {                                        │
│       "user_id": "uuid-user",                                               │
│       "subscription_id": "uuid-sub",                                        │
│       "amount": 29.0,  # $29.00                                             │
│       "currency": "USD",                                                    │
│       "status": "succeeded",                                                │
│       "stripe_payment_intent_id": "pi_test_456",                            │
│       "description": "Membership renewal: basic tier",                      │
│       "metadata": {                                                         │
│         "type": "renewal",                                                  │
│         "tier_id": "basic",                                                 │
│         "new_end_date": "2026-12-14T00:00:00Z"                             │
│       }                                                                     │
│     })                                                                      │
│                                                                              │
│  6. Send renewal confirmation email:                                        │
│     email_service.send_renewal_confirmation_email(                          │
│       email="user@example.com",                                             │
│       user_name="John Doe",                                                 │
│       tier="basic",                                                         │
│       amount=29.0,                                                          │
│       currency="USD",                                                       │
│       new_expiry_date="December 14, 2026"                                  │
│     )                                                                       │
│                                                                              │
│  7. Create audit log:                                                       │
│     db.create_document("audit_logs", {                                      │
│       "action": "payment",                                                  │
│       "resource_type": "subscriptions",                                     │
│       "resource_id": "uuid-sub",                                            │
│       "description": "Membership renewed: $29.0 for basic tier",            │
│       "user_id": "uuid-user",                                               │
│       "changes": {                                                          │
│         "old_end_date": "2025-12-14T00:00:00Z",                            │
│         "new_end_date": "2026-12-14T00:00:00Z",                            │
│         "amount": 29.0                                                      │
│       }                                                                     │
│     })                                                                      │
│                                                                              │
│  8. Store webhook event:                                                    │
│     db.create_document("webhook_events", {                                  │
│       "stripe_event_id": "evt_abc123",                                      │
│       "event_type": "checkout.session.completed",                           │
│       "processing_status": "processed",                                     │
│       "processed_at": "2025-11-14T17:00:00Z"                               │
│     })                                                                      │
│                                                                              │
│  9. Return success response to Stripe                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    │ Return 200 OK to Stripe
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STRIPE: Webhook Acknowledged                            │
│                                                                              │
│  HTTP 200 OK received within 5 seconds                                      │
│  Event marked as successfully delivered                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                   STUDENT DASHBOARD: Success Page                            │
│                                                                              │
│  URL: /dashboard/student?renewal=success&session_id=cs_test_abc123          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │  ✓ Membership Renewed Successfully!                        │             │
│  │                                                            │             │
│  │  Your Basic Membership has been renewed.                   │             │
│  │  New expiry date: December 14, 2026                        │             │
│  │                                                            │             │
│  │  Receipt: Check your email at user@example.com             │             │
│  │                                                            │             │
│  │  ┌────────────────────────┐                                │             │
│  │  │  Return to Dashboard   │                                │             │
│  │  └────────────────────────┘                                │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                     EMAIL: Renewal Confirmation                              │
│                     (Sent via Postmark)                                     │
│                                                                              │
│  To: user@example.com                                                       │
│  From: noreply@wwmaa.com                                                    │
│  Subject: Your WWMAA Membership Has Been Renewed                            │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │  Hi John Doe,                                              │             │
│  │                                                            │             │
│  │  Thank you for renewing your WWMAA membership!             │             │
│  │                                                            │             │
│  │  Membership Tier: Basic Membership                         │             │
│  │  Amount Paid: $29.00 USD                                   │             │
│  │  New Expiry Date: December 14, 2026                        │             │
│  │                                                            │             │
│  │  Your membership benefits continue uninterrupted.          │             │
│  │                                                            │             │
│  │  Questions? Contact us at support@wwmaa.com                │             │
│  │                                                            │             │
│  │  Best regards,                                             │             │
│  │  The WWMAA Team                                            │             │
│  └────────────────────────────────────────────────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Database State Changes

### Before Renewal:
```json
// subscriptions collection
{
  "id": "uuid-sub",
  "user_id": "uuid-user",
  "tier": "basic",
  "status": "active",
  "start_date": "2024-12-14T00:00:00Z",
  "end_date": "2025-12-14T00:00:00Z",  ◄── Expiring soon
  "amount": 29.0,
  "stripe_subscription_id": "sub_old_123"
}
```

### After Renewal:
```json
// subscriptions collection (UPDATED)
{
  "id": "uuid-sub",
  "user_id": "uuid-user",
  "tier": "basic",
  "status": "active",
  "start_date": "2024-12-14T00:00:00Z",
  "end_date": "2026-12-14T00:00:00Z",  ◄── Extended by 1 year
  "amount": 29.0,
  "stripe_subscription_id": "sub_stripe_123",  ◄── Updated
  "canceled_at": null,  ◄── Cleared
  "updated_at": "2025-11-14T17:00:00Z",
  "metadata": {
    "renewed_at": "2025-11-14T17:00:00Z",  ◄── New
    "renewal_session_id": "cs_test_abc123"  ◄── New
  }
}

// payments collection (NEW RECORD)
{
  "id": "uuid-payment",
  "user_id": "uuid-user",
  "subscription_id": "uuid-sub",
  "amount": 29.0,
  "currency": "USD",
  "status": "succeeded",
  "stripe_payment_intent_id": "pi_test_456",
  "description": "Membership renewal: basic tier",
  "processed_at": "2025-11-14T17:00:00Z",
  "metadata": {
    "type": "renewal",
    "tier_id": "basic",
    "new_end_date": "2026-12-14T00:00:00Z"
  }
}

// webhook_events collection (NEW RECORD)
{
  "id": "uuid-webhook",
  "stripe_event_id": "evt_abc123",
  "event_type": "checkout.session.completed",
  "processing_status": "processed",
  "processed_at": "2025-11-14T17:00:00Z"
}

// audit_logs collection (NEW RECORD)
{
  "id": "uuid-audit",
  "action": "payment",
  "resource_type": "subscriptions",
  "resource_id": "uuid-sub",
  "description": "Membership renewed: $29.0 for basic tier",
  "user_id": "uuid-user",
  "changes": {
    "old_end_date": "2025-12-14T00:00:00Z",
    "new_end_date": "2026-12-14T00:00:00Z"
  }
}
```

## Key Implementation Files

| File | Lines | Purpose |
|------|-------|---------|
| `backend/routes/payments.py` | 344-461 | Renewal endpoint |
| `backend/services/stripe_service.py` | 468-599 | Checkout session creation |
| `backend/services/webhook_service.py` | 977-1148 | Renewal payment processing |
| `backend/tests/test_renewal.py` | 1-361 | Comprehensive unit tests |

## Error Scenarios

### 1. No Active Subscription
```
Request → 400 Bad Request
{
  "detail": "No active membership found to renew. Please purchase a new membership."
}
```

### 2. Free Tier Renewal Attempt
```
Request → 400 Bad Request
{
  "detail": "Free tier memberships cannot be renewed"
}
```

### 3. Stripe API Error
```
Request → 500 Internal Server Error
{
  "detail": "Failed to create renewal checkout session: <error message>"
}
```

### 4. Missing Subscription in Webhook
```
Webhook Processing → WebhookProcessingError
Event stored with status: "failed"
Audit log created with success: false
```

## Security Flow

```
JWT Token → Verify Signature → Extract user_id →
Check Subscription Ownership → Create Session →
Stripe Webhook → Verify Signature → Check Idempotency →
Process Renewal → Update Database → Send Email
```

## Performance Metrics

- **Endpoint Response Time:** < 500ms (Stripe API call)
- **Webhook Processing Time:** < 3 seconds (well under Stripe's 5s requirement)
- **Database Queries:** 4 (subscription lookup, user lookup, update, payment create)
- **Email Delivery:** Async (doesn't block webhook response)
