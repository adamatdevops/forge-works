/**
 * Services API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { servicesApi } from './services';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Services API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =============================================================================
  // getAll Tests
  // =============================================================================

  describe('getAll', () => {
    it('should fetch all services', async () => {
      const mockServices = [
        { id: '1', name: 'service-a', status: 'healthy' },
        { id: '2', name: 'service-b', status: 'degraded' },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: mockServices,
        total: 2,
      });

      const result = await servicesApi.getAll();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/services');
      expect(result).toEqual(mockServices);
    });

    it('should return empty array when no services exist', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
      });

      const result = await servicesApi.getAll();

      expect(result).toEqual([]);
    });

    it('should propagate API errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('API Error: 500'));

      await expect(servicesApi.getAll()).rejects.toThrow('API Error: 500');
    });
  });

  // =============================================================================
  // getById Tests
  // =============================================================================

  describe('getById', () => {
    it('should fetch service by ID', async () => {
      const mockService = {
        id: '1',
        name: 'service-a',
        status: 'healthy',
        owner: 'team-platform',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockService);

      const result = await servicesApi.getById('1');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/services/1');
      expect(result).toEqual(mockService);
    });

    it('should handle UUID format IDs', async () => {
      const uuid = '550e8400-e29b-41d4-a716-446655440000';
      vi.mocked(apiClient.get).mockResolvedValueOnce({ id: uuid });

      await servicesApi.getById(uuid);

      expect(apiClient.get).toHaveBeenCalledWith(`/api/v1/services/${uuid}`);
    });

    it('should propagate 404 errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 404 Not Found')
      );

      await expect(servicesApi.getById('nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });
  });

  // =============================================================================
  // create Tests
  // =============================================================================

  describe('create', () => {
    it('should create new service', async () => {
      const newService = {
        name: 'new-service',
        description: 'A new service',
        owner: 'team-platform',
      };
      const createdService = {
        id: '3',
        ...newService,
        status: 'provisioning',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(createdService);

      const result = await servicesApi.create(newService);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/services', newService);
      expect(result).toEqual(createdService);
    });

    it('should handle minimal service data', async () => {
      const minimalService = { name: 'minimal-service' };
      vi.mocked(apiClient.post).mockResolvedValueOnce({
        id: '4',
        ...minimalService,
      });

      await servicesApi.create(minimalService);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/services', minimalService);
    });

    it('should propagate validation errors', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new Error('API Error: 422 Unprocessable Entity')
      );

      await expect(servicesApi.create({})).rejects.toThrow(
        'API Error: 422 Unprocessable Entity'
      );
    });
  });

  // =============================================================================
  // getStats Tests
  // =============================================================================

  describe('getStats', () => {
    it('should fetch service statistics', async () => {
      const mockStats = {
        total: 10,
        healthy: 7,
        degraded: 2,
        unhealthy: 1,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockStats);

      const result = await servicesApi.getStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/services/stats');
      expect(result).toEqual(mockStats);
    });

    it('should return zero stats when no services exist', async () => {
      const emptyStats = {
        total: 0,
        healthy: 0,
        degraded: 0,
        unhealthy: 0,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(emptyStats);

      const result = await servicesApi.getStats();

      expect(result.total).toBe(0);
    });
  });
});
