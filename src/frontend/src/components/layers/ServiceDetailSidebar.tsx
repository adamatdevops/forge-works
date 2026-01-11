'use client';

/**
 * ServiceDetailSidebar Component
 * Displays detailed information about the selected service
 * Receives service_id from GlueBus
 */

import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Calendar,
  CheckCircle,
  Clock,
  ExternalLink,
  GitBranch,
  Layers,
  RefreshCw,
  Server,
  Users,
  X,
  XCircle,
} from 'lucide-react';
import { servicesApi } from '@/lib/api';
import { useSelectedService, useGluePublish } from '@/lib/store';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { Service } from '@/types';

function StatusIcon({ status }: { status: Service['status'] }) {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'degraded':
      return <Activity className="h-5 w-5 text-yellow-500" />;
    case 'unhealthy':
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <Server className="h-5 w-5 text-gray-400" />;
  }
}

function StatusBadge({ status }: { status: Service['status'] }) {
  const colors: Record<Service['status'], string> = {
    healthy: 'bg-green-500/10 text-green-500 border-green-500/20',
    degraded: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    unhealthy: 'bg-red-500/10 text-red-500 border-red-500/20',
    unknown: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  };

  return (
    <Badge variant="outline" className={cn('capitalize', colors[status])}>
      {status}
    </Badge>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
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

function ServiceDetailLoading() {
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    </div>
  );
}

export function ServiceDetailSidebar() {
  const selectedServiceId = useSelectedService();
  const publish = useGluePublish();

  const { data: service, isLoading, error } = useQuery({
    queryKey: ['service', selectedServiceId],
    queryFn: () => servicesApi.getById(selectedServiceId!),
    enabled: !!selectedServiceId,
  });

  const handleClose = () => {
    publish('service_id', null, 'services');
  };

  if (!selectedServiceId) {
    return null;
  }

  return (
    <div className="flex h-full w-80 flex-col border-l bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="font-semibold">Service Details</h2>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={handleClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      {isLoading ? (
        <ServiceDetailLoading />
      ) : error ? (
        <div className="flex items-center justify-center p-8">
          <div className="text-center text-red-500">
            <XCircle className="h-8 w-8 mx-auto mb-2" />
            <p className="text-sm">Failed to load service</p>
          </div>
        </div>
      ) : service ? (
        <div className="flex-1 overflow-auto">
          {/* Service Header */}
          <div className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <StatusIcon status={service.status} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold truncate">{service.name}</h3>
                <p className="text-sm text-muted-foreground font-mono">{service.id}</p>
              </div>
            </div>

            {service.description && (
              <p className="mt-3 text-sm text-muted-foreground">{service.description}</p>
            )}

            <div className="mt-4 flex items-center gap-2">
              <StatusBadge status={service.status} />
            </div>
          </div>

          <Separator />

          {/* Details */}
          <div className="p-4 space-y-4">
            <div>
              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                Information
              </h4>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Team:</span>
                  <span className="font-medium">{service.team_id}</span>
                </div>

                {service.template_id && (
                  <div className="flex items-center gap-3 text-sm">
                    <Layers className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Template:</span>
                    <span className="font-medium font-mono text-xs">{service.template_id}</span>
                  </div>
                )}

                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Created:</span>
                  <span className="font-medium">{formatDate(service.created_at)}</span>
                </div>

                <div className="flex items-center gap-3 text-sm">
                  <RefreshCw className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Updated:</span>
                  <span className="font-medium">{formatTimeAgo(service.updated_at)}</span>
                </div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Quick Actions */}
          <div className="p-4 space-y-2">
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Quick Actions
            </h4>
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <GitBranch className="h-4 w-4" />
              View Pipeline Runs
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <Activity className="h-4 w-4" />
              View Anomalies
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <ExternalLink className="h-4 w-4" />
              Open in Catalog
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default ServiceDetailSidebar;
