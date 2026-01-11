'use client';

/**
 * LayerPanel Component
 * Figma-like layer panel with visibility toggles and drag-to-reorder
 * Core component of the Layers Architecture
 */

import { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Eye, EyeOff, GripVertical, Layers } from 'lucide-react';
import { useLayerStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { Layer } from '@/types';

interface SortableLayerItemProps {
  layer: Layer;
  isActive: boolean;
  onToggleVisibility: () => void;
  onSelect: () => void;
}

function SortableLayerItem({ layer, isActive, onToggleVisibility, onSelect }: SortableLayerItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: layer.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'group flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors',
        'hover:bg-accent/50',
        isActive && 'bg-accent',
        !layer.visible && 'opacity-50',
        isDragging && 'opacity-70 bg-accent shadow-lg z-50'
      )}
      onClick={onSelect}
    >
      {/* Drag Handle */}
      <button
        className="touch-none"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-4 w-4 text-muted-foreground opacity-50 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing" />
      </button>

      {/* Visibility Toggle */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={(e) => {
                e.stopPropagation();
                onToggleVisibility();
              }}
            >
              {layer.visible ? (
                <Eye className="h-4 w-4 text-foreground" />
              ) : (
                <EyeOff className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            {layer.visible ? 'Hide layer' : 'Show layer'}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Layer Icon */}
      <LayerIcon type={layer.type} />

      {/* Layer Name */}
      <span className="flex-1 text-sm font-medium truncate">{layer.name}</span>

      {/* Glue Indicator */}
      {layer.glueKeys.length > 0 && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <div className="h-2 w-2 rounded-full bg-blue-500" />
            </TooltipTrigger>
            <TooltipContent side="right">
              <p className="text-xs">Publishes: {layer.glueKeys.join(', ')}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
}

function LayerIcon({ type }: { type: Layer['type'] }) {
  const iconClass = 'h-4 w-4';

  switch (type) {
    case 'services':
      return (
        <div className={cn(iconClass, 'rounded bg-green-500/20 p-0.5')}>
          <div className="h-full w-full rounded-sm bg-green-500" />
        </div>
      );
    case 'templates':
      return (
        <div className={cn(iconClass, 'rounded bg-purple-500/20 p-0.5')}>
          <div className="h-full w-full rounded-sm bg-purple-500" />
        </div>
      );
    case 'anomalies':
      return (
        <div className={cn(iconClass, 'rounded bg-red-500/20 p-0.5')}>
          <div className="h-full w-full rounded-sm bg-red-500" />
        </div>
      );
    case 'pipeline':
      return (
        <div className={cn(iconClass, 'rounded bg-blue-500/20 p-0.5')}>
          <div className="h-full w-full rounded-sm bg-blue-500" />
        </div>
      );
    case 'metrics':
      return (
        <div className={cn(iconClass, 'rounded bg-yellow-500/20 p-0.5')}>
          <div className="h-full w-full rounded-sm bg-yellow-500" />
        </div>
      );
    default:
      return (
        <div className={cn(iconClass, 'rounded bg-gray-500/20 p-0.5')}>
          <div className="h-full w-full rounded-sm bg-gray-500" />
        </div>
      );
  }
}

export function LayerPanel() {
  const { layers, activeLayerId, toggleLayer, setActiveLayer, setLayerOrder } = useLayerStore();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Require 8px movement before activating drag
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = layers.findIndex((layer) => layer.id === active.id);
      const newIndex = layers.findIndex((layer) => layer.id === over.id);

      const newLayers = arrayMove(layers, oldIndex, newIndex).map((layer, index) => ({
        ...layer,
        zIndex: layers.length - index, // Update zIndex based on new position
      }));

      setLayerOrder(newLayers);
    }
  };

  const visibleCount = layers.filter((l) => l.visible).length;

  return (
    <div className="flex h-full w-64 flex-col border-r bg-background">
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <Layers className="h-5 w-5" />
        <h2 className="font-semibold">Layers</h2>
        <span className="ml-auto text-xs text-muted-foreground">
          {visibleCount}/{layers.length}
        </span>
      </div>

      {/* Layer List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={layers.map((l) => l.id)}
              strategy={verticalListSortingStrategy}
            >
              {layers.map((layer) => (
                <SortableLayerItem
                  key={layer.id}
                  layer={layer}
                  isActive={activeLayerId === layer.id}
                  onToggleVisibility={() => toggleLayer(layer.id)}
                  onSelect={() => setActiveLayer(layer.id)}
                />
              ))}
            </SortableContext>
          </DndContext>
        </div>
      </ScrollArea>

      {/* Footer */}
      <Separator />
      <div className="p-3">
        <p className="text-xs text-muted-foreground text-center">
          Drag to reorder • Toggle visibility
        </p>
      </div>
    </div>
  );
}

export default LayerPanel;
