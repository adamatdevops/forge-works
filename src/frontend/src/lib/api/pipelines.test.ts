/**
 * Pipelines API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { pipelinesApi } from './pipelines';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Pipelines API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =============================================================================
  // getAll Tests
  // =============================================================================

  describe('getAll', () => {
    it('should fetch all pipelines without filters', async () => {
      const mockPipelines = [
        { id: '1', name: 'build-main', status: 'success' },
        { id: '2', name: 'deploy-prod', status: 'running' },
        { id: '3', name: 'test-suite', status: 'pending' },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: mockPipelines,
        total: 3,
      });

      const result = await pipelinesApi.getAll();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/pipelines');
      expect(result).toEqual(mockPipelines);
      expect(result).toHaveLength(3);
    });

    it('should filter by service_id', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
      });

      await pipelinesApi.getAll({ service_id: 'service-123' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('service_id=service-123')
      );
    });

    it('should filter by status', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [{ id: '1', status: 'failed' }],
        total: 1,
      });

      await pipelinesApi.getAll({ status: 'failed' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('status=failed')
      );
    });

    it('should limit results', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [{ id: '1' }],
        total: 1,
      });

      await pipelinesApi.getAll({ limit: 5 });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('limit=5')
      );
    });

    it('should combine multiple filters', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
      });

      await pipelinesApi.getAll({
        service_id: 'svc-1',
        status: 'success',
        limit: 10,
      });

      const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(calledUrl).toContain('service_id=svc-1');
      expect(calledUrl).toContain('status=success');
      expect(calledUrl).toContain('limit=10');
    });

    it('should return empty array when no pipelines exist', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
      });

      const result = await pipelinesApi.getAll();

      expect(result).toEqual([]);
    });
  });

  // =============================================================================
  // getById Tests
  // =============================================================================

  describe('getById', () => {
    it('should fetch pipeline by ID', async () => {
      const mockPipeline = {
        id: '1',
        name: 'build-main',
        status: 'success',
        started_at: '2024-01-15T10:00:00Z',
        finished_at: '2024-01-15T10:05:00Z',
        duration_seconds: 300,
        stages: [
          { name: 'build', status: 'success' },
          { name: 'test', status: 'success' },
          { name: 'deploy', status: 'success' },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockPipeline);

      const result = await pipelinesApi.getById('1');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/pipelines/1');
      expect(result).toEqual(mockPipeline);
    });

    it('should propagate 404 errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 404 Not Found')
      );

      await expect(pipelinesApi.getById('nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });
  });

  // =============================================================================
  // getStats Tests
  // =============================================================================

  describe('getStats', () => {
    it('should fetch pipeline statistics', async () => {
      const mockStats = {
        total: 150,
        by_status: {
          pending: 5,
          running: 3,
          success: 130,
          failed: 12,
        },
        success_rate: 0.867,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockStats);

      const result = await pipelinesApi.getStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/pipelines/stats');
      expect(result).toEqual(mockStats);
    });

    it('should handle zero pipelines', async () => {
      const emptyStats = {
        total: 0,
        by_status: {
          pending: 0,
          running: 0,
          success: 0,
          failed: 0,
        },
        success_rate: 0,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(emptyStats);

      const result = await pipelinesApi.getStats();

      expect(result.total).toBe(0);
      expect(result.success_rate).toBe(0);
    });
  });

  // =============================================================================
  // retry Tests
  // =============================================================================

  describe('retry', () => {
    it('should retry a failed pipeline', async () => {
      const mockRetried = {
        id: '1-retry-1',
        original_id: '1',
        status: 'pending',
        started_at: '2024-01-15T11:00:00Z',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockRetried);

      const result = await pipelinesApi.retry('1');

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/pipelines/1/retry');
      expect(result.status).toBe('pending');
    });

    it('should propagate errors when retry fails', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new Error('API Error: 400 Bad Request')
      );

      await expect(pipelinesApi.retry('1')).rejects.toThrow(
        'API Error: 400 Bad Request'
      );
    });

    it('should propagate errors when pipeline not found', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new Error('API Error: 404 Not Found')
      );

      await expect(pipelinesApi.retry('nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });
  });

  // =============================================================================
  // Error Handling Tests
  // =============================================================================

  describe('error handling', () => {
    it('should propagate network errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(pipelinesApi.getAll()).rejects.toThrow('Network error');
    });

    it('should propagate 500 errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 500 Internal Server Error')
      );

      await expect(pipelinesApi.getStats()).rejects.toThrow(
        'API Error: 500 Internal Server Error'
      );
    });
  });
});
