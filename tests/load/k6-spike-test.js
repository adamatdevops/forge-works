/**
 * K6 Spike Test
 * ForgeWorks Backend
 *
 * Tests system behavior under sudden traffic spikes
 *
 * Usage:
 *   k6 run tests/load/k6-spike-test.js
 *   k6 run --env SPIKE_VUS=100 tests/load/k6-spike-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// =============================================================================
// Configuration
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const SPIKE_VUS = parseInt(__ENV.SPIKE_VUS) || 30;

// Custom metrics
const errorRate = new Rate('error_rate');
const recoveryTrend = new Trend('recovery_time');

export const options = {
  stages: [
    { duration: '30s', target: 3 },        // Normal load
    { duration: '10s', target: SPIKE_VUS }, // Spike!
    { duration: '1m', target: SPIKE_VUS },  // Maintain spike
    { duration: '10s', target: 3 },         // Scale down
    { duration: '30s', target: 3 },         // Recovery period
    { duration: '30s', target: 0 },         // Wind down
  ],

  thresholds: {
    http_req_duration: ['p(95)<3000'],    // 95% under 3s during spike
    http_req_failed: ['rate<0.20'],        // Error rate under 20% during spike
    error_rate: ['rate<0.25'],             // Custom error rate under 25%
  },
};

// =============================================================================
// Setup
// =============================================================================

export function setup() {
  const health = http.get(`${BASE_URL}/health`);
  if (health.status !== 200) {
    throw new Error('API not available');
  }
  console.log(`Spike testing ${BASE_URL} with ${SPIKE_VUS} VU spike`);
  return { startTime: Date.now() };
}

// =============================================================================
// Spike Test Scenario
// =============================================================================

export default function () {
  const iterationStart = Date.now();

  group('Critical Path', () => {
    // Health check - must always work
    const health = http.get(`${BASE_URL}/health`);
    check(health, { 'health OK': (r) => r.status === 200 }) || errorRate.add(1);

    // Core services endpoint
    const services = http.get(`${BASE_URL}/api/v1/services`);
    check(services, { 'services OK': (r) => r.status === 200 }) || errorRate.add(1);

    // Core templates endpoint
    const templates = http.get(`${BASE_URL}/api/v1/templates`);
    check(templates, { 'templates OK': (r) => r.status === 200 }) || errorRate.add(1);
  });

  group('ML Operations', () => {
    // ML recommendation - computationally heavier
    const payload = JSON.stringify({
      workload_type: 'api',
      language: 'python',
    });

    const recommend = http.post(`${BASE_URL}/api/v1/ml/recommend`, payload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: '15s',
    });

    check(recommend, { 'recommend OK': (r) => r.status === 200 }) || errorRate.add(1);
  });

  group('Aggregation Endpoints', () => {
    // Metrics - requires aggregation
    const metrics = http.get(`${BASE_URL}/api/v1/metrics`);
    check(metrics, { 'metrics OK': (r) => r.status === 200 }) || errorRate.add(1);

    // Stats endpoints
    const serviceStats = http.get(`${BASE_URL}/api/v1/services/stats`);
    check(serviceStats, { 'service stats OK': (r) => r.status === 200 }) || errorRate.add(1);
  });

  // Track iteration time
  const iterationDuration = Date.now() - iterationStart;
  recoveryTrend.add(iterationDuration);

  sleep(0.3);
}

// =============================================================================
// Teardown
// =============================================================================

export function teardown(data) {
  const totalDuration = (Date.now() - data.startTime) / 1000;
  console.log(`Spike test completed in ${totalDuration.toFixed(2)} seconds`);
}
