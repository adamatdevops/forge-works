'use client';

/**
 * WebSocket Health Dashboard
 * Developer debug page showing WebSocket status and event log
 * Only for development mode
 */

import { useCallback, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertCircle,
  Radio,
  RefreshCw,
  Send,
  Trash2,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useWebSocket } from '@/hooks';
import { ConnectionIndicator } from '@/components/ui/ConnectionIndicator';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import type { WebSocketEvent } from '@/types/websocket';

interface EventLogEntry {
  id: string;
  timestamp: Date;
  event: WebSocketEvent;
}

interface DemoStatus {
  demo_mode_enabled: boolean;
  environment: string;
  websocket_stats: {
    total_connections: number;
    current_connections: number;
    messages_sent: number;
    messages_received: number;
  };
  available_event_types: number;
}

interface DemoEventType {
  type: string;
  name: string;
  sample_data: Record<string, unknown>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function WebSocketDashboard() {
  const [eventLog, setEventLog] = useState<EventLogEntry[]>([]);
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [isSending, setIsSending] = useState(false);

  // WebSocket connection
  const handleEvent = useCallback((event: WebSocketEvent) => {
    const entry: EventLogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      timestamp: new Date(),
      event,
    };
    setEventLog((prev) => [entry, ...prev].slice(0, 100));
  }, []);

  const { status, isConnected, reconnectAttempts } = useWebSocket({
    channels: ['all'],
    onEvent: handleEvent,
  });

  // Fetch demo status
  const { data: demoStatus, refetch: refetchStatus, isRefetching } = useQuery<DemoStatus>({
    queryKey: ['demo-status'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/demo/status`);
      if (!response.ok) throw new Error('Failed to fetch demo status');
      return response.json();
    },
    refetchInterval: 5000,
  });

  // Fetch available event types
  const { data: eventTypes } = useQuery<{ event_types: DemoEventType[] }>({
    queryKey: ['demo-event-types'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/demo/event-types`);
      if (!response.ok) throw new Error('Failed to fetch event types');
      return response.json();
    },
  });

  // Trigger demo event
  const triggerEvent = async () => {
    if (!selectedEventType) return;

    setIsSending(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/demo/trigger-event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: selectedEventType }),
      });

      if (!response.ok) {
        throw new Error('Failed to trigger event');
      }
    } catch (error) {
      console.error('Error triggering event:', error);
    } finally {
      setIsSending(false);
    }
  };

  // Clear event log
  const clearLog = () => setEventLog([]);

  // Check if demo mode is enabled
  const isDemoEnabled = demoStatus?.demo_mode_enabled ?? false;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">WebSocket Health Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Monitor real-time connections and test events
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <ConnectionIndicator status={status} reconnectAttempts={reconnectAttempts} />
            {!isDemoEnabled && (
              <Badge variant="destructive" className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Demo Mode Disabled
              </Badge>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Connection Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <Wifi className="h-5 w-5 text-green-500" />
                ) : (
                  <WifiOff className="h-5 w-5 text-red-500" />
                )}
                <span className="text-2xl font-bold">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Connections
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">
                  {demoStatus?.websocket_stats.current_connections ?? 0}
                </span>
                <span className="text-sm text-muted-foreground">
                  / {demoStatus?.websocket_stats.total_connections ?? 0} total
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Messages Sent
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">
                {demoStatus?.websocket_stats.messages_sent ?? 0}
              </span>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Messages Received
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">
                {demoStatus?.websocket_stats.messages_received ?? 0}
              </span>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Event Trigger Panel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Send className="h-5 w-5" />
                Trigger Test Event
              </CardTitle>
              <CardDescription>
                Send demo events to test real-time functionality
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select
                value={selectedEventType}
                onValueChange={setSelectedEventType}
                disabled={!isDemoEnabled}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select event type..." />
                </SelectTrigger>
                <SelectContent>
                  {eventTypes?.event_types.map((et) => (
                    <SelectItem key={et.type} value={et.type}>
                      {et.type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedEventType && eventTypes?.event_types && (
                <div className="p-3 bg-muted rounded-md">
                  <p className="text-xs font-medium mb-2">Sample Data:</p>
                  <pre className="text-xs overflow-auto max-h-32">
                    {JSON.stringify(
                      eventTypes.event_types.find((et) => et.type === selectedEventType)
                        ?.sample_data,
                      null,
                      2
                    )}
                  </pre>
                </div>
              )}

              <Button
                onClick={triggerEvent}
                disabled={!selectedEventType || isSending || !isDemoEnabled}
                className="w-full"
              >
                {isSending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Trigger Event
                  </>
                )}
              </Button>

              {!isDemoEnabled && (
                <p className="text-xs text-destructive text-center">
                  Demo mode is disabled. Set environment to development.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Event Log */}
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Radio className="h-5 w-5" />
                  Event Log
                </CardTitle>
                <CardDescription>
                  Real-time WebSocket events ({eventLog.length} events)
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchStatus()}
                  disabled={isRefetching}
                >
                  <RefreshCw
                    className={cn('h-4 w-4', isRefetching && 'animate-spin')}
                  />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearLog}
                  disabled={eventLog.length === 0}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-96 overflow-auto border rounded-md">
                {eventLog.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <p>No events received yet. Trigger an event to see it here.</p>
                  </div>
                ) : (
                  <div className="divide-y">
                    {eventLog.map((entry) => (
                      <EventLogItem key={entry.id} entry={entry} />
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Environment Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Environment Info</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Environment:</span>{' '}
                <Badge variant="outline">{demoStatus?.environment ?? 'unknown'}</Badge>
              </div>
              <div>
                <span className="text-muted-foreground">API URL:</span>{' '}
                <code className="text-xs bg-muted px-1 py-0.5 rounded">{API_BASE}</code>
              </div>
              <div>
                <span className="text-muted-foreground">Available Event Types:</span>{' '}
                <Badge variant="secondary">
                  {demoStatus?.available_event_types ?? 0}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function EventLogItem({ entry }: { entry: EventLogEntry }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const typeColors: Record<string, string> = {
    service: 'text-blue-500',
    anomaly: 'text-yellow-500',
    pipeline: 'text-purple-500',
    pod: 'text-cyan-500',
    deployment: 'text-green-500',
    template: 'text-pink-500',
    metrics: 'text-orange-500',
  };

  const eventPrefix = entry.event.type.split('.')[0];
  const color = typeColors[eventPrefix] || 'text-gray-500';

  return (
    <div className="p-3 hover:bg-muted/50 transition-colors">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-20">
            {entry.timestamp.toLocaleTimeString()}
          </span>
          <Badge variant="outline" className={cn('font-mono text-xs', color)}>
            {entry.event.type}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            {entry.event.channel}
          </Badge>
        </div>
        <span className="text-xs text-muted-foreground">
          {isExpanded ? 'Click to collapse' : 'Click to expand'}
        </span>
      </div>
      {isExpanded && (
        <div className="mt-2 p-2 bg-muted rounded-md">
          <pre className="text-xs overflow-auto max-h-48">
            {JSON.stringify(entry.event.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
