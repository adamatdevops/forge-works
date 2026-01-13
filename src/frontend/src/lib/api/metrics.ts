/**
 * Metrics API
 * ForgeWorks Backend Integration
 */

import { apiClient } from './client';

export interface DeploymentMetrics {
  total_deploys: number;
  successful_deploys: number;
  failed_deploys: number;
  deploy_success_rate: number;
  deploys_today: number;
  deploys_this_week: number;
  avg_deploys_per_day: number;
  rollbacks_this_week: number;
}

export interface PipelineMetrics {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  pending_runs: number;
  running_now: number;
  success_rate: number;
  avg_duration_seconds: number;
  p95_duration_seconds: number;
}

export interface ServiceHealthMetrics {
  total_services: number;
  healthy_services: number;
  degraded_services: number;
  unhealthy_services: number;
  provisioning_services: number;
  health_score: number;
}

export interface DORAMetrics {
  deployment_frequency: string;
  deployment_frequency_score: number;
  lead_time_for_changes: string;
  lead_time_minutes: number;
  change_failure_rate: number;
  mean_time_to_recovery: string;
  mttr_minutes: number;
  overall_score: string;
}

export interface TemplateMetrics {
  total_templates: number;
  active_templates: number;
  most_popular: string | null;
  adoption_rate: number;
  services_without_template: number;
}

export interface AnomalyMetrics {
  total_anomalies: number;
  active_anomalies: number;
  critical_anomalies: number;
  warning_anomalies: number;
  resolved_today: number;
  avg_resolution_time_hours: number;
}

export interface TeamMetrics {
  total_teams: number;
  active_teams: number;
  services_per_team_avg: number;
  most_active_team: string | null;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface TimeSeries {
  name: string;
  data: TimeSeriesPoint[];
  unit: string;
}

export interface MetricsDashboard {
  deployment: DeploymentMetrics;
  pipeline: PipelineMetrics;
  service_health: ServiceHealthMetrics;
  dora: DORAMetrics;
  template: TemplateMetrics;
  anomaly: AnomalyMetrics;
  team: TeamMetrics;
  deploy_trend?: TimeSeries;
  error_trend?: TimeSeries;
  generated_at: string;
  data_freshness: string;
}

interface MetricsQuery {
  service_id?: string;
  team_id?: string;
  time_range?: string;
  include_trends?: boolean;
}

export const metricsApi = {
  // GET /api/v1/metrics
  getDashboard: async (query?: MetricsQuery): Promise<MetricsDashboard> => {
    const params = new URLSearchParams();
    if (query?.service_id) params.set('service_id', query.service_id);
    if (query?.team_id) params.set('team_id', query.team_id);
    if (query?.time_range) params.set('time_range', query.time_range);
    if (query?.include_trends) params.set('include_trends', 'true');

    const queryString = params.toString();
    const url = queryString ? `/api/v1/metrics?${queryString}` : '/api/v1/metrics';
    return apiClient.get<MetricsDashboard>(url);
  },

  // GET /api/v1/metrics/dora
  getDORA: async (): Promise<DORAMetrics> => {
    return apiClient.get<DORAMetrics>('/api/v1/metrics/dora');
  },

  // GET /api/v1/metrics/health
  getHealth: async (serviceId?: string): Promise<ServiceHealthMetrics> => {
    const url = serviceId
      ? `/api/v1/metrics/health?service_id=${serviceId}`
      : '/api/v1/metrics/health';
    return apiClient.get<ServiceHealthMetrics>(url);
  },

  // GET /api/v1/metrics/deployment
  getDeployment: async (serviceId?: string): Promise<DeploymentMetrics> => {
    const url = serviceId
      ? `/api/v1/metrics/deployment?service_id=${serviceId}`
      : '/api/v1/metrics/deployment';
    return apiClient.get<DeploymentMetrics>(url);
  },
};

export default metricsApi;
