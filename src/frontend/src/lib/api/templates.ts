/**
 * Templates API
 * ForgeWorks Backend Integration
 */

import { apiClient } from './client';
import type { Template, RecommendationResponse } from '@/types';

interface TemplatesResponse {
  items: Template[];
  total: number;
}

interface RecommendRequest {
  workload_type: 'api' | 'batch' | 'stream' | 'ml';
  language: 'python' | 'go' | 'typescript';
  requirements?: string[];
  team_id?: string;
}

export const templatesApi = {
  // GET /api/v1/templates
  getAll: async (): Promise<Template[]> => {
    const response = await apiClient.get<TemplatesResponse>('/api/v1/templates');
    return response.items;
  },

  // GET /api/v1/templates/:id
  getById: async (id: string): Promise<Template> => {
    return apiClient.get<Template>(`/api/v1/templates/${id}`);
  },

  // POST /api/v1/templates/recommend
  getRecommendations: async (request: RecommendRequest): Promise<RecommendationResponse> => {
    return apiClient.post<RecommendationResponse>('/api/v1/templates/recommend', request);
  },
};

export default templatesApi;
