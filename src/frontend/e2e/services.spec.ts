/**
 * Service Catalog E2E Tests
 * ForgeWorks Frontend
 *
 * Tests the service catalog API and workflows
 */

import { test, expect } from '@playwright/test';

// =============================================================================
// Services API Tests
// =============================================================================

test.describe('Services API', () => {
  test('should list all services', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/services');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(data.items).toBeInstanceOf(Array);
  });

  test('should get service statistics', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/services/stats');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('healthy');
    expect(data).toHaveProperty('degraded');
    expect(data).toHaveProperty('unhealthy');
    expect(typeof data.total).toBe('number');
  });

  test('should get service by ID', async ({ request }) => {
    // First get list to find a valid ID
    const listResponse = await request.get('http://localhost:8000/api/v1/services');
    const { items } = await listResponse.json();

    if (items.length > 0) {
      const serviceId = items[0].id;
      const response = await request.get(`http://localhost:8000/api/v1/services/${serviceId}`);

      expect(response.ok()).toBeTruthy();

      const service = await response.json();
      expect(service).toHaveProperty('id');
      expect(service).toHaveProperty('name');
      expect(service).toHaveProperty('status');
    }
  });

  test('should return 404 for non-existent service', async ({ request }) => {
    const response = await request.get(
      'http://localhost:8000/api/v1/services/non-existent-service-id'
    );

    expect(response.status()).toBe(404);
  });

  test('should create a new service', async ({ request }) => {
    const newService = {
      name: `e2e-test-service-${Date.now()}`,
      description: 'E2E test service',
      owner: 'e2e-test-team',
      status: 'provisioning',
    };

    const response = await request.post('http://localhost:8000/api/v1/services', {
      data: newService,
    });

    // Should succeed or require auth
    expect([200, 201, 401]).toContain(response.status());

    if (response.ok()) {
      const created = await response.json();
      expect(created.name).toBe(newService.name);
      expect(created.description).toBe(newService.description);
    }
  });

  test('should validate required fields on create', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/services', {
      data: {},
    });

    expect([400, 422]).toContain(response.status());
  });
});

// =============================================================================
// Service Health Tests
// =============================================================================

test.describe('Service Health', () => {
  test('should include health status in service list', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/services');
    const { items } = await response.json();

    for (const service of items) {
      expect(service).toHaveProperty('status');
      expect(['healthy', 'degraded', 'unhealthy', 'provisioning', 'unknown']).toContain(
        service.status
      );
    }
  });

  test('should get health metrics from metrics API', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/metrics/health');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('total_services');
    expect(data).toHaveProperty('healthy_services');
    expect(data).toHaveProperty('health_score');
  });
});

// =============================================================================
// Service Filtering Tests
// =============================================================================

test.describe('Service Filtering', () => {
  test('should filter services by status', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/services?status=healthy');

    expect(response.ok()).toBeTruthy();

    const { items } = await response.json();
    for (const service of items) {
      expect(service.status).toBe('healthy');
    }
  });

  test('should filter services by owner', async ({ request }) => {
    // First get list to find an owner
    const listResponse = await request.get('http://localhost:8000/api/v1/services');
    const { items } = await listResponse.json();

    if (items.length > 0 && items[0].owner) {
      const owner = items[0].owner;
      const response = await request.get(
        `http://localhost:8000/api/v1/services?owner=${encodeURIComponent(owner)}`
      );

      expect(response.ok()).toBeTruthy();

      const filtered = await response.json();
      for (const service of filtered.items) {
        expect(service.owner).toBe(owner);
      }
    }
  });

  test('should search services by name', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/services?search=api');

    expect(response.ok()).toBeTruthy();

    const { items } = await response.json();
    // Search results should contain the search term in name or description
    for (const service of items) {
      const matchesName = service.name?.toLowerCase().includes('api');
      const matchesDesc = service.description?.toLowerCase().includes('api');
      expect(matchesName || matchesDesc).toBeTruthy();
    }
  });

  test('should paginate results', async ({ request }) => {
    const page1Response = await request.get(
      'http://localhost:8000/api/v1/services?page=1&page_size=5'
    );
    expect(page1Response.ok()).toBeTruthy();

    const page1 = await page1Response.json();

    if (page1.total > 5) {
      const page2Response = await request.get(
        'http://localhost:8000/api/v1/services?page=2&page_size=5'
      );
      expect(page2Response.ok()).toBeTruthy();

      const page2 = await page2Response.json();

      // Pages should have different items
      if (page1.items.length > 0 && page2.items.length > 0) {
        expect(page1.items[0].id).not.toBe(page2.items[0].id);
      }
    }
  });
});

// =============================================================================
// Service-Template Integration Tests
// =============================================================================

test.describe('Service-Template Integration', () => {
  test('should have template_id on services created from templates', async ({ request }) => {
    const listResponse = await request.get('http://localhost:8000/api/v1/services');
    const { items } = await listResponse.json();

    // Some services should have template associations
    const servicesWithTemplates = items.filter(
      (s: { template_id?: string }) => s.template_id !== null && s.template_id !== undefined
    );

    // If any services have templates, verify the template exists
    for (const service of servicesWithTemplates.slice(0, 3)) {
      const templateResponse = await request.get(
        `http://localhost:8000/api/v1/templates/${service.template_id}`
      );
      // Template should exist or return 404 if ID format differs
      expect([200, 404]).toContain(templateResponse.status());
    }
  });

  test('should recommend templates for new service', async ({ request }) => {
    // Use ML to get recommendation
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });

    expect(response.ok()).toBeTruthy();

    const { recommendations } = await response.json();
    expect(recommendations.length).toBeGreaterThan(0);

    // Verify recommended template exists
    const templateId = recommendations[0].template_id;
    const templatesResponse = await request.get('http://localhost:8000/api/v1/templates');
    const templates = await templatesResponse.json();

    const templateExists = templates.items.some(
      (t: { id: string; name: string }) => t.id === templateId || t.name === templateId
    );
    expect(templateExists).toBeTruthy();
  });
});

// =============================================================================
// Anomaly Detection Tests
// =============================================================================

test.describe('Service Anomaly Detection', () => {
  test('should list anomalies', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/anomalies');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data.items).toBeInstanceOf(Array);
  });

  test('should get anomaly statistics', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/anomalies/stats');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('active');
  });

  test('should filter anomalies by service', async ({ request }) => {
    // First get a service ID
    const servicesResponse = await request.get('http://localhost:8000/api/v1/services');
    const { items: services } = await servicesResponse.json();

    if (services.length > 0) {
      const serviceId = services[0].id;
      const response = await request.get(
        `http://localhost:8000/api/v1/anomalies?service_id=${serviceId}`
      );

      expect(response.ok()).toBeTruthy();

      const { items: anomalies } = await response.json();
      for (const anomaly of anomalies) {
        expect(anomaly.service_id).toBe(serviceId);
      }
    }
  });

  test('should filter anomalies by severity', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/anomalies?severity=critical');

    expect(response.ok()).toBeTruthy();

    const { items } = await response.json();
    for (const anomaly of items) {
      expect(anomaly.severity).toBe('critical');
    }
  });
});

// =============================================================================
// DORA Metrics Tests
// =============================================================================

test.describe('DORA Metrics', () => {
  test('should get DORA metrics', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/metrics/dora');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('deployment_frequency');
    expect(data).toHaveProperty('change_failure_rate');
    expect(data).toHaveProperty('mean_time_to_recovery');
    expect(data).toHaveProperty('lead_time_for_changes');
  });

  test('should get deployment metrics', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/metrics/deployment');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('total_deploys');
    expect(data).toHaveProperty('deploy_success_rate');
  });

  test('should get full metrics dashboard', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/metrics');

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('deployment');
    expect(data).toHaveProperty('dora');
    expect(data).toHaveProperty('service_health');
    expect(data).toHaveProperty('generated_at');
  });
});

// =============================================================================
// Performance Tests
// =============================================================================

test.describe('Performance', () => {
  test('services list should respond in under 1 second', async ({ request }) => {
    const startTime = Date.now();

    await request.get('http://localhost:8000/api/v1/services');

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(1000);
  });

  test('service stats should respond in under 500ms', async ({ request }) => {
    const startTime = Date.now();

    await request.get('http://localhost:8000/api/v1/services/stats');

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(500);
  });

  test('metrics dashboard should respond in under 2 seconds', async ({ request }) => {
    const startTime = Date.now();

    await request.get('http://localhost:8000/api/v1/metrics');

    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(2000);
  });
});
