/**
 * ML API Functions
 * ForgeWorks Frontend
 */

import type {
  RecommendationFeedback,
  RecommendationResponse,
  TemplateInfo,
  TemplatesListResponse,
  WorkloadFeatures,
} from '@/types/ml';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get template recommendation based on workload features
 */
export async function getRecommendation(
  features: WorkloadFeatures
): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE}/api/v1/ml/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(features),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to get recommendation');
  }

  return response.json();
}

/**
 * List all available templates
 */
export async function listTemplates(): Promise<TemplatesListResponse> {
  const response = await fetch(`${API_BASE}/api/v1/ml/templates`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }

  return response.json();
}

/**
 * Get details for a specific template
 */
export async function getTemplate(templateId: string): Promise<TemplateInfo> {
  const response = await fetch(`${API_BASE}/api/v1/ml/templates/${templateId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Template '${templateId}' not found`);
    }
    throw new Error('Failed to fetch template');
  }

  return response.json();
}

/**
 * Submit feedback on a recommendation
 */
export async function submitFeedback(
  feedback: RecommendationFeedback
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/v1/ml/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedback),
  });

  if (!response.ok) {
    throw new Error('Failed to submit feedback');
  }

  return response.json();
}

/**
 * Check ML service health
 */
export async function checkMLHealth(): Promise<{
  status: string;
  model_loaded: boolean;
  mode: 'ml' | 'rule-based';
}> {
  const response = await fetch(`${API_BASE}/api/v1/ml/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('ML service unavailable');
  }

  return response.json();
}
