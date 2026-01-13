/**
 * Kubernetes API
 * ForgeWorks Backend Integration - Phase 4.2
 */

import { apiClient } from './client';
import type {
  KubernetesClusterInfo,
  KubernetesDeployment,
  KubernetesNamespace,
  KubernetesNode,
  KubernetesPod,
  KubernetesStats,
} from '@/types';

interface PodLogsResponse {
  namespace: string;
  pod: string;
  container: string | null;
  lines: string[];
  line_count: number;
}

export const kubernetesApi = {
  // GET /api/v1/kubernetes/cluster
  getClusterInfo: async (): Promise<KubernetesClusterInfo> => {
    return apiClient.get<KubernetesClusterInfo>('/api/v1/kubernetes/cluster');
  },

  // GET /api/v1/kubernetes/stats
  getStats: async (): Promise<KubernetesStats> => {
    return apiClient.get<KubernetesStats>('/api/v1/kubernetes/stats');
  },

  // GET /api/v1/kubernetes/namespaces
  getNamespaces: async (): Promise<KubernetesNamespace[]> => {
    return apiClient.get<KubernetesNamespace[]>('/api/v1/kubernetes/namespaces');
  },

  // GET /api/v1/kubernetes/nodes
  getNodes: async (): Promise<KubernetesNode[]> => {
    return apiClient.get<KubernetesNode[]>('/api/v1/kubernetes/nodes');
  },

  // GET /api/v1/kubernetes/deployments
  getDeployments: async (params?: {
    namespace?: string;
    label_selector?: string;
  }): Promise<KubernetesDeployment[]> => {
    const searchParams = new URLSearchParams();
    if (params?.namespace) searchParams.set('namespace', params.namespace);
    if (params?.label_selector) searchParams.set('label_selector', params.label_selector);

    const query = searchParams.toString();
    const url = query ? `/api/v1/kubernetes/deployments?${query}` : '/api/v1/kubernetes/deployments';
    return apiClient.get<KubernetesDeployment[]>(url);
  },

  // GET /api/v1/kubernetes/deployments/:namespace/:name
  getDeployment: async (namespace: string, name: string): Promise<KubernetesDeployment> => {
    return apiClient.get<KubernetesDeployment>(`/api/v1/kubernetes/deployments/${namespace}/${name}`);
  },

  // GET /api/v1/kubernetes/pods
  getPods: async (params?: {
    namespace?: string;
    label_selector?: string;
  }): Promise<KubernetesPod[]> => {
    const searchParams = new URLSearchParams();
    if (params?.namespace) searchParams.set('namespace', params.namespace);
    if (params?.label_selector) searchParams.set('label_selector', params.label_selector);

    const query = searchParams.toString();
    const url = query ? `/api/v1/kubernetes/pods?${query}` : '/api/v1/kubernetes/pods';
    return apiClient.get<KubernetesPod[]>(url);
  },

  // GET /api/v1/kubernetes/pods/:namespace/:name/logs
  getPodLogs: async (
    namespace: string,
    name: string,
    params?: { container?: string; tail_lines?: number }
  ): Promise<PodLogsResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.container) searchParams.set('container', params.container);
    if (params?.tail_lines) searchParams.set('tail_lines', params.tail_lines.toString());

    const query = searchParams.toString();
    const url = query
      ? `/api/v1/kubernetes/pods/${namespace}/${name}/logs?${query}`
      : `/api/v1/kubernetes/pods/${namespace}/${name}/logs`;
    return apiClient.get<PodLogsResponse>(url);
  },
};

export default kubernetesApi;
