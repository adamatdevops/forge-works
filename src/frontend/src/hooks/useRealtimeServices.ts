'use client';

/**
 * useRealtimeServices Hook
 * Integrates WebSocket events with TanStack Query for real-time service updates
 *
 * Usage:
 *   const { services, isLoading, isConnected } = useRealtimeServices();
 *
 * This hook:
 * - Fetches services via React Query
 * - Listens for WebSocket events
 * - Automatically invalidates cache on service changes
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import type { WebSocketEvent } from '@/types/websocket';

export function useRealtimeServices() {
  const queryClient = useQueryClient();

  // Handle WebSocket events
  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      // Only handle service events
      if (!event.type.startsWith('service.')) return;

      // Invalidate services query to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['services'] });

      // For specific events, we could also optimistically update the cache
      // but invalidation is simpler and ensures consistency
      console.log('[RealtimeServices] Event received:', event.type, event.data);
    },
    [queryClient]
  );

  const { status, isConnected, lastEvent, subscribe, unsubscribe } = useWebSocket({
    channels: ['services'],
    onEvent: handleEvent,
  });

  return {
    wsStatus: status,
    isConnected,
    lastEvent,
    subscribe,
    unsubscribe,
  };
}

/**
 * useRealtimeAnomalies Hook
 * Integrates WebSocket events with TanStack Query for real-time anomaly updates
 */
export function useRealtimeAnomalies() {
  const queryClient = useQueryClient();

  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      if (!event.type.startsWith('anomaly.')) return;
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      console.log('[RealtimeAnomalies] Event received:', event.type, event.data);
    },
    [queryClient]
  );

  const { status, isConnected, lastEvent, subscribe, unsubscribe } = useWebSocket({
    channels: ['anomalies'],
    onEvent: handleEvent,
  });

  return {
    wsStatus: status,
    isConnected,
    lastEvent,
    subscribe,
    unsubscribe,
  };
}

/**
 * useRealtimePipelines Hook
 * Integrates WebSocket events with TanStack Query for real-time pipeline updates
 */
export function useRealtimePipelines() {
  const queryClient = useQueryClient();

  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      if (!event.type.startsWith('pipeline.')) return;
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      console.log('[RealtimePipelines] Event received:', event.type, event.data);
    },
    [queryClient]
  );

  const { status, isConnected, lastEvent, subscribe, unsubscribe } = useWebSocket({
    channels: ['pipelines'],
    onEvent: handleEvent,
  });

  return {
    wsStatus: status,
    isConnected,
    lastEvent,
    subscribe,
    unsubscribe,
  };
}

/**
 * useRealtimeAll Hook
 * Subscribes to all channels for the main dashboard
 */
export function useRealtimeAll() {
  const queryClient = useQueryClient();

  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      // Route events to appropriate query invalidations
      if (event.type.startsWith('service.')) {
        queryClient.invalidateQueries({ queryKey: ['services'] });
      } else if (event.type.startsWith('anomaly.')) {
        queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      } else if (event.type.startsWith('pipeline.')) {
        queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      } else if (event.type.startsWith('template.')) {
        queryClient.invalidateQueries({ queryKey: ['templates'] });
      } else if (event.type.startsWith('metrics.')) {
        queryClient.invalidateQueries({ queryKey: ['metrics'] });
      }

      console.log('[RealtimeAll] Event received:', event.type, event.channel);
    },
    [queryClient]
  );

  const { status, isConnected, lastEvent, reconnectAttempts } = useWebSocket({
    channels: ['all'],
    onEvent: handleEvent,
  });

  return {
    wsStatus: status,
    isConnected,
    lastEvent,
    reconnectAttempts,
  };
}

/**
 * useRealtimeKubernetes Hook
 * Integrates WebSocket events with TanStack Query for real-time Kubernetes updates
 */
export function useRealtimeKubernetes() {
  const queryClient = useQueryClient();

  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      // Only handle kubernetes events
      if (!event.type.startsWith('pod.') && !event.type.startsWith('deployment.')) return;

      // Invalidate all kubernetes-related queries
      queryClient.invalidateQueries({ queryKey: ['kubernetes'] });
      queryClient.invalidateQueries({ queryKey: ['kubernetes-stats'] });
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
      queryClient.invalidateQueries({ queryKey: ['pods'] });
      queryClient.invalidateQueries({ queryKey: ['nodes'] });

      console.log('[RealtimeKubernetes] Event received:', event.type, event.data);
    },
    [queryClient]
  );

  const { status, isConnected, lastEvent, subscribe, unsubscribe } = useWebSocket({
    channels: ['kubernetes'],
    onEvent: handleEvent,
  });

  return {
    wsStatus: status,
    isConnected,
    lastEvent,
    subscribe,
    unsubscribe,
  };
}

export default useRealtimeServices;
