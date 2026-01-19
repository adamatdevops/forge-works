/**
 * Anomalies API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { anomaliesApi } from './anomalies';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Anomalies API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =============================================================================
  // getAll Tests
  // =============================================================================

  describe('getAll', () => {
    it('should fetch all anomalies without filters', async () => {
      const mockAnomalies = [
        { id: '1', type: 'high_deploy_frequency', severity: 'warning' },
        { id: '2', type: 'consecutive_rollbacks', severity: 'critical' },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: mockAnomalies,
        total: 2,
        page: 1,
        page_size: 10,
        pages: 1,
      });

      const result = await anomaliesApi.getAll();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/anomalies');
      expect(result).toEqual(mockAnomalies);
    });

    it('should filter by severity', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        pages: 0,
      });

      await anomaliesApi.getAll({ severity: 'critical' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('severity=critical')
      );
    });

    it('should filter by service_id', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        pages: 0,
      });

      await anomaliesApi.getAll({ service_id: 'service-123' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('service_id=service-123')
      );
    });

    it('should filter by active status', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        pages: 0,
      });

      await anomaliesApi.getAll({ active: true });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('active=true')
      );
    });

    it('should handle pagination params', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 100,
        page: 2,
        page_size: 20,
        pages: 5,
      });

      await anomaliesApi.getAll({ page: 2, page_size: 20 });

      const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(calledUrl).toContain('page=2');
      expect(calledUrl).toContain('page_size=20');
    });

    it('should combine multiple filters', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
        pages: 0,
      });

      await anomaliesApi.getAll({
        severity: 'warning',
        active: true,
        type: 'high_deploy_frequency',
      });

      const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(calledUrl).toContain('severity=warning');
      expect(calledUrl).toContain('active=true');
      expect(calledUrl).toContain('type=high_deploy_frequency');
    });
  });

  // =============================================================================
  // getAllPaginated Tests
  // =============================================================================

  describe('getAllPaginated', () => {
    it('should return full pagination response', async () => {
      const mockResponse = {
        items: [{ id: '1' }],
        total: 50,
        page: 1,
        page_size: 10,
        pages: 5,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await anomaliesApi.getAllPaginated({ page: 1 });

      expect(result).toEqual(mockResponse);
      expect(result.pages).toBe(5);
    });
  });

  // =============================================================================
  // getById Tests
  // =============================================================================

  describe('getById', () => {
    it('should fetch anomaly by ID', async () => {
      const mockAnomaly = {
        id: '1',
        type: 'high_deploy_frequency',
        severity: 'warning',
        service_id: 'service-123',
        detected_at: '2024-01-15T10:00:00Z',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockAnomaly);

      const result = await anomaliesApi.getById('1');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/anomalies/1');
      expect(result).toEqual(mockAnomaly);
    });

    it('should propagate 404 errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 404 Not Found')
      );

      await expect(anomaliesApi.getById('nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });
  });

  // =============================================================================
  // getStats Tests
  // =============================================================================

  describe('getStats', () => {
    it('should fetch anomaly statistics', async () => {
      const mockStats = {
        total: 25,
        by_severity: { critical: 3, warning: 12, info: 10 },
        by_type: { high_deploy_frequency: 8, consecutive_rollbacks: 5 },
        active: 15,
        acknowledged: 5,
        unresolved: 18,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockStats);

      const result = await anomaliesApi.getStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/anomalies/stats');
      expect(result).toEqual(mockStats);
    });
  });

  // =============================================================================
  // acknowledge Tests
  // =============================================================================

  describe('acknowledge', () => {
    it('should acknowledge an anomaly', async () => {
      const acknowledgeData = { acknowledged_by: 'user@example.com' };
      const mockResponse = {
        id: '1',
        is_acknowledged: true,
        acknowledged_by: 'user@example.com',
        acknowledged_at: '2024-01-15T11:00:00Z',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await anomaliesApi.acknowledge('1', acknowledgeData);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/anomalies/1/acknowledge',
        acknowledgeData
      );
      expect(result.is_acknowledged).toBe(true);
    });
  });

  // =============================================================================
  // resolve Tests
  // =============================================================================

  describe('resolve', () => {
    it('should resolve an anomaly with note', async () => {
      const resolveData = { resolution_note: 'Fixed by reducing deploy frequency' };
      const mockResponse = {
        id: '1',
        is_resolved: true,
        resolution_note: resolveData.resolution_note,
        resolved_at: '2024-01-15T12:00:00Z',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await anomaliesApi.resolve('1', resolveData);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/anomalies/1/resolve',
        resolveData
      );
      expect(result.is_resolved).toBe(true);
    });

    it('should resolve an anomaly without note', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({
        id: '1',
        is_resolved: true,
      });

      await anomaliesApi.resolve('1');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/anomalies/1/resolve',
        undefined
      );
    });
  });

  // =============================================================================
  // delete Tests
  // =============================================================================

  describe('delete', () => {
    it('should delete an anomaly', async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce(undefined);

      await anomaliesApi.delete('1');

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/anomalies/1');
    });

    it('should propagate 403 errors', async () => {
      vi.mocked(apiClient.delete).mockRejectedValueOnce(
        new Error('API Error: 403 Forbidden')
      );

      await expect(anomaliesApi.delete('1')).rejects.toThrow(
        'API Error: 403 Forbidden'
      );
    });
  });
});
