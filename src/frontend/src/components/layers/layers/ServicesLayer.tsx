'use client';

/**
 * ServicesLayer Component
 * Displays the Service Catalog from ForgeWorks API
 * Publishes selected service_id to GlueBus
 */

import { useQuery } from '@tanstack/react-query';
import { Activity, AlertCircle, CheckCircle, HelpCircle, XCircle } from 'lucide-react';
import { servicesApi } from '@/lib/api';
import { useGluePublish, useSelectedService } from '@/lib/store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { Service } from '@/types';

function ServiceStatusIcon({ status }: { status: Service['status'] }) {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'degraded':
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    case 'unhealthy':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <HelpCircle className="h-4 w-4 text-gray-500" />;
  }
}

function ServiceStatusBadge({ status }: { status: Service['status'] }) {
  const variants: Record<Service['status'], string> = {
    healthy: 'bg-green-500/10 text-green-500 border-green-500/20',
    degraded: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    unhealthy: 'bg-red-500/10 text-red-500 border-red-500/20',
    unknown: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  };

  return (
    <Badge variant="outline" className={cn('capitalize', variants[status])}>
      {status}
    </Badge>
  );
}

interface ServiceCardProps {
  service: Service;
  isSelected: boolean;
  onSelect: () => void;
}

function ServiceCard({ service, isSelected, onSelect }: ServiceCardProps) {
  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        isSelected && 'ring-2 ring-primary'
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <ServiceStatusIcon status={service.status} />
            <CardTitle className="text-base">{service.name}</CardTitle>
          </div>
          <ServiceStatusBadge status={service.status} />
        </div>
        {service.description && (
          <CardDescription className="line-clamp-2">
            {service.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>Team: {service.team_id}</span>
          {service.template_id && (
            <span>Template: {service.template_id}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ServicesLoading() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {[...Array(6)].map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-4 rounded-full" />
              <Skeleton className="h-5 w-32" />
            </div>
            <Skeleton className="h-4 w-full mt-2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-3 w-24" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ServicesError({ error }: { error: Error }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium">Failed to load services</h3>
        <p className="text-sm text-muted-foreground mt-1">{error.message}</p>
      </div>
    </div>
  );
}

function ServicesEmpty() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium">No services found</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Create your first service to get started
        </p>
      </div>
    </div>
  );
}

export function ServicesLayer() {
  const publish = useGluePublish();
  const selectedServiceId = useSelectedService();

  const { data: services, isLoading, error } = useQuery({
    queryKey: ['services'],
    queryFn: servicesApi.getAll,
  });

  const handleSelectService = (service: Service) => {
    publish('service_id', service.id, 'services');
  };

  if (isLoading) {
    return <ServicesLoading />;
  }

  if (error) {
    return <ServicesError error={error as Error} />;
  }

  if (!services || services.length === 0) {
    return <ServicesEmpty />;
  }

  return (
    <div className="p-4">
      {/* Stats Summary */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        <span className="font-medium">{services.length} services</span>
        <span className="text-green-500">
          {services.filter((s) => s.status === 'healthy').length} healthy
        </span>
        <span className="text-yellow-500">
          {services.filter((s) => s.status === 'degraded').length} degraded
        </span>
        <span className="text-red-500">
          {services.filter((s) => s.status === 'unhealthy').length} unhealthy
        </span>
      </div>

      {/* Service Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((service) => (
          <ServiceCard
            key={service.id}
            service={service}
            isSelected={selectedServiceId === service.id}
            onSelect={() => handleSelectService(service)}
          />
        ))}
      </div>
    </div>
  );
}

export default ServicesLayer;
