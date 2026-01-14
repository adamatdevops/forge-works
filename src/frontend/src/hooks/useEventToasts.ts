'use client';

/**
 * useEventToasts Hook
 * Maps WebSocket events to toast notifications
 *
 * Usage:
 *   // In your dashboard or provider
 *   useEventToasts();
 *
 * This hook automatically shows toast notifications for:
 * - Anomaly detection (warning)
 * - Pipeline failures (error)
 * - Service status changes (info/warning)
 * - Deployment events (info)
 */

import { useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { toast } from '@/components/ui/toast';
import type { WebSocketEvent } from '@/types/websocket';

interface EventToastConfig {
  enabled: boolean;
  soundEnabled: boolean;
  showAnomalies: boolean;
  showPipelines: boolean;
  showServices: boolean;
  showKubernetes: boolean;
}

const DEFAULT_CONFIG: EventToastConfig = {
  enabled: true,
  soundEnabled: true,
  showAnomalies: true,
  showPipelines: true,
  showServices: false, // Too noisy by default
  showKubernetes: false, // Too noisy by default
};

export function useEventToasts(config: Partial<EventToastConfig> = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  const configRef = useRef(mergedConfig);
  configRef.current = mergedConfig;

  const handleEvent = useCallback((event: WebSocketEvent) => {
    const cfg = configRef.current;
    if (!cfg.enabled) return;

    const eventType = event.type;
    const data = (event.data || {}) as Record<string, unknown>;

    // Anomaly events
    if (cfg.showAnomalies && eventType.startsWith('anomaly.')) {
      handleAnomalyEvent(eventType, data, cfg.soundEnabled);
      return;
    }

    // Pipeline events
    if (cfg.showPipelines && eventType.startsWith('pipeline.')) {
      handlePipelineEvent(eventType, data, cfg.soundEnabled);
      return;
    }

    // Service events
    if (cfg.showServices && eventType.startsWith('service.')) {
      handleServiceEvent(eventType, data);
      return;
    }

    // Kubernetes events
    if (cfg.showKubernetes) {
      if (eventType.startsWith('pod.') || eventType.startsWith('deployment.')) {
        handleKubernetesEvent(eventType, data);
      }
    }
  }, []);

  useWebSocket({
    channels: ['all'],
    onEvent: handleEvent,
  });
}

function handleAnomalyEvent(
  eventType: string,
  data: Record<string, unknown>,
  soundEnabled: boolean
) {
  const anomaly = (data.anomaly || data) as Record<string, unknown>;

  switch (eventType) {
    case 'anomaly.detected': {
      const severity = anomaly.severity as string;
      const title = anomaly.title as string || 'Anomaly Detected';
      const description = anomaly.description as string;
      const serviceId = anomaly.service_id as string;

      if (severity === 'critical') {
        toast.error(
          title,
          description || `Critical issue detected${serviceId ? ` in service ${serviceId}` : ''}`,
          { sound: soundEnabled, duration: 10000 }
        );
      } else if (severity === 'warning') {
        toast.warning(
          title,
          description || `Warning detected${serviceId ? ` in service ${serviceId}` : ''}`,
          { sound: soundEnabled }
        );
      } else {
        toast.info(title, description);
      }
      break;
    }
    case 'anomaly.resolved': {
      const anomalyId = data.anomaly_id as string;
      toast.success(
        'Anomaly Resolved',
        `Issue ${anomalyId?.slice(0, 8) || ''} has been resolved`
      );
      break;
    }
    case 'anomaly.acknowledged': {
      const anomalyId = data.anomaly_id as string;
      const acknowledgedBy = data.acknowledged_by as string;
      toast.info(
        'Anomaly Acknowledged',
        `${acknowledgedBy || 'Someone'} acknowledged issue ${anomalyId?.slice(0, 8) || ''}`
      );
      break;
    }
  }
}

function handlePipelineEvent(
  eventType: string,
  data: Record<string, unknown>,
  soundEnabled: boolean
) {
  const pipeline = (data.pipeline || data) as Record<string, unknown>;

  switch (eventType) {
    case 'pipeline.started': {
      const branch = pipeline.branch as string || 'unknown';
      const commitSha = pipeline.commit_sha as string;
      toast.info(
        'Pipeline Started',
        `Build started for ${branch}${commitSha ? ` (${commitSha.slice(0, 7)})` : ''}`
      );
      break;
    }
    case 'pipeline.completed': {
      const status = data.status as string;
      const duration = data.duration_seconds as number;
      const durationText = duration ? ` in ${Math.round(duration)}s` : '';

      if (status === 'success') {
        toast.success('Pipeline Succeeded', `Build completed successfully${durationText}`);
      } else {
        toast.warning('Pipeline Completed', `Build finished with status: ${status}${durationText}`);
      }
      break;
    }
    case 'pipeline.failed': {
      const error = data.error as string;
      const pipelineId = data.pipeline_id as string;
      toast.error(
        'Pipeline Failed',
        error || `Build ${pipelineId?.slice(0, 8) || ''} failed`,
        { sound: soundEnabled, duration: 10000 }
      );
      break;
    }
  }
}

function handleServiceEvent(eventType: string, data: Record<string, unknown>) {
  const service = (data.service || data) as Record<string, unknown>;

  switch (eventType) {
    case 'service.created': {
      const name = service.name as string;
      toast.success('Service Created', `New service "${name}" has been created`);
      break;
    }
    case 'service.deleted': {
      const name = data.name as string || data.service_id as string;
      toast.info('Service Deleted', `Service "${name}" has been removed`);
      break;
    }
    case 'service.status_changed': {
      const serviceId = data.service_id as string;
      const oldStatus = data.old_status as string;
      const newStatus = data.new_status as string;

      if (newStatus === 'unhealthy') {
        toast.error(
          'Service Unhealthy',
          `Service ${serviceId?.slice(0, 8) || ''} changed from ${oldStatus} to ${newStatus}`
        );
      } else if (newStatus === 'degraded') {
        toast.warning(
          'Service Degraded',
          `Service ${serviceId?.slice(0, 8) || ''} is now degraded`
        );
      } else if (oldStatus === 'unhealthy' && newStatus === 'healthy') {
        toast.success(
          'Service Recovered',
          `Service ${serviceId?.slice(0, 8) || ''} is now healthy`
        );
      }
      break;
    }
  }
}

function handleKubernetesEvent(eventType: string, data: Record<string, unknown>) {
  switch (eventType) {
    case 'pod.created': {
      const pod = (data.pod || data) as Record<string, unknown>;
      const name = pod.name as string;
      const namespace = pod.namespace as string;
      toast.info('Pod Created', `Pod ${name} created in ${namespace || 'default'}`);
      break;
    }
    case 'pod.deleted': {
      const podName = data.pod_name as string;
      const namespace = data.namespace as string;
      toast.info('Pod Deleted', `Pod ${podName} removed from ${namespace || 'default'}`);
      break;
    }
    case 'deployment.scaled': {
      const deploymentName = data.deployment_name as string;
      const replicas = data.replicas as number;
      toast.info(
        'Deployment Scaled',
        `${deploymentName} scaled to ${replicas} replica${replicas !== 1 ? 's' : ''}`
      );
      break;
    }
  }
}

export default useEventToasts;
