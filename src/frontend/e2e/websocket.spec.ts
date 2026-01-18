/**
 * WebSocket E2E Tests
 * ForgeWorks Frontend
 *
 * Tests WebSocket connection and real-time event handling
 * Note: These tests require the backend WebSocket server to be running
 */

import { test, expect } from '@playwright/test';

// =============================================================================
// WebSocket Status Endpoint Tests
// =============================================================================

test.describe('WebSocket Status API', () => {
  test('should return WebSocket server status', async ({ request }) => {
    const response = await request.get('http://localhost:8000/ws/status');

    expect(response.ok()).toBeTruthy();

    const status = await response.json();
    expect(status).toHaveProperty('active_connections');
    expect(status).toHaveProperty('client_ids');
    expect(status).toHaveProperty('channels');
    expect(status).toHaveProperty('status');
    expect(status.status).toBe('healthy');
  });

  test('should return channel subscriber counts', async ({ request }) => {
    const response = await request.get('http://localhost:8000/ws/status');
    const status = await response.json();

    // Should have all channel stats
    expect(status.channels).toHaveProperty('all');
    expect(status.channels).toHaveProperty('services');
    expect(status.channels).toHaveProperty('anomalies');
    expect(status.channels).toHaveProperty('pipelines');
    expect(status.channels).toHaveProperty('templates');
    expect(status.channels).toHaveProperty('metrics');
    expect(status.channels).toHaveProperty('kubernetes');
  });
});

// =============================================================================
// WebSocket Connection Tests
// =============================================================================

test.describe('WebSocket Connection', () => {
  test('should connect to WebSocket endpoint', async ({ page }) => {
    // Navigate to a page that uses WebSocket
    await page.goto('http://localhost:3000');

    // Wait for WebSocket connection indicator if available
    const connectionStatus = await page.evaluate(async () => {
      return new Promise<string>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-test-client');

        ws.onopen = () => {
          ws.close();
          resolve('connected');
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Connection timeout')), 5000);
      });
    });

    expect(connectionStatus).toBe('connected');
  });

  test('should receive connection confirmation event', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const connectionEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-test-confirm');

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          ws.close();
          resolve(data);
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Message timeout')), 5000);
      });
    });

    expect(connectionEvent).toHaveProperty('type', 'connected');
    expect(connectionEvent).toHaveProperty('channel', 'all');
    expect(connectionEvent).toHaveProperty('data');
    expect((connectionEvent.data as Record<string, unknown>).client_id).toBe('e2e-test-confirm');
  });

  test('should auto-generate client ID if not provided', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const connectionEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws'); // No client_id

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          ws.close();
          resolve(data);
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Message timeout')), 5000);
      });
    });

    expect(connectionEvent.type).toBe('connected');
    const clientId = (connectionEvent.data as Record<string, unknown>).client_id as string;
    expect(clientId).toMatch(/^client-[a-f0-9]+$/);
  });
});

// =============================================================================
// WebSocket Subscription Tests
// =============================================================================

test.describe('WebSocket Subscriptions', () => {
  test('should subscribe to a channel', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const subscriptionEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-subscribe-test');
        let messageCount = 0;

        ws.onmessage = (event) => {
          messageCount++;
          const data = JSON.parse(event.data);

          // First message is connection confirmation
          if (messageCount === 1) {
            // Subscribe to services channel
            ws.send(JSON.stringify({ action: 'subscribe', channel: 'services' }));
          }

          // Second message should be subscription confirmation
          if (messageCount === 2) {
            ws.close();
            resolve(data);
          }
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Subscription timeout')), 5000);
      });
    });

    expect(subscriptionEvent.type).toBe('subscribed');
    expect(subscriptionEvent.channel).toBe('services');
    const subscriptions = (subscriptionEvent.data as Record<string, unknown>)
      .subscriptions as string[];
    expect(subscriptions).toContain('services');
  });

  test('should unsubscribe from a channel', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const unsubscribeEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-unsubscribe-test');
        let messageCount = 0;

        ws.onmessage = (event) => {
          messageCount++;
          const data = JSON.parse(event.data);

          if (messageCount === 1) {
            // Subscribe first
            ws.send(JSON.stringify({ action: 'subscribe', channel: 'pipelines' }));
          }

          if (messageCount === 2) {
            // Then unsubscribe
            ws.send(JSON.stringify({ action: 'unsubscribe', channel: 'pipelines' }));
          }

          if (messageCount === 3) {
            ws.close();
            resolve(data);
          }
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Unsubscribe timeout')), 5000);
      });
    });

    expect(unsubscribeEvent.type).toBe('unsubscribed');
    expect(unsubscribeEvent.channel).toBe('pipelines');
    const subscriptions = (unsubscribeEvent.data as Record<string, unknown>)
      .subscriptions as string[];
    expect(subscriptions).not.toContain('pipelines');
  });

  test('should handle invalid channel subscription gracefully', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const errorEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-invalid-channel');
        let messageCount = 0;

        ws.onmessage = (event) => {
          messageCount++;
          const data = JSON.parse(event.data);

          if (messageCount === 1) {
            // Try to subscribe to invalid channel
            ws.send(JSON.stringify({ action: 'subscribe', channel: 'invalid_channel' }));
          }

          if (messageCount === 2) {
            ws.close();
            resolve(data);
          }
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Error response timeout')), 5000);
      });
    });

    expect(errorEvent.type).toBe('error');
    expect((errorEvent.data as Record<string, unknown>).error).toContain('Unknown channel');
  });
});

// =============================================================================
// WebSocket Ping/Pong Tests
// =============================================================================

test.describe('WebSocket Keepalive', () => {
  test('should respond to ping with pong', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const pongEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-ping-test');
        let messageCount = 0;

        ws.onmessage = (event) => {
          messageCount++;
          const data = JSON.parse(event.data);

          if (messageCount === 1) {
            // Send ping
            ws.send(JSON.stringify({ action: 'ping' }));
          }

          if (messageCount === 2) {
            ws.close();
            resolve(data);
          }
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Ping timeout')), 5000);
      });
    });

    expect(pongEvent.type).toBe('connected'); // Backend sends connected with pong data
    expect((pongEvent.data as Record<string, unknown>).pong).toBe(true);
  });
});

// =============================================================================
// WebSocket Error Handling Tests
// =============================================================================

test.describe('WebSocket Error Handling', () => {
  test('should handle unknown action gracefully', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const errorEvent = await page.evaluate(async () => {
      return new Promise<Record<string, unknown>>((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=e2e-unknown-action');
        let messageCount = 0;

        ws.onmessage = (event) => {
          messageCount++;
          const data = JSON.parse(event.data);

          if (messageCount === 1) {
            // Send unknown action
            ws.send(JSON.stringify({ action: 'unknown_action' }));
          }

          if (messageCount === 2) {
            ws.close();
            resolve(data);
          }
        };

        ws.onerror = () => {
          reject(new Error('WebSocket connection failed'));
        };

        setTimeout(() => reject(new Error('Error response timeout')), 5000);
      });
    });

    expect(errorEvent.type).toBe('error');
    expect((errorEvent.data as Record<string, unknown>).error).toContain('Unknown action');
  });
});

// =============================================================================
// WebSocket Dashboard Tests (if available)
// =============================================================================

test.describe('WebSocket Dashboard', () => {
  test('should load WebSocket dashboard page', async ({ page }) => {
    const response = await page.goto('http://localhost:3000/ws/dashboard');

    // Dashboard might not exist or might redirect - just check it doesn't error
    if (response) {
      expect(response.status()).toBeLessThan(500);
    }
  });
});

// =============================================================================
// Connection Resilience Tests
// =============================================================================

test.describe('WebSocket Resilience', () => {
  test('should handle rapid connect/disconnect', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const results = await page.evaluate(async () => {
      const connections: boolean[] = [];

      for (let i = 0; i < 5; i++) {
        const connected = await new Promise<boolean>((resolve) => {
          const ws = new WebSocket(`ws://localhost:8000/ws?client_id=e2e-rapid-${i}`);

          ws.onopen = () => {
            ws.close();
            resolve(true);
          };

          ws.onerror = () => resolve(false);

          setTimeout(() => resolve(false), 2000);
        });

        connections.push(connected);
      }

      return connections;
    });

    // All connections should succeed
    expect(results.every((r) => r)).toBeTruthy();
  });

  test('should handle concurrent connections', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const results = await page.evaluate(async () => {
      const promises = Array(5)
        .fill(null)
        .map(
          (_, i) =>
            new Promise<boolean>((resolve) => {
              const ws = new WebSocket(`ws://localhost:8000/ws?client_id=e2e-concurrent-${i}`);

              ws.onopen = () => {
                ws.close();
                resolve(true);
              };

              ws.onerror = () => resolve(false);

              setTimeout(() => resolve(false), 5000);
            })
        );

      return Promise.all(promises);
    });

    // All concurrent connections should succeed
    expect(results.every((r) => r)).toBeTruthy();
  });
});
