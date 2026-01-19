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
import type { WorkloadFeatures, RecommendationFeedback } from '@/types/ml';

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
      const features: WorkloadFeatures = {
        workload_type: 'api',
        language: 'python',
        needs_database: true,
        database_type: 'postgresql',
        needs_queue: false,
        needs_cache: true,
        needs_gpu: false,
        expected_rps: 100,
        expected_memory_mb: 512,
        team_size: 5,
        compliance_required: false,
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
      const features: WorkloadFeatures = {
        workload_type: 'batch',
        language: 'python',
        needs_database: false,
        database_type: 'none',
        needs_queue: true,
        needs_cache: false,
        needs_gpu: false,
        expected_rps: 10,
        expected_memory_mb: 1024,
        team_size: 3,
        compliance_required: false,
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
      const features: WorkloadFeatures = {
        workload_type: 'api',
        language: 'python',
        needs_database: true,
        database_type: 'postgresql',
        needs_queue: false,
        needs_cache: false,
        needs_gpu: false,
        expected_rps: 100,
        expected_memory_mb: 512,
        team_size: 5,
        compliance_required: false,
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid workload type' }),
      });

      await expect(getRecommendation(features)).rejects.toThrow('Invalid workload type');
    });

    it('should throw generic error when no detail', async () => {
      const features: WorkloadFeatures = {
        workload_type: 'api',
        language: 'python',
        needs_database: true,
        database_type: 'postgresql',
        needs_queue: false,
        needs_cache: false,
        needs_gpu: false,
        expected_rps: 100,
        expected_memory_mb: 512,
        team_size: 5,
        compliance_required: false,
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.reject(new Error('Parse error')),
      });

      await expect(getRecommendation(features)).rejects.toThrow('Failed to get recommendation');
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
      const feedback: RecommendationFeedback = {
        recommendation_id: 'rec-123',
        selected_template: 'microservice-python',
        was_primary: true,
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
      const feedback: RecommendationFeedback = {
        recommendation_id: 'rec-456',
        selected_template: 'worker-service',
        was_primary: false,
        feedback_text: 'Not suitable for our use case',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'success', message: 'Recorded' }),
      });

      await submitFeedback(feedback);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: expect.stringContaining('"was_primary":false'),
        })
      );
    });

    it('should throw error on failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      const feedback: RecommendationFeedback = {
        selected_template: 'microservice-node',
        was_primary: true,
      };

      await expect(submitFeedback(feedback)).rejects.toThrow('Failed to submit feedback');
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
