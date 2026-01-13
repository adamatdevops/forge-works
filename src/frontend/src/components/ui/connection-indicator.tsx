'use client';

/**
 * Connection Indicator Component
 * Shows WebSocket connection status in the UI
 */

import { useRealtimeAll } from '@/hooks';
import type { ConnectionStatus } from '@/types/websocket';
import { cn } from '@/lib/utils';

interface ConnectionIndicatorProps {
  /**
   * Show detailed status text
   * @default false
   */
  showLabel?: boolean;

  /**
   * Additional CSS classes
   */
  className?: string;
}

const statusConfig: Record<
  ConnectionStatus,
  { color: string; label: string; pulse: boolean }
> = {
  connected: {
    color: 'bg-green-500',
    label: 'Connected',
    pulse: false,
  },
  connecting: {
    color: 'bg-yellow-500',
    label: 'Connecting...',
    pulse: true,
  },
  reconnecting: {
    color: 'bg-yellow-500',
    label: 'Reconnecting...',
    pulse: true,
  },
  disconnected: {
    color: 'bg-gray-400',
    label: 'Disconnected',
    pulse: false,
  },
  error: {
    color: 'bg-red-500',
    label: 'Connection Error',
    pulse: false,
  },
};

export function ConnectionIndicator({
  showLabel = false,
  className,
}: ConnectionIndicatorProps) {
  const { wsStatus, reconnectAttempts } = useRealtimeAll();
  const config = statusConfig[wsStatus];

  return (
    <div
      className={cn('flex items-center gap-2', className)}
      title={`WebSocket: ${config.label}${
        wsStatus === 'reconnecting' ? ` (attempt ${reconnectAttempts})` : ''
      }`}
    >
      <span className="relative flex h-2.5 w-2.5">
        {config.pulse && (
          <span
            className={cn(
              'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
              config.color
            )}
          />
        )}
        <span
          className={cn(
            'relative inline-flex h-2.5 w-2.5 rounded-full',
            config.color
          )}
        />
      </span>
      {showLabel && (
        <span className="text-xs text-muted-foreground">
          {config.label}
          {wsStatus === 'reconnecting' && ` (${reconnectAttempts})`}
        </span>
      )}
    </div>
  );
}

export default ConnectionIndicator;
