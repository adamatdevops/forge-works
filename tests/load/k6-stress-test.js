/**
 * K6 Stress Test
 * ForgeWorks Backend
 *
 * Tests system behavior under extreme load to find breaking points
 *
 * Usage:
 *   k6 run tests/load/k6-stress-test.js
 *   k6 run --env MAX_VUS=100 tests/load/k6-stress-test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

// =============================================================================
// Configuration
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const MAX_VUS = parseInt(__ENV.MAX_VUS) || 50;

// Custom metrics
const errorRate = new Rate('error_rate');
const timeoutCount = new Counter('timeouts');

export const options = {
  stages: [
    { duration: '1m', target: 10 },     // Warm up
    { duration: '2m', target: 20 },     // Normal load
    { duration: '2m', target: 30 },     // High load
    { duration: '2m', target: MAX_VUS }, // Stress load
    { duration: '3m', target: MAX_VUS }, // Sustain stress
    { duration: '2m', target: 0 },       // Recovery
  ],

  thresholds: {
    http_req_duration: ['p(95)<2000'],   // 95% under 2s during stress
    http_req_failed: ['rate<0.10'],       // Error rate under 10% during stress
    error_rate: ['rate<0.15'],            // Custom error rate under 15%
  },
};

// =============================================================================
// Setup
// =============================================================================

export function setup() {
  const health = http.get(`${BASE_URL}/health`, { timeout: '5s' });
  if (health.status !== 200) {
    throw new Error('API not available');
  }
  console.log(`Stress testing ${BASE_URL} with max ${MAX_VUS} VUs`);
  return {};
}

// =============================================================================
// Stress Test Scenario
// =============================================================================

export default function () {
  const timeout = '10s';

  // Heavy read operations
  const services = http.get(`${BASE_URL}/api/v1/services`, { timeout });
  if (!check(services, { 'services OK': (r) => r.status === 200 })) {
    errorRate.add(1);
    if (services.status === 0) timeoutCount.add(1);
  }

  const templates = http.get(`${BASE_URL}/api/v1/templates`, { timeout });
  if (!check(templates, { 'templates OK': (r) => r.status === 200 })) {
    errorRate.add(1);
  }

  // ML computation (heavier operation)
  const recommendPayload = JSON.stringify({
    workload_type: ['api', 'batch', 'stream', 'ml'][Math.floor(Math.random() * 4)],
    language: ['python', 'go', 'typescript'][Math.floor(Math.random() * 3)],
    requirements: ['database', 'caching'],
  });

  const recommend = http.post(
    `${BASE_URL}/api/v1/ml/recommend`,
    recommendPayload,
    { headers: { 'Content-Type': 'application/json' }, timeout }
  );

  if (!check(recommend, { 'recommend OK': (r) => r.status === 200 })) {
    errorRate.add(1);
    if (recommend.status === 0) timeoutCount.add(1);
  }

  // Metrics aggregation
  const metrics = http.get(`${BASE_URL}/api/v1/metrics`, { timeout });
  if (!check(metrics, { 'metrics OK': (r) => r.status === 200 })) {
    errorRate.add(1);
  }

  // Anomalies with filters
  const anomalies = http.get(`${BASE_URL}/api/v1/anomalies?active=true&severity=critical`, { timeout });
  if (!check(anomalies, { 'anomalies OK': (r) => r.status === 200 })) {
    errorRate.add(1);
  }

  sleep(0.2); // Short pause between iterations
}

// =============================================================================
// Teardown
// =============================================================================

export function teardown() {
  console.log('Stress test completed');
}
