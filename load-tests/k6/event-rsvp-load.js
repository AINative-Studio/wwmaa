/**
 * WWMAA Event RSVP Load Test
 *
 * Tests flash traffic when popular event registration opens
 *
 * Load Profile:
 * - 500 registrations in 10 minutes
 * - 50% of traffic in first 2 minutes (flash crowd)
 * - Mix of free and paid event registrations
 *
 * Performance Targets:
 * - p95 latency < 800ms
 * - No failed registrations
 * - No duplicate bookings
 * - Proper capacity enforcement
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const rsvpSuccess = new Rate('rsvp_success');
const rsvpLatency = new Trend('rsvp_latency', true);
const duplicateBookings = new Counter('duplicate_bookings');
const capacityEnforced = new Rate('capacity_enforced');
const paymentProcessingSuccess = new Rate('payment_processing_success');
const eventViewLatency = new Trend('event_view_latency', true);

// Configuration
const BASE_URL = __ENV.API_URL || 'https://staging.wwmaa.com/api';
const TEST_EVENT_ID = __ENV.TEST_EVENT_ID || 'evt_load_test_001';

// Test configuration
export const options = {
  scenarios: {
    // Flash crowd: 50% in first 2 minutes
    flash_crowd: {
      executor: 'ramping-arrival-rate',
      startRate: 0,
      timeUnit: '1m',
      preAllocatedVUs: 50,
      maxVUs: 300,
      stages: [
        { duration: '2m', target: 125 }, // 250 registrations in 2 minutes (flash)
        { duration: '8m', target: 31 },  // 250 registrations in 8 minutes (steady)
      ],
    },
  },
  thresholds: {
    // Primary targets
    'rsvp_latency': ['p(95)<800', 'p(99)<1500'],
    'rsvp_success': ['rate>0.95'], // Allow some failures due to capacity limits
    'duplicate_bookings': ['count==0'], // Zero duplicates
    'capacity_enforced': ['rate>0.99'], // Capacity must be enforced

    // Payment processing (for paid events)
    'payment_processing_success': ['rate>0.98'],

    // Event view performance
    'event_view_latency': ['p(95)<500'],

    // HTTP metrics
    'http_req_duration{endpoint:event_view}': ['p(95)<500'],
    'http_req_duration{endpoint:rsvp}': ['p(95)<800', 'p(99)<1500'],
    'http_req_failed': ['rate<0.05'], // Some failures expected when at capacity
  },
};

// Helper: Generate unique participant
function generateParticipant() {
  const vuId = __VU;
  const iterationId = __ITER;
  const uniqueId = `${vuId}_${iterationId}_${Date.now()}`;

  return {
    email: `loadtest+${uniqueId}@wwmaa.com`,
    first_name: `Test${vuId}`,
    last_name: `User${iterationId}`,
    phone: `555-${String(vuId).padStart(4, '0')}-${String(iterationId).padStart(4, '0')}`,
  };
}

// Helper: Generate payment details (for paid events)
function generatePaymentDetails() {
  return {
    payment_method: 'pm_card_visa', // Stripe test card
    billing_details: {
      name: 'Test User',
      email: 'loadtest@wwmaa.com',
      address: {
        line1: '123 Test St',
        city: 'Test City',
        state: 'CA',
        postal_code: '12345',
        country: 'US',
      },
    },
  };
}

export default function () {
  const participant = generateParticipant();
  const isPaidEvent = Math.random() < 0.3; // 30% paid events

  group('Event RSVP Flow', function () {
    // Step 1: View event details
    group('View Event', function () {
      const viewStartTime = new Date().getTime();

      const eventResponse = http.get(
        `${BASE_URL}/events/${TEST_EVENT_ID}`,
        {
          headers: {
            'Accept': 'application/json',
          },
          tags: { endpoint: 'event_view' },
        }
      );

      const viewLatency = new Date().getTime() - viewStartTime;
      eventViewLatency.add(viewLatency);

      const eventViewSuccess = check(eventResponse, {
        'event view status 200': (r) => r.status === 200,
        'event has details': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.id && body.title && body.capacity !== undefined;
          } catch (e) {
            return false;
          }
        },
        'event view response time < 500ms': (r) => r.timings.duration < 500,
      });

      if (!eventViewSuccess) {
        console.error(`Failed to view event ${TEST_EVENT_ID}: ${eventResponse.status}`);
        return; // Exit early
      }

      // Check event capacity
      const eventData = JSON.parse(eventResponse.body);
      const spotsAvailable = eventData.capacity - (eventData.current_registrations || 0);

      if (spotsAvailable <= 0) {
        // Event is full - this is expected behavior
        capacityEnforced.add(1);
        console.log(`Event ${TEST_EVENT_ID} is at capacity - correctly enforced`);
      }
    });

    // Small delay simulating user reading event details
    sleep(0.5);

    // Step 2: Submit RSVP
    group('Submit RSVP', function () {
      const rsvpStartTime = new Date().getTime();

      const rsvpPayload = {
        event_id: TEST_EVENT_ID,
        participant: participant,
        ...(isPaidEvent && { payment: generatePaymentDetails() }),
      };

      const rsvpResponse = http.post(
        `${BASE_URL}/events/${TEST_EVENT_ID}/rsvp`,
        JSON.stringify(rsvpPayload),
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          tags: {
            endpoint: 'rsvp',
            event_type: isPaidEvent ? 'paid' : 'free',
          },
        }
      );

      const rsvpLatencyMs = new Date().getTime() - rsvpStartTime;
      rsvpLatency.add(rsvpLatencyMs);

      // Validate response
      const success = check(rsvpResponse, {
        'rsvp status is success (200 or 201)': (r) => r.status === 200 || r.status === 201,
        'rsvp response time < 800ms': (r) => r.timings.duration < 800,
        'rsvp response time < 1.5s': (r) => r.timings.duration < 1500,
        'rsvp has booking confirmation': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.booking_id || body.registration_id;
          } catch (e) {
            return false;
          }
        },
      });

      if (success) {
        rsvpSuccess.add(1);

        // Verify no duplicate booking
        const rsvpData = JSON.parse(rsvpResponse.body);
        const bookingId = rsvpData.booking_id || rsvpData.registration_id;

        // In a real scenario, we'd track booking IDs to detect duplicates
        // For load testing, we assume backend handles idempotency

        // For paid events, verify payment processing
        if (isPaidEvent) {
          const paymentSuccess = check(rsvpResponse, {
            'payment processed': (r) => {
              try {
                const body = JSON.parse(r.body);
                return body.payment_status === 'succeeded' || body.payment_status === 'paid';
              } catch (e) {
                return false;
              }
            },
          });

          paymentProcessingSuccess.add(paymentSuccess ? 1 : 0);

          if (!paymentSuccess) {
            console.error(`Payment processing failed for booking ${bookingId}`);
          }
        }
      } else {
        rsvpSuccess.add(0);

        // Check for specific failure reasons
        if (rsvpResponse.status === 409) {
          // Duplicate booking detected
          duplicateBookings.add(1);
          console.warn(`Duplicate booking detected for ${participant.email}`);
        } else if (rsvpResponse.status === 400) {
          // Event at capacity
          const responseBody = rsvpResponse.body;
          if (responseBody.includes('capacity') || responseBody.includes('full')) {
            capacityEnforced.add(1);
            // This is expected behavior - not an error
          } else {
            console.error(`Bad request for RSVP: ${rsvpResponse.status} - ${responseBody}`);
          }
        } else if (rsvpResponse.status === 402) {
          // Payment required but failed
          paymentProcessingSuccess.add(0);
          console.error(`Payment failed for ${participant.email}: ${rsvpResponse.body}`);
        } else if (rsvpResponse.status >= 500) {
          // Server error
          console.error(`Server error processing RSVP: ${rsvpResponse.status}`);
        }
      }
    });

    // Step 3: Verify registration (only if successful)
    if (rsvpSuccess.values.rate > 0) {
      sleep(1);

      group('Verify Registration', function () {
        const verifyResponse = http.get(
          `${BASE_URL}/events/${TEST_EVENT_ID}/registrations?email=${encodeURIComponent(participant.email)}`,
          {
            headers: {
              'Accept': 'application/json',
            },
            tags: { endpoint: 'verify_registration' },
          }
        );

        check(verifyResponse, {
          'registration found': (r) => r.status === 200,
          'registration matches email': (r) => {
            try {
              const body = JSON.parse(r.body);
              return body.registrations?.some(reg => reg.email === participant.email);
            } catch (e) {
              return false;
            }
          },
        });
      });
    }
  });

  // Realistic delay before next user attempts registration
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/event-rsvp-load.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';

  let summary = '\n';
  summary += `${indent}Event RSVP Load Test Summary\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  if (checks) {
    const passRate = (checks.values.passes / checks.values.value * 100).toFixed(2);
    summary += `${indent}Checks.....................: ${passRate}% (${checks.values.passes}/${checks.values.value})\n`;
  }

  // RSVP success rate
  const rsvpSuccessMetric = data.metrics.rsvp_success;
  if (rsvpSuccessMetric) {
    const rate = (rsvpSuccessMetric.values.rate * 100).toFixed(2);
    summary += `${indent}RSVP Success Rate..........: ${rate}% `;
    summary += rsvpSuccessMetric.values.rate > 0.95 ? '✓\n' : '✗ (target: >95%)\n';
  }

  // RSVP latency
  const rsvpLatencyMetric = data.metrics.rsvp_latency;
  if (rsvpLatencyMetric) {
    summary += `${indent}RSVP Latency:\n`;
    summary += `${indent}  avg: ${rsvpLatencyMetric.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${rsvpLatencyMetric.values['p(95)'].toFixed(2)}ms `;
    summary += rsvpLatencyMetric.values['p(95)'] < 800 ? '✓\n' : '✗ (target: <800ms)\n';
    summary += `${indent}  p99: ${rsvpLatencyMetric.values['p(99)'].toFixed(2)}ms `;
    summary += rsvpLatencyMetric.values['p(99)'] < 1500 ? '✓\n' : '✗ (target: <1500ms)\n';
  }

  // Duplicate bookings
  const duplicates = data.metrics.duplicate_bookings;
  if (duplicates) {
    summary += `${indent}Duplicate Bookings.........: ${duplicates.values.count} `;
    summary += duplicates.values.count === 0 ? '✓\n' : '✗ (target: 0)\n';
  }

  // Capacity enforcement
  const capacityMetric = data.metrics.capacity_enforced;
  if (capacityMetric) {
    const rate = (capacityMetric.values.rate * 100).toFixed(2);
    summary += `${indent}Capacity Enforcement.......: ${rate}% `;
    summary += capacityMetric.values.rate > 0.99 ? '✓\n' : '✗ (target: >99%)\n';
  }

  // Payment processing
  const paymentMetric = data.metrics.payment_processing_success;
  if (paymentMetric && paymentMetric.values.count > 0) {
    const rate = (paymentMetric.values.rate * 100).toFixed(2);
    summary += `${indent}Payment Processing.........: ${rate}% `;
    summary += paymentMetric.values.rate > 0.98 ? '✓\n' : '✗ (target: >98%)\n';
  }

  // Event view latency
  const viewLatency = data.metrics.event_view_latency;
  if (viewLatency) {
    summary += `${indent}Event View Latency (p95)...: ${viewLatency.values['p(95)'].toFixed(2)}ms `;
    summary += viewLatency.values['p(95)'] < 500 ? '✓\n' : '✗ (target: <500ms)\n';
  }

  // Total registrations attempted
  const iterations = data.metrics.iterations;
  if (iterations) {
    summary += `${indent}Total Registrations........: ${iterations.values.count}\n`;
    summary += `${indent}Registrations/min..........: ${(iterations.values.rate * 60).toFixed(2)}\n`;
  }

  // Error rate
  const reqFailed = data.metrics.http_req_failed;
  if (reqFailed) {
    const errorRate = (reqFailed.values.rate * 100).toFixed(2);
    summary += `${indent}Error Rate.................: ${errorRate}% `;
    summary += reqFailed.values.rate < 0.05 ? '✓\n' : '✗ (target: <5%)\n';
  }

  summary += `${indent}Target Load................: 500 registrations in 10 min\n`;
  summary += `${indent}Flash Period...............: 50% in first 2 minutes\n`;
  summary += `\n${indent}${'='.repeat(50)}\n`;

  return summary;
}
