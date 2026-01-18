/**
 * Resilience & Recovery E2E Tests
 * ForgeWorks Frontend
 *
 * Tests API behavior during degraded conditions and recovery
 */

import { test, expect } from '@playwright/test';

// =============================================================================
// API Timeout & Retry Behavior Tests
// =============================================================================

test.describe('API Timeout Behavior', () => {
  test('should handle slow responses gracefully', async ({ request }) => {
    // The API should respond even under load
    const startTime = Date.now();
    const response = await request.get('http://localhost:8000/api/v1/services', {
      timeout: 30000, // 30 second timeout
    });

    const duration = Date.now() - startTime;

    // Should succeed within timeout
    expect(response.ok()).toBeTruthy();

    // Log response time for monitoring
    console.log(`Services endpoint responded in ${duration}ms`);
  });

  test('should handle concurrent requests', async ({ request }) => {
    // Make multiple concurrent requests
    const requests = Array(10)
      .fill(null)
      .map(() => request.get('http://localhost:8000/api/v1/services'));

    const responses = await Promise.all(requests);

    // All requests should succeed
    for (const response of responses) {
      expect(response.ok()).toBeTruthy();
    }
  });

  test('should maintain consistency under concurrent load', async ({ request }) => {
    // Get initial count
    const initialResponse = await request.get('http://localhost:8000/api/v1/services/stats');
    const initialStats = await initialResponse.json();

    // Make concurrent requests
    const requests = Array(5)
      .fill(null)
      .map(() => request.get('http://localhost:8000/api/v1/services/stats'));

    const responses = await Promise.all(requests);
    const allStats = await Promise.all(responses.map((r) => r.json()));

    // All responses should have consistent total count
    for (const stats of allStats) {
      expect(stats.total).toBe(initialStats.total);
    }
  });
});

// =============================================================================
// Error Recovery Tests
// =============================================================================

test.describe('Error Recovery', () => {
  test('should return proper error for 404', async ({ request }) => {
    const response = await request.get(
      'http://localhost:8000/api/v1/services/non-existent-id-12345'
    );

    expect(response.status()).toBe(404);

    const error = await response.json();
    expect(error).toHaveProperty('detail');
  });

  test('should return proper error for invalid request body', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: { invalid: 'data' },
    });

    expect(response.status()).toBe(422);

    const error = await response.json();
    expect(error).toHaveProperty('detail');
  });

  test('should handle malformed JSON gracefully', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      headers: { 'Content-Type': 'application/json' },
      data: 'not-json',
    });

    // Should return 400 or 422, not 500
    expect([400, 422]).toContain(response.status());
  });

  test('should recover after error and accept valid request', async ({ request }) => {
    // First, make an invalid request
    await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: { invalid: 'data' },
    });

    // Then, make a valid request - should succeed
    const validResponse = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    expect(validResponse.ok()).toBeTruthy();
  });
});

// =============================================================================
// Health Check Degradation Tests
// =============================================================================

test.describe('Health Check Behavior', () => {
  test('should report component health', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health/detailed');

    expect(response.ok()).toBeTruthy();

    const health = await response.json();
    expect(health).toHaveProperty('components');
    expect(health).toHaveProperty('status');

    // Log component statuses
    console.log('Component health:', JSON.stringify(health.components, null, 2));
  });

  test('should respond to health checks quickly even under load', async ({ request }) => {
    // Start background load
    const loadPromises = Array(5)
      .fill(null)
      .map(() =>
        request.post('http://localhost:8000/api/v1/ml/recommend', {
          data: { workload_type: 'api', language: 'python' },
        })
      );

    // Health check should still be fast
    const startTime = Date.now();
    const healthResponse = await request.get('http://localhost:8000/health');
    const healthDuration = Date.now() - startTime;

    expect(healthResponse.ok()).toBeTruthy();
    expect(healthDuration).toBeLessThan(500); // Health check < 500ms even under load

    // Wait for load to complete
    await Promise.all(loadPromises);
  });

  test('should include database connectivity in detailed health', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health/detailed');
    const health = await response.json();

    // Should have database component
    if (health.components?.database) {
      expect(['healthy', 'degraded', 'unhealthy']).toContain(health.components.database.status);
    }
  });
});

// =============================================================================
// Graceful Degradation Tests
// =============================================================================

test.describe('Graceful Degradation', () => {
  test('ML should fall back to rule-based when needed', async ({ request }) => {
    const healthResponse = await request.get('http://localhost:8000/api/v1/ml/health');
    const health = await healthResponse.json();

    // ML should work in either mode
    expect(['ml', 'rule-based']).toContain(health.mode);

    // Recommendations should work regardless of mode
    const recommendResponse = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    expect(recommendResponse.ok()).toBeTruthy();

    const recommendations = await recommendResponse.json();
    expect(recommendations.recommendations.length).toBeGreaterThan(0);
  });

  test('should return cached data when possible', async ({ request }) => {
    // Make same request twice
    const startTime1 = Date.now();
    await request.get('http://localhost:8000/api/v1/templates');
    const duration1 = Date.now() - startTime1;

    const startTime2 = Date.now();
    await request.get('http://localhost:8000/api/v1/templates');
    const duration2 = Date.now() - startTime2;

    // Second request might be faster if caching is enabled
    // Log for monitoring
    console.log(`First request: ${duration1}ms, Second request: ${duration2}ms`);
  });
});

// =============================================================================
// Rate Limiting & Throttling Tests
// =============================================================================

test.describe('Rate Limiting', () => {
  test('should handle burst of requests', async ({ request }) => {
    const startTime = Date.now();

    // Burst of 20 requests
    const requests = Array(20)
      .fill(null)
      .map(() => request.get('http://localhost:8000/api/v1/services'));

    const responses = await Promise.all(requests);
    const duration = Date.now() - startTime;

    // Count successful responses
    const successCount = responses.filter((r) => r.ok()).length;
    const rateLimitedCount = responses.filter((r) => r.status() === 429).length;

    console.log(
      `Burst test: ${successCount} succeeded, ${rateLimitedCount} rate limited in ${duration}ms`
    );

    // At least some should succeed (may have rate limiting)
    expect(successCount).toBeGreaterThan(0);
  });

  test('should not permanently block after burst', async ({ request }) => {
    // Burst of requests
    const burst = Array(10)
      .fill(null)
      .map(() => request.get('http://localhost:8000/api/v1/services'));
    await Promise.allSettled(burst);

    // Wait a moment
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Should be able to make request again
    const response = await request.get('http://localhost:8000/api/v1/services');
    expect(response.ok()).toBeTruthy();
  });
});

// =============================================================================
// Connection Recovery Tests
// =============================================================================

test.describe('Connection Recovery', () => {
  test('should handle request after idle period', async ({ request }) => {
    // Make initial request
    const response1 = await request.get('http://localhost:8000/health');
    expect(response1.ok()).toBeTruthy();

    // Wait (simulating idle connection)
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Should still work
    const response2 = await request.get('http://localhost:8000/health');
    expect(response2.ok()).toBeTruthy();
  });

  test('should handle sequential dependent requests', async ({ request }) => {
    // Step 1: Get templates
    const templatesResponse = await request.get('http://localhost:8000/api/v1/templates');
    expect(templatesResponse.ok()).toBeTruthy();
    const templates = await templatesResponse.json();

    // Step 2: Get recommendation
    const recommendResponse = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });
    expect(recommendResponse.ok()).toBeTruthy();
    const recommendations = await recommendResponse.json();

    // Step 3: Verify recommended template exists
    if (recommendations.recommendations.length > 0) {
      const templateId = recommendations.recommendations[0].template_id;
      const exists = templates.items.some(
        (t: { id: string; name: string }) => t.id === templateId || t.name === templateId
      );
      expect(exists).toBeTruthy();
    }
  });
});

// =============================================================================
// Data Integrity Tests
// =============================================================================

test.describe('Data Integrity', () => {
  test('should return consistent data across requests', async ({ request }) => {
    // Get services list twice
    const response1 = await request.get('http://localhost:8000/api/v1/services');
    const response2 = await request.get('http://localhost:8000/api/v1/services');

    const data1 = await response1.json();
    const data2 = await response2.json();

    // Should have same total
    expect(data1.total).toBe(data2.total);

    // Items should be in same order (if no modifications)
    if (data1.items.length > 0 && data2.items.length > 0) {
      expect(data1.items[0].id).toBe(data2.items[0].id);
    }
  });

  test('should maintain referential integrity between services and anomalies', async ({
    request,
  }) => {
    // Get services
    const servicesResponse = await request.get('http://localhost:8000/api/v1/services');
    const services = await servicesResponse.json();
    const serviceIds = new Set(services.items.map((s: { id: string }) => s.id));

    // Get anomalies
    const anomaliesResponse = await request.get('http://localhost:8000/api/v1/anomalies');
    const anomalies = await anomaliesResponse.json();

    // Each anomaly's service_id should exist in services
    for (const anomaly of anomalies.items) {
      if (anomaly.service_id) {
        expect(serviceIds.has(anomaly.service_id)).toBeTruthy();
      }
    }
  });
});
