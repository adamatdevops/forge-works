'use client';

/**
 * LayerRenderer Component
 * Conditionally renders layers based on visibility
 * Handles lazy loading and layer composition
 */

import { Suspense, lazy, type ComponentType } from 'react';
import { useLayerStore } from '@/lib/store';
import { Skeleton } from '@/components/ui/skeleton';
import type { Layer, LayerType } from '@/types';

// Lazy load layer components for performance
const ServicesLayer = lazy(() => import('./layers/ServicesLayer'));
const TemplatesLayer = lazy(() => import('./layers/TemplatesLayer'));
const AnomaliesLayer = lazy(() => import('./layers/AnomaliesLayer'));
const PipelineLayer = lazy(() => import('./layers/PipelineLayer'));

// Layer component mapping
const layerComponents: Record<LayerType, ComponentType> = {
  services: ServicesLayer,
  templates: TemplatesLayer,
  anomalies: AnomaliesLayer,
  pipeline: PipelineLayer,
  metrics: () => <MetricsPlaceholder />, // Placeholder for now
};

function LayerSkeleton() {
  return (
    <div className="p-4 space-y-3">
      <Skeleton className="h-8 w-48" />
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    </div>
  );
}

function MetricsPlaceholder() {
  return (
    <div className="p-4 text-center text-muted-foreground">
      <p>Metrics Layer - Coming Soon</p>
    </div>
  );
}

interface LayerContainerProps {
  layer: Layer;
  children: React.ReactNode;
}

function LayerContainer({ layer, children }: LayerContainerProps) {
  return (
    <section
      className="layer-container border-b last:border-b-0"
      data-layer-id={layer.id}
      data-layer-type={layer.type}
      style={{ zIndex: layer.zIndex }}
    >
      {/* Layer Header */}
      <div className="flex items-center gap-2 bg-muted/30 px-4 py-2 border-b">
        <LayerBadge type={layer.type} />
        <h3 className="text-sm font-medium">{layer.name}</h3>
      </div>

      {/* Layer Content */}
      <div className="layer-content">
        {children}
      </div>
    </section>
  );
}

function LayerBadge({ type }: { type: LayerType }) {
  const colors: Record<LayerType, string> = {
    services: 'bg-green-500',
    templates: 'bg-purple-500',
    anomalies: 'bg-red-500',
    pipeline: 'bg-blue-500',
    metrics: 'bg-yellow-500',
  };

  return (
    <div className={`h-2 w-2 rounded-full ${colors[type]}`} />
  );
}

export function LayerRenderer() {
  const layers = useLayerStore((state) => state.layers);
  const visibleLayers = layers.filter((layer) => layer.visible);

  if (visibleLayers.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <p className="text-lg font-medium">No layers visible</p>
          <p className="text-sm">Toggle layers in the panel to see content</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto">
      {visibleLayers.map((layer) => {
        const LayerComponent = layerComponents[layer.type];

        return (
          <LayerContainer key={layer.id} layer={layer}>
            <Suspense fallback={<LayerSkeleton />}>
              <LayerComponent />
            </Suspense>
          </LayerContainer>
        );
      })}
    </div>
  );
}

export default LayerRenderer;
