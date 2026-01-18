/**
 * K6 Load Test - API Baseline
 * ForgeWorks Backend
 *
 * Baseline performance tests for ForgeWorks API endpoints
 *
 * Usage:
 *   k6 run tests/load/k6-api-baseline.js
 *   k6 run --vus 10 --duration 30s tests/load/k6-api-baseline.js
 *   k6 run --env BASE_URL=http://api.example.com tests/load/k6-api-baseline.js
 *
 * Install k6: brew install k6
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// =============================================================================
// Configuration
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Custom metrics
const errorRate = new Rate('errors');
const servicesTrend = new Trend('services_duration');
const templatesTrend = new Trend('templates_duration');
const recommendTrend = new Trend('recommend_duration');
const healthTrend = new Trend('health_duration');

export const options = {
  // Stages for ramping up/down
  stages: [
    { duration: '30s', target: 5 },   // Warm up to 5 users
    { duration: '1m', target: 10 },   // Ramp up to 10 users
    { duration: '2m', target: 10 },   // Steady state at 10 users
    { duration: '30s', target: 0 },   // Ramp down
  ],

  // Thresholds for pass/fail
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% under 500ms, 99% under 1s
    http_req_failed: ['rate<0.01'],                  // Error rate under 1%
    errors: ['rate<0.05'],                           // Custom error rate under 5%
    services_duration: ['p(95)<300'],                // Services endpoint p95 < 300ms
    templates_duration: ['p(95)<300'],               // Templates endpoint p95 < 300ms
    recommend_duration: ['p(95)<1000'],              // ML recommend p95 < 1s
    health_duration: ['p(95)<100'],                  // Health check p95 < 100ms
  },
};

// =============================================================================
// Setup
// =============================================================================

export function setup() {
  // Verify API is up before testing
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'API is healthy': (r) => r.status === 200,
  });

  if (healthCheck.status !== 200) {
    throw new Error('API is not healthy, aborting load test');
  }

  console.log(`Load testing ${BASE_URL}`);
  return { startTime: Date.now() };
}

// =============================================================================
// Main Test Scenario
// =============================================================================

export default function () {
  // Health Check
  group('Health Endpoints', () => {
    const healthRes = http.get(`${BASE_URL}/health`);
    healthTrend.add(healthRes.timings.duration);
    check(healthRes, {
      'health status is 200': (r) => r.status === 200,
      'health is healthy': (r) => {
        try {
          return JSON.parse(r.body).status === 'healthy';
        } catch {
          return false;
        }
      },
    }) || errorRate.add(1);

    const detailedHealth = http.get(`${BASE_URL}/health/detailed`);
    check(detailedHealth, {
      'detailed health is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  // Services API
  group('Services API', () => {
    // List services
    const servicesRes = http.get(`${BASE_URL}/api/v1/services`);
    servicesTrend.add(servicesRes.timings.duration);
    check(servicesRes, {
      'services status is 200': (r) => r.status === 200,
      'services has items': (r) => {
        try {
          return JSON.parse(r.body).items !== undefined;
        } catch {
          return false;
        }
      },
    }) || errorRate.add(1);

    // Service stats
    const statsRes = http.get(`${BASE_URL}/api/v1/services/stats`);
    check(statsRes, {
      'service stats is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  // Templates API
  group('Templates API', () => {
    // List templates
    const templatesRes = http.get(`${BASE_URL}/api/v1/templates`);
    templatesTrend.add(templatesRes.timings.duration);
    check(templatesRes, {
      'templates status is 200': (r) => r.status === 200,
      'templates has items': (r) => {
        try {
          return JSON.parse(r.body).items !== undefined;
        } catch {
          return false;
        }
      },
    }) || errorRate.add(1);

    // Filter by workload type
    const apiTemplates = http.get(`${BASE_URL}/api/v1/templates?workload_type=api`);
    check(apiTemplates, {
      'filtered templates is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  // ML Recommendation API
  group('ML Recommendation API', () => {
    const payload = JSON.stringify({
      workload_type: 'api',
      language: 'python',
    });

    const headers = { 'Content-Type': 'application/json' };
    const recommendRes = http.post(`${BASE_URL}/api/v1/ml/recommend`, payload, { headers });
    recommendTrend.add(recommendRes.timings.duration);

    check(recommendRes, {
      'recommend status is 200': (r) => r.status === 200,
      'recommend has recommendations': (r) => {
        try {
          return JSON.parse(r.body).recommendations !== undefined;
        } catch {
          return false;
        }
      },
    }) || errorRate.add(1);

    // ML Health
    const mlHealth = http.get(`${BASE_URL}/api/v1/ml/health`);
    check(mlHealth, {
      'ML health is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  // Metrics API
  group('Metrics API', () => {
    const metricsRes = http.get(`${BASE_URL}/api/v1/metrics`);
    check(metricsRes, {
      'metrics dashboard is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    const doraRes = http.get(`${BASE_URL}/api/v1/metrics/dora`);
    check(doraRes, {
      'DORA metrics is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(0.5);

  // Anomalies API
  group('Anomalies API', () => {
    const anomaliesRes = http.get(`${BASE_URL}/api/v1/anomalies`);
    check(anomaliesRes, {
      'anomalies is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    const statsRes = http.get(`${BASE_URL}/api/v1/anomalies/stats`);
    check(statsRes, {
      'anomaly stats is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  });

  sleep(1);
}

// =============================================================================
// Teardown
// =============================================================================

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${duration.toFixed(2)} seconds`);
}
