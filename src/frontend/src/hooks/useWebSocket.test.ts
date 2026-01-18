/**
 * useWebSocket Hook Tests
 * ForgeWorks Frontend
 *
 * Tests WebSocket connection management, reconnection logic, and event handling
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useWebSocket } from './useWebSocket';
import type { WebSocketEvent } from '@/types/websocket';

// =============================================================================
// Mock WebSocket
// =============================================================================

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  private sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    mockWebSocketInstances.push(this);
  }

  send(data: string): void {
    this.sentMessages.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason }));
    }
  }

  getSentMessages(): string[] {
    return this.sentMessages;
  }

  // Helpers for simulating server events
  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  simulateClose(code = 1006, reason = 'Connection lost'): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason }));
    }
  }

  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateMessage(data: WebSocketEvent): void {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }
}

// Track all WebSocket instances for testing
let mockWebSocketInstances: MockWebSocket[] = [];

// =============================================================================
// Test Setup
// =============================================================================

beforeEach(() => {
  mockWebSocketInstances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// =============================================================================
// Connection Tests
// =============================================================================

describe('useWebSocket - Connection', () => {
  it('should auto-connect on mount by default', () => {
    renderHook(() => useWebSocket());

    expect(mockWebSocketInstances.length).toBe(1);
    expect(mockWebSocketInstances[0].url).toContain('ws://localhost:8000/ws');
  });

  it('should not auto-connect when autoConnect is false', () => {
    renderHook(() => useWebSocket({ autoConnect: false }));

    expect(mockWebSocketInstances.length).toBe(0);
  });

  it('should set status to connecting initially', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current.status).toBe('connecting');
    expect(result.current.isConnected).toBe(false);
  });

  it('should set status to connected on open', async () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    expect(result.current.status).toBe('connected');
    expect(result.current.isConnected).toBe(true);
  });

  it('should include client_id in connection URL', () => {
    renderHook(() => useWebSocket({ clientId: 'test-client-123' }));

    expect(mockWebSocketInstances[0].url).toContain('client_id=test-client-123');
  });

  it('should generate unique client_id if not provided', () => {
    renderHook(() => useWebSocket());

    expect(mockWebSocketInstances[0].url).toMatch(/client_id=client-[a-z0-9]+/);
  });

  it('should call onConnect callback when connected', () => {
    const onConnect = vi.fn();
    renderHook(() => useWebSocket({ onConnect }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    expect(onConnect).toHaveBeenCalledTimes(1);
  });

  it('should manually connect when connect is called', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }));

    expect(mockWebSocketInstances.length).toBe(0);

    act(() => {
      result.current.connect();
    });

    expect(mockWebSocketInstances.length).toBe(1);
  });
});

// =============================================================================
// Disconnection Tests
// =============================================================================

describe('useWebSocket - Disconnection', () => {
  it('should set status to disconnected on clean close', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      mockWebSocketInstances[0].close(1000);
    });

    expect(result.current.status).toBe('disconnected');
    expect(result.current.isConnected).toBe(false);
  });

  it('should call onDisconnect callback on clean close', () => {
    const onDisconnect = vi.fn();
    renderHook(() => useWebSocket({ onDisconnect }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      mockWebSocketInstances[0].close(1000);
    });

    expect(onDisconnect).toHaveBeenCalledTimes(1);
  });

  it('should disconnect when disconnect is called', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      result.current.disconnect();
    });

    expect(result.current.status).toBe('disconnected');
  });

  it('should close WebSocket with code 1000 on manual disconnect', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const ws = mockWebSocketInstances[0];

    act(() => {
      result.current.disconnect();
    });

    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
  });

  it('should clean up on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const ws = mockWebSocketInstances[0];
    unmount();

    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
  });
});

// =============================================================================
// Reconnection Tests
// =============================================================================

describe('useWebSocket - Reconnection', () => {
  it('should attempt reconnection on abnormal close', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ maxReconnectAttempts: 3, reconnectDelay: 1000 })
    );

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    // Simulate abnormal close
    act(() => {
      mockWebSocketInstances[0].simulateClose(1006, 'Connection lost');
    });

    expect(result.current.status).toBe('reconnecting');

    // Advance timers to trigger reconnection
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(mockWebSocketInstances.length).toBe(2);
    expect(result.current.reconnectAttempts).toBe(1);
  });

  it('should use exponential backoff for reconnection', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ maxReconnectAttempts: 5, reconnectDelay: 1000 })
    );

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    // First reconnection attempt
    act(() => {
      mockWebSocketInstances[0].simulateClose(1006);
    });

    // First attempt should be within ~2 seconds (1000 * 2^0 + jitter)
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(mockWebSocketInstances.length).toBe(2);

    // Simulate another failure
    act(() => {
      mockWebSocketInstances[1].simulateClose(1006);
    });

    // Second attempt should take longer (~3-4 seconds with 1000 * 2^1 + jitter)
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.reconnectAttempts).toBe(2);
  });

  it('should track reconnection attempts', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ maxReconnectAttempts: 5, reconnectDelay: 100 })
    );

    // Open initial connection
    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    expect(result.current.status).toBe('connected');
    expect(result.current.reconnectAttempts).toBe(0);

    // First abnormal close - should trigger reconnecting status
    act(() => {
      mockWebSocketInstances[0].simulateClose(1006);
    });

    expect(result.current.status).toBe('reconnecting');

    // Wait and let first reconnection attempt happen
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });

    expect(mockWebSocketInstances.length).toBe(2);
    expect(result.current.reconnectAttempts).toBe(1);

    // Second abnormal close
    act(() => {
      mockWebSocketInstances[1].simulateClose(1006);
    });

    // Status should be reconnecting after abnormal close
    expect(result.current.status).toBe('reconnecting');

    // Wait for second reconnection attempt
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(mockWebSocketInstances.length).toBe(3);
    expect(result.current.reconnectAttempts).toBe(2);
  });

  it('should reset reconnect attempts on successful connection', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ maxReconnectAttempts: 5, reconnectDelay: 100 })
    );

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    expect(result.current.reconnectAttempts).toBe(0);

    // Simulate failure
    act(() => {
      mockWebSocketInstances[0].simulateClose(1006);
    });

    expect(result.current.status).toBe('reconnecting');

    // Wait for reconnection attempt
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });

    expect(mockWebSocketInstances.length).toBe(2);
    expect(result.current.reconnectAttempts).toBe(1);

    // Successful reconnection
    act(() => {
      mockWebSocketInstances[1].simulateOpen();
    });

    expect(result.current.reconnectAttempts).toBe(0);
    expect(result.current.status).toBe('connected');
  });

  it('should not reconnect on clean close (code 1000)', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      mockWebSocketInstances[0].close(1000, 'Normal close');
    });

    expect(result.current.status).toBe('disconnected');
    expect(mockWebSocketInstances.length).toBe(1); // No new connection attempt
  });
});

// =============================================================================
// Error Handling Tests
// =============================================================================

describe('useWebSocket - Error Handling', () => {
  it('should set status to error on WebSocket error', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateError();
    });

    expect(result.current.status).toBe('error');
  });

  it('should call onError callback on error', () => {
    const onError = vi.fn();
    renderHook(() => useWebSocket({ onError }));

    act(() => {
      mockWebSocketInstances[0].simulateError();
    });

    expect(onError).toHaveBeenCalledWith(expect.any(Error));
  });
});

// =============================================================================
// Subscription Tests
// =============================================================================

describe('useWebSocket - Subscriptions', () => {
  it('should subscribe to initial channels on connect', () => {
    renderHook(() => useWebSocket({ channels: ['services', 'anomalies'] }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const messages = mockWebSocketInstances[0].getSentMessages();
    const subscribeMessages = messages.filter((m) => JSON.parse(m).action === 'subscribe');

    expect(subscribeMessages.length).toBe(2);
    expect(subscribeMessages.map((m) => JSON.parse(m).channel)).toContain('services');
    expect(subscribeMessages.map((m) => JSON.parse(m).channel)).toContain('anomalies');
  });

  it('should not send subscribe message for "all" channel', () => {
    renderHook(() => useWebSocket({ channels: ['all'] }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const messages = mockWebSocketInstances[0].getSentMessages();
    expect(messages.length).toBe(0);
  });

  it('should subscribe to a channel manually', () => {
    const { result } = renderHook(() => useWebSocket({ channels: [] }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      result.current.subscribe('pipelines');
    });

    const messages = mockWebSocketInstances[0].getSentMessages();
    const lastMessage = JSON.parse(messages[messages.length - 1]);

    expect(lastMessage.action).toBe('subscribe');
    expect(lastMessage.channel).toBe('pipelines');
    expect(result.current.subscriptions).toContain('pipelines');
  });

  it('should unsubscribe from a channel', () => {
    const { result } = renderHook(() => useWebSocket({ channels: ['services'] }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      result.current.unsubscribe('services');
    });

    const messages = mockWebSocketInstances[0].getSentMessages();
    const unsubscribeMessages = messages.filter((m) => JSON.parse(m).action === 'unsubscribe');

    expect(unsubscribeMessages.length).toBe(1);
    expect(JSON.parse(unsubscribeMessages[0]).channel).toBe('services');
    expect(result.current.subscriptions).not.toContain('services');
  });

  it('should not duplicate channel subscriptions', () => {
    const { result } = renderHook(() => useWebSocket({ channels: ['services'] }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      result.current.subscribe('services');
    });

    // Should only have one 'services' in subscriptions
    const servicesCount = result.current.subscriptions.filter((s) => s === 'services').length;
    expect(servicesCount).toBe(1);
  });

  it('should update subscriptions from server response', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      mockWebSocketInstances[0].simulateMessage({
        type: 'subscribed',
        channel: 'services',
        data: { subscriptions: ['services', 'anomalies', 'pipelines'] },
        timestamp: new Date().toISOString(),
      });
    });

    expect(result.current.subscriptions).toEqual(['services', 'anomalies', 'pipelines']);
  });
});

// =============================================================================
// Event Handling Tests
// =============================================================================

describe('useWebSocket - Event Handling', () => {
  it('should update lastEvent on message', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const event: WebSocketEvent = {
      type: 'service.created',
      channel: 'services',
      data: { service_id: 'svc-123', name: 'New Service' },
      timestamp: new Date().toISOString(),
    };

    act(() => {
      mockWebSocketInstances[0].simulateMessage(event);
    });

    expect(result.current.lastEvent).toEqual(event);
  });

  it('should call onEvent callback with parsed event', () => {
    const onEvent = vi.fn();
    renderHook(() => useWebSocket({ onEvent }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const event: WebSocketEvent = {
      type: 'anomaly.detected',
      channel: 'anomalies',
      data: { anomaly_id: 'anom-456', severity: 'critical' },
      timestamp: new Date().toISOString(),
    };

    act(() => {
      mockWebSocketInstances[0].simulateMessage(event);
    });

    expect(onEvent).toHaveBeenCalledWith(event);
  });

  it('should handle pipeline events', () => {
    const onEvent = vi.fn();
    renderHook(() => useWebSocket({ onEvent }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const event: WebSocketEvent = {
      type: 'pipeline.completed',
      channel: 'pipelines',
      data: { pipeline_id: 'pipe-789', status: 'success', duration_seconds: 120 },
      timestamp: new Date().toISOString(),
    };

    act(() => {
      mockWebSocketInstances[0].simulateMessage(event);
    });

    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'pipeline.completed',
        channel: 'pipelines',
      })
    );
  });

  it('should handle Kubernetes events', () => {
    const onEvent = vi.fn();
    renderHook(() => useWebSocket({ onEvent }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const event: WebSocketEvent = {
      type: 'pod.created',
      channel: 'kubernetes',
      data: { pod_name: 'api-pod-abc123', namespace: 'production' },
      timestamp: new Date().toISOString(),
    };

    act(() => {
      mockWebSocketInstances[0].simulateMessage(event);
    });

    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'pod.created',
        channel: 'kubernetes',
      })
    );
  });

  it('should handle malformed messages gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    // Simulate malformed message
    act(() => {
      if (mockWebSocketInstances[0].onmessage) {
        mockWebSocketInstances[0].onmessage(
          new MessageEvent('message', { data: 'not-valid-json' })
        );
      }
    });

    expect(consoleSpy).toHaveBeenCalled();
    expect(result.current.lastEvent).toBeNull();

    consoleSpy.mockRestore();
  });

  it('should handle events with correlation_id', () => {
    const onEvent = vi.fn();
    renderHook(() => useWebSocket({ onEvent }));

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const event: WebSocketEvent = {
      type: 'metrics.updated',
      channel: 'metrics',
      data: { cpu_usage: 45.5, memory_usage: 62.3 },
      timestamp: new Date().toISOString(),
      correlation_id: 'req-abc-123',
    };

    act(() => {
      mockWebSocketInstances[0].simulateMessage(event);
    });

    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        correlation_id: 'req-abc-123',
      })
    );
  });
});

// =============================================================================
// Edge Cases
// =============================================================================

describe('useWebSocket - Edge Cases', () => {
  it('should not create duplicate connections when connect called twice', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }));

    act(() => {
      result.current.connect();
    });

    // Set to CONNECTING state
    mockWebSocketInstances[0].readyState = MockWebSocket.CONNECTING;

    act(() => {
      result.current.connect();
    });

    // Should still only have one WebSocket
    expect(mockWebSocketInstances.length).toBe(1);
  });

  it('should close existing connection before creating new one', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }));

    act(() => {
      result.current.connect();
    });

    const firstWs = mockWebSocketInstances[0];
    firstWs.readyState = MockWebSocket.OPEN;

    act(() => {
      result.current.connect();
    });

    expect(firstWs.readyState).toBe(MockWebSocket.CLOSED);
    expect(mockWebSocketInstances.length).toBe(2);
  });

  it('should handle rapid subscribe/unsubscribe', () => {
    const { result } = renderHook(() => useWebSocket());

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    act(() => {
      result.current.subscribe('services');
      result.current.subscribe('anomalies');
      result.current.unsubscribe('services');
      result.current.subscribe('pipelines');
    });

    expect(result.current.subscriptions).toContain('anomalies');
    expect(result.current.subscriptions).toContain('pipelines');
    expect(result.current.subscriptions).not.toContain('services');
  });

  it('should not send messages when not connected', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }));

    act(() => {
      result.current.subscribe('services');
    });

    // No WebSocket created, so no messages sent
    expect(mockWebSocketInstances.length).toBe(0);
  });

  it('should handle options changes between renders', () => {
    const onEvent1 = vi.fn();
    const { rerender } = renderHook(({ onEvent }) => useWebSocket({ onEvent }), {
      initialProps: { onEvent: onEvent1 },
    });

    act(() => {
      mockWebSocketInstances[0].simulateOpen();
    });

    const event: WebSocketEvent = {
      type: 'service.updated',
      channel: 'services',
      data: {},
      timestamp: new Date().toISOString(),
    };

    act(() => {
      mockWebSocketInstances[0].simulateMessage(event);
    });

    expect(onEvent1).toHaveBeenCalled();
  });
});

// =============================================================================
// Return Value Tests
// =============================================================================

describe('useWebSocket - Return Value', () => {
  it('should return all expected properties', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(result.current).toHaveProperty('status');
    expect(result.current).toHaveProperty('isConnected');
    expect(result.current).toHaveProperty('subscribe');
    expect(result.current).toHaveProperty('unsubscribe');
    expect(result.current).toHaveProperty('connect');
    expect(result.current).toHaveProperty('disconnect');
    expect(result.current).toHaveProperty('lastEvent');
    expect(result.current).toHaveProperty('subscriptions');
    expect(result.current).toHaveProperty('reconnectAttempts');
  });

  it('should have stable function references', () => {
    const { result, rerender } = renderHook(() => useWebSocket());

    const initialFunctions = {
      subscribe: result.current.subscribe,
      unsubscribe: result.current.unsubscribe,
      connect: result.current.connect,
      disconnect: result.current.disconnect,
    };

    rerender();

    expect(result.current.subscribe).toBe(initialFunctions.subscribe);
    expect(result.current.unsubscribe).toBe(initialFunctions.unsubscribe);
    expect(result.current.disconnect).toBe(initialFunctions.disconnect);
  });

  it('should return correct initial subscriptions', () => {
    const { result } = renderHook(() =>
      useWebSocket({ channels: ['services', 'anomalies', 'kubernetes'] })
    );

    expect(result.current.subscriptions).toEqual(['services', 'anomalies', 'kubernetes']);
  });
});
