/**
 * Templates API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { templatesApi } from './templates';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Templates API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =============================================================================
  // getAll Tests
  // =============================================================================

  describe('getAll', () => {
    it('should fetch all templates', async () => {
      const mockTemplates = [
        { id: '1', name: 'python-api', workload_type: 'api' },
        { id: '2', name: 'go-service', workload_type: 'api' },
        { id: '3', name: 'stream-processor', workload_type: 'stream' },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: mockTemplates,
        total: 3,
      });

      const result = await templatesApi.getAll();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/templates');
      expect(result).toEqual(mockTemplates);
      expect(result).toHaveLength(3);
    });

    it('should return empty array when no templates exist', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        items: [],
        total: 0,
      });

      const result = await templatesApi.getAll();

      expect(result).toEqual([]);
    });

    it('should propagate API errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('API Error: 500'));

      await expect(templatesApi.getAll()).rejects.toThrow('API Error: 500');
    });
  });

  // =============================================================================
  // getById Tests
  // =============================================================================

  describe('getById', () => {
    it('should fetch template by ID', async () => {
      const mockTemplate = {
        id: '1',
        name: 'python-api',
        description: 'FastAPI + PostgreSQL template',
        workload_type: 'api',
        language: 'python',
        capabilities: ['database', 'caching', 'monitoring'],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockTemplate);

      const result = await templatesApi.getById('1');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/templates/1');
      expect(result).toEqual(mockTemplate);
    });

    it('should handle UUID format IDs', async () => {
      const uuid = '550e8400-e29b-41d4-a716-446655440000';
      vi.mocked(apiClient.get).mockResolvedValueOnce({ id: uuid });

      await templatesApi.getById(uuid);

      expect(apiClient.get).toHaveBeenCalledWith(`/api/v1/templates/${uuid}`);
    });

    it('should propagate 404 errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 404 Not Found')
      );

      await expect(templatesApi.getById('nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });
  });

  // =============================================================================
  // getRecommendations Tests
  // =============================================================================

  describe('getRecommendations', () => {
    it('should get recommendations for Python API workload', async () => {
      const request = {
        workload_type: 'api' as const,
        language: 'python' as const,
      };
      const mockResponse = {
        recommendations: [
          { template_id: '1', score: 0.95, reason: 'Best match for Python API' },
        ],
        model_version: 'v1.0.0',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await templatesApi.getRecommendations(request);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/templates/recommend',
        request
      );
      expect(result).toEqual(mockResponse);
    });

    it('should get recommendations for Go streaming workload', async () => {
      const request = {
        workload_type: 'stream' as const,
        language: 'go' as const,
        requirements: ['kafka', 'high-throughput'],
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({
        recommendations: [],
      });

      await templatesApi.getRecommendations(request);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/templates/recommend',
        request
      );
    });

    it('should include optional team_id in request', async () => {
      const request = {
        workload_type: 'batch' as const,
        language: 'python' as const,
        team_id: 'team-data-engineering',
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({
        recommendations: [],
      });

      await templatesApi.getRecommendations(request);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/templates/recommend',
        expect.objectContaining({ team_id: 'team-data-engineering' })
      );
    });

    it('should handle ML workload type', async () => {
      const request = {
        workload_type: 'ml' as const,
        language: 'python' as const,
        requirements: ['tensorflow', 'gpu'],
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce({
        recommendations: [
          { template_id: 'ml-service', score: 0.98 },
        ],
      });

      const result = await templatesApi.getRecommendations(request);

      expect(result.recommendations).toHaveLength(1);
    });

    it('should propagate validation errors', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new Error('API Error: 422 Unprocessable Entity')
      );

      await expect(
        templatesApi.getRecommendations({
          workload_type: 'api',
          language: 'python',
        })
      ).rejects.toThrow('API Error: 422 Unprocessable Entity');
    });
  });
});
