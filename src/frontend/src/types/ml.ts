/**
 * ML Types for Template Recommendation
 * ForgeWorks Frontend
 */

// Enums matching backend
export type WorkloadType = 'api' | 'worker' | 'cron' | 'ml-pipeline' | 'frontend' | 'batch';
export type ProgrammingLanguage = 'python' | 'javascript' | 'typescript' | 'go' | 'java' | 'rust';
export type DatabaseType = 'postgresql' | 'mongodb' | 'redis' | 'mysql' | 'none';
export type TemplateType =
  | 'microservice-python'
  | 'microservice-node'
  | 'worker-service'
  | 'ml-pipeline'
  | 'frontend-app';

// Input for recommendation
export interface WorkloadFeatures {
  language: ProgrammingLanguage;
  framework?: string | null;
  workload_type: WorkloadType;
  service_name?: string | null;
  needs_database: boolean;
  database_type: DatabaseType;
  needs_queue: boolean;
  needs_cache: boolean;
  needs_gpu: boolean;
  expected_rps: number;
  expected_memory_mb: number;
  team_size: number;
  compliance_required: boolean;
}

// Single recommendation
export interface TemplateRecommendation {
  template: TemplateType;
  confidence: number;
  reasons: string[];
}

// Full recommendation response
export interface RecommendationResponse {
  primary: TemplateRecommendation;
  alternatives: TemplateRecommendation[];
  input_summary: Record<string, unknown>;
}

// Template info
export interface TemplateInfo {
  id: TemplateType;
  name: string;
  description: string;
  best_for: string[];
  includes: string[];
}

// Templates list response
export interface TemplatesListResponse {
  templates: TemplateInfo[];
  count: number;
}

// Feedback
export interface RecommendationFeedback {
  recommendation_id?: string | null;
  selected_template: TemplateType;
  was_primary: boolean;
  feedback_text?: string | null;
}

// Default values for form
export const DEFAULT_WORKLOAD_FEATURES: WorkloadFeatures = {
  language: 'python',
  framework: null,
  workload_type: 'api',
  service_name: null,
  needs_database: true,
  database_type: 'postgresql',
  needs_queue: false,
  needs_cache: false,
  needs_gpu: false,
  expected_rps: 100,
  expected_memory_mb: 512,
  team_size: 5,
  compliance_required: false,
};

// Display names for enums
export const LANGUAGE_LABELS: Record<ProgrammingLanguage, string> = {
  python: 'Python',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  go: 'Go',
  java: 'Java',
  rust: 'Rust',
};

export const WORKLOAD_LABELS: Record<WorkloadType, string> = {
  api: 'REST API',
  worker: 'Background Worker',
  cron: 'Scheduled Job',
  'ml-pipeline': 'ML Pipeline',
  frontend: 'Frontend App',
  batch: 'Batch Processing',
};

export const DATABASE_LABELS: Record<DatabaseType, string> = {
  none: 'None',
  postgresql: 'PostgreSQL',
  mongodb: 'MongoDB',
  redis: 'Redis',
  mysql: 'MySQL',
};

export const TEMPLATE_LABELS: Record<TemplateType, string> = {
  'microservice-python': 'Python Microservice',
  'microservice-node': 'Node.js Microservice',
  'worker-service': 'Worker Service',
  'ml-pipeline': 'ML Pipeline',
  'frontend-app': 'Frontend App',
};
