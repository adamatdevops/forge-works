/**
 * Template Flow E2E Tests
 * ForgeWorks Frontend
 *
 * Tests the complete ML-powered template recommendation workflow
 */

import { test, expect } from '@playwright/test';

// =============================================================================
// ML Recommendation API Tests
// =============================================================================

test.describe('ML Recommendation API', () => {
  test('should get recommendations for Python API workload', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('recommendations');
    expect(data.recommendations).toBeInstanceOf(Array);
    expect(data.recommendations.length).toBeGreaterThan(0);
  });

  test('should get recommendations for Go streaming workload', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'stream',
        language: 'go',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.recommendations).toBeInstanceOf(Array);
  });

  test('should get recommendations for TypeScript batch workload', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'batch',
        language: 'typescript',
      },
    });

    expect(response.ok()).toBeTruthy();
  });

  test('should get recommendations for ML workload', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'ml',
        language: 'python',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.recommendations).toBeInstanceOf(Array);
  });

  test('should include confidence scores in recommendations', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    const data = await response.json();

    // Each recommendation should have a confidence/score
    for (const rec of data.recommendations) {
      expect(rec).toHaveProperty('template_id');
      expect(typeof rec.confidence === 'number' || typeof rec.score === 'number').toBeTruthy();
    }
  });

  test('should handle requirements parameter', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
        requirements: ['database', 'caching', 'authentication'],
      },
    });

    expect(response.ok()).toBeTruthy();
  });
});

// =============================================================================
// Templates API Tests
// =============================================================================

test.describe('Templates API', () => {
  test('should list all templates', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/templates');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data.items).toBeInstanceOf(Array);
  });

  test('should get template by ID', async ({ request }) => {
    // First get list to find a valid ID
    const listResponse = await request.get('http://localhost:8000/api/v1/templates');
    const { items } = await listResponse.json();

    if (items.length > 0) {
      const templateId = items[0].id;
      const response = await request.get(`http://localhost:8000/api/v1/templates/${templateId}`);

      expect(response.ok()).toBeTruthy();

      const template = await response.json();
      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('name');
    }
  });

  test('should return 404 for non-existent template', async ({ request }) => {
    const response = await request.get(
      'http://localhost:8000/api/v1/templates/non-existent-template-id'
    );

    expect(response.status()).toBe(404);
  });

  test('should filter templates by workload type', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/templates?workload_type=api');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    // All returned templates should match the filter
    for (const template of data.items) {
      expect(template.workload_type).toBe('api');
    }
  });

  test('should filter templates by language', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/templates?language=python');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    // All returned templates should match the filter
    for (const template of data.items) {
      expect(template.language).toBe('python');
    }
  });
});

// =============================================================================
// ML Health & Status Tests
// =============================================================================

test.describe('ML Service Health', () => {
  test('should report ML service health', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/ml/health');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(['healthy', 'degraded', 'unhealthy']).toContain(data.status);
    expect(data).toHaveProperty('mode');
    expect(['ml', 'rule-based']).toContain(data.mode);
  });

  test('should list available ML templates', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/ml/templates');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('templates');
  });
});

// =============================================================================
// Feedback API Tests
// =============================================================================

test.describe('Feedback API', () => {
  test('should accept positive feedback', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/feedback', {
      data: {
        recommendation_id: 'test-recommendation-1',
        template_id: 'python-api',
        accepted: true,
      },
    });

    // Should succeed or return a specific validation error
    expect([200, 201, 422]).toContain(response.status());
  });

  test('should accept negative feedback with reason', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/feedback', {
      data: {
        recommendation_id: 'test-recommendation-2',
        template_id: 'go-service',
        accepted: false,
        reason: 'Not suitable for our use case',
      },
    });

    expect([200, 201, 422]).toContain(response.status());
  });
});

// =============================================================================
// Complete Template Workflow Tests
// =============================================================================

test.describe('Complete Template Workflow', () => {
  test('end-to-end: get recommendation -> select template -> view details', async ({
    request,
  }) => {
    // Step 1: Get ML recommendations
    const recommendResponse = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    expect(recommendResponse.ok()).toBeTruthy();
    const recommendations = await recommendResponse.json();
    expect(recommendations.recommendations.length).toBeGreaterThan(0);

    // Step 2: Get the top recommended template ID
    const topRecommendation = recommendations.recommendations[0];
    const templateId = topRecommendation.template_id;

    // Step 3: Fetch template details from the templates API
    const templatesResponse = await request.get('http://localhost:8000/api/v1/templates');
    expect(templatesResponse.ok()).toBeTruthy();

    const templates = await templatesResponse.json();
    const selectedTemplate = templates.items.find(
      (t: { id: string; name: string }) => t.id === templateId || t.name === templateId
    );

    // Verify template exists and has expected structure
    if (selectedTemplate) {
      expect(selectedTemplate).toHaveProperty('id');
      expect(selectedTemplate).toHaveProperty('name');
    }
  });

  test('workflow: explore templates -> filter -> select', async ({ request }) => {
    // Step 1: List all templates
    const allTemplatesResponse = await request.get('http://localhost:8000/api/v1/templates');
    expect(allTemplatesResponse.ok()).toBeTruthy();

    const allTemplates = await allTemplatesResponse.json();
    const totalCount = allTemplates.items.length;

    // Step 2: Filter by workload type
    const apiTemplatesResponse = await request.get(
      'http://localhost:8000/api/v1/templates?workload_type=api'
    );
    expect(apiTemplatesResponse.ok()).toBeTruthy();

    const apiTemplates = await apiTemplatesResponse.json();

    // Filtered count should be less than or equal to total
    expect(apiTemplates.items.length).toBeLessThanOrEqual(totalCount);

    // Step 3: Filter by language
    const pythonApiResponse = await request.get(
      'http://localhost:8000/api/v1/templates?workload_type=api&language=python'
    );
    expect(pythonApiResponse.ok()).toBeTruthy();

    const pythonApiTemplates = await pythonApiResponse.json();

    // Double filter should be more restrictive
    expect(pythonApiTemplates.items.length).toBeLessThanOrEqual(apiTemplates.items.length);
  });
});

// =============================================================================
// Error Handling Tests
// =============================================================================

test.describe('Error Handling', () => {
  test('should handle invalid workload type', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'invalid_type',
        language: 'python',
      },
    });

    expect(response.status()).toBe(422);
  });

  test('should handle invalid language', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'invalid_language',
      },
    });

    expect(response.status()).toBe(422);
  });

  test('should handle missing required fields', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {},
    });

    expect(response.status()).toBe(422);
  });

  test('should handle malformed JSON', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      headers: { 'Content-Type': 'application/json' },
      data: 'not valid json',
    });

    // Should return 400 or 422 for malformed requests
    expect([400, 422]).toContain(response.status());
  });
});

// =============================================================================
// Performance Tests
// =============================================================================

test.describe('Performance', () => {
  test('recommendation should respond in under 2 seconds', async ({ request }) => {
    const startTime = Date.now();

    await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(2000);
  });

  test('template list should respond in under 1 second', async ({ request }) => {
    const startTime = Date.now();

    await request.get('http://localhost:8000/api/v1/templates');

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(1000);
  });

  test('ML health check should respond in under 500ms', async ({ request }) => {
    const startTime = Date.now();

    await request.get('http://localhost:8000/api/v1/ml/health');

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(500);
  });
});
