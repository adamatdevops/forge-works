/**
 * WebSocket Types
 * Type definitions for real-time WebSocket communication
 */

/**
 * WebSocket event types matching backend EventType enum
 */
export type EventType =
  // Connection events
  | 'connected'
  | 'disconnected'
  | 'subscribed'
  | 'unsubscribed'
  | 'error'
  // Service events
  | 'service.created'
  | 'service.updated'
  | 'service.deleted'
  | 'service.status_changed'
  // Anomaly events
  | 'anomaly.detected'
  | 'anomaly.acknowledged'
  | 'anomaly.resolved'
  // Pipeline events
  | 'pipeline.started'
  | 'pipeline.completed'
  | 'pipeline.failed'
  // Template events
  | 'template.created'
  | 'template.updated'
  // Metrics events
  | 'metrics.updated'
  // Kubernetes events
  | 'pod.created'
  | 'pod.deleted'
  | 'deployment.scaled';

/**
 * WebSocket channels matching backend Channel enum
 */
export type Channel =
  | 'all'
  | 'services'
  | 'anomalies'
  | 'pipelines'
  | 'templates'
  | 'metrics'
  | 'kubernetes';

/**
 * WebSocket event structure from backend
 */
export interface WebSocketEvent<T = unknown> {
  type: EventType;
  channel: Channel;
  data: T;
  timestamp: string;
  correlation_id?: string | null;
}

/**
 * Service event data structures
 */
export interface ServiceEventData {
  service?: Record<string, unknown>;
  service_id?: string;
  name?: string;
  changes?: Record<string, unknown>;
  old_status?: string;
  new_status?: string;
  action: 'created' | 'updated' | 'deleted' | 'status_changed';
}

/**
 * Anomaly event data structures
 */
export interface AnomalyEventData {
  anomaly?: Record<string, unknown>;
  anomaly_id?: string;
  acknowledged_by?: string;
  resolved_by?: string;
  resolution?: string;
  action: 'detected' | 'acknowledged' | 'resolved';
}

/**
 * Pipeline event data structures
 */
export interface PipelineEventData {
  pipeline?: Record<string, unknown>;
  pipeline_id?: string;
  status?: string;
  duration_seconds?: number;
  error?: string;
  action: 'started' | 'completed' | 'failed';
}

/**
 * Client message to server
 */
export interface WebSocketClientMessage {
  action: 'subscribe' | 'unsubscribe' | 'ping';
  channel?: Channel;
}

/**
 * Connection status
 */
export type ConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'error';

/**
 * WebSocket hook options
 */
export interface UseWebSocketOptions {
  /**
   * Whether to automatically connect on mount
   * @default true
   */
  autoConnect?: boolean;

  /**
   * Initial channels to subscribe to
   * @default ['all']
   */
  channels?: Channel[];

  /**
   * Maximum reconnection attempts
   * @default 5
   */
  maxReconnectAttempts?: number;

  /**
   * Base delay for reconnection (exponential backoff)
   * @default 1000
   */
  reconnectDelay?: number;

  /**
   * Client identifier (generated if not provided)
   */
  clientId?: string;

  /**
   * Callback when connection is established
   */
  onConnect?: () => void;

  /**
   * Callback when connection is lost
   */
  onDisconnect?: () => void;

  /**
   * Callback when an error occurs
   */
  onError?: (error: Error) => void;

  /**
   * Callback when any event is received
   */
  onEvent?: (event: WebSocketEvent) => void;
}

/**
 * WebSocket hook return type
 */
export interface UseWebSocketReturn {
  /**
   * Current connection status
   */
  status: ConnectionStatus;

  /**
   * Whether the connection is active
   */
  isConnected: boolean;

  /**
   * Subscribe to a channel
   */
  subscribe: (channel: Channel) => void;

  /**
   * Unsubscribe from a channel
   */
  unsubscribe: (channel: Channel) => void;

  /**
   * Manually connect
   */
  connect: () => void;

  /**
   * Manually disconnect
   */
  disconnect: () => void;

  /**
   * Last received event
   */
  lastEvent: WebSocketEvent | null;

  /**
   * Current subscriptions
   */
  subscriptions: Channel[];

  /**
   * Number of reconnection attempts
   */
  reconnectAttempts: number;
}
