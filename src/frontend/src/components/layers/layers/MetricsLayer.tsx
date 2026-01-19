'use client';

/**
 * MetricsLayer Component
 * Displays platform engineering metrics dashboard
 * Including DORA metrics, deployment stats, service health
 */

import { memo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  BarChart3,
  CheckCircle,
  Clock,
  GitBranch,
  Heart,
  Layers,
  RefreshCw,
  Rocket,
  Target,
  TrendingUp,
  Users,
  XCircle,
  Zap,
} from 'lucide-react';
import { metricsApi } from '@/lib/api';
import { useSelectedService } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { MetricsDashboard, DORAMetrics } from '@/lib/api/metrics';

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ReactNode;
  trend?: { value: number; positive: boolean };
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

const MetricCard = memo(function MetricCard({
  title,
  value,
  description,
  icon,
  trend,
  variant = 'default',
}: MetricCardProps) {
  const variants = {
    default: 'bg-card',
    success: 'bg-green-500/5 border-green-500/20',
    warning: 'bg-yellow-500/5 border-yellow-500/20',
    danger: 'bg-red-500/5 border-red-500/20',
  };

  return (
    <Card className={cn(variants[variant])}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <div className="text-2xl font-bold">{value}</div>
          {trend && (
            <span
              className={cn(
                'flex items-center text-xs',
                trend.positive ? 'text-green-500' : 'text-red-500'
              )}
            >
              {trend.positive ? (
                <ArrowUp className="h-3 w-3" aria-hidden="true" />
              ) : (
                <ArrowDown className="h-3 w-3" aria-hidden="true" />
              )}
              {trend.value}%
            </span>
          )}
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
});

// DORA Score Badge
function DORAScoreBadge({ score }: { score: string }) {
  const colors: Record<string, string> = {
    Elite: 'bg-green-500/10 text-green-500 border-green-500/20',
    High: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    Medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    Low: 'bg-red-500/10 text-red-500 border-red-500/20',
    Unknown: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  };

  return (
    <Badge variant="outline" className={cn('text-xs', colors[score] || colors.Unknown)}>
      {score}
    </Badge>
  );
}

// DORA Metrics Panel
interface DORAPanelProps {
  dora: DORAMetrics;
}

const DORAPanel = memo(function DORAPanel({ dora }: DORAPanelProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-4 w-4" aria-hidden="true" />
              DORA Metrics
            </CardTitle>
            <CardDescription>DevOps Research and Assessment</CardDescription>
          </div>
          <DORAScoreBadge score={dora.overall_score} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {/* Deployment Frequency */}
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Deploy Frequency</span>
              <span className="font-medium">{dora.deployment_frequency}</span>
            </div>
            <Progress value={dora.deployment_frequency_score} className="h-1.5 mt-1" />
          </div>

          {/* Lead Time */}
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Lead Time</span>
              <span className="font-medium">{dora.lead_time_for_changes}</span>
            </div>
            <Progress value={Math.min((60 / dora.lead_time_minutes) * 100, 100)} className="h-1.5 mt-1" />
          </div>

          {/* Change Failure Rate */}
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Change Failure Rate</span>
              <span className={cn(
                'font-medium',
                dora.change_failure_rate > 15 ? 'text-red-500' : 'text-green-500'
              )}>
                {dora.change_failure_rate}%
              </span>
            </div>
            <Progress
              value={100 - dora.change_failure_rate}
              className="h-1.5 mt-1"
            />
          </div>

          {/* MTTR */}
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">MTTR</span>
              <span className="font-medium">{dora.mean_time_to_recovery}</span>
            </div>
            <Progress value={Math.min((60 / dora.mttr_minutes) * 100, 100)} className="h-1.5 mt-1" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

// Service Health Panel
interface HealthPanelProps {
  health: MetricsDashboard['service_health'];
}

const HealthPanel = memo(function HealthPanel({ health }: HealthPanelProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Heart className="h-4 w-4" aria-hidden="true" />
          Service Health
        </CardTitle>
        <CardDescription>
          {health.total_services} total services
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Health Score */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Health Score</span>
            <span className={cn(
              'text-lg font-bold',
              health.health_score >= 80 ? 'text-green-500' :
              health.health_score >= 50 ? 'text-yellow-500' : 'text-red-500'
            )}>
              {health.health_score}%
            </span>
          </div>
          <Progress value={health.health_score} className="h-2" />

          {/* Breakdown */}
          <div className="flex items-center justify-between text-xs pt-2">
            <span className="flex items-center gap-1 text-green-500">
              <CheckCircle className="h-3 w-3" aria-hidden="true" />
              {health.healthy_services} healthy
            </span>
            <span className="flex items-center gap-1 text-yellow-500">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              {health.degraded_services} degraded
            </span>
            <span className="flex items-center gap-1 text-red-500">
              <XCircle className="h-3 w-3" aria-hidden="true" />
              {health.unhealthy_services} unhealthy
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

// Pipeline Stats Panel
interface PipelinePanelProps {
  pipeline: MetricsDashboard['pipeline'];
}

const PipelinePanel = memo(function PipelinePanel({ pipeline }: PipelinePanelProps) {
  const avgMinutes = Math.floor(pipeline.avg_duration_seconds / 60);
  const avgSeconds = pipeline.avg_duration_seconds % 60;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <GitBranch className="h-4 w-4" aria-hidden="true" />
          Pipeline
        </CardTitle>
        <CardDescription>{pipeline.total_runs} total runs</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Success Rate */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Success Rate</span>
          <span className={cn(
            'font-medium',
            pipeline.success_rate >= 90 ? 'text-green-500' :
            pipeline.success_rate >= 70 ? 'text-yellow-500' : 'text-red-500'
          )}>
            {pipeline.success_rate}%
          </span>
        </div>
        <Progress value={pipeline.success_rate} className="h-1.5" />

        {/* Stats */}
        <div className="flex items-center justify-between text-xs pt-2">
          <span className="text-green-500">{pipeline.successful_runs} passed</span>
          <span className="text-red-500">{pipeline.failed_runs} failed</span>
          <span className="text-blue-500">{pipeline.running_now} running</span>
        </div>

        {/* Duration */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1">
          <Clock className="h-3 w-3" aria-hidden="true" />
          Avg: {avgMinutes}m {avgSeconds}s
        </div>
      </CardContent>
    </Card>
  );
});

// Loading State
function MetricsLoading() {
  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-20" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-3 w-24 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
          <CardContent><Skeleton className="h-24" /></CardContent>
        </Card>
        <Card>
          <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
          <CardContent><Skeleton className="h-24" /></CardContent>
        </Card>
      </div>
    </div>
  );
}

// Main Component
export function MetricsLayer() {
  const selectedServiceId = useSelectedService();

  const { data: metrics, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['metrics', selectedServiceId],
    queryFn: () => metricsApi.getDashboard({
      service_id: selectedServiceId || undefined,
      include_trends: true,
    }),
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) {
    return <MetricsLoading />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8" role="alert" aria-live="assertive">
        <div className="text-center text-red-500">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm">Failed to load metrics</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
        <div className="text-center text-muted-foreground">
          <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" aria-hidden="true" />
          <p className="font-medium">No metrics available</p>
        </div>
      </div>
    );
  }

  return (
    <section className="p-4 space-y-4" aria-label="Platform metrics dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          <h2 className="text-lg font-semibold">Platform Metrics</h2>
          {selectedServiceId && (
            <Badge variant="outline" className="text-xs">
              Filtered by service
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Updated: {new Date(metrics.generated_at).toLocaleTimeString()}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => refetch()}
            disabled={isRefetching}
            aria-label={isRefetching ? 'Refreshing metrics' : 'Refresh metrics'}
          >
            <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} aria-hidden="true" />
          </Button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Deploys Today"
          value={metrics.deployment.deploys_today}
          description={`${metrics.deployment.avg_deploys_per_day}/day avg`}
          icon={<Rocket className="h-4 w-4" />}
          variant={metrics.deployment.deploys_today > 0 ? 'success' : 'default'}
        />
        <MetricCard
          title="Deploy Success"
          value={`${metrics.deployment.deploy_success_rate}%`}
          description={`${metrics.deployment.rollbacks_this_week} rollbacks this week`}
          icon={<TrendingUp className="h-4 w-4" />}
          variant={metrics.deployment.deploy_success_rate >= 90 ? 'success' :
                   metrics.deployment.deploy_success_rate >= 70 ? 'warning' : 'danger'}
        />
        <MetricCard
          title="Active Anomalies"
          value={metrics.anomaly.active_anomalies}
          description={`${metrics.anomaly.critical_anomalies} critical`}
          icon={<AlertTriangle className="h-4 w-4" />}
          variant={metrics.anomaly.critical_anomalies > 0 ? 'danger' :
                   metrics.anomaly.active_anomalies > 0 ? 'warning' : 'success'}
        />
        <MetricCard
          title="Template Adoption"
          value={`${metrics.template.adoption_rate}%`}
          description={`${metrics.template.services_without_template} without templates`}
          icon={<Layers className="h-4 w-4" />}
          variant={metrics.template.adoption_rate >= 80 ? 'success' : 'warning'}
        />
      </div>

      {/* Detail Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <DORAPanel dora={metrics.dora} />
        <HealthPanel health={metrics.service_health} />
        <PipelinePanel pipeline={metrics.pipeline} />
      </div>

      {/* Team & Template Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Active Teams"
          value={metrics.team.active_teams}
          description={`${metrics.team.services_per_team_avg} services/team`}
          icon={<Users className="h-4 w-4" />}
        />
        <MetricCard
          title="Templates"
          value={metrics.template.total_templates}
          description={`${metrics.template.active_templates} in use`}
          icon={<Layers className="h-4 w-4" />}
        />
        <MetricCard
          title="Pipeline Runs"
          value={metrics.pipeline.running_now}
          description={`${metrics.pipeline.pending_runs} pending`}
          icon={<Activity className="h-4 w-4" />}
          variant={metrics.pipeline.running_now > 0 ? 'success' : 'default'}
        />
        <MetricCard
          title="Resolved Today"
          value={metrics.anomaly.resolved_today}
          description={`${metrics.anomaly.avg_resolution_time_hours}h avg resolution`}
          icon={<Zap className="h-4 w-4" />}
        />
      </div>
    </section>
  );
}

export default MetricsLayer;
