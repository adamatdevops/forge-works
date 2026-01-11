/**
 * Services API
 * ForgeWorks Backend Integration
 */

import { apiClient } from './client';
import type { Service } from '@/types';

interface ServicesResponse {
  items: Service[];
  total: number;
}

interface ServiceStats {
  total: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
}

export const servicesApi = {
  // GET /api/v1/services
  getAll: async (): Promise<Service[]> => {
    const response = await apiClient.get<ServicesResponse>('/api/v1/services');
    return response.items;
  },

  // GET /api/v1/services/:id
  getById: async (id: string): Promise<Service> => {
    return apiClient.get<Service>(`/api/v1/services/${id}`);
  },

  // POST /api/v1/services
  create: async (data: Partial<Service>): Promise<Service> => {
    return apiClient.post<Service>('/api/v1/services', data);
  },

  // GET /api/v1/services/stats
  getStats: async (): Promise<ServiceStats> => {
    return apiClient.get<ServiceStats>('/api/v1/services/stats');
  },
};

export default servicesApi;
