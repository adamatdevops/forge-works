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
  | 'metrics';

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
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  message: string;
  detected_at: string;
  resolved_at?: string;
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
