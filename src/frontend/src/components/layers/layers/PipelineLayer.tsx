'use client';

/**
 * PipelineLayer Component
 * Displays CI/CD pipeline status from GitHub adapter
 * Links to services via GlueBus
 */

import { useQuery } from '@tanstack/react-query';
import {
  GitBranch,
  GitCommit,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  RefreshCw,
  User,
  Timer,
} from 'lucide-react';
import { pipelinesApi } from '@/lib/api';
import { useSelectedService, useGluePublish } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { PipelineRun } from '@/types';

function StatusIcon({ status }: { status: PipelineRun['status'] }) {
  switch (status) {
    case 'success':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    case 'running':
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    case 'pending':
      return <Clock className="h-4 w-4 text-yellow-500" />;
  }
}

function StatusBadge({ status }: { status: PipelineRun['status'] }) {
  const colors: Record<PipelineRun['status'], string> = {
    pending: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    running: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    success: 'bg-green-500/10 text-green-500 border-green-500/20',
    failed: 'bg-red-500/10 text-red-500 border-red-500/20',
  };

  return (
    <Badge variant="outline" className={cn('capitalize', colors[status])}>
      {status}
    </Badge>
  );
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

function PipelinesLoading() {
  return (
    <div className="p-4 space-y-3">
      {[...Array(4)].map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-5 w-16" />
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full" />
            <div className="flex gap-4 mt-2">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-3 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface PipelineCardProps {
  pipeline: PipelineRun;
  onSelectService: () => void;
  onPublishCommit: () => void;
}

function PipelineCard({ pipeline, onSelectService, onPublishCommit }: PipelineCardProps) {
  const borderColors: Record<PipelineRun['status'], string> = {
    success: 'border-l-green-500',
    failed: 'border-l-red-500',
    running: 'border-l-blue-500',
    pending: 'border-l-yellow-500',
  };

  return (
    <Card className={cn('border-l-4', borderColors[pipeline.status])}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <StatusIcon status={pipeline.status} />
            <button
              className="font-mono text-sm hover:underline"
              onClick={onPublishCommit}
            >
              {pipeline.commit_sha.slice(0, 7)}
            </button>
          </CardTitle>
          <StatusBadge status={pipeline.status} />
        </div>
      </CardHeader>
      <CardContent>
        {pipeline.message && (
          <p className="text-sm truncate mb-2">{pipeline.message}</p>
        )}
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span className="flex items-center gap-1">
            <GitBranch className="h-3 w-3" />
            {pipeline.branch}
          </span>
          {pipeline.service_id && (
            <Button
              variant="link"
              size="sm"
              className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
              onClick={onSelectService}
            >
              <GitCommit className="h-3 w-3 mr-1" />
              {pipeline.service_id}
            </Button>
          )}
          {pipeline.author && (
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {pipeline.author}
            </span>
          )}
          <span>{formatTimeAgo(pipeline.started_at)}</span>
          {pipeline.duration_seconds && (
            <span className="flex items-center gap-1">
              <Timer className="h-3 w-3" />
              {formatDuration(pipeline.duration_seconds)}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function PipelineLayer() {
  const selectedServiceId = useSelectedService();
  const publish = useGluePublish();

  const { data: pipelines, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['pipelines', selectedServiceId],
    queryFn: () => pipelinesApi.getAll({
      service_id: selectedServiceId || undefined,
      limit: 20,
    }),
  });

  const handleSelectService = (serviceId: string) => {
    publish('service_id', serviceId, 'pipeline');
  };

  const handlePublishCommit = (commitSha: string) => {
    publish('commit_sha', commitSha, 'pipeline');
  };

  if (isLoading) {
    return <PipelinesLoading />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center text-red-500">
          <XCircle className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">Failed to load pipelines</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!pipelines || pipelines.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center text-muted-foreground">
          <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="font-medium">No pipeline runs found</p>
          {selectedServiceId && (
            <p className="text-sm mt-1">for selected service</p>
          )}
        </div>
      </div>
    );
  }

  // Calculate stats
  const stats = {
    total: pipelines.length,
    success: pipelines.filter((p) => p.status === 'success').length,
    failed: pipelines.filter((p) => p.status === 'failed').length,
    running: pipelines.filter((p) => p.status === 'running').length,
  };

  const successRate = stats.total > 0
    ? Math.round((stats.success / (stats.success + stats.failed)) * 100) || 0
    : 0;

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm">
          <span className="font-medium flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            {stats.total} runs
          </span>
          {stats.running > 0 && (
            <span className="text-blue-500 flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              {stats.running} running
            </span>
          )}
          {stats.failed > 0 && (
            <span className="text-red-500">{stats.failed} failed</span>
          )}
          <span className="text-muted-foreground">{successRate}% success</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => refetch()}
          disabled={isRefetching}
        >
          <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} />
        </Button>
      </div>

      {selectedServiceId && (
        <p className="text-sm text-muted-foreground">
          Showing pipelines for: <span className="font-medium">{selectedServiceId}</span>
        </p>
      )}

      {/* Pipeline Cards */}
      <div className="space-y-3">
        {pipelines.map((pipeline) => (
          <PipelineCard
            key={pipeline.id}
            pipeline={pipeline}
            onSelectService={() => pipeline.service_id && handleSelectService(pipeline.service_id)}
            onPublishCommit={() => handlePublishCommit(pipeline.commit_sha)}
          />
        ))}
      </div>
    </div>
  );
}

export default PipelineLayer;
