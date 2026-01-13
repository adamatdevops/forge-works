/**
 * Anomalies API
 * ForgeWorks Backend Integration
 */

import { apiClient } from './client';
import type { Anomaly } from '@/types';

interface AnomaliesResponse {
  items: Anomaly[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface AnomalyStats {
  total: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  active: number;
  acknowledged: number;
  unresolved: number;
}

interface AnomaliesQuery {
  service_id?: string;
  severity?: Anomaly['severity'];
  type?: string;
  active?: boolean;
  resolved?: boolean;
  page?: number;
  page_size?: number;
}

interface AcknowledgeData {
  acknowledged_by: string;
}

interface ResolveData {
  resolution_note?: string;
}

export const anomaliesApi = {
  // GET /api/v1/anomalies
  getAll: async (query?: AnomaliesQuery): Promise<Anomaly[]> => {
    const params = new URLSearchParams();
    if (query?.service_id) params.set('service_id', query.service_id);
    if (query?.severity) params.set('severity', query.severity);
    if (query?.type) params.set('type', query.type);
    if (query?.active !== undefined) params.set('active', String(query.active));
    if (query?.resolved !== undefined) params.set('resolved', String(query.resolved));
    if (query?.page) params.set('page', String(query.page));
    if (query?.page_size) params.set('page_size', String(query.page_size));

    const queryString = params.toString();
    const url = queryString ? `/api/v1/anomalies?${queryString}` : '/api/v1/anomalies';
    const response = await apiClient.get<AnomaliesResponse>(url);
    return response.items;
  },

  // GET /api/v1/anomalies with pagination
  getAllPaginated: async (query?: AnomaliesQuery): Promise<AnomaliesResponse> => {
    const params = new URLSearchParams();
    if (query?.service_id) params.set('service_id', query.service_id);
    if (query?.severity) params.set('severity', query.severity);
    if (query?.type) params.set('type', query.type);
    if (query?.active !== undefined) params.set('active', String(query.active));
    if (query?.resolved !== undefined) params.set('resolved', String(query.resolved));
    if (query?.page) params.set('page', String(query.page));
    if (query?.page_size) params.set('page_size', String(query.page_size));

    const queryString = params.toString();
    const url = queryString ? `/api/v1/anomalies?${queryString}` : '/api/v1/anomalies';
    return apiClient.get<AnomaliesResponse>(url);
  },

  // GET /api/v1/anomalies/:id
  getById: async (id: string): Promise<Anomaly> => {
    return apiClient.get<Anomaly>(`/api/v1/anomalies/${id}`);
  },

  // GET /api/v1/anomalies/stats
  getStats: async (): Promise<AnomalyStats> => {
    return apiClient.get<AnomalyStats>('/api/v1/anomalies/stats');
  },

  // POST /api/v1/anomalies/:id/acknowledge
  acknowledge: async (id: string, data: AcknowledgeData): Promise<Anomaly> => {
    return apiClient.post<Anomaly>(`/api/v1/anomalies/${id}/acknowledge`, data);
  },

  // POST /api/v1/anomalies/:id/resolve
  resolve: async (id: string, data?: ResolveData): Promise<Anomaly> => {
    return apiClient.post<Anomaly>(`/api/v1/anomalies/${id}/resolve`, data);
  },

  // DELETE /api/v1/anomalies/:id
  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/api/v1/anomalies/${id}`);
  },
};

export default anomaliesApi;
