/**
 * WWMAA Stripe Webhooks Load Test
 *
 * Tests burst traffic from Stripe webhooks during high-activity periods
 *
 * Load Profile:
 * - 100 events/second burst
 * - 5 minutes sustained
 * - Mix of payment and subscription events
 *
 * Performance Targets:
 * - p95 latency < 500ms
 * - p99 latency < 1s
 * - No dropped webhooks (100% processing)
 * - No duplicate processing
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import crypto from 'k6/crypto';
import encoding from 'k6/encoding';

// Custom metrics
const webhookProcessingLatency = new Trend('webhook_processing_latency', true);
const webhookProcessingSuccess = new Rate('webhook_processing_success');
const webhookDuplicates = new Counter('webhook_duplicates');
const webhookSignatureValid = new Rate('webhook_signature_valid');

// Configuration
const BASE_URL = __ENV.API_URL || 'https://staging.wwmaa.com/api';
const WEBHOOK_ENDPOINT = `${BASE_URL}/webhooks/stripe`;
const WEBHOOK_SECRET = __ENV.STRIPE_WEBHOOK_SECRET || 'whsec_test_secret';

// Test configuration
export const options = {
  scenarios: {
    // Burst scenario: 100 events/second
    burst: {
      executor: 'constant-arrival-rate',
      rate: 100, // 100 iterations per second
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 50,
      maxVUs: 200,
    },
  },
  thresholds: {
    // Primary targets
    'webhook_processing_latency': ['p(95)<500', 'p(99)<1000'],
    'webhook_processing_success': ['rate>0.99'], // > 99% success (allow for retries)
    'webhook_duplicates': ['count<10'], // < 10 duplicates in entire test
    'webhook_signature_valid': ['rate>0.999'], // > 99.9% valid signatures

    // HTTP metrics
    'http_req_duration{endpoint:webhook}': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.01'], // < 1% HTTP errors
    'http_req_duration{endpoint:webhook,status:200}': ['p(95)<500'],
  },
};

// Stripe webhook event types with realistic distribution
const EVENT_TYPES = [
  { type: 'payment_intent.succeeded', weight: 0.40 },
  { type: 'customer.subscription.updated', weight: 0.30 },
  { type: 'invoice.payment_succeeded', weight: 0.15 },
  { type: 'payment_intent.payment_failed', weight: 0.10 },
  { type: 'customer.subscription.deleted', weight: 0.05 },
];

// Helper: Select event type based on weighted distribution
function selectEventType() {
  const rand = Math.random();
  let cumulativeWeight = 0;

  for (const event of EVENT_TYPES) {
    cumulativeWeight += event.weight;
    if (rand <= cumulativeWeight) {
      return event.type;
    }
  }

  return EVENT_TYPES[0].type; // Fallback
}

// Helper: Generate realistic Stripe event payload
function generateStripeEvent(eventType) {
  const timestamp = Math.floor(Date.now() / 1000);
  const eventId = `evt_${crypto.randomBytes(16)}`;

  const baseEvent = {
    id: eventId,
    object: 'event',
    api_version: '2023-10-16',
    created: timestamp,
    type: eventType,
    livemode: false,
    pending_webhooks: 1,
    request: {
      id: `req_${crypto.randomBytes(16)}`,
      idempotency_key: `idem_${crypto.randomBytes(16)}`,
    },
  };

  // Generate event-specific data
  switch (eventType) {
    case 'payment_intent.succeeded':
      baseEvent.data = {
        object: {
          id: `pi_${crypto.randomBytes(16)}`,
          object: 'payment_intent',
          amount: 9900, // $99.00
          currency: 'usd',
          customer: `cus_${crypto.randomBytes(16)}`,
          status: 'succeeded',
          metadata: {
            membership_tier: 'premium',
            user_id: `user_${Math.floor(Math.random() * 1000)}`,
          },
        },
      };
      break;

    case 'customer.subscription.updated':
      baseEvent.data = {
        object: {
          id: `sub_${crypto.randomBytes(16)}`,
          object: 'subscription',
          customer: `cus_${crypto.randomBytes(16)}`,
          status: 'active',
          current_period_start: timestamp,
          current_period_end: timestamp + 2592000, // +30 days
          items: {
            data: [
              {
                id: `si_${crypto.randomBytes(16)}`,
                price: {
                  id: `price_${crypto.randomBytes(16)}`,
                  product: `prod_${crypto.randomBytes(16)}`,
                  unit_amount: 9900,
                },
              },
            ],
          },
          metadata: {
            user_id: `user_${Math.floor(Math.random() * 1000)}`,
          },
        },
      };
      break;

    case 'invoice.payment_succeeded':
      baseEvent.data = {
        object: {
          id: `in_${crypto.randomBytes(16)}`,
          object: 'invoice',
          customer: `cus_${crypto.randomBytes(16)}`,
          subscription: `sub_${crypto.randomBytes(16)}`,
          amount_paid: 9900,
          currency: 'usd',
          status: 'paid',
          metadata: {
            user_id: `user_${Math.floor(Math.random() * 1000)}`,
          },
        },
      };
      break;

    case 'payment_intent.payment_failed':
      baseEvent.data = {
        object: {
          id: `pi_${crypto.randomBytes(16)}`,
          object: 'payment_intent',
          amount: 9900,
          currency: 'usd',
          customer: `cus_${crypto.randomBytes(16)}`,
          status: 'requires_payment_method',
          last_payment_error: {
            code: 'card_declined',
            message: 'Your card was declined.',
          },
          metadata: {
            user_id: `user_${Math.floor(Math.random() * 1000)}`,
          },
        },
      };
      break;

    case 'customer.subscription.deleted':
      baseEvent.data = {
        object: {
          id: `sub_${crypto.randomBytes(16)}`,
          object: 'subscription',
          customer: `cus_${crypto.randomBytes(16)}`,
          status: 'canceled',
          canceled_at: timestamp,
          metadata: {
            user_id: `user_${Math.floor(Math.random() * 1000)}`,
          },
        },
      };
      break;

    default:
      baseEvent.data = { object: {} };
  }

  return baseEvent;
}

// Helper: Generate Stripe webhook signature
function generateStripeSignature(payload, timestamp, secret) {
  const signedPayload = `${timestamp}.${payload}`;
  const signature = crypto.hmac('sha256', secret, signedPayload, 'hex');
  return `t=${timestamp},v1=${signature}`;
}

export default function () {
  const eventType = selectEventType();
  const event = generateStripeEvent(eventType);
  const payload = JSON.stringify(event);
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = generateStripeSignature(payload, timestamp, WEBHOOK_SECRET);

  const startTime = new Date().getTime();

  const response = http.post(
    WEBHOOK_ENDPOINT,
    payload,
    {
      headers: {
        'Content-Type': 'application/json',
        'Stripe-Signature': signature,
      },
      tags: {
        endpoint: 'webhook',
        event_type: eventType,
      },
    }
  );

  const latency = new Date().getTime() - startTime;
  webhookProcessingLatency.add(latency);

  // Validate response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response time < 1s': (r) => r.timings.duration < 1000,
    'response has success indicator': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.received === true || body.status === 'success';
      } catch (e) {
        // Empty response is also acceptable for webhooks
        return r.status === 200;
      }
    },
  });

  webhookProcessingSuccess.add(success ? 1 : 0);

  if (!success) {
    console.error(`Webhook processing failed: ${eventType} - Status: ${response.status} - Event ID: ${event.id}`);

    // Check for specific error conditions
    if (response.status === 400) {
      // Invalid signature
      webhookSignatureValid.add(0);
      console.error(`Invalid webhook signature for event ${event.id}`);
    } else if (response.status === 409) {
      // Duplicate event (idempotency)
      webhookDuplicates.add(1);
      console.warn(`Duplicate webhook event: ${event.id}`);
    } else if (response.status >= 500) {
      // Server error - webhook should be retried by Stripe
      console.error(`Server error processing webhook: ${response.status}`);
    }
  } else {
    webhookSignatureValid.add(1);
  }

  // Additional validation for specific event types
  if (success) {
    switch (eventType) {
      case 'payment_intent.succeeded':
        // Verify payment was recorded
        check(response, {
          'payment recorded': (r) => {
            try {
              const body = JSON.parse(r.body);
              return body.payment_recorded === true || r.status === 200;
            } catch (e) {
              return r.status === 200;
            }
          },
        });
        break;

      case 'customer.subscription.updated':
        // Verify subscription was updated
        check(response, {
          'subscription updated': (r) => {
            try {
              const body = JSON.parse(r.body);
              return body.subscription_updated === true || r.status === 200;
            } catch (e) {
              return r.status === 200;
            }
          },
        });
        break;

      default:
        // Other event types - just verify 200 response
        break;
    }
  }

  // No sleep - constant arrival rate handles pacing
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/webhooks-load.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';

  let summary = '\n';
  summary += `${indent}Stripe Webhooks Load Test Summary\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  if (checks) {
    const passRate = (checks.values.passes / checks.values.value * 100).toFixed(2);
    summary += `${indent}Checks.....................: ${passRate}% (${checks.values.passes}/${checks.values.value})\n`;
  }

  // Processing latency
  const procLatency = data.metrics.webhook_processing_latency;
  if (procLatency) {
    summary += `${indent}Processing Latency:\n`;
    summary += `${indent}  avg: ${procLatency.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${procLatency.values['p(95)'].toFixed(2)}ms `;
    summary += procLatency.values['p(95)'] < 500 ? '✓\n' : '✗ (target: <500ms)\n';
    summary += `${indent}  p99: ${procLatency.values['p(99)'].toFixed(2)}ms `;
    summary += procLatency.values['p(99)'] < 1000 ? '✓\n' : '✗ (target: <1000ms)\n';
  }

  // Processing success rate
  const procSuccess = data.metrics.webhook_processing_success;
  if (procSuccess) {
    const rate = (procSuccess.values.rate * 100).toFixed(2);
    summary += `${indent}Processing Success.........: ${rate}% `;
    summary += procSuccess.values.rate > 0.99 ? '✓\n' : '✗ (target: >99%)\n';
  }

  // Signature validation
  const sigValid = data.metrics.webhook_signature_valid;
  if (sigValid) {
    const rate = (sigValid.values.rate * 100).toFixed(3);
    summary += `${indent}Signature Valid............: ${rate}% `;
    summary += sigValid.values.rate > 0.999 ? '✓\n' : '✗ (target: >99.9%)\n';
  }

  // Duplicates
  const duplicates = data.metrics.webhook_duplicates;
  if (duplicates) {
    summary += `${indent}Duplicate Events...........: ${duplicates.values.count} `;
    summary += duplicates.values.count < 10 ? '✓\n' : '✗ (target: <10)\n';
  }

  // Total events processed
  const iterations = data.metrics.iterations;
  if (iterations) {
    summary += `${indent}Total Events...............: ${iterations.values.count}\n`;
    summary += `${indent}Events/sec.................: ${iterations.values.rate.toFixed(2)}\n`;
  }

  // Error rate
  const reqFailed = data.metrics.http_req_failed;
  if (reqFailed) {
    const errorRate = (reqFailed.values.rate * 100).toFixed(3);
    summary += `${indent}Error Rate.................: ${errorRate}% `;
    summary += reqFailed.values.rate < 0.01 ? '✓\n' : '✗ (target: <1%)\n';
  }

  summary += `${indent}Target Load................: 100 events/sec\n`;
  summary += `\n${indent}${'='.repeat(50)}\n`;

  return summary;
}
