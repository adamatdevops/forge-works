/**
 * Pipelines API
 * ForgeWorks Backend Integration (GitHub Adapter)
 */

import { apiClient } from './client';
import type { PipelineRun } from '@/types';

interface PipelinesResponse {
  items: PipelineRun[];
  total: number;
}

interface PipelineStats {
  total: number;
  by_status: {
    pending: number;
    running: number;
    success: number;
    failed: number;
  };
  success_rate: number;
}

interface PipelinesQuery {
  service_id?: string;
  status?: PipelineRun['status'];
  limit?: number;
}

export const pipelinesApi = {
  // GET /api/v1/pipelines
  getAll: async (query?: PipelinesQuery): Promise<PipelineRun[]> => {
    const params = new URLSearchParams();
    if (query?.service_id) params.set('service_id', query.service_id);
    if (query?.status) params.set('status', query.status);
    if (query?.limit) params.set('limit', String(query.limit));

    const queryString = params.toString();
    const url = queryString ? `/api/v1/pipelines?${queryString}` : '/api/v1/pipelines';
    const response = await apiClient.get<PipelinesResponse>(url);
    return response.items;
  },

  // GET /api/v1/pipelines/:id
  getById: async (id: string): Promise<PipelineRun> => {
    return apiClient.get<PipelineRun>(`/api/v1/pipelines/${id}`);
  },

  // GET /api/v1/pipelines/stats
  getStats: async (): Promise<PipelineStats> => {
    return apiClient.get<PipelineStats>('/api/v1/pipelines/stats');
  },

  // POST /api/v1/pipelines/:id/retry
  retry: async (id: string): Promise<PipelineRun> => {
    return apiClient.post<PipelineRun>(`/api/v1/pipelines/${id}/retry`);
  },
};

export default pipelinesApi;
