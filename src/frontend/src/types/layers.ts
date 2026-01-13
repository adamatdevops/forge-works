/**
 * Layers Architecture Type Definitions
 * ForgeWorks Frontend - Phase 3
 */

// Layer Types
export type LayerType =
  | 'services'
  | 'templates'
  | 'anomalies'
  | 'pipeline'
  | 'metrics'
  | 'kubernetes';

// Layer Definition
export interface Layer {
  id: string;
  name: string;
  type: LayerType;
  visible: boolean;
  collapsed: boolean;
  zIndex: number;
  apiEndpoint?: string;
  glueKeys: string[];
  subscriptions: string[];
}

// Glue Value Types
export type GlueKey =
  | 'service_id'
  | 'template_id'
  | 'commit_sha'
  | 'release_version'
  | 'timestamp'
  | 'anomaly_id';

export interface GlueValue {
  key: GlueKey;
  value: string | number | null;
  source: LayerType;
  timestamp: number;
}

// Glue Bus Interface
export interface GlueBus {
  values: Map<GlueKey, GlueValue>;
  subscribe: (key: GlueKey, callback: (value: GlueValue) => void) => () => void;
  publish: (key: GlueKey, value: GlueValue) => void;
  get: (key: GlueKey) => GlueValue | undefined;
  clear: (key?: GlueKey) => void;
}

// Layer State
export interface LayerState {
  layers: Layer[];
  activeLayerId: string | null;
  setLayerVisibility: (id: string, visible: boolean) => void;
  setLayerOrder: (layers: Layer[]) => void;
  toggleLayer: (id: string) => void;
  setActiveLayer: (id: string | null) => void;
}

// API Response Types (from FastAPI backend)
export interface Service {
  id: string;
  name: string;
  description?: string;
  team_id: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  template_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: string;
  name: string;
  description?: string;
  type: 'api' | 'batch' | 'stream' | 'ml';
  language: 'python' | 'go' | 'typescript';
  popularity: number;
  created_at: string;
}

export interface TemplateRecommendation {
  template: Template;
  score: number;
  reason: string;
}

export interface RecommendationResponse {
  recommendations: TemplateRecommendation[];
  warnings: string[];
  override_allowed: boolean;
}

export interface Anomaly {
  id: string;
  service_id: string;
  severity: 'info' | 'warning' | 'critical';
  type: string;
  title: string;
  description: string;
  suggestion?: string;
  detected_value?: string;
  expected_value?: string;
  detection_rule?: string;
  context: Record<string, unknown>;
  is_active: boolean;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  is_resolved: boolean;
  resolved_at?: string;
  resolution_note?: string;
  detected_at: string;
  created_at: string;
  updated_at: string;
  service?: {
    id: string;
    name: string;
    slug: string;
    status: string;
  };
}

export interface PipelineRun {
  id: string;
  service_id?: string;
  commit_sha: string;
  branch: string;
  message?: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  started_at: string;
  completed_at?: string;
  author?: string;
  duration_seconds?: number;
}

// Kubernetes Types (Phase 4.2)
export interface ResourceMetrics {
  cpu_cores: number;
  cpu_percent: number;
  memory_bytes: number;
  memory_mb: number;
  memory_percent: number;
}

export interface KubernetesContainer {
  name: string;
  image: string;
  state: 'waiting' | 'running' | 'terminated';
  ready: boolean;
  restart_count: number;
  started_at?: string;
  reason?: string;
}

export interface KubernetesPod {
  name: string;
  namespace: string;
  phase: 'Pending' | 'Running' | 'Succeeded' | 'Failed' | 'Unknown';
  node_name?: string;
  ip?: string;
  containers: KubernetesContainer[];
  created_at: string;
  labels: Record<string, string>;
  metrics?: ResourceMetrics;
  ready: boolean;
  restart_count: number;
}

export interface KubernetesDeployment {
  name: string;
  namespace: string;
  replicas: number;
  ready_replicas: number;
  available_replicas: number;
  unavailable_replicas: number;
  updated_replicas: number;
  strategy: string;
  created_at: string;
  labels: Record<string, string>;
  conditions: Array<{
    type: string;
    status: string;
    reason?: string;
    message?: string;
  }>;
  healthy: boolean;
  progress_percent: number;
}

export interface KubernetesNamespace {
  name: string;
  phase: string;
  created_at: string;
  labels: Record<string, string>;
  pod_count: number;
  deployment_count: number;
}

export interface KubernetesNode {
  name: string;
  status: string;
  roles: string[];
  kubernetes_version: string;
  os_image: string;
  container_runtime: string;
  created_at: string;
  capacity: {
    cpu?: string;
    memory?: string;
    pods?: string;
  };
  allocatable: {
    cpu?: string;
    memory?: string;
    pods?: string;
  };
  conditions: Array<{
    type: string;
    status: string;
    reason?: string;
    message?: string;
  }>;
  metrics?: ResourceMetrics;
}

export interface KubernetesClusterInfo {
  version: string;
  platform: string;
  node_count: number;
  namespace_count: number;
  pod_count: number;
  deployment_count: number;
  adapter_mode: string;
}

export interface KubernetesStats {
  nodes: {
    total: number;
    healthy: number;
    unhealthy: number;
  };
  namespaces: {
    total: number;
  };
  deployments: {
    total: number;
    healthy: number;
    degraded: number;
  };
  pods: {
    total: number;
    running: number;
    pending: number;
    failed: number;
    total_restarts: number;
  };
  cluster_version: string;
  adapter_mode: string;
}
