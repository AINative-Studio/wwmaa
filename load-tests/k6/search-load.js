/**
 * WWMAA Search Load Test
 *
 * Tests the primary use case: members searching for martial arts content
 *
 * Load Profile:
 * - 100 concurrent users
 * - 1000 queries per minute sustained
 * - Mix of simple, filtered, and semantic searches
 *
 * Performance Targets:
 * - p95 latency < 1.2s
 * - p99 latency < 2s
 * - Error rate < 0.1%
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const searchLatency = new Trend('search_latency', true);
const searchErrors = new Rate('search_errors');
const semanticSearchLatency = new Trend('semantic_search_latency', true);
const filteredSearchLatency = new Trend('filtered_search_latency', true);

// Configuration
const BASE_URL = __ENV.API_URL || 'https://staging.wwmaa.com/api';

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Sustain 100 users (1000 queries/min)
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    // Primary targets
    'http_req_duration{endpoint:search}': ['p(95)<1200', 'p(99)<2000'],
    'search_latency': ['p(95)<1200', 'p(99)<2000'],
    'http_req_failed': ['rate<0.001'], // < 0.1% error rate
    'search_errors': ['rate<0.001'],

    // Semantic search (more expensive)
    'semantic_search_latency': ['p(95)<1500', 'p(99)<2500'],

    // Filtered search (should be faster with indexes)
    'filtered_search_latency': ['p(95)<800', 'p(99)<1200'],

    // HTTP metrics
    'http_req_connecting': ['p(95)<100'],
    'http_req_tls_handshaking': ['p(95)<200'],
    'http_req_sending': ['p(95)<10'],
    'http_req_waiting': ['p(95)<1000'],
    'http_req_receiving': ['p(95)<100'],
  },
  // Load profile: 100 VUs making ~10 requests/minute each = 1000 req/min
  // With sleep(1), each VU makes ~60 iterations in 10 minutes
};

// Test data: realistic search queries
const SEARCH_QUERIES = {
  simple: [
    'kata',
    'kumite',
    'karate',
    'judo',
    'aikido',
    'kendo',
    'taekwondo',
    'brazilian jiu jitsu',
    'muay thai',
    'wing chun',
    'shotokan',
    'kyokushin',
    'goju ryu',
    'wado ryu',
    'sensei',
    'dojo',
    'belt test',
    'tournament',
    'sparring',
    'forms',
  ],
  filtered: [
    { q: 'kata', style: 'karate' },
    { q: 'kumite', location: 'New York' },
    { q: 'training', instructor: 'Smith' },
    { q: 'beginner', level: 'beginner' },
    { q: 'advanced', level: 'advanced' },
    { q: 'competition', type: 'event' },
    { q: 'seminar', type: 'training' },
    { q: 'black belt', rank: 'black' },
    { q: 'kids', age_group: 'children' },
    { q: 'women', category: 'womens' },
  ],
  semantic: [
    'how to improve my front kick technique',
    'what is the difference between shotokan and kyokushin',
    'best exercises for martial arts flexibility',
    'how to prepare for black belt test',
    'what equipment do I need for sparring',
    'tips for tournament preparation',
    'how to find a good martial arts instructor',
    'what style is best for self defense',
    'how long does it take to get a black belt',
    'exercises to improve balance and coordination',
  ],
  complex: [
    { q: 'kata', style: 'karate', location: 'California', level: 'intermediate' },
    { q: 'competition', type: 'event', date_from: '2025-01-01', date_to: '2025-12-31' },
    { q: 'training', instructor: 'certified', style: 'judo', location: 'Texas' },
    { q: 'kids class', age_group: 'children', level: 'beginner', location: 'nearby' },
    { q: 'black belt', rank: 'black', style: 'taekwondo', verified: 'true' },
  ],
};

// Helper: Build query string from object
function buildQueryString(params) {
  return Object.keys(params)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&');
}

// Helper: Select random item from array
function randomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

// Helper: Determine search type based on distribution
function selectSearchType() {
  const rand = Math.random();
  if (rand < 0.40) return 'simple';      // 40%
  if (rand < 0.70) return 'filtered';    // 30%
  if (rand < 0.90) return 'semantic';    // 20%
  return 'complex';                      // 10%
}

export default function () {
  const searchType = selectSearchType();

  group('Search Request', function () {
    let url, queryParams, response;
    const startTime = new Date().getTime();

    switch (searchType) {
      case 'simple':
        const query = randomItem(SEARCH_QUERIES.simple);
        url = `${BASE_URL}/search?q=${encodeURIComponent(query)}`;
        response = http.get(url, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          tags: { endpoint: 'search', type: 'simple' },
        });
        break;

      case 'filtered':
        queryParams = randomItem(SEARCH_QUERIES.filtered);
        url = `${BASE_URL}/search?${buildQueryString(queryParams)}`;
        response = http.get(url, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          tags: { endpoint: 'search', type: 'filtered' },
        });

        const filteredLatency = new Date().getTime() - startTime;
        filteredSearchLatency.add(filteredLatency);
        break;

      case 'semantic':
        const semanticQuery = randomItem(SEARCH_QUERIES.semantic);
        url = `${BASE_URL}/search?q=${encodeURIComponent(semanticQuery)}&semantic=true`;
        response = http.get(url, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          tags: { endpoint: 'search', type: 'semantic' },
        });

        const semanticLatency = new Date().getTime() - startTime;
        semanticSearchLatency.add(semanticLatency);
        break;

      case 'complex':
        queryParams = randomItem(SEARCH_QUERIES.complex);
        url = `${BASE_URL}/search?${buildQueryString(queryParams)}`;
        response = http.get(url, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          tags: { endpoint: 'search', type: 'complex' },
        });
        break;
    }

    // Record metrics
    const latency = new Date().getTime() - startTime;
    searchLatency.add(latency);

    // Validate response
    const success = check(response, {
      'status is 200': (r) => r.status === 200,
      'response time < 1.2s': (r) => r.timings.duration < 1200,
      'response time < 2s': (r) => r.timings.duration < 2000,
      'has results': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.results !== undefined;
        } catch (e) {
          return false;
        }
      },
      'content-type is json': (r) => r.headers['Content-Type']?.includes('application/json'),
    });

    if (!success) {
      searchErrors.add(1);
      console.error(`Search failed: ${searchType} - ${url} - Status: ${response.status}`);
    } else {
      searchErrors.add(0);
    }

    // Additional validation for semantic searches
    if (searchType === 'semantic') {
      check(response, {
        'semantic results have relevance scores': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.results?.some(result => result.relevance_score !== undefined);
          } catch (e) {
            return false;
          }
        },
      });
    }
  });

  // Realistic user behavior: think time between searches
  // With 100 VUs and 1s sleep, we get ~6000 requests in 10 minutes
  // That's ~600 requests/minute sustained (adjust sleep to hit 1000 req/min)
  sleep(0.6); // Sleep 600ms to achieve ~1000 requests/minute with 100 VUs
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/search-load.json': JSON.stringify(data, null, 2),
  };
}

// Helper function for text summary (k6 provides this)
function textSummary(data, options) {
  const indent = options?.indent || '';
  const enableColors = options?.enableColors || false;

  let summary = '\n';
  summary += `${indent}Search Load Test Summary\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  if (checks) {
    const passRate = (checks.values.passes / checks.values.value * 100).toFixed(2);
    summary += `${indent}Checks.....................: ${passRate}% (${checks.values.passes}/${checks.values.value})\n`;
  }

  // Request duration
  const reqDuration = data.metrics.http_req_duration;
  if (reqDuration) {
    summary += `${indent}Request Duration:\n`;
    summary += `${indent}  avg: ${reqDuration.values.avg.toFixed(2)}ms\n`;
    summary += `${indent}  min: ${reqDuration.values.min.toFixed(2)}ms\n`;
    summary += `${indent}  med: ${reqDuration.values.med.toFixed(2)}ms\n`;
    summary += `${indent}  max: ${reqDuration.values.max.toFixed(2)}ms\n`;
    summary += `${indent}  p95: ${reqDuration.values['p(95)'].toFixed(2)}ms `;
    summary += reqDuration.values['p(95)'] < 1200 ? '✓\n' : '✗ (target: <1200ms)\n';
    summary += `${indent}  p99: ${reqDuration.values['p(99)'].toFixed(2)}ms `;
    summary += reqDuration.values['p(99)'] < 2000 ? '✓\n' : '✗ (target: <2000ms)\n';
  }

  // Error rate
  const reqFailed = data.metrics.http_req_failed;
  if (reqFailed) {
    const errorRate = (reqFailed.values.rate * 100).toFixed(3);
    summary += `${indent}Error Rate................: ${errorRate}% `;
    summary += reqFailed.values.rate < 0.001 ? '✓\n' : '✗ (target: <0.1%)\n';
  }

  // Requests
  const iterations = data.metrics.iterations;
  if (iterations) {
    summary += `${indent}Total Requests............: ${iterations.values.count}\n`;
    summary += `${indent}Requests/sec..............: ${iterations.values.rate.toFixed(2)}\n`;
  }

  // Virtual users
  summary += `${indent}Virtual Users.............: 100 (peak)\n`;

  summary += `\n${indent}${'='.repeat(50)}\n`;

  return summary;
}
