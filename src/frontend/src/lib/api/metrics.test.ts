/**
 * Metrics API Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { metricsApi } from './metrics';
import { apiClient } from './client';

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('Metrics API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =============================================================================
  // getDashboard Tests
  // =============================================================================

  describe('getDashboard', () => {
    it('should fetch full metrics dashboard', async () => {
      const mockDashboard = {
        deployment: {
          total_deploys: 100,
          successful_deploys: 95,
          failed_deploys: 5,
          deploy_success_rate: 0.95,
        },
        pipeline: {
          total_runs: 200,
          success_rate: 0.92,
        },
        service_health: {
          total_services: 20,
          healthy_services: 18,
          health_score: 0.9,
        },
        dora: {
          deployment_frequency: 'daily',
          overall_score: 'elite',
        },
        generated_at: '2024-01-15T10:00:00Z',
        data_freshness: '5 minutes ago',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockDashboard);

      const result = await metricsApi.getDashboard();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/metrics');
      expect(result).toEqual(mockDashboard);
    });

    it('should filter by service_id', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({});

      await metricsApi.getDashboard({ service_id: 'service-123' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('service_id=service-123')
      );
    });

    it('should filter by team_id', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({});

      await metricsApi.getDashboard({ team_id: 'team-platform' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('team_id=team-platform')
      );
    });

    it('should filter by time_range', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({});

      await metricsApi.getDashboard({ time_range: '7d' });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('time_range=7d')
      );
    });

    it('should include trends when requested', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        deploy_trend: { name: 'deploys', data: [], unit: 'count' },
        error_trend: { name: 'errors', data: [], unit: 'count' },
      });

      await metricsApi.getDashboard({ include_trends: true });

      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('include_trends=true')
      );
    });

    it('should combine multiple query params', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({});

      await metricsApi.getDashboard({
        service_id: 'svc-1',
        team_id: 'team-1',
        time_range: '30d',
        include_trends: true,
      });

      const calledUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(calledUrl).toContain('service_id=svc-1');
      expect(calledUrl).toContain('team_id=team-1');
      expect(calledUrl).toContain('time_range=30d');
      expect(calledUrl).toContain('include_trends=true');
    });
  });

  // =============================================================================
  // getDORA Tests
  // =============================================================================

  describe('getDORA', () => {
    it('should fetch DORA metrics', async () => {
      const mockDORA = {
        deployment_frequency: 'daily',
        deployment_frequency_score: 4,
        lead_time_for_changes: '2 hours',
        lead_time_minutes: 120,
        change_failure_rate: 0.05,
        mean_time_to_recovery: '30 minutes',
        mttr_minutes: 30,
        overall_score: 'elite',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockDORA);

      const result = await metricsApi.getDORA();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/metrics/dora');
      expect(result).toEqual(mockDORA);
      expect(result.overall_score).toBe('elite');
    });
  });

  // =============================================================================
  // getHealth Tests
  // =============================================================================

  describe('getHealth', () => {
    it('should fetch overall health metrics', async () => {
      const mockHealth = {
        total_services: 25,
        healthy_services: 22,
        degraded_services: 2,
        unhealthy_services: 1,
        provisioning_services: 0,
        health_score: 0.88,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockHealth);

      const result = await metricsApi.getHealth();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/metrics/health');
      expect(result).toEqual(mockHealth);
    });

    it('should fetch health for specific service', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        total_services: 1,
        healthy_services: 1,
        health_score: 1.0,
      });

      await metricsApi.getHealth('service-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/metrics/health?service_id=service-123'
      );
    });
  });

  // =============================================================================
  // getDeployment Tests
  // =============================================================================

  describe('getDeployment', () => {
    it('should fetch overall deployment metrics', async () => {
      const mockDeployment = {
        total_deploys: 500,
        successful_deploys: 485,
        failed_deploys: 15,
        deploy_success_rate: 0.97,
        deploys_today: 12,
        deploys_this_week: 85,
        avg_deploys_per_day: 12.1,
        rollbacks_this_week: 3,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockDeployment);

      const result = await metricsApi.getDeployment();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/metrics/deployment');
      expect(result).toEqual(mockDeployment);
    });

    it('should fetch deployment metrics for specific service', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        total_deploys: 50,
        deploy_success_rate: 1.0,
      });

      await metricsApi.getDeployment('service-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/metrics/deployment?service_id=service-123'
      );
    });
  });

  // =============================================================================
  // Error Handling Tests
  // =============================================================================

  describe('error handling', () => {
    it('should propagate API errors from getDashboard', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 500 Internal Server Error')
      );

      await expect(metricsApi.getDashboard()).rejects.toThrow(
        'API Error: 500 Internal Server Error'
      );
    });

    it('should propagate API errors from getDORA', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error('API Error: 503 Service Unavailable')
      );

      await expect(metricsApi.getDORA()).rejects.toThrow(
        'API Error: 503 Service Unavailable'
      );
    });
  });
});
