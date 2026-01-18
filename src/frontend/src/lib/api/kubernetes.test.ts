/**
 * Kubernetes API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { kubernetesApi } from './kubernetes';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('Kubernetes API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =============================================================================
  // getClusterInfo Tests
  // =============================================================================

  describe('getClusterInfo', () => {
    it('should fetch cluster information', async () => {
      const mockClusterInfo = {
        name: 'production-cluster',
        version: 'v1.28.0',
        platform: 'aws-eks',
        region: 'us-east-1',
        node_count: 10,
        status: 'healthy',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockClusterInfo);

      const result = await kubernetesApi.getClusterInfo();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/kubernetes/cluster');
      expect(result).toEqual(mockClusterInfo);
    });
  });

  // =============================================================================
  // getStats Tests
  // =============================================================================

  describe('getStats', () => {
    it('should fetch kubernetes statistics', async () => {
      const mockStats = {
        nodes: { total: 10, ready: 9, not_ready: 1 },
        pods: { total: 150, running: 145, pending: 3, failed: 2 },
        deployments: { total: 25, available: 24, unavailable: 1 },
        namespaces: { total: 8, active: 8 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockStats);

      const result = await kubernetesApi.getStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/kubernetes/stats');
      expect(result).toEqual(mockStats);
    });
  });

  // =============================================================================
  // getNamespaces Tests
  // =============================================================================

  describe('getNamespaces', () => {
    it('should fetch all namespaces', async () => {
      const mockNamespaces = [
        { name: 'default', status: 'Active', labels: {} },
        { name: 'kube-system', status: 'Active', labels: {} },
        { name: 'forge-works', status: 'Active', labels: { app: 'forge-works' } },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockNamespaces);

      const result = await kubernetesApi.getNamespaces();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/kubernetes/namespaces');
      expect(result).toEqual(mockNamespaces);
      expect(result).toHaveLength(3);
    });
  });

  // =============================================================================
  // getNodes Tests
  // =============================================================================

  describe('getNodes', () => {
    it('should fetch all nodes', async () => {
      const mockNodes = [
        {
          name: 'node-1',
          status: 'Ready',
          roles: ['worker'],
          cpu_capacity: '4',
          memory_capacity: '16Gi',
        },
        {
          name: 'node-2',
          status: 'Ready',
          roles: ['worker'],
          cpu_capacity: '8',
          memory_capacity: '32Gi',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockNodes);

      const result = await kubernetesApi.getNodes();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/kubernetes/nodes');
      expect(result).toEqual(mockNodes);
    });
  });

  // =============================================================================
  // getDeployments Tests
  // =============================================================================

  describe('getDeployments', () => {
    it('should fetch all deployments without filters', async () => {
      const mockDeployments = [
        { name: 'api-gateway', namespace: 'default', replicas: 3, available: 3 },
        { name: 'backend-api', namespace: 'forge-works', replicas: 2, available: 2 },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockDeployments);

      const result = await kubernetesApi.getDeployments();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/kubernetes/deployments');
      expect(result).toEqual(mockDeployments);
    });

    it('should filter by namespace', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);

      await kubernetesApi.getDeployments({ namespace: 'forge-works' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('namespace=forge-works')
      );
    });

    it('should filter by label selector', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);

      await kubernetesApi.getDeployments({ label_selector: 'app=backend' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('label_selector=app%3Dbackend')
      );
    });

    it('should combine namespace and label selector', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);

      await kubernetesApi.getDeployments({
        namespace: 'production',
        label_selector: 'tier=frontend',
      });

      const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(calledUrl).toContain('namespace=production');
      expect(calledUrl).toContain('label_selector=');
    });
  });

  // =============================================================================
  // getDeployment Tests
  // =============================================================================

  describe('getDeployment', () => {
    it('should fetch specific deployment by namespace and name', async () => {
      const mockDeployment = {
        name: 'backend-api',
        namespace: 'forge-works',
        replicas: 3,
        available: 3,
        strategy: 'RollingUpdate',
        containers: [
          { name: 'api', image: 'forge-works/api:v1.0.0' },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockDeployment);

      const result = await kubernetesApi.getDeployment('forge-works', 'backend-api');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/kubernetes/deployments/forge-works/backend-api'
      );
      expect(result).toEqual(mockDeployment);
    });

    it('should handle 404 for non-existent deployment', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 404 Not Found')
      );

      await expect(
        kubernetesApi.getDeployment('default', 'nonexistent')
      ).rejects.toThrow('API Error: 404 Not Found');
    });
  });

  // =============================================================================
  // getPods Tests
  // =============================================================================

  describe('getPods', () => {
    it('should fetch all pods without filters', async () => {
      const mockPods = [
        { name: 'api-pod-1', namespace: 'default', status: 'Running' },
        { name: 'api-pod-2', namespace: 'default', status: 'Running' },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockPods);

      const result = await kubernetesApi.getPods();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/kubernetes/pods');
      expect(result).toEqual(mockPods);
    });

    it('should filter by namespace', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);

      await kubernetesApi.getPods({ namespace: 'forge-works' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('namespace=forge-works')
      );
    });

    it('should filter by label selector', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce([]);

      await kubernetesApi.getPods({ label_selector: 'app=backend' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('label_selector=')
      );
    });
  });

  // =============================================================================
  // getPodLogs Tests
  // =============================================================================

  describe('getPodLogs', () => {
    it('should fetch pod logs without params', async () => {
      const mockLogs = {
        namespace: 'forge-works',
        pod: 'backend-api-1',
        container: null,
        lines: ['Starting server...', 'Listening on port 8000'],
        line_count: 2,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockLogs);

      const result = await kubernetesApi.getPodLogs('forge-works', 'backend-api-1');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/kubernetes/pods/forge-works/backend-api-1/logs'
      );
      expect(result).toEqual(mockLogs);
    });

    it('should fetch logs for specific container', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        namespace: 'forge-works',
        pod: 'backend-api-1',
        container: 'sidecar',
        lines: [],
        line_count: 0,
      });

      await kubernetesApi.getPodLogs('forge-works', 'backend-api-1', {
        container: 'sidecar',
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('container=sidecar')
      );
    });

    it('should limit log lines with tail_lines', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        lines: ['line1', 'line2'],
        line_count: 2,
      });

      await kubernetesApi.getPodLogs('forge-works', 'backend-api-1', {
        tail_lines: 100,
      });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('tail_lines=100')
      );
    });

    it('should combine container and tail_lines params', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        lines: [],
        line_count: 0,
      });

      await kubernetesApi.getPodLogs('forge-works', 'backend-api-1', {
        container: 'api',
        tail_lines: 50,
      });

      const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(calledUrl).toContain('container=api');
      expect(calledUrl).toContain('tail_lines=50');
    });
  });

  // =============================================================================
  // Error Handling Tests
  // =============================================================================

  describe('error handling', () => {
    it('should propagate cluster connection errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 503 Service Unavailable')
      );

      await expect(kubernetesApi.getClusterInfo()).rejects.toThrow(
        'API Error: 503 Service Unavailable'
      );
    });

    it('should propagate unauthorized errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 401 Unauthorized')
      );

      await expect(kubernetesApi.getDeployments()).rejects.toThrow(
        'API Error: 401 Unauthorized'
      );
    });

    it('should propagate forbidden errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 403 Forbidden')
      );

      await expect(kubernetesApi.getPodLogs('default', 'pod-1')).rejects.toThrow(
        'API Error: 403 Forbidden'
      );
    });
  });
});
