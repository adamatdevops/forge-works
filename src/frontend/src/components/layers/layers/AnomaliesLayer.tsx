'use client';

/**
 * AnomaliesLayer Component
 * Displays anomaly alerts and patterns
 * Links to services via GlueBus
 */

import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle, Clock, RefreshCw, XCircle } from 'lucide-react';
import { anomaliesApi } from '@/lib/api';
import { useSelectedService, useGluePublish } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { Anomaly } from '@/types';

function SeverityBadge({ severity }: { severity: Anomaly['severity'] }) {
  const colors: Record<Anomaly['severity'], string> = {
    low: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    medium: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    high: 'bg-red-500/10 text-red-500 border-red-500/20',
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
      return <XCircle className={cn(className, 'text-red-700')} />;
    case 'high':
      return <AlertTriangle className={cn(className, 'text-red-500')} />;
    case 'medium':
      return <AlertTriangle className={cn(className, 'text-orange-500')} />;
    case 'low':
      return <Clock className={cn(className, 'text-yellow-500')} />;
    default:
      return <AlertTriangle className={cn(className, 'text-gray-500')} />;
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
}

function AnomalyCard({ anomaly, onSelectService }: AnomalyCardProps) {
  const borderColors: Record<Anomaly['severity'], string> = {
    critical: 'border-l-red-700',
    high: 'border-l-red-500',
    medium: 'border-l-orange-500',
    low: 'border-l-yellow-500',
  };

  return (
    <Card className={cn('border-l-4', borderColors[anomaly.severity])}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <SeverityIcon severity={anomaly.severity} />
            {anomaly.type}
          </CardTitle>
          <SeverityBadge severity={anomaly.severity} />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{anomaly.message}</p>
        <div className="flex items-center justify-between mt-3">
          <Button
            variant="link"
            size="sm"
            className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
            onClick={onSelectService}
          >
            Service: {anomaly.service_id}
          </Button>
          <span className="text-xs text-muted-foreground">
            {formatTimeAgo(anomaly.detected_at)}
          </span>
        </div>
        {anomaly.resolved_at && (
          <div className="flex items-center gap-1 mt-2 text-xs text-green-500">
            <CheckCircle className="h-3 w-3" />
            Resolved {formatTimeAgo(anomaly.resolved_at)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function AnomaliesLayer() {
  const selectedServiceId = useSelectedService();
  const publish = useGluePublish();

  const { data: anomalies, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['anomalies', selectedServiceId],
    queryFn: () => anomaliesApi.getAll({
      service_id: selectedServiceId || undefined,
      resolved: false,
    }),
  });

  const handleSelectService = (serviceId: string) => {
    publish('service_id', serviceId, 'anomalies');
  };

  if (isLoading) {
    return <AnomaliesLoading />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center text-red-500">
          <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
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
      <div className="flex items-center justify-center p-8">
        <div className="text-center text-muted-foreground">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500 opacity-50" />
          <p className="font-medium">No anomalies detected</p>
          {selectedServiceId && (
            <p className="text-sm mt-1">for selected service</p>
          )}
          <p className="text-xs mt-2">All systems operating normally</p>
        </div>
      </div>
    );
  }

  // Group anomalies by severity
  const bySeverity = anomalies.reduce((acc, anomaly) => {
    if (!acc[anomaly.severity]) acc[anomaly.severity] = 0;
    acc[anomaly.severity]++;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm">
          <span className="font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            {anomalies.length} anomalies
          </span>
          {bySeverity.critical && (
            <Badge variant="destructive" className="text-xs">
              {bySeverity.critical} critical
            </Badge>
          )}
          {bySeverity.high && (
            <span className="text-red-500 text-xs">{bySeverity.high} high</span>
          )}
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
          Showing anomalies for: <span className="font-medium">{selectedServiceId}</span>
        </p>
      )}

      {/* Anomaly Cards */}
      <div className="space-y-3">
        {anomalies.map((anomaly) => (
          <AnomalyCard
            key={anomaly.id}
            anomaly={anomaly}
            onSelectService={() => handleSelectService(anomaly.service_id)}
          />
        ))}
      </div>
    </div>
  );
}

export default AnomaliesLayer;
