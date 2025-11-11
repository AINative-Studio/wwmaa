/**
 * WWMAA Page Load Test
 *
 * Tests general website traffic across all pages
 *
 * Load Profile:
 * - 10,000 concurrent visitors
 * - 70% anonymous, 30% authenticated
 * - Realistic page mix
 *
 * Performance Targets:
 * - p95 LCP < 2.5s
 * - p95 API response < 300ms
 * - Error rate < 0.1%
 * - No 5xx errors
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const pageLoadTime = new Trend('page_load_time', true);
const apiResponseTime = new Trend('api_response_time', true);
const lcpMetric = new Trend('lcp_metric', true);
const authSuccess = new Rate('auth_success');
const pageLoadSuccess = new Rate('page_load_success');
const serverErrors = new Counter('server_errors');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'https://staging.wwmaa.com';
const API_URL = __ENV.API_URL || 'https://staging.wwmaa.com/api';

// Test configuration
export const options = {
  stages: [
    { duration: '3m', target: 1000 },   // Ramp up to 1k users
    { duration: '2m', target: 5000 },   // Ramp up to 5k users
    { duration: '2m', target: 10000 },  // Ramp up to 10k users
    { duration: '5m', target: 10000 },  // Sustain 10k users
    { duration: '3m', target: 0 },      // Ramp down
  ],
  thresholds: {
    // Primary targets
    'page_load_time': ['p(95)<2500'], // LCP < 2.5s
    'api_response_time': ['p(95)<300', 'p(99)<500'],
    'http_req_failed': ['rate<0.001'], // < 0.1% error rate
    'server_errors': ['count==0'], // No 5xx errors

    // Page-specific thresholds
    'http_req_duration{page:homepage}': ['p(95)<2000'],
    'http_req_duration{page:events}': ['p(95)<2500'],
    'http_req_duration{page:instructors}': ['p(95)<2000'],
    'http_req_duration{page:search}': ['p(95)<2500'],
    'http_req_duration{page:dashboard}': ['p(95)<2500'],

    // API thresholds
    'http_req_duration{type:api}': ['p(95)<300', 'p(99)<500'],
    'http_req_duration{endpoint:search_api}': ['p(95)<1200'],

    // Success rates
    'page_load_success': ['rate>0.999'], // > 99.9% success
    'auth_success': ['rate>0.99'], // > 99% auth success
  },
};

// Page mix distribution (based on realistic traffic)
const PAGE_MIX = [
  { path: '/', weight: 0.30, name: 'homepage', requiresAuth: false },
  { path: '/events', weight: 0.25, name: 'events', requiresAuth: false },
  { path: '/instructors', weight: 0.20, name: 'instructors', requiresAuth: false },
  { path: '/search?q=karate', weight: 0.15, name: 'search', requiresAuth: false },
  { path: '/dashboard', weight: 0.10, name: 'dashboard', requiresAuth: true },
];

// Common static assets to load with each page
const STATIC_ASSETS = [
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/images/logo.png',
];

// Helper: Select page based on weighted distribution
function selectPage() {
  const rand = Math.random();
  let cumulativeWeight = 0;

  for (const page of PAGE_MIX) {
    cumulativeWeight += page.weight;
    if (rand <= cumulativeWeight) {
      return page;
    }
  }

  return PAGE_MIX[0]; // Fallback
}

// Helper: Determine if user is authenticated (30% authenticated)
function isAuthenticatedUser() {
  return Math.random() < 0.30;
}

// Helper: Simulate authentication
function authenticate() {
  const authStartTime = new Date().getTime();

  const authResponse = http.post(
    `${API_URL}/auth/login`,
    JSON.stringify({
      email: `loadtest_user_${__VU}@wwmaa.com`,
      password: 'test_password_123',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
      },
      tags: { type: 'api', endpoint: 'auth' },
    }
  );

  const authLatency = new Date().getTime() - authStartTime;
  apiResponseTime.add(authLatency);

  const success = check(authResponse, {
    'auth status 200': (r) => r.status === 200,
    'received access token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.access_token !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  authSuccess.add(success ? 1 : 0);

  if (success) {
    const authData = JSON.parse(authResponse.body);
    return authData.access_token;
  }

  return null;
}

// Helper: Load static assets
function loadStaticAssets(baseUrl) {
  const requests = STATIC_ASSETS.map(asset => ({
    method: 'GET',
    url: `${baseUrl}${asset}`,
    params: {
      tags: { type: 'static' },
    },
  }));

  const responses = http.batch(requests);

  // Validate static assets loaded successfully
  responses.forEach((response, index) => {
    check(response, {
      [`static asset ${STATIC_ASSETS[index]} loaded`]: (r) => r.status === 200,
    });
  });
}

// Helper: Measure Largest Contentful Paint (LCP) approximation
function measureLCP(response) {
  // In real browser testing, LCP is measured by the browser
  // For k6, we approximate it as the time to load the HTML + critical assets
  // This is a simplified metric for load testing purposes
  const htmlLoadTime = response.timings.duration;

  // Assume LCP is roughly HTML load time + largest asset load time
  // For simplicity, we'll use HTML load time as a proxy
  lcpMetric.add(htmlLoadTime);

  return htmlLoadTime;
}

export default function () {
  const isAuthenticated = isAuthenticatedUser();
  let accessToken = null;

  // Authenticate if needed
  if (isAuthenticated) {
    group('Authentication', function () {
      accessToken = authenticate();

      if (!accessToken) {
        // Authentication failed - proceed as anonymous user
        console.warn(`Authentication failed for VU ${__VU}, proceeding as anonymous`);
      }
    });

    sleep(0.5);
  }

  // Select page to visit
  const page = selectPage();

  // Skip authenticated pages if not logged in
  if (page.requiresAuth && !accessToken) {
    // Select alternative non-authenticated page
    const altPage = PAGE_MIX.find(p => !p.requiresAuth) || PAGE_MIX[0];
    page.path = altPage.path;
    page.name = altPage.name;
  }

  group(`Page Load: ${page.name}`, function () {
    const pageStartTime = new Date().getTime();

    // Load HTML page
    const headers = {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.5',
      'Accept-Encoding': 'gzip, deflate, br',
    };

    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const pageResponse = http.get(
      `${BASE_URL}${page.path}`,
      {
        headers: headers,
        tags: {
          page: page.name,
          type: 'page',
        },
      }
    );

    const htmlLoadTime = new Date().getTime() - pageStartTime;

    // Validate page load
    const success = check(pageResponse, {
      'page status 200': (r) => r.status === 200,
      'page load time < 2.5s': (r) => r.timings.duration < 2500,
      'page has content': (r) => r.body && r.body.length > 0,
      'content-type is html': (r) => r.headers['Content-Type']?.includes('text/html'),
    });

    pageLoadSuccess.add(success ? 1 : 0);

    if (!success) {
      console.error(`Page load failed: ${page.name} - Status: ${pageResponse.status}`);

      if (pageResponse.status >= 500) {
        serverErrors.add(1);
        console.error(`Server error on ${page.name}: ${pageResponse.status}`);
      }
    }

    // Measure LCP
    const lcp = measureLCP(pageResponse);
    pageLoadTime.add(htmlLoadTime);

    // Load static assets (parallel)
    loadStaticAssets(BASE_URL);

    // Page-specific API calls
    switch (page.name) {
      case 'events':
        // Load events list
        group('Events API', function () {
          const apiStartTime = new Date().getTime();

          const eventsResponse = http.get(
            `${API_URL}/events?limit=20`,
            {
              headers: {
                'Accept': 'application/json',
              },
              tags: { type: 'api', endpoint: 'events_list' },
            }
          );

          const apiLatency = new Date().getTime() - apiStartTime;
          apiResponseTime.add(apiLatency);

          check(eventsResponse, {
            'events API status 200': (r) => r.status === 200,
            'events API response time < 300ms': (r) => r.timings.duration < 300,
            'events API has data': (r) => {
              try {
                const body = JSON.parse(r.body);
                return body.events && Array.isArray(body.events);
              } catch (e) {
                return false;
              }
            },
          });
        });
        break;

      case 'instructors':
        // Load instructors list
        group('Instructors API', function () {
          const apiStartTime = new Date().getTime();

          const instructorsResponse = http.get(
            `${API_URL}/instructors?limit=20`,
            {
              headers: {
                'Accept': 'application/json',
              },
              tags: { type: 'api', endpoint: 'instructors_list' },
            }
          );

          const apiLatency = new Date().getTime() - apiStartTime;
          apiResponseTime.add(apiLatency);

          check(instructorsResponse, {
            'instructors API status 200': (r) => r.status === 200,
            'instructors API response time < 300ms': (r) => r.timings.duration < 300,
          });
        });
        break;

      case 'search':
        // Execute search query
        group('Search API', function () {
          const apiStartTime = new Date().getTime();

          const searchResponse = http.get(
            `${API_URL}/search?q=karate&limit=20`,
            {
              headers: {
                'Accept': 'application/json',
              },
              tags: { type: 'api', endpoint: 'search_api' },
            }
          );

          const apiLatency = new Date().getTime() - apiStartTime;
          apiResponseTime.add(apiLatency);

          check(searchResponse, {
            'search API status 200': (r) => r.status === 200,
            'search API response time < 1.2s': (r) => r.timings.duration < 1200,
            'search API has results': (r) => {
              try {
                const body = JSON.parse(r.body);
                return body.results !== undefined;
              } catch (e) {
                return false;
              }
            },
          });
        });
        break;

      case 'dashboard':
        // Load user dashboard data
        if (accessToken) {
          group('Dashboard API', function () {
            const apiStartTime = new Date().getTime();

            const dashboardResponse = http.get(
              `${API_URL}/users/me/dashboard`,
              {
                headers: {
                  'Accept': 'application/json',
                  'Authorization': `Bearer ${accessToken}`,
                },
                tags: { type: 'api', endpoint: 'dashboard' },
              }
            );

            const apiLatency = new Date().getTime() - apiStartTime;
            apiResponseTime.add(apiLatency);

            check(dashboardResponse, {
              'dashboard API status 200': (r) => r.status === 200,
              'dashboard API response time < 300ms': (r) => r.timings.duration < 300,
            });
          });
        }
        break;

      default:
        // Homepage - no additional API calls
        break;
    }
  });

  // Realistic user think time (5-10 seconds between pages)
  sleep(5 + Math.random() * 5);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/page-load.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';

  let summary = '\n';
  summary += `${indent}Page Load Test Summary\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  if (checks) {
    const passRate = (checks.values.passes / checks.values.value * 100).toFixed(2);
    summary += `${indent}Checks.....................: ${passRate}% (${checks.values.passes}/${checks.values.value})\n`;
  }

  // Page load time (LCP proxy)
  const pageLoad = data.metrics.page_load_time;
  if (pageLoad) {
    summary += `${indent}Page Load Time (LCP):\n`;
    summary += `${indent}  avg: ${pageLoad.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${pageLoad.values['p(95)'].toFixed(2)}ms `;
    summary += pageLoad.values['p(95)'] < 2500 ? '✓\n' : '✗ (target: <2500ms)\n';
    summary += `${indent}  p99: ${pageLoad.values['p(99)'].toFixed(2)}ms\n`;
  }

  // API response time
  const apiResponse = data.metrics.api_response_time;
  if (apiResponse) {
    summary += `${indent}API Response Time:\n`;
    summary += `${indent}  avg: ${apiResponse.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${apiResponse.values['p(95)'].toFixed(2)}ms `;
    summary += apiResponse.values['p(95)'] < 300 ? '✓\n' : '✗ (target: <300ms)\n';
    summary += `${indent}  p99: ${apiResponse.values['p(99)'].toFixed(2)}ms `;
    summary += apiResponse.values['p(99)'] < 500 ? '✓\n' : '✗ (target: <500ms)\n';
  }

  // Page load success rate
  const loadSuccess = data.metrics.page_load_success;
  if (loadSuccess) {
    const rate = (loadSuccess.values.rate * 100).toFixed(3);
    summary += `${indent}Page Load Success..........: ${rate}% `;
    summary += loadSuccess.values.rate > 0.999 ? '✓\n' : '✗ (target: >99.9%)\n';
  }

  // Auth success rate
  const authSuccessMetric = data.metrics.auth_success;
  if (authSuccessMetric && authSuccessMetric.values.count > 0) {
    const rate = (authSuccessMetric.values.rate * 100).toFixed(2);
    summary += `${indent}Auth Success...............: ${rate}% `;
    summary += authSuccessMetric.values.rate > 0.99 ? '✓\n' : '✗ (target: >99%)\n';
  }

  // Server errors
  const serverErrs = data.metrics.server_errors;
  if (serverErrs) {
    summary += `${indent}Server Errors (5xx)........: ${serverErrs.values.count} `;
    summary += serverErrs.values.count === 0 ? '✓\n' : '✗ (target: 0)\n';
  }

  // Error rate
  const reqFailed = data.metrics.http_req_failed;
  if (reqFailed) {
    const errorRate = (reqFailed.values.rate * 100).toFixed(3);
    summary += `${indent}Error Rate.................: ${errorRate}% `;
    summary += reqFailed.values.rate < 0.001 ? '✓\n' : '✗ (target: <0.1%)\n';
  }

  // Virtual users
  const vus = data.metrics.vus;
  if (vus) {
    summary += `${indent}Concurrent Users (peak)....: ${vus.values.max}\n`;
  }

  // Total page views
  const iterations = data.metrics.iterations;
  if (iterations) {
    summary += `${indent}Total Page Views...........: ${iterations.values.count}\n`;
  }

  summary += `\n${indent}${'='.repeat(50)}\n`;

  return summary;
}
