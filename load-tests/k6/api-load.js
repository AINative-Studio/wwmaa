/**
 * WWMAA API Endpoints Load Test
 *
 * Tests key API endpoints under load
 *
 * Load Profile:
 * - Test authentication endpoints
 * - Test event management endpoints
 * - Test subscription endpoints
 * - Mix of read and write operations
 *
 * Performance Targets:
 * - p95 latency < 300ms
 * - p99 latency < 500ms
 * - Error rate < 1%
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const apiLatency = new Trend('api_latency', true);
const apiSuccess = new Rate('api_success');
const authLatency = new Trend('auth_latency', true);
const eventsApiLatency = new Trend('events_api_latency', true);
const subscriptionsApiLatency = new Trend('subscriptions_api_latency', true);

// Configuration
const BASE_URL = __ENV.API_URL || 'https://staging.wwmaa.com/api';

// Test configuration
export const options = {
  scenarios: {
    // Auth endpoints: 100 req/s
    auth_load: {
      executor: 'constant-arrival-rate',
      rate: 100,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 20,
      maxVUs: 100,
      exec: 'authScenario',
    },
    // Events endpoints: 200 req/s
    events_load: {
      executor: 'constant-arrival-rate',
      rate: 200,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 40,
      maxVUs: 200,
      exec: 'eventsScenario',
      startTime: '30s', // Start after auth stabilizes
    },
    // Subscriptions endpoints: 50 req/s
    subscriptions_load: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 10,
      maxVUs: 50,
      exec: 'subscriptionsScenario',
      startTime: '1m', // Start after events stabilizes
    },
  },
  thresholds: {
    // Overall API performance
    'api_latency': ['p(95)<300', 'p(99)<500'],
    'api_success': ['rate>0.99'], // > 99% success

    // Endpoint-specific thresholds
    'auth_latency': ['p(95)<300', 'p(99)<500'],
    'events_api_latency': ['p(95)<300', 'p(99)<500'],
    'subscriptions_api_latency': ['p(95)<300', 'p(99)<500'],

    // HTTP metrics
    'http_req_duration{endpoint:auth}': ['p(95)<300'],
    'http_req_duration{endpoint:events}': ['p(95)<300'],
    'http_req_duration{endpoint:subscriptions}': ['p(95)<300'],
    'http_req_failed': ['rate<0.01'], // < 1% error rate
  },
};

// Test data
const TEST_USERS = Array.from({ length: 100 }, (_, i) => ({
  email: `loadtest_user_${i}@wwmaa.com`,
  password: 'test_password_123',
}));

// Helper: Get random user
function getRandomUser() {
  return TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
}

// Auth Scenario: Login, refresh token, logout
export function authScenario() {
  const user = getRandomUser();

  group('Authentication Flow', function () {
    // Login
    const loginStartTime = Date.now();

    const loginResponse = http.post(
      `${BASE_URL}/auth/login`,
      JSON.stringify({
        email: user.email,
        password: user.password,
      }),
      {
        headers: {
          'Content-Type': 'application/json',
        },
        tags: { endpoint: 'auth', operation: 'login' },
      }
    );

    const loginLatency = Date.now() - loginStartTime;
    authLatency.add(loginLatency);
    apiLatency.add(loginLatency);

    const loginSuccess = check(loginResponse, {
      'login status 200': (r) => r.status === 200,
      'login response time < 300ms': (r) => r.timings.duration < 300,
      'received access token': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.access_token !== undefined;
        } catch (e) {
          return false;
        }
      },
    });

    apiSuccess.add(loginSuccess ? 1 : 0);

    if (!loginSuccess) {
      console.error(`Login failed for ${user.email}: ${loginResponse.status}`);
      return;
    }

    const authData = JSON.parse(loginResponse.body);
    const accessToken = authData.access_token;
    const refreshToken = authData.refresh_token;

    sleep(1);

    // Verify token (simulate authenticated request)
    const verifyResponse = http.get(
      `${BASE_URL}/auth/me`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        tags: { endpoint: 'auth', operation: 'verify' },
      }
    );

    const verifyLatency = verifyResponse.timings.duration;
    authLatency.add(verifyLatency);
    apiLatency.add(verifyLatency);

    const verifySuccess = check(verifyResponse, {
      'verify status 200': (r) => r.status === 200,
      'verify response time < 300ms': (r) => r.timings.duration < 300,
    });

    apiSuccess.add(verifySuccess ? 1 : 0);

    sleep(1);

    // Refresh token
    const refreshStartTime = Date.now();

    const refreshResponse = http.post(
      `${BASE_URL}/auth/refresh`,
      JSON.stringify({
        refresh_token: refreshToken,
      }),
      {
        headers: {
          'Content-Type': 'application/json',
        },
        tags: { endpoint: 'auth', operation: 'refresh' },
      }
    );

    const refreshLatency = Date.now() - refreshStartTime;
    authLatency.add(refreshLatency);
    apiLatency.add(refreshLatency);

    const refreshSuccess = check(refreshResponse, {
      'refresh status 200': (r) => r.status === 200,
      'refresh response time < 300ms': (r) => r.timings.duration < 300,
      'received new access token': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.access_token !== undefined && body.access_token !== accessToken;
        } catch (e) {
          return false;
        }
      },
    });

    apiSuccess.add(refreshSuccess ? 1 : 0);
  });
}

// Events Scenario: List, view, search events
export function eventsScenario() {
  group('Events API', function () {
    // List events
    const listStartTime = Date.now();

    const listResponse = http.get(
      `${BASE_URL}/events?limit=20&page=1`,
      {
        headers: {
          'Accept': 'application/json',
        },
        tags: { endpoint: 'events', operation: 'list' },
      }
    );

    const listLatency = Date.now() - listStartTime;
    eventsApiLatency.add(listLatency);
    apiLatency.add(listLatency);

    const listSuccess = check(listResponse, {
      'events list status 200': (r) => r.status === 200,
      'events list response time < 300ms': (r) => r.timings.duration < 300,
      'events list has data': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.events && Array.isArray(body.events);
        } catch (e) {
          return false;
        }
      },
    });

    apiSuccess.add(listSuccess ? 1 : 0);

    if (!listSuccess) {
      console.error(`Events list failed: ${listResponse.status}`);
      return;
    }

    const eventsData = JSON.parse(listResponse.body);
    const events = eventsData.events || [];

    if (events.length > 0) {
      // View random event details
      const randomEvent = events[Math.floor(Math.random() * events.length)];
      const eventId = randomEvent.id;

      sleep(0.5);

      const viewStartTime = Date.now();

      const viewResponse = http.get(
        `${BASE_URL}/events/${eventId}`,
        {
          headers: {
            'Accept': 'application/json',
          },
          tags: { endpoint: 'events', operation: 'view' },
        }
      );

      const viewLatency = Date.now() - viewStartTime;
      eventsApiLatency.add(viewLatency);
      apiLatency.add(viewLatency);

      const viewSuccess = check(viewResponse, {
        'event view status 200': (r) => r.status === 200,
        'event view response time < 300ms': (r) => r.timings.duration < 300,
        'event has details': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.id && body.title && body.description;
          } catch (e) {
            return false;
          }
        },
      });

      apiSuccess.add(viewSuccess ? 1 : 0);
    }

    sleep(0.5);

    // Search events
    const searchQueries = ['martial arts', 'training', 'tournament', 'beginner', 'advanced'];
    const query = searchQueries[Math.floor(Math.random() * searchQueries.length)];

    const searchStartTime = Date.now();

    const searchResponse = http.get(
      `${BASE_URL}/events/search?q=${encodeURIComponent(query)}`,
      {
        headers: {
          'Accept': 'application/json',
        },
        tags: { endpoint: 'events', operation: 'search' },
      }
    );

    const searchLatency = Date.now() - searchStartTime;
    eventsApiLatency.add(searchLatency);
    apiLatency.add(searchLatency);

    const searchSuccess = check(searchResponse, {
      'events search status 200': (r) => r.status === 200,
      'events search response time < 500ms': (r) => r.timings.duration < 500,
    });

    apiSuccess.add(searchSuccess ? 1 : 0);
  });
}

// Subscriptions Scenario: List plans, check status
export function subscriptionsScenario() {
  const user = getRandomUser();

  group('Subscriptions API', function () {
    // First, authenticate
    const loginResponse = http.post(
      `${BASE_URL}/auth/login`,
      JSON.stringify({
        email: user.email,
        password: user.password,
      }),
      {
        headers: {
          'Content-Type': 'application/json',
        },
        tags: { endpoint: 'auth', operation: 'login' },
      }
    );

    if (loginResponse.status !== 200) {
      console.warn(`Login failed for subscriptions test: ${user.email}`);
      return;
    }

    const authData = JSON.parse(loginResponse.body);
    const accessToken = authData.access_token;

    sleep(0.5);

    // List subscription plans
    const plansStartTime = Date.now();

    const plansResponse = http.get(
      `${BASE_URL}/subscriptions/plans`,
      {
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        tags: { endpoint: 'subscriptions', operation: 'list_plans' },
      }
    );

    const plansLatency = Date.now() - plansStartTime;
    subscriptionsApiLatency.add(plansLatency);
    apiLatency.add(plansLatency);

    const plansSuccess = check(plansResponse, {
      'plans list status 200': (r) => r.status === 200,
      'plans list response time < 300ms': (r) => r.timings.duration < 300,
      'plans list has data': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.plans && Array.isArray(body.plans);
        } catch (e) {
          return false;
        }
      },
    });

    apiSuccess.add(plansSuccess ? 1 : 0);

    sleep(0.5);

    // Check user subscription status
    const statusStartTime = Date.now();

    const statusResponse = http.get(
      `${BASE_URL}/subscriptions/my-subscription`,
      {
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        tags: { endpoint: 'subscriptions', operation: 'status' },
      }
    );

    const statusLatency = Date.now() - statusStartTime;
    subscriptionsApiLatency.add(statusLatency);
    apiLatency.add(statusLatency);

    const statusSuccess = check(statusResponse, {
      'subscription status response': (r) => r.status === 200 || r.status === 404, // 404 if no subscription
      'subscription status response time < 300ms': (r) => r.timings.duration < 300,
    });

    apiSuccess.add(statusSuccess ? 1 : 0);
  });
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/api-load.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';

  let summary = '\n';
  summary += `${indent}API Endpoints Load Test Summary\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  if (checks) {
    const passRate = (checks.values.passes / checks.values.value * 100).toFixed(2);
    summary += `${indent}Checks.....................: ${passRate}% (${checks.values.passes}/${checks.values.value})\n`;
  }

  // Overall API latency
  const apiLat = data.metrics.api_latency;
  if (apiLat) {
    summary += `${indent}API Latency:\n`;
    summary += `${indent}  avg: ${apiLat.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${apiLat.values['p(95)'].toFixed(2)}ms `;
    summary += apiLat.values['p(95)'] < 300 ? '✓\n' : '✗ (target: <300ms)\n';
    summary += `${indent}  p99: ${apiLat.values['p(99)'].toFixed(2)}ms `;
    summary += apiLat.values['p(99)'] < 500 ? '✓\n' : '✗ (target: <500ms)\n';
  }

  // Auth endpoint latency
  const authLat = data.metrics.auth_latency;
  if (authLat) {
    summary += `${indent}Auth Endpoint Latency (p95): ${authLat.values['p(95)'].toFixed(2)}ms `;
    summary += authLat.values['p(95)'] < 300 ? '✓\n' : '✗\n';
  }

  // Events endpoint latency
  const eventsLat = data.metrics.events_api_latency;
  if (eventsLat) {
    summary += `${indent}Events Endpoint Latency (p95): ${eventsLat.values['p(95)'].toFixed(2)}ms `;
    summary += eventsLat.values['p(95)'] < 300 ? '✓\n' : '✗\n';
  }

  // Subscriptions endpoint latency
  const subsLat = data.metrics.subscriptions_api_latency;
  if (subsLat) {
    summary += `${indent}Subscriptions Endpoint Latency (p95): ${subsLat.values['p(95)'].toFixed(2)}ms `;
    summary += subsLat.values['p(95)'] < 300 ? '✓\n' : '✗\n';
  }

  // API success rate
  const apiSuccessRate = data.metrics.api_success;
  if (apiSuccessRate) {
    const rate = (apiSuccessRate.values.rate * 100).toFixed(2);
    summary += `${indent}API Success Rate...........: ${rate}% `;
    summary += apiSuccessRate.values.rate > 0.99 ? '✓\n' : '✗ (target: >99%)\n';
  }

  // Error rate
  const reqFailed = data.metrics.http_req_failed;
  if (reqFailed) {
    const errorRate = (reqFailed.values.rate * 100).toFixed(3);
    summary += `${indent}Error Rate.................: ${errorRate}% `;
    summary += reqFailed.values.rate < 0.01 ? '✓\n' : '✗ (target: <1%)\n';
  }

  // Total requests
  const iterations = data.metrics.iterations;
  if (iterations) {
    summary += `${indent}Total Requests.............: ${iterations.values.count}\n`;
    summary += `${indent}Requests/sec...............: ${iterations.values.rate.toFixed(2)}\n`;
  }

  summary += `${indent}Target Load:\n`;
  summary += `${indent}  - Auth: 100 req/s\n`;
  summary += `${indent}  - Events: 200 req/s\n`;
  summary += `${indent}  - Subscriptions: 50 req/s\n`;
  summary += `\n${indent}${'='.repeat(50)}\n`;

  return summary;
}
