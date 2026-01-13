'use client';

/**
 * useWebSocket Hook
 * React hook for WebSocket connection with auto-reconnect
 *
 * Features:
 * - Automatic connection management
 * - Exponential backoff reconnection
 * - Channel-based subscriptions
 * - Type-safe event handling
 *
 * Usage:
 *   const { status, subscribe, lastEvent } = useWebSocket({
 *     channels: ['services', 'anomalies'],
 *     onEvent: (event) => console.log(event),
 *   });
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  Channel,
  ConnectionStatus,
  UseWebSocketOptions,
  UseWebSocketReturn,
  WebSocketClientMessage,
  WebSocketEvent,
} from '@/types/websocket';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

/**
 * Generate a unique client ID
 */
function generateClientId(): string {
  return `client-${Math.random().toString(36).substring(2, 10)}`;
}

/**
 * Calculate exponential backoff delay
 */
function getReconnectDelay(attempt: number, baseDelay: number): number {
  // Exponential backoff with jitter: baseDelay * 2^attempt + random jitter
  const exponentialDelay = baseDelay * Math.pow(2, attempt);
  const jitter = Math.random() * 1000;
  return Math.min(exponentialDelay + jitter, 30000); // Cap at 30 seconds
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    channels = ['all'],
    maxReconnectAttempts = 5,
    reconnectDelay = 1000,
    clientId: providedClientId,
    onConnect,
    onDisconnect,
    onError,
    onEvent,
  } = options;

  // State
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);
  const [subscriptions, setSubscriptions] = useState<Channel[]>(channels);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Refs to avoid stale closures
  const wsRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef(providedClientId || generateClientId());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Send message to server
  const sendMessage = useCallback((message: WebSocketClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Subscribe to a channel
  const subscribe = useCallback(
    (channel: Channel) => {
      sendMessage({ action: 'subscribe', channel });
      setSubscriptions((prev) => (prev.includes(channel) ? prev : [...prev, channel]));
    },
    [sendMessage]
  );

  // Unsubscribe from a channel
  const unsubscribe = useCallback(
    (channel: Channel) => {
      sendMessage({ action: 'unsubscribe', channel });
      setSubscriptions((prev) => prev.filter((c) => c !== channel));
    },
    [sendMessage]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Don't connect if already connecting or connected
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('connecting');
    clearReconnectTimeout();

    const wsUrl = `${WS_BASE_URL}/ws?client_id=${clientIdRef.current}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      if (!mountedRef.current) return;

      setStatus('connected');
      setReconnectAttempts(0);

      // Subscribe to initial channels
      channels.forEach((channel) => {
        if (channel !== 'all') {
          sendMessage({ action: 'subscribe', channel });
        }
      });

      onConnect?.();
    };

    ws.onclose = (event) => {
      if (!mountedRef.current) return;

      wsRef.current = null;

      // Don't reconnect if closed cleanly (code 1000) or component unmounted
      if (event.code === 1000) {
        setStatus('disconnected');
        onDisconnect?.();
        return;
      }

      // Attempt reconnection
      if (reconnectAttempts < maxReconnectAttempts) {
        setStatus('reconnecting');
        const delay = getReconnectDelay(reconnectAttempts, reconnectDelay);

        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) {
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }
        }, delay);
      } else {
        setStatus('disconnected');
        onDisconnect?.();
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus('error');
      onError?.(new Error('WebSocket connection error'));
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;

      try {
        const wsEvent = JSON.parse(event.data) as WebSocketEvent;
        setLastEvent(wsEvent);

        // Update subscriptions from server response
        if (wsEvent.type === 'subscribed' || wsEvent.type === 'unsubscribed') {
          const data = wsEvent.data as { subscriptions?: string[] };
          if (data.subscriptions) {
            setSubscriptions(data.subscriptions as Channel[]);
          }
        }

        onEvent?.(wsEvent);
      } catch {
        console.error('Failed to parse WebSocket message:', event.data);
      }
    };

    wsRef.current = ws;
  }, [
    channels,
    clearReconnectTimeout,
    maxReconnectAttempts,
    onConnect,
    onDisconnect,
    onError,
    onEvent,
    reconnectAttempts,
    reconnectDelay,
    sendMessage,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    setReconnectAttempts(0);

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setStatus('disconnected');
  }, [clearReconnectTimeout]);

  // Auto-connect on mount
  useEffect(() => {
    mountedRef.current = true;

    if (autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      clearReconnectTimeout();

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    status,
    isConnected: status === 'connected',
    subscribe,
    unsubscribe,
    connect,
    disconnect,
    lastEvent,
    subscriptions,
    reconnectAttempts,
  };
}

export default useWebSocket;
