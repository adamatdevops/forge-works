/**
 * Anomalies API
 * ForgeWorks Backend Integration
 */

import { apiClient } from './client';
import type { Anomaly } from '@/types';

interface AnomaliesResponse {
  items: Anomaly[];
  total: number;
}

interface AnomalyStats {
  total: number;
  by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  unresolved: number;
}

interface AnomaliesQuery {
  service_id?: string;
  severity?: Anomaly['severity'];
  resolved?: boolean;
  limit?: number;
}

export const anomaliesApi = {
  // GET /api/v1/anomalies
  getAll: async (query?: AnomaliesQuery): Promise<Anomaly[]> => {
    const params = new URLSearchParams();
    if (query?.service_id) params.set('service_id', query.service_id);
    if (query?.severity) params.set('severity', query.severity);
    if (query?.resolved !== undefined) params.set('resolved', String(query.resolved));
    if (query?.limit) params.set('limit', String(query.limit));

    const queryString = params.toString();
    const url = queryString ? `/api/v1/anomalies?${queryString}` : '/api/v1/anomalies';
    const response = await apiClient.get<AnomaliesResponse>(url);
    return response.items;
  },

  // GET /api/v1/anomalies/:id
  getById: async (id: string): Promise<Anomaly> => {
    return apiClient.get<Anomaly>(`/api/v1/anomalies/${id}`);
  },

  // GET /api/v1/anomalies/stats
  getStats: async (): Promise<AnomalyStats> => {
    return apiClient.get<AnomalyStats>('/api/v1/anomalies/stats');
  },

  // POST /api/v1/anomalies/:id/resolve
  resolve: async (id: string): Promise<Anomaly> => {
    return apiClient.post<Anomaly>(`/api/v1/anomalies/${id}/resolve`);
  },
};

export default anomaliesApi;
