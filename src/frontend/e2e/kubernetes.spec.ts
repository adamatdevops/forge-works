/**
 * Kubernetes API E2E Tests
 * ForgeWorks Frontend
 *
 * Tests Kubernetes cluster management and monitoring APIs
 * Note: Tests run against mock adapter in development mode
 */

import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8000/api/v1';

// =============================================================================
// Cluster Info Tests
// =============================================================================

test.describe('Kubernetes Cluster Info', () => {
  test('should get cluster overview', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/cluster`);

    expect(response.ok()).toBeTruthy();

    const cluster = await response.json();
    expect(cluster).toHaveProperty('version');
    expect(cluster).toHaveProperty('platform');
    expect(cluster).toHaveProperty('node_count');
    expect(cluster).toHaveProperty('namespace_count');
    expect(cluster).toHaveProperty('pod_count');
    expect(cluster).toHaveProperty('deployment_count');
    expect(cluster).toHaveProperty('adapter_mode');
  });

  test('should include adapter mode in response', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/cluster`);
    const cluster = await response.json();

    // Should be 'mock' in development or 'live' in production
    expect(['mock', 'live']).toContain(cluster.adapter_mode);
  });
});

// =============================================================================
// Namespace Tests
// =============================================================================

test.describe('Kubernetes Namespaces', () => {
  test('should list all namespaces', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/namespaces`);

    expect(response.ok()).toBeTruthy();

    const namespaces = await response.json();
    expect(Array.isArray(namespaces)).toBeTruthy();
    expect(namespaces.length).toBeGreaterThan(0);
  });

  test('should include namespace details', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/namespaces`);
    const namespaces = await response.json();

    const namespace = namespaces[0];
    expect(namespace).toHaveProperty('name');
    expect(namespace).toHaveProperty('status');
    expect(namespace).toHaveProperty('pod_count');
    expect(namespace).toHaveProperty('deployment_count');
    expect(namespace).toHaveProperty('created_at');
  });

  test('should have common namespaces', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/namespaces`);
    const namespaces = await response.json();

    const namespaceNames = namespaces.map((ns: { name: string }) => ns.name);

    // Common K8s namespaces (mock data should include these)
    const expectedNamespaces = ['default', 'kube-system'];
    for (const expected of expectedNamespaces) {
      expect(namespaceNames).toContain(expected);
    }
  });
});

// =============================================================================
// Node Tests
// =============================================================================

test.describe('Kubernetes Nodes', () => {
  test('should list all nodes', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/nodes`);

    expect(response.ok()).toBeTruthy();

    const nodes = await response.json();
    expect(Array.isArray(nodes)).toBeTruthy();
    expect(nodes.length).toBeGreaterThan(0);
  });

  test('should include node details', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/nodes`);
    const nodes = await response.json();

    const node = nodes[0];
    expect(node).toHaveProperty('name');
    expect(node).toHaveProperty('status');
    expect(node).toHaveProperty('cpu_capacity');
    expect(node).toHaveProperty('memory_capacity');
    expect(node).toHaveProperty('roles');
  });

  test('should have at least one Ready node', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/nodes`);
    const nodes = await response.json();

    const readyNodes = nodes.filter((n: { status: string }) => n.status === 'Ready');
    expect(readyNodes.length).toBeGreaterThan(0);
  });

  test('should include node resource metrics', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/nodes`);
    const nodes = await response.json();

    const node = nodes[0];
    expect(node).toHaveProperty('cpu_usage');
    expect(node).toHaveProperty('memory_usage');
    expect(node).toHaveProperty('pod_count');
  });
});

// =============================================================================
// Deployment Tests
// =============================================================================

test.describe('Kubernetes Deployments', () => {
  test('should list all deployments', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/deployments`);

    expect(response.ok()).toBeTruthy();

    const deployments = await response.json();
    expect(Array.isArray(deployments)).toBeTruthy();
    expect(deployments.length).toBeGreaterThan(0);
  });

  test('should include deployment details', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/deployments`);
    const deployments = await response.json();

    const deployment = deployments[0];
    expect(deployment).toHaveProperty('name');
    expect(deployment).toHaveProperty('namespace');
    expect(deployment).toHaveProperty('replicas');
    expect(deployment).toHaveProperty('ready_replicas');
    expect(deployment).toHaveProperty('available_replicas');
  });

  test('should filter deployments by namespace', async ({ request }) => {
    // First get all deployments to find a namespace
    const allResponse = await request.get(`${API_BASE}/kubernetes/deployments`);
    const allDeployments = await allResponse.json();

    if (allDeployments.length > 0) {
      const namespace = allDeployments[0].namespace;

      const filteredResponse = await request.get(
        `${API_BASE}/kubernetes/deployments?namespace=${namespace}`
      );
      const filteredDeployments = await filteredResponse.json();

      // All filtered deployments should be in the specified namespace
      for (const dep of filteredDeployments) {
        expect(dep.namespace).toBe(namespace);
      }
    }
  });

  test('should filter deployments by label selector', async ({ request }) => {
    const response = await request.get(
      `${API_BASE}/kubernetes/deployments?label_selector=app=forge-api`
    );

    expect(response.ok()).toBeTruthy();

    const deployments = await response.json();
    expect(Array.isArray(deployments)).toBeTruthy();
  });

  test('should get specific deployment by name and namespace', async ({ request }) => {
    // First get a deployment to use
    const listResponse = await request.get(`${API_BASE}/kubernetes/deployments`);
    const deployments = await listResponse.json();

    if (deployments.length > 0) {
      const { name, namespace } = deployments[0];

      const detailResponse = await request.get(
        `${API_BASE}/kubernetes/deployments/${namespace}/${name}`
      );

      expect(detailResponse.ok()).toBeTruthy();

      const deployment = await detailResponse.json();
      expect(deployment.name).toBe(name);
      expect(deployment.namespace).toBe(namespace);
    }
  });

  test('should return 404 for non-existent deployment', async ({ request }) => {
    const response = await request.get(
      `${API_BASE}/kubernetes/deployments/default/non-existent-deployment-12345`
    );

    expect(response.status()).toBe(404);
  });
});

// =============================================================================
// Pod Tests
// =============================================================================

test.describe('Kubernetes Pods', () => {
  test('should list all pods', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/pods`);

    expect(response.ok()).toBeTruthy();

    const pods = await response.json();
    expect(Array.isArray(pods)).toBeTruthy();
    expect(pods.length).toBeGreaterThan(0);
  });

  test('should include pod details', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/pods`);
    const pods = await response.json();

    const pod = pods[0];
    expect(pod).toHaveProperty('name');
    expect(pod).toHaveProperty('namespace');
    expect(pod).toHaveProperty('phase');
    expect(pod).toHaveProperty('containers');
    expect(pod).toHaveProperty('node');
  });

  test('should include container details', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/pods`);
    const pods = await response.json();

    const podWithContainers = pods.find(
      (p: { containers: unknown[] }) => p.containers && p.containers.length > 0
    );

    if (podWithContainers) {
      const container = podWithContainers.containers[0];
      expect(container).toHaveProperty('name');
      expect(container).toHaveProperty('image');
      expect(container).toHaveProperty('ready');
      expect(container).toHaveProperty('restart_count');
    }
  });

  test('should filter pods by namespace', async ({ request }) => {
    const allResponse = await request.get(`${API_BASE}/kubernetes/pods`);
    const allPods = await allResponse.json();

    if (allPods.length > 0) {
      const namespace = allPods[0].namespace;

      const filteredResponse = await request.get(
        `${API_BASE}/kubernetes/pods?namespace=${namespace}`
      );
      const filteredPods = await filteredResponse.json();

      for (const pod of filteredPods) {
        expect(pod.namespace).toBe(namespace);
      }
    }
  });

  test('should filter pods by label selector', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/pods?label_selector=app=forge-api`);

    expect(response.ok()).toBeTruthy();

    const pods = await response.json();
    expect(Array.isArray(pods)).toBeTruthy();
  });

  test('should have pods in different phases', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/pods`);
    const pods = await response.json();

    const phases = new Set(pods.map((p: { phase: string }) => p.phase));

    // At minimum, should have Running pods
    expect(phases.has('Running')).toBeTruthy();
  });
});

// =============================================================================
// Pod Logs Tests
// =============================================================================

test.describe('Kubernetes Pod Logs', () => {
  test('should get pod logs', async ({ request }) => {
    // First get a running pod
    const podsResponse = await request.get(`${API_BASE}/kubernetes/pods`);
    const pods = await podsResponse.json();

    const runningPod = pods.find((p: { phase: string }) => p.phase === 'Running');

    if (runningPod) {
      const { name, namespace } = runningPod;

      const logsResponse = await request.get(
        `${API_BASE}/kubernetes/pods/${namespace}/${name}/logs`
      );

      expect(logsResponse.ok()).toBeTruthy();

      const logs = await logsResponse.json();
      expect(logs).toHaveProperty('namespace', namespace);
      expect(logs).toHaveProperty('pod', name);
      expect(logs).toHaveProperty('lines');
      expect(logs).toHaveProperty('line_count');
      expect(Array.isArray(logs.lines)).toBeTruthy();
    }
  });

  test('should limit log lines with tail_lines parameter', async ({ request }) => {
    const podsResponse = await request.get(`${API_BASE}/kubernetes/pods`);
    const pods = await podsResponse.json();

    const runningPod = pods.find((p: { phase: string }) => p.phase === 'Running');

    if (runningPod) {
      const { name, namespace } = runningPod;

      const logsResponse = await request.get(
        `${API_BASE}/kubernetes/pods/${namespace}/${name}/logs?tail_lines=10`
      );

      expect(logsResponse.ok()).toBeTruthy();

      const logs = await logsResponse.json();
      expect(logs.line_count).toBeLessThanOrEqual(10);
    }
  });
});

// =============================================================================
// Cluster Stats Tests
// =============================================================================

test.describe('Kubernetes Cluster Stats', () => {
  test('should get cluster statistics', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/stats`);

    expect(response.ok()).toBeTruthy();

    const stats = await response.json();
    expect(stats).toHaveProperty('nodes');
    expect(stats).toHaveProperty('namespaces');
    expect(stats).toHaveProperty('deployments');
    expect(stats).toHaveProperty('pods');
    expect(stats).toHaveProperty('cluster_version');
  });

  test('should include node statistics', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/stats`);
    const stats = await response.json();

    expect(stats.nodes).toHaveProperty('total');
    expect(stats.nodes).toHaveProperty('healthy');
    expect(stats.nodes).toHaveProperty('unhealthy');
    expect(stats.nodes.total).toBe(stats.nodes.healthy + stats.nodes.unhealthy);
  });

  test('should include deployment statistics', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/stats`);
    const stats = await response.json();

    expect(stats.deployments).toHaveProperty('total');
    expect(stats.deployments).toHaveProperty('healthy');
    expect(stats.deployments).toHaveProperty('degraded');
    expect(stats.deployments.total).toBe(stats.deployments.healthy + stats.deployments.degraded);
  });

  test('should include pod statistics', async ({ request }) => {
    const response = await request.get(`${API_BASE}/kubernetes/stats`);
    const stats = await response.json();

    expect(stats.pods).toHaveProperty('total');
    expect(stats.pods).toHaveProperty('running');
    expect(stats.pods).toHaveProperty('pending');
    expect(stats.pods).toHaveProperty('failed');
    expect(stats.pods).toHaveProperty('total_restarts');
  });

  test('should have consistent counts across endpoints', async ({ request }) => {
    const [statsResponse, nodesResponse, deploymentsResponse, podsResponse] = await Promise.all([
      request.get(`${API_BASE}/kubernetes/stats`),
      request.get(`${API_BASE}/kubernetes/nodes`),
      request.get(`${API_BASE}/kubernetes/deployments`),
      request.get(`${API_BASE}/kubernetes/pods`),
    ]);

    const stats = await statsResponse.json();
    const nodes = await nodesResponse.json();
    const deployments = await deploymentsResponse.json();
    const pods = await podsResponse.json();

    expect(stats.nodes.total).toBe(nodes.length);
    expect(stats.deployments.total).toBe(deployments.length);
    expect(stats.pods.total).toBe(pods.length);
  });
});

// =============================================================================
// Error Handling Tests
// =============================================================================

test.describe('Kubernetes Error Handling', () => {
  test('should handle invalid namespace gracefully', async ({ request }) => {
    const response = await request.get(
      `${API_BASE}/kubernetes/pods?namespace=invalid-namespace-that-does-not-exist`
    );

    // Should succeed but return empty list, or handle gracefully
    expect(response.ok() || response.status() === 404).toBeTruthy();
  });

  test('should validate tail_lines parameter', async ({ request }) => {
    const podsResponse = await request.get(`${API_BASE}/kubernetes/pods`);
    const pods = await podsResponse.json();

    if (pods.length > 0) {
      const { name, namespace } = pods[0];

      // Try invalid tail_lines (greater than 1000)
      const invalidResponse = await request.get(
        `${API_BASE}/kubernetes/pods/${namespace}/${name}/logs?tail_lines=5000`
      );

      expect(invalidResponse.status()).toBe(422);
    }
  });
});

// =============================================================================
// Performance Tests
// =============================================================================

test.describe('Kubernetes Performance', () => {
  test('should respond to cluster info within 2 seconds', async ({ request }) => {
    const startTime = Date.now();
    const response = await request.get(`${API_BASE}/kubernetes/cluster`);
    const duration = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();
    expect(duration).toBeLessThan(2000);
  });

  test('should respond to stats within 3 seconds', async ({ request }) => {
    const startTime = Date.now();
    const response = await request.get(`${API_BASE}/kubernetes/stats`);
    const duration = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();
    expect(duration).toBeLessThan(3000);
  });

  test('should handle concurrent kubernetes requests', async ({ request }) => {
    const requests = [
      request.get(`${API_BASE}/kubernetes/cluster`),
      request.get(`${API_BASE}/kubernetes/nodes`),
      request.get(`${API_BASE}/kubernetes/namespaces`),
      request.get(`${API_BASE}/kubernetes/deployments`),
      request.get(`${API_BASE}/kubernetes/pods`),
    ];

    const responses = await Promise.all(requests);

    for (const response of responses) {
      expect(response.ok()).toBeTruthy();
    }
  });
});
