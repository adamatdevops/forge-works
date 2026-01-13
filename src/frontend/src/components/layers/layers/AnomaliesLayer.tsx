'use client';

/**
 * AnomaliesLayer Component
 * Displays anomaly alerts and patterns
 * Links to services via GlueBus
 * Supports acknowledge and resolve actions
 */

import { memo, useCallback, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  XCircle,
  Info,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { anomaliesApi } from '@/lib/api';
import { useSelectedService, useGluePublish } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import type { Anomaly } from '@/types';

function SeverityBadge({ severity }: { severity: Anomaly['severity'] }) {
  const colors: Record<Anomaly['severity'], string> = {
    info: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    warning: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    critical: 'bg-red-700/10 text-red-700 border-red-700/20',
  };

  return (
    <Badge variant="outline" className={cn('capitalize', colors[severity])}>
      {severity}
    </Badge>
  );
}

function SeverityIcon({ severity }: { severity: Anomaly['severity'] }) {
  const className = 'h-4 w-4';
  switch (severity) {
    case 'critical':
      return <XCircle className={cn(className, 'text-red-700')} aria-hidden="true" />;
    case 'warning':
      return <AlertTriangle className={cn(className, 'text-yellow-500')} aria-hidden="true" />;
    case 'info':
      return <Info className={cn(className, 'text-blue-500')} aria-hidden="true" />;
    default:
      return <AlertTriangle className={cn(className, 'text-gray-500')} aria-hidden="true" />;
  }
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

function AnomaliesLoading() {
  return (
    <div className="p-4 space-y-3">
      {[...Array(3)].map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-5 w-16" />
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-3 w-24 mt-2" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface AnomalyCardProps {
  anomaly: Anomaly;
  onSelectService: () => void;
  onAcknowledge: () => void;
  onResolve: () => void;
  isAcknowledging: boolean;
  isResolving: boolean;
}

const AnomalyCard = memo(function AnomalyCard({
  anomaly,
  onSelectService,
  onAcknowledge,
  onResolve,
  isAcknowledging,
  isResolving,
}: AnomalyCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const borderColors: Record<Anomaly['severity'], string> = {
    critical: 'border-l-red-700',
    warning: 'border-l-yellow-500',
    info: 'border-l-blue-500',
  };

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setIsExpanded(!isExpanded);
    }
  }, [isExpanded]);

  return (
    <Card className={cn('border-l-4', borderColors[anomaly.severity])}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <SeverityIcon severity={anomaly.severity} />
              {anomaly.title}
            </CardTitle>
            <div className="flex items-center gap-2">
              <SeverityBadge severity={anomaly.severity} />
              {anomaly.is_acknowledged && (
                <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20 text-xs">
                  <Eye className="h-3 w-3 mr-1" aria-hidden="true" />
                  Ack
                </Badge>
              )}
            </div>
          </div>
          <CardDescription className="text-xs text-muted-foreground mt-1">
            {anomaly.type.replace(/_/g, ' ')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{anomaly.description}</p>

          {/* Detected vs Expected values */}
          {(anomaly.detected_value || anomaly.expected_value) && (
            <div className="flex gap-4 mt-2 text-xs">
              {anomaly.detected_value && (
                <span className="text-red-500">
                  Detected: <span className="font-medium">{anomaly.detected_value}</span>
                </span>
              )}
              {anomaly.expected_value && (
                <span className="text-green-500">
                  Expected: <span className="font-medium">{anomaly.expected_value}</span>
                </span>
              )}
            </div>
          )}

          {/* Suggestion */}
          {anomaly.suggestion && (
            <div className="mt-2 p-2 bg-muted/50 rounded-md">
              <p className="text-xs text-muted-foreground">
                <span className="font-medium">Suggestion:</span> {anomaly.suggestion}
              </p>
            </div>
          )}

          {/* Expandable details */}
          <CollapsibleContent className="mt-3 pt-3 border-t">
            <div className="space-y-2 text-xs text-muted-foreground">
              {anomaly.detection_rule && (
                <p><span className="font-medium">Detection Rule:</span> {anomaly.detection_rule}</p>
              )}
              {anomaly.acknowledged_by && (
                <p>
                  <span className="font-medium">Acknowledged by:</span> {anomaly.acknowledged_by}
                  {anomaly.acknowledged_at && ` (${formatTimeAgo(anomaly.acknowledged_at)})`}
                </p>
              )}
              {anomaly.resolution_note && (
                <p><span className="font-medium">Resolution:</span> {anomaly.resolution_note}</p>
              )}
              {Object.keys(anomaly.context || {}).length > 0 && (
                <details className="mt-2">
                  <summary className="cursor-pointer font-medium">Context Data</summary>
                  <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-auto">
                    {JSON.stringify(anomaly.context, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </CollapsibleContent>

          {/* Footer with actions */}
          <div className="flex items-center justify-between mt-3 pt-2 border-t">
            <div className="flex items-center gap-2">
              <Button
                variant="link"
                size="sm"
                className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
                onClick={onSelectService}
              >
                {anomaly.service?.name || `Service: ${anomaly.service_id.slice(0, 8)}...`}
              </Button>
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onKeyDown={handleKeyDown}
                  aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
                >
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <ChevronDown className="h-4 w-4" aria-hidden="true" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" aria-hidden="true" />
                {formatTimeAgo(anomaly.detected_at)}
              </span>
              {!anomaly.is_acknowledged && !anomaly.is_resolved && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={onAcknowledge}
                  disabled={isAcknowledging}
                >
                  <EyeOff className="h-3 w-3 mr-1" aria-hidden="true" />
                  {isAcknowledging ? 'Ack...' : 'Acknowledge'}
                </Button>
              )}
              {!anomaly.is_resolved && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-6 text-xs text-green-600 hover:text-green-700"
                  onClick={onResolve}
                  disabled={isResolving}
                >
                  <CheckCircle className="h-3 w-3 mr-1" aria-hidden="true" />
                  {isResolving ? 'Resolving...' : 'Resolve'}
                </Button>
              )}
            </div>
          </div>

          {anomaly.is_resolved && anomaly.resolved_at && (
            <div className="flex items-center gap-1 mt-2 text-xs text-green-500">
              <CheckCircle className="h-3 w-3" aria-hidden="true" />
              Resolved {formatTimeAgo(anomaly.resolved_at)}
            </div>
          )}
        </CardContent>
      </Collapsible>
    </Card>
  );
});

export function AnomaliesLayer() {
  const selectedServiceId = useSelectedService();
  const publish = useGluePublish();
  const queryClient = useQueryClient();
  const [showResolved, setShowResolved] = useState(false);

  const { data: anomalies, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['anomalies', selectedServiceId, showResolved],
    queryFn: () => anomaliesApi.getAll({
      service_id: selectedServiceId || undefined,
      resolved: showResolved ? undefined : false,
      active: showResolved ? undefined : true,
    }),
  });

  const { data: stats } = useQuery({
    queryKey: ['anomalies-stats'],
    queryFn: anomaliesApi.getStats,
    refetchInterval: 30000, // Refresh stats every 30s
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => anomaliesApi.acknowledge(id, { acknowledged_by: 'Current User' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      queryClient.invalidateQueries({ queryKey: ['anomalies-stats'] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (id: string) => anomaliesApi.resolve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      queryClient.invalidateQueries({ queryKey: ['anomalies-stats'] });
    },
  });

  const handleSelectService = useCallback((serviceId: string) => {
    publish('service_id', serviceId, 'anomalies');
  }, [publish]);

  // Group anomalies by severity
  const groupedStats = useMemo(() => {
    if (!anomalies) return { total: 0, critical: 0, warning: 0, info: 0 };
    return anomalies.reduce((acc, anomaly) => {
      acc.total++;
      acc[anomaly.severity]++;
      return acc;
    }, { total: 0, critical: 0, warning: 0, info: 0 } as Record<string, number>);
  }, [anomalies]);

  if (isLoading) {
    return <AnomaliesLoading />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8" role="alert" aria-live="assertive">
        <div className="text-center text-red-500">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm">Failed to load anomalies</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
        <div className="text-center text-muted-foreground">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500 opacity-50" aria-hidden="true" />
          <p className="font-medium">No anomalies detected</p>
          {selectedServiceId && (
            <p className="text-sm mt-1">for selected service</p>
          )}
          <p className="text-xs mt-2">All systems operating normally</p>
          {stats && stats.total > 0 && (
            <Button
              variant="link"
              size="sm"
              className="mt-2"
              onClick={() => setShowResolved(true)}
            >
              Show {stats.total} resolved anomalies
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <section className="p-4 space-y-4" aria-label="Anomalies detection">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm" role="status" aria-live="polite">
          <span className="font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-500" aria-hidden="true" />
            {groupedStats.total} anomalies
          </span>
          {groupedStats.critical > 0 && (
            <Badge variant="destructive" className="text-xs">
              {groupedStats.critical} critical
            </Badge>
          )}
          {groupedStats.warning > 0 && (
            <span className="text-yellow-500 text-xs">{groupedStats.warning} warning</span>
          )}
          {groupedStats.info > 0 && (
            <span className="text-blue-500 text-xs">{groupedStats.info} info</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className={cn('h-8 text-xs', showResolved && 'bg-muted')}
            onClick={() => setShowResolved(!showResolved)}
            aria-pressed={showResolved}
          >
            {showResolved ? 'Hide Resolved' : 'Show All'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => refetch()}
            disabled={isRefetching}
            aria-label={isRefetching ? 'Refreshing anomalies' : 'Refresh anomalies'}
          >
            <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} aria-hidden="true" />
          </Button>
        </div>
      </div>

      {selectedServiceId && (
        <p className="text-sm text-muted-foreground">
          Showing anomalies for: <span className="font-medium">{selectedServiceId}</span>
        </p>
      )}

      {/* Stats Bar */}
      {stats && (
        <div className="flex gap-4 text-xs text-muted-foreground bg-muted/50 rounded-md p-2">
          <span>Total: {stats.total}</span>
          <span className="text-green-500">Resolved: {stats.total - stats.unresolved}</span>
          <span className="text-blue-500">Acknowledged: {stats.acknowledged}</span>
          <span className="text-yellow-500">Active: {stats.active}</span>
        </div>
      )}

      {/* Anomaly Cards */}
      <div className="space-y-3" role="list" aria-label="Anomaly list">
        {anomalies.map((anomaly) => (
          <AnomalyCard
            key={anomaly.id}
            anomaly={anomaly}
            onSelectService={() => handleSelectService(anomaly.service_id)}
            onAcknowledge={() => acknowledgeMutation.mutate(anomaly.id)}
            onResolve={() => resolveMutation.mutate(anomaly.id)}
            isAcknowledging={acknowledgeMutation.isPending && acknowledgeMutation.variables === anomaly.id}
            isResolving={resolveMutation.isPending && resolveMutation.variables === anomaly.id}
          />
        ))}
      </div>
    </section>
  );
}

export default AnomaliesLayer;
