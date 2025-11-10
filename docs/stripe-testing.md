# Stripe Testing Guide for WWMAA

This document provides comprehensive guidance for testing Stripe integration in the WWMAA backend system.

## Table of Contents

1. [Overview](#overview)
2. [Test Mode Configuration](#test-mode-configuration)
3. [Test Card Numbers](#test-card-numbers)
4. [Testing Subscriptions](#testing-subscriptions)
5. [Testing Webhooks](#testing-webhooks)
6. [Product Setup](#product-setup)
7. [Common Test Scenarios](#common-test-scenarios)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The WWMAA backend uses Stripe for payment processing with three membership tiers:

- **Basic Membership**: $29/year
- **Premium Membership**: $79/year
- **Instructor Membership**: $149/year

All subscriptions use **annual billing cycles** as specified in US-021.

---

## Test Mode Configuration

### Environment Variables

Ensure your `.env` file has test mode Stripe keys:

```bash
# Test Mode Keys (from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_test_your_test_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### Verifying Test Mode

Test mode keys always start with:
- Secret Key: `sk_test_`
- Publishable Key: `pk_test_`
- Webhook Secret: `whsec_test_`

**Important**: Never use live mode keys (`sk_live_`, `pk_live_`) during development or testing!

---

## Test Card Numbers

Stripe provides test card numbers that simulate different scenarios. **Never use real card numbers in test mode.**

### Successful Payments

#### Basic Test Card
```
Card Number: 4242 4242 4242 4242
Expiration: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

#### International Test Cards

**Visa (3D Secure 2 - Authentication Required)**
```
Card Number: 4000 0027 6000 3184
Expiration: Any future date
CVC: Any 3 digits
```

**Mastercard**
```
Card Number: 5555 5555 5555 4444
Expiration: Any future date
CVC: Any 3 digits
```

**American Express**
```
Card Number: 3782 822463 10005
Expiration: Any future date
CVC: Any 4 digits
```

### Failed Payments

Use these cards to test error handling:

#### Generic Decline
```
Card Number: 4000 0000 0000 0002
Result: Card declined
```

#### Insufficient Funds
```
Card Number: 4000 0000 0000 9995
Result: Card declined - insufficient_funds
```

#### Expired Card
```
Card Number: 4000 0000 0000 0069
Result: Card declined - expired_card
```

#### Processing Error
```
Card Number: 4000 0000 0000 0119
Result: Card declined - processing_error
```

#### Incorrect CVC
```
Card Number: 4000 0000 0000 0127
Result: Card declined - incorrect_cvc
```

### Specific Response Codes

#### Requires Authentication (3D Secure)
```
Card Number: 4000 0025 0000 3155
Result: Requires authentication
Action: Complete 3D Secure flow
```

#### Rate Limit Error
```
Card Number: 4000 0000 0000 0275
Result: Simulates rate limiting
```

---

## Testing Subscriptions

### Creating Test Subscriptions

#### 1. Basic Membership ($29/year)

```bash
# Create checkout session
curl -X POST http://localhost:8000/api/stripe/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "application_id": "app_123",
    "tier_id": "basic",
    "customer_email": "test@example.com"
  }'
```

**Expected Response:**
```json
{
  "session_id": "cs_test_...",
  "url": "https://checkout.stripe.com/...",
  "amount": 2900,
  "currency": "usd",
  "tier": "basic",
  "mode": "subscription"
}
```

#### 2. Premium Membership ($79/year)

```bash
curl -X POST http://localhost:8000/api/stripe/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_456",
    "application_id": "app_456",
    "tier_id": "premium",
    "customer_email": "premium@example.com"
  }'
```

#### 3. Instructor Membership ($149/year)

```bash
curl -X POST http://localhost:8000/api/stripe/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_789",
    "application_id": "app_789",
    "tier_id": "lifetime",
    "customer_email": "instructor@example.com"
  }'
```

### Testing Annual Billing

All subscriptions use **annual billing cycles**. To verify:

1. Create a subscription using test card `4242 4242 4242 4242`
2. Check Stripe Dashboard → Subscriptions
3. Verify "Billing interval" shows "Yearly"
4. Verify "Next payment" is 1 year from creation date

### Testing Trial Periods

To test subscriptions with trial periods:

```python
# In Python code
from backend.services.stripe_service import get_stripe_service

service = get_stripe_service()
session = service.create_checkout_session(
    user_id="user_123",
    application_id="app_123",
    tier_id="premium",
    customer_email="test@example.com"
)
```

Then modify the subscription in Stripe Dashboard to add a trial period.

### Canceling Test Subscriptions

```python
# Cancel at period end
from backend.services.stripe_service import get_stripe_service

service = get_stripe_service()
# subscription cancellation logic here
```

---

## Testing Webhooks

Webhooks allow Stripe to notify your application about payment events.

### Webhook Endpoint

```
https://api.wwmaa.com/api/webhooks/stripe
```

For local development:
```
http://localhost:8000/api/webhooks/stripe
```

### Setting Up Webhook Testing

#### Option 1: Stripe CLI (Recommended)

1. **Install Stripe CLI**
   ```bash
   brew install stripe/stripe-cli/stripe  # macOS
   # or download from https://stripe.com/docs/stripe-cli
   ```

2. **Login to Stripe**
   ```bash
   stripe login
   ```

3. **Forward Webhooks to Local Server**
   ```bash
   stripe listen --forward-to localhost:8000/api/webhooks/stripe
   ```

4. **Get Webhook Signing Secret**
   ```bash
   # The CLI will display a webhook signing secret like:
   # whsec_test_secret_abc123xyz789
   ```

5. **Update .env File**
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_test_secret_abc123xyz789
   ```

#### Option 2: ngrok (Alternative)

1. **Install ngrok**
   ```bash
   npm install -g ngrok
   # or download from https://ngrok.com/
   ```

2. **Start ngrok tunnel**
   ```bash
   ngrok http 8000
   ```

3. **Configure Webhook in Stripe Dashboard**
   - Go to Stripe Dashboard → Developers → Webhooks
   - Click "Add endpoint"
   - Enter ngrok URL: `https://abc123.ngrok.io/api/webhooks/stripe`
   - Select events to listen for (see below)
   - Copy webhook signing secret to `.env`

### Important Webhook Events

Configure these webhook events in Stripe Dashboard:

#### Payment Events
- `checkout.session.completed` - Payment completed
- `checkout.session.expired` - Checkout session expired
- `invoice.payment_succeeded` - Subscription payment succeeded
- `invoice.payment_failed` - Subscription payment failed

#### Subscription Events
- `customer.subscription.created` - New subscription created
- `customer.subscription.updated` - Subscription updated
- `customer.subscription.deleted` - Subscription canceled

#### Customer Events
- `customer.created` - New customer created
- `customer.updated` - Customer updated
- `payment_method.attached` - Payment method added

### Testing Webhook Signature Verification

```python
# Test webhook signature verification
from backend.services.stripe_service import get_stripe_service

service = get_stripe_service()

# This will raise StripeWebhookError if signature is invalid
event = service.verify_webhook_signature(
    payload=request_body_bytes,
    signature=request.headers.get('Stripe-Signature')
)
```

### Triggering Test Webhooks

#### Using Stripe CLI
```bash
# Trigger a payment succeeded event
stripe trigger payment_intent.succeeded

# Trigger a subscription created event
stripe trigger customer.subscription.created

# Trigger a checkout session completed event
stripe trigger checkout.session.completed
```

#### Using Stripe Dashboard
1. Go to Stripe Dashboard → Developers → Events
2. Click on any event
3. Click "Send test webhook"

---

## Product Setup

### Running the Product Setup Script

The `setup_stripe_products.py` script creates products and prices in Stripe.

#### Test Mode (Recommended for Development)

```bash
cd /Users/aideveloper/Desktop/wwmaa/backend

# Setup products in test mode
python scripts/setup_stripe_products.py --mode test

# Force recreate if products already exist
python scripts/setup_stripe_products.py --mode test --force
```

**Expected Output:**
```
======================================================================
Stripe Product Setup - TEST mode
======================================================================

Setting up membership tiers...
======================================================================

Creating product: Basic Membership
  Description: Basic WWMAA membership with access to member directory and events
  ✓ Product created: prod_test_abc123

Creating price for Basic Membership
  Amount: $29.00 USD
  Billing: Annual
  ✓ Price created: price_test_xyz789

[Similar output for Premium and Instructor tiers]

======================================================================
Setup Summary
======================================================================

Mode: TEST
Products created: 3
Prices created: 3

✓ All products and prices created successfully!

Product & Price IDs:

  BASIC:
    Product ID: prod_test_abc123
    Price ID:   price_test_xyz789
    Amount:     $29.00/year

  PREMIUM:
    Product ID: prod_test_def456
    Price ID:   price_test_uvw012
    Amount:     $79.00/year

  INSTRUCTOR:
    Product ID: prod_test_ghi789
    Price ID:   price_test_rst345
    Amount:     $149.00/year

======================================================================

✓ Results saved to: /path/to/stripe_products_test.json
```

#### Live Mode (Production Only)

**WARNING**: Only run this in production when ready to go live!

```bash
# Setup products in live mode
python scripts/setup_stripe_products.py --mode live

# You will be prompted to confirm:
# WARNING: Using live mode. This will create real products in Stripe!
# Continue? (yes/no): yes
```

### Verifying Products in Stripe Dashboard

1. Go to Stripe Dashboard → Products
2. Verify three products exist:
   - Basic Membership ($29.00/year)
   - Premium Membership ($79.00/year)
   - Instructor Membership ($149.00/year)
3. Click on each product to verify annual billing cycle

---

## Common Test Scenarios

### Scenario 1: Successful Payment Flow

1. **Create checkout session** for Basic tier
2. **Use test card** `4242 4242 4242 4242`
3. **Complete payment** in Stripe Checkout
4. **Verify webhook** `checkout.session.completed` is received
5. **Check database** for subscription record
6. **Verify user** has active subscription

### Scenario 2: Failed Payment

1. **Create checkout session** for Premium tier
2. **Use declined card** `4000 0000 0000 0002`
3. **Attempt payment** in Stripe Checkout
4. **Verify error** is displayed to user
5. **Check logs** for proper error handling

### Scenario 3: Expired Checkout Session

1. **Create checkout session**
2. **Wait 30+ minutes** (or modify expiration)
3. **Attempt to access** expired session URL
4. **Verify proper** "Session expired" handling

### Scenario 4: Subscription Renewal

1. **Create subscription** with immediate renewal (for testing)
2. **Use Stripe Dashboard** to advance time (test clocks)
3. **Trigger renewal** invoice
4. **Verify webhook** `invoice.payment_succeeded`
5. **Check subscription** status updated

### Scenario 5: Subscription Cancellation

1. **Create active subscription**
2. **Cancel subscription** (at period end)
3. **Verify status** shows `cancel_at_period_end: true`
4. **Advance to end date** using test clocks
5. **Verify webhook** `customer.subscription.deleted`

---

## Troubleshooting

### Issue: Webhook signature verification fails

**Solution:**
1. Check that `STRIPE_WEBHOOK_SECRET` in `.env` matches Stripe Dashboard
2. Verify you're using the correct secret for test vs. live mode
3. Ensure request body is not modified before signature verification
4. Check that request is sent as raw bytes, not parsed JSON

```python
# Correct: Use raw body
payload = request.body  # Django
payload = await request.body()  # FastAPI

# Incorrect: Don't parse first
payload = request.json()  # ✗ Wrong - breaks signature
```

### Issue: "No such product" error

**Solution:**
1. Run product setup script: `python scripts/setup_stripe_products.py --mode test`
2. Verify products exist in Stripe Dashboard
3. Check you're using correct product IDs in code

### Issue: Test payments not working

**Solution:**
1. Verify using test mode API key (`sk_test_...`)
2. Use correct test card number: `4242 4242 4242 4242`
3. Check Stripe Dashboard → Logs for detailed error messages
4. Ensure expiration date is in the future

### Issue: Webhooks not received locally

**Solution:**
1. Ensure Stripe CLI is running: `stripe listen --forward-to localhost:8000/api/webhooks/stripe`
2. Or ensure ngrok tunnel is active: `ngrok http 8000`
3. Check webhook endpoint is publicly accessible
4. Verify webhook endpoint returns 200 status code

### Issue: Amount mismatch

**Solution:**
1. Verify pricing in code matches US-021 requirements:
   - Basic: $29/year = 2900 cents
   - Premium: $79/year = 7900 cents
   - Instructor: $149/year = 14900 cents
2. Check `TIER_PRICING` in `stripe_service.py`

### Issue: Subscription not created in database

**Solution:**
1. Check ZeroDB connection is working
2. Verify `process_successful_payment()` is called after checkout
3. Check application logs for database errors
4. Ensure webhook handler is processing events correctly

---

## Best Practices

### Development
- Always use test mode during development
- Never commit API keys to version control
- Use Stripe CLI for webhook testing
- Test all three membership tiers
- Test both successful and failed payments

### Testing
- Write tests for all payment scenarios
- Mock Stripe API calls in unit tests
- Use Stripe test cards for integration tests
- Verify webhook signature validation
- Test idempotency (running operations multiple times)

### Security
- Always validate webhook signatures
- Never log full credit card numbers (even test cards)
- Implement rate limiting on payment endpoints
- Use HTTPS in production
- Rotate webhook secrets periodically

### Monitoring
- Log all Stripe API calls
- Track payment success/failure rates
- Monitor webhook delivery success
- Set up alerts for payment failures
- Review Stripe Dashboard regularly

---

## Additional Resources

- [Stripe Testing Documentation](https://stripe.com/docs/testing)
- [Stripe Webhook Testing](https://stripe.com/docs/webhooks/test)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Test Card Numbers](https://stripe.com/docs/testing#cards)

---

## Support

For Stripe-related issues:
1. Check Stripe Dashboard → Developers → Logs
2. Review application logs
3. Consult Stripe documentation
4. Contact Stripe support (for account-specific issues)

For WWMAA-specific issues:
1. Check application logs in `/backend/logs/`
2. Review test output and coverage reports
3. Consult this documentation
4. Contact the development team
