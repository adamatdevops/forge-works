/**
 * ML API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  getRecommendation,
  listTemplates,
  getTemplate,
  submitFeedback,
  checkMLHealth,
} from './ml';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ML API', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  // =============================================================================
  // getRecommendation Tests
  // =============================================================================

  describe('getRecommendation', () => {
    it('should get recommendation for workload features', async () => {
      const features = {
        workload_type: 'api' as const,
        language: 'python' as const,
        requirements: ['database', 'caching'],
      };
      const mockResponse = {
        template_id: 'python-api',
        confidence: 0.95,
        alternatives: [
          { template_id: 'python-fastapi', confidence: 0.85 },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await getRecommendation(features);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ml/recommend',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(features),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle batch workload type', async () => {
      const features = {
        workload_type: 'batch' as const,
        language: 'python' as const,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ template_id: 'data-pipeline' }),
      });

      await getRecommendation(features);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"workload_type":"batch"'),
        })
      );
    });

    it('should throw error with detail from API', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid workload type' }),
      });

      await expect(
        getRecommendation({ workload_type: 'api', language: 'python' })
      ).rejects.toThrow('Invalid workload type');
    });

    it('should throw generic error when no detail', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.reject(new Error('Parse error')),
      });

      await expect(
        getRecommendation({ workload_type: 'api', language: 'python' })
      ).rejects.toThrow('Failed to get recommendation');
    });
  });

  // =============================================================================
  // listTemplates Tests
  // =============================================================================

  describe('listTemplates', () => {
    it('should list all templates', async () => {
      const mockTemplates = {
        templates: [
          { id: 'python-api', name: 'Python API', workload_type: 'api' },
          { id: 'go-service', name: 'Go Service', workload_type: 'api' },
          { id: 'stream-processor', name: 'Stream Processor', workload_type: 'stream' },
        ],
        total: 3,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTemplates),
      });

      const result = await listTemplates();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ml/templates',
        expect.objectContaining({
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })
      );
      expect(result).toEqual(mockTemplates);
    });

    it('should throw error on failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      await expect(listTemplates()).rejects.toThrow('Failed to fetch templates');
    });
  });

  // =============================================================================
  // getTemplate Tests
  // =============================================================================

  describe('getTemplate', () => {
    it('should get template by ID', async () => {
      const mockTemplate = {
        id: 'python-api',
        name: 'Python API',
        description: 'FastAPI + PostgreSQL template',
        workload_type: 'api',
        language: 'python',
        capabilities: ['database', 'caching', 'monitoring'],
        files: ['Dockerfile', 'docker-compose.yml', 'pyproject.toml'],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTemplate),
      });

      const result = await getTemplate('python-api');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ml/templates/python-api',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockTemplate);
    });

    it('should throw 404 error for non-existent template', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(getTemplate('nonexistent')).rejects.toThrow(
        "Template 'nonexistent' not found"
      );
    });

    it('should throw generic error for other failures', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(getTemplate('python-api')).rejects.toThrow(
        'Failed to fetch template'
      );
    });
  });

  // =============================================================================
  // submitFeedback Tests
  // =============================================================================

  describe('submitFeedback', () => {
    it('should submit positive feedback', async () => {
      const feedback = {
        recommendation_id: 'rec-123',
        accepted: true,
        template_id: 'python-api',
      };
      const mockResponse = {
        status: 'success',
        message: 'Feedback recorded',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await submitFeedback(feedback);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ml/feedback',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(feedback),
        })
      );
      expect(result.status).toBe('success');
    });

    it('should submit negative feedback with reason', async () => {
      const feedback = {
        recommendation_id: 'rec-456',
        accepted: false,
        template_id: 'go-service',
        reason: 'Not suitable for our use case',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'success', message: 'Recorded' }),
      });

      await submitFeedback(feedback);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"accepted":false'),
        })
      );
    });

    it('should throw error on failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      await expect(
        submitFeedback({ recommendation_id: 'rec-1', accepted: true, template_id: 'test' })
      ).rejects.toThrow('Failed to submit feedback');
    });
  });

  // =============================================================================
  // checkMLHealth Tests
  // =============================================================================

  describe('checkMLHealth', () => {
    it('should return healthy status with ML mode', async () => {
      const mockHealth = {
        status: 'healthy',
        model_loaded: true,
        mode: 'ml' as const,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockHealth),
      });

      const result = await checkMLHealth();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/ml/health',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockHealth);
      expect(result.mode).toBe('ml');
    });

    it('should return healthy status with rule-based mode', async () => {
      const mockHealth = {
        status: 'healthy',
        model_loaded: false,
        mode: 'rule-based' as const,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockHealth),
      });

      const result = await checkMLHealth();

      expect(result.model_loaded).toBe(false);
      expect(result.mode).toBe('rule-based');
    });

    it('should throw error when service unavailable', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      await expect(checkMLHealth()).rejects.toThrow('ML service unavailable');
    });

    it('should throw error on network failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(checkMLHealth()).rejects.toThrow('Network error');
    });
  });
});
