'use client';

/**
 * KubernetesLayer Component
 * Displays Kubernetes cluster status, deployments, pods, and nodes
 * Supports real-time updates via WebSocket
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  CheckCircle,
  Cloud,
  Container,
  Cpu,
  HardDrive,
  Layers,
  Radio,
  RefreshCw,
  Server,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { kubernetesApi } from '@/lib/api';
import { useRealtimeKubernetes } from '@/hooks';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import type { KubernetesDeployment, KubernetesPod, KubernetesNode } from '@/types';

type ViewMode = 'overview' | 'deployments' | 'pods' | 'nodes';

function StatusBadge({ healthy, total }: { healthy: number; total: number }) {
  const isHealthy = healthy === total;
  const isDegraded = healthy > 0 && healthy < total;

  return (
    <Badge
      variant="outline"
      className={cn(
        isHealthy && 'bg-green-500/10 text-green-500 border-green-500/20',
        isDegraded && 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
        !isHealthy && !isDegraded && 'bg-red-500/10 text-red-500 border-red-500/20'
      )}
    >
      {healthy}/{total}
    </Badge>
  );
}

function DeploymentCard({ deployment }: { deployment: KubernetesDeployment }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const borderColor = deployment.healthy
    ? 'border-l-green-500'
    : deployment.ready_replicas > 0
      ? 'border-l-yellow-500'
      : 'border-l-red-500';

  return (
    <Card className={cn('border-l-4', borderColor)}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="h-4 w-4" aria-hidden="true" />
              {deployment.name}
            </CardTitle>
            <StatusBadge healthy={deployment.ready_replicas} total={deployment.replicas} />
          </div>
          <CardDescription className="text-xs">
            {deployment.namespace}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Progress</span>
              <span>{deployment.progress_percent}%</span>
            </div>
            <Progress value={deployment.progress_percent} className="h-1.5" />
          </div>

          <CollapsibleContent className="mt-3 pt-3 border-t">
            <div className="space-y-2 text-xs text-muted-foreground">
              <p><span className="font-medium">Strategy:</span> {deployment.strategy}</p>
              <p><span className="font-medium">Available:</span> {deployment.available_replicas}</p>
              <p><span className="font-medium">Updated:</span> {deployment.updated_replicas}</p>
              {deployment.unavailable_replicas > 0 && (
                <p className="text-red-500">
                  <span className="font-medium">Unavailable:</span> {deployment.unavailable_replicas}
                </p>
              )}
            </div>
          </CollapsibleContent>

          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-muted-foreground">
              {Object.keys(deployment.labels).length} labels
            </span>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
          </div>
        </CardContent>
      </Collapsible>
    </Card>
  );
}

function PodCard({ pod }: { pod: KubernetesPod }) {
  const phaseColors: Record<string, string> = {
    Running: 'text-green-500',
    Pending: 'text-yellow-500',
    Succeeded: 'text-blue-500',
    Failed: 'text-red-500',
    Unknown: 'text-gray-500',
  };

  const borderColors: Record<string, string> = {
    Running: 'border-l-green-500',
    Pending: 'border-l-yellow-500',
    Succeeded: 'border-l-blue-500',
    Failed: 'border-l-red-500',
    Unknown: 'border-l-gray-500',
  };

  return (
    <Card className={cn('border-l-4', borderColors[pod.phase])}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2 truncate">
            <Container className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <span className="truncate">{pod.name}</span>
          </CardTitle>
          <Badge
            variant="outline"
            className={cn('capitalize text-xs', phaseColors[pod.phase])}
          >
            {pod.phase}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1 text-xs text-muted-foreground">
          <p><span className="font-medium">Namespace:</span> {pod.namespace}</p>
          {pod.node_name && <p><span className="font-medium">Node:</span> {pod.node_name}</p>}
          {pod.ip && <p><span className="font-medium">IP:</span> {pod.ip}</p>}
          <p>
            <span className="font-medium">Containers:</span> {pod.containers.length}
            {pod.restart_count > 0 && (
              <span className="text-yellow-500 ml-2">({pod.restart_count} restarts)</span>
            )}
          </p>
          {pod.metrics && (
            <div className="flex gap-4 mt-2 pt-2 border-t">
              <span className="flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {pod.metrics.cpu_percent.toFixed(1)}%
              </span>
              <span className="flex items-center gap-1">
                <HardDrive className="h-3 w-3" />
                {pod.metrics.memory_mb.toFixed(0)}MB
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function NodeCard({ node }: { node: KubernetesNode }) {
  const isReady = node.status === 'Ready';

  return (
    <Card className={cn('border-l-4', isReady ? 'border-l-green-500' : 'border-l-red-500')}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Server className="h-4 w-4" aria-hidden="true" />
            {node.name}
          </CardTitle>
          <Badge
            variant="outline"
            className={cn(
              isReady
                ? 'bg-green-500/10 text-green-500 border-green-500/20'
                : 'bg-red-500/10 text-red-500 border-red-500/20'
            )}
          >
            {node.status}
          </Badge>
        </div>
        <CardDescription className="text-xs">
          {node.roles.join(', ')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-1 text-xs text-muted-foreground">
          <p><span className="font-medium">Version:</span> {node.kubernetes_version}</p>
          <p><span className="font-medium">OS:</span> {node.os_image}</p>
          <p><span className="font-medium">Runtime:</span> {node.container_runtime}</p>
          <div className="flex gap-4 mt-2 pt-2 border-t">
            <span>CPU: {node.capacity.cpu}</span>
            <span>Memory: {node.capacity.memory}</span>
            <span>Pods: {node.capacity.pods}</span>
          </div>
          {node.metrics && (
            <div className="flex gap-4 mt-2">
              <span className="flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {node.metrics.cpu_percent.toFixed(1)}%
              </span>
              <span className="flex items-center gap-1">
                <HardDrive className="h-3 w-3" />
                {node.metrics.memory_percent.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function KubernetesLoading() {
  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

function StatsCard({
  title,
  icon: Icon,
  healthy,
  total,
  extra,
}: {
  title: string;
  icon: React.ElementType;
  healthy: number;
  total: number;
  extra?: React.ReactNode;
}) {
  const isHealthy = healthy === total;
  const percent = total > 0 ? (healthy / total) * 100 : 0;

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">{title}</span>
          </div>
          {isHealthy ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          )}
        </div>
        <div className="mt-2">
          <div className="text-2xl font-bold">{healthy}/{total}</div>
          <Progress value={percent} className="h-1 mt-2" />
        </div>
        {extra && <div className="mt-2 text-xs text-muted-foreground">{extra}</div>}
      </CardContent>
    </Card>
  );
}

export function KubernetesLayer() {
  const [viewMode, setViewMode] = useState<ViewMode>('overview');

  // Real-time updates via WebSocket
  const { isConnected } = useRealtimeKubernetes();

  // Fetch stats
  const { data: stats, isLoading: statsLoading, refetch, isRefetching } = useQuery({
    queryKey: ['kubernetes-stats'],
    queryFn: kubernetesApi.getStats,
  });

  // Fetch deployments
  const { data: deployments } = useQuery({
    queryKey: ['deployments'],
    queryFn: () => kubernetesApi.getDeployments(),
    enabled: viewMode === 'overview' || viewMode === 'deployments',
  });

  // Fetch pods
  const { data: pods } = useQuery({
    queryKey: ['pods'],
    queryFn: () => kubernetesApi.getPods(),
    enabled: viewMode === 'overview' || viewMode === 'pods',
  });

  // Fetch nodes
  const { data: nodes } = useQuery({
    queryKey: ['nodes'],
    queryFn: kubernetesApi.getNodes,
    enabled: viewMode === 'overview' || viewMode === 'nodes',
  });

  if (statsLoading) {
    return <KubernetesLoading />;
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center p-8" role="alert">
        <div className="text-center text-red-500">
          <XCircle className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">Failed to load Kubernetes data</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <section className="p-4 space-y-4" aria-label="Kubernetes cluster">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Cloud className="h-5 w-5 text-blue-500" />
            <h2 className="font-medium">Kubernetes Cluster</h2>
          </div>
          <Badge variant="secondary" className="text-xs">
            v{stats.cluster_version}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {stats.adapter_mode}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          {/* Real-time indicator */}
          <span
            className={cn(
              'flex items-center gap-1 text-xs',
              isConnected ? 'text-green-500' : 'text-gray-400'
            )}
            title={isConnected ? 'Real-time updates active' : 'Real-time updates disconnected'}
          >
            <Radio className="h-3 w-3" aria-hidden="true" />
            <span>{isConnected ? 'Live' : 'Offline'}</span>
          </span>
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
      </div>

      {/* View Mode Tabs */}
      <div className="flex gap-2">
        {(['overview', 'deployments', 'pods', 'nodes'] as ViewMode[]).map((mode) => (
          <Button
            key={mode}
            variant={viewMode === mode ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode(mode)}
            className="capitalize"
          >
            {mode}
          </Button>
        ))}
      </div>

      {/* Stats Overview */}
      {viewMode === 'overview' && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatsCard
              title="Nodes"
              icon={Server}
              healthy={stats.nodes.healthy}
              total={stats.nodes.total}
            />
            <StatsCard
              title="Deployments"
              icon={Layers}
              healthy={stats.deployments.healthy}
              total={stats.deployments.total}
            />
            <StatsCard
              title="Pods"
              icon={Container}
              healthy={stats.pods.running}
              total={stats.pods.total}
              extra={
                <>
                  {stats.pods.pending > 0 && (
                    <span className="text-yellow-500">{stats.pods.pending} pending</span>
                  )}
                  {stats.pods.failed > 0 && (
                    <span className="text-red-500 ml-2">{stats.pods.failed} failed</span>
                  )}
                </>
              }
            />
            <StatsCard
              title="Namespaces"
              icon={Box}
              healthy={stats.namespaces.total}
              total={stats.namespaces.total}
            />
          </div>

          {/* Quick View of Recent Issues */}
          {deployments && deployments.filter((d) => !d.healthy).length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-yellow-500">Degraded Deployments</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {deployments.filter((d) => !d.healthy).map((dep) => (
                  <DeploymentCard key={`${dep.namespace}/${dep.name}`} deployment={dep} />
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Deployments View */}
      {viewMode === 'deployments' && deployments && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {deployments.map((dep) => (
            <DeploymentCard key={`${dep.namespace}/${dep.name}`} deployment={dep} />
          ))}
        </div>
      )}

      {/* Pods View */}
      {viewMode === 'pods' && pods && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pods.map((pod) => (
            <PodCard key={`${pod.namespace}/${pod.name}`} pod={pod} />
          ))}
        </div>
      )}

      {/* Nodes View */}
      {viewMode === 'nodes' && nodes && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {nodes.map((node) => (
            <NodeCard key={node.name} node={node} />
          ))}
        </div>
      )}
    </section>
  );
}

export default KubernetesLayer;
