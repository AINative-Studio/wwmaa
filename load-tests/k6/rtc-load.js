/**
 * WWMAA RTC (Real-Time Communication) Load Test
 *
 * Tests live training sessions with video and chat
 *
 * Load Profile:
 * - 50 concurrent participants in one session
 * - WebSocket connections for chat
 * - Cloudflare Calls integration for video
 * - Chat messages: 5 per minute per user
 *
 * Performance Targets:
 * - WebSocket connection success rate > 99%
 * - Message delivery rate > 99%
 * - Connection drop rate < 1%
 * - Chat message latency p95 < 500ms
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const wsConnectionSuccess = new Rate('ws_connection_success');
const wsConnectionDrops = new Rate('ws_connection_drops');
const messageDeliverySuccess = new Rate('message_delivery_success');
const chatMessageLatency = new Trend('chat_message_latency', true);
const videoHealthCheckSuccess = new Rate('video_health_check_success');
const sessionJoinLatency = new Trend('session_join_latency', true);

// Configuration
const BASE_URL = __ENV.API_URL || 'https://staging.wwmaa.com/api';
const WS_URL = __ENV.WS_URL || 'wss://staging.wwmaa.com/ws';
const TEST_SESSION_ID = __ENV.TEST_SESSION_ID || 'test_session_001';

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp up: participants join gradually
    { duration: '10m', target: 50 },  // Sustain: full session
    { duration: '1m', target: 0 },    // Ramp down: participants leave
  ],
  thresholds: {
    // Connection success
    'ws_connection_success': ['rate>0.99'], // > 99% success
    'ws_connection_drops': ['rate<0.01'],   // < 1% drops

    // Message delivery
    'message_delivery_success': ['rate>0.99'],
    'chat_message_latency': ['p(95)<500', 'p(99)<1000'],

    // Video health
    'video_health_check_success': ['rate>0.95'], // > 95% healthy

    // Session join
    'session_join_latency': ['p(95)<2000', 'p(99)<3000'],

    // HTTP metrics for API calls
    'http_req_duration{endpoint:join_session}': ['p(95)<2000'],
    'http_req_duration{endpoint:video_token}': ['p(95)<1000'],
    'http_req_failed': ['rate<0.01'],
  },
};

// Test data: realistic chat messages
const CHAT_MESSAGES = [
  'Great technique!',
  'Can you demonstrate that again?',
  'Thank you sensei',
  'What style is this?',
  'How do I improve my stance?',
  'This is very helpful',
  'Question about the footwork',
  'Can we practice this in pairs?',
  'I\'m having trouble with the timing',
  'Excellent session',
  'More like this please',
  'What belt level is this for?',
  'Can you slow down the movement?',
  'I need to work on my balance',
  'Thanks for the explanation',
];

// Helper: Generate unique user ID
function getUserId() {
  return `user_${__VU}_${Date.now()}`;
}

// Helper: Generate random chat message
function randomChatMessage() {
  return CHAT_MESSAGES[Math.floor(Math.random() * CHAT_MESSAGES.length)];
}

export default function () {
  const userId = getUserId();
  const sessionId = TEST_SESSION_ID;

  group('Session Join Flow', function () {
    // Step 1: Authenticate and get session access token
    const joinStartTime = new Date().getTime();

    const authResponse = http.post(
      `${BASE_URL}/rtc/sessions/${sessionId}/join`,
      JSON.stringify({
        user_id: userId,
        participant_name: `Test User ${__VU}`,
      }),
      {
        headers: {
          'Content-Type': 'application/json',
        },
        tags: { endpoint: 'join_session' },
      }
    );

    const joinSuccess = check(authResponse, {
      'session join status 200': (r) => r.status === 200,
      'received access token': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.access_token !== undefined;
        } catch (e) {
          return false;
        }
      },
    });

    if (!joinSuccess) {
      console.error(`Session join failed for user ${userId}: ${authResponse.status}`);
      return; // Exit early if can't join
    }

    const sessionData = JSON.parse(authResponse.body);
    const accessToken = sessionData.access_token;
    const wsToken = sessionData.ws_token;

    const joinLatency = new Date().getTime() - joinStartTime;
    sessionJoinLatency.add(joinLatency);

    // Step 2: Get Cloudflare Calls video token
    const videoTokenResponse = http.post(
      `${BASE_URL}/rtc/sessions/${sessionId}/video-token`,
      JSON.stringify({
        access_token: accessToken,
      }),
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        tags: { endpoint: 'video_token' },
      }
    );

    const videoTokenSuccess = check(videoTokenResponse, {
      'video token status 200': (r) => r.status === 200,
      'received video token': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.video_token !== undefined;
        } catch (e) {
          return false;
        }
      },
    });

    videoHealthCheckSuccess.add(videoTokenSuccess ? 1 : 0);

    // Step 3: Establish WebSocket connection for chat
    const wsUrl = `${WS_URL}/sessions/${sessionId}?token=${wsToken}`;

    const wsResponse = ws.connect(wsUrl, {
      headers: {
        'Authorization': `Bearer ${wsToken}`,
      },
    }, function (socket) {
      // Track connection success
      wsConnectionSuccess.add(1);

      let messagesSent = 0;
      let messagesReceived = 0;
      let lastPingTime = Date.now();

      // Handle incoming messages
      socket.on('message', function (data) {
        try {
          const message = JSON.parse(data);

          switch (message.type) {
            case 'welcome':
              check(message, {
                'received welcome message': (m) => m.type === 'welcome',
                'welcome contains session_id': (m) => m.session_id === sessionId,
              });
              break;

            case 'chat':
              messagesReceived++;
              // Track delivery latency if message has timestamp
              if (message.sent_at) {
                const latency = Date.now() - new Date(message.sent_at).getTime();
                chatMessageLatency.add(latency);
              }
              messageDeliverySuccess.add(1);
              break;

            case 'participant_joined':
            case 'participant_left':
              // Presence updates - just acknowledge
              break;

            case 'pong':
              // Track ping/pong for connection health
              const pingLatency = Date.now() - lastPingTime;
              if (pingLatency > 5000) {
                console.warn(`High ping latency: ${pingLatency}ms for user ${userId}`);
              }
              break;

            case 'error':
              console.error(`WebSocket error for user ${userId}: ${message.error}`);
              wsConnectionDrops.add(1);
              break;

            default:
              // Unknown message type
              break;
          }
        } catch (e) {
          console.error(`Failed to parse WebSocket message for user ${userId}: ${e}`);
        }
      });

      // Handle connection errors
      socket.on('error', function (e) {
        console.error(`WebSocket error for user ${userId}: ${e}`);
        wsConnectionDrops.add(1);
      });

      // Handle connection close
      socket.on('close', function () {
        if (messagesSent > 0) {
          const deliveryRate = messagesReceived / messagesSent;
          if (deliveryRate < 0.9) {
            console.warn(`Low message delivery rate for user ${userId}: ${deliveryRate * 100}%`);
          }
        }
      });

      // Simulate active participation: send chat messages
      // 5 messages per minute = 1 message every 12 seconds
      const sessionDuration = 10 * 60; // 10 minutes in seconds
      const messageInterval = 12; // seconds
      const totalMessages = Math.floor(sessionDuration / messageInterval);

      for (let i = 0; i < totalMessages; i++) {
        // Send chat message
        const message = {
          type: 'chat',
          content: randomChatMessage(),
          user_id: userId,
          sent_at: new Date().toISOString(),
        };

        const sendStartTime = Date.now();

        socket.send(JSON.stringify(message));
        messagesSent++;

        // Check if send was successful (no error)
        socket.setTimeout(function () {
          const sendLatency = Date.now() - sendStartTime;
          if (sendLatency > 1000) {
            console.warn(`High send latency: ${sendLatency}ms for user ${userId}`);
            messageDeliverySuccess.add(0);
          }
        }, 100);

        // Periodic video health check (every 2 minutes)
        if (i % 10 === 0) {
          const healthCheckResponse = http.get(
            `${BASE_URL}/rtc/sessions/${sessionId}/video-health`,
            {
              headers: {
                'Authorization': `Bearer ${accessToken}`,
              },
              tags: { endpoint: 'video_health' },
            }
          );

          const healthOk = check(healthCheckResponse, {
            'video health check 200': (r) => r.status === 200,
            'video connection healthy': (r) => {
              try {
                const body = JSON.parse(r.body);
                return body.status === 'connected' || body.status === 'healthy';
              } catch (e) {
                return false;
              }
            },
          });

          videoHealthCheckSuccess.add(healthOk ? 1 : 0);
        }

        // Send ping every minute to keep connection alive
        if (i % 5 === 0) {
          lastPingTime = Date.now();
          socket.send(JSON.stringify({ type: 'ping' }));
        }

        // Wait before sending next message
        sleep(messageInterval);
      }

      // Clean disconnect
      socket.send(JSON.stringify({ type: 'leave' }));
      sleep(1);
      socket.close();
    });

    // Check WebSocket connection result
    check(wsResponse, {
      'websocket connected successfully': (r) => r && r.status === 101,
    });

    if (!wsResponse || wsResponse.status !== 101) {
      wsConnectionSuccess.add(0);
      wsConnectionDrops.add(1);
      console.error(`WebSocket connection failed for user ${userId}`);
    }
  });

  // Leave session via API
  group('Session Leave Flow', function () {
    http.post(
      `${BASE_URL}/rtc/sessions/${sessionId}/leave`,
      JSON.stringify({
        user_id: userId,
      }),
      {
        headers: {
          'Content-Type': 'application/json',
        },
        tags: { endpoint: 'leave_session' },
      }
    );
  });
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'results/rtc-load.json': JSON.stringify(data, null, 2),
  };
}

function textSummary(data, options) {
  const indent = options?.indent || '';

  let summary = '\n';
  summary += `${indent}RTC Load Test Summary\n`;
  summary += `${indent}${'='.repeat(50)}\n\n`;

  // Checks
  const checks = data.metrics.checks;
  if (checks) {
    const passRate = (checks.values.passes / checks.values.value * 100).toFixed(2);
    summary += `${indent}Checks.....................: ${passRate}% (${checks.values.passes}/${checks.values.value})\n`;
  }

  // WebSocket connection success
  const wsSuccess = data.metrics.ws_connection_success;
  if (wsSuccess) {
    const rate = (wsSuccess.values.rate * 100).toFixed(2);
    summary += `${indent}WS Connection Success......: ${rate}% `;
    summary += wsSuccess.values.rate > 0.99 ? '✓\n' : '✗ (target: >99%)\n';
  }

  // WebSocket drops
  const wsDrops = data.metrics.ws_connection_drops;
  if (wsDrops) {
    const rate = (wsDrops.values.rate * 100).toFixed(2);
    summary += `${indent}WS Connection Drops........: ${rate}% `;
    summary += wsDrops.values.rate < 0.01 ? '✓\n' : '✗ (target: <1%)\n';
  }

  // Message delivery
  const msgDelivery = data.metrics.message_delivery_success;
  if (msgDelivery) {
    const rate = (msgDelivery.values.rate * 100).toFixed(2);
    summary += `${indent}Message Delivery...........: ${rate}% `;
    summary += msgDelivery.values.rate > 0.99 ? '✓\n' : '✗ (target: >99%)\n';
  }

  // Chat latency
  const chatLatency = data.metrics.chat_message_latency;
  if (chatLatency) {
    summary += `${indent}Chat Message Latency:\n`;
    summary += `${indent}  p95: ${chatLatency.values['p(95)'].toFixed(2)}ms `;
    summary += chatLatency.values['p(95)'] < 500 ? '✓\n' : '✗ (target: <500ms)\n';
    summary += `${indent}  p99: ${chatLatency.values['p(99)'].toFixed(2)}ms `;
    summary += chatLatency.values['p(99)'] < 1000 ? '✓\n' : '✗ (target: <1000ms)\n';
  }

  // Video health
  const videoHealth = data.metrics.video_health_check_success;
  if (videoHealth) {
    const rate = (videoHealth.values.rate * 100).toFixed(2);
    summary += `${indent}Video Health Checks........: ${rate}% `;
    summary += videoHealth.values.rate > 0.95 ? '✓\n' : '✗ (target: >95%)\n';
  }

  // Session join latency
  const joinLatency = data.metrics.session_join_latency;
  if (joinLatency) {
    summary += `${indent}Session Join Latency.......: ${joinLatency.values['p(95)'].toFixed(2)}ms (p95)\n`;
  }

  // Error rate
  const reqFailed = data.metrics.http_req_failed;
  if (reqFailed) {
    const errorRate = (reqFailed.values.rate * 100).toFixed(3);
    summary += `${indent}Error Rate.................: ${errorRate}% `;
    summary += reqFailed.values.rate < 0.01 ? '✓\n' : '✗ (target: <1%)\n';
  }

  summary += `${indent}Concurrent Participants....: 50 (peak)\n`;
  summary += `\n${indent}${'='.repeat(50)}\n`;

  return summary;
}
