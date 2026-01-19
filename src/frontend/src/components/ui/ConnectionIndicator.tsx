'use client';

/**
 * Connection Indicator Component
 * Shows WebSocket connection status with visual feedback
 */

import { Radio, Wifi, WifiOff } from 'lucide-react';

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { ConnectionStatus } from '@/types/websocket';

interface ConnectionIndicatorProps {
  status: ConnectionStatus;
  reconnectAttempts?: number;
  className?: string;
}

const STATUS_CONFIG: Record<
  ConnectionStatus,
  { color: string; bgColor: string; label: string; icon: React.ElementType }
> = {
  connected: {
    color: 'text-green-500',
    bgColor: 'bg-green-500',
    label: 'Connected',
    icon: Wifi,
  },
  connecting: {
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500',
    label: 'Connecting...',
    icon: Radio,
  },
  disconnected: {
    color: 'text-gray-400',
    bgColor: 'bg-gray-400',
    label: 'Disconnected',
    icon: WifiOff,
  },
  reconnecting: {
    color: 'text-orange-500',
    bgColor: 'bg-orange-500',
    label: 'Reconnecting...',
    icon: Radio,
  },
  error: {
    color: 'text-red-500',
    bgColor: 'bg-red-500',
    label: 'Connection Error',
    icon: WifiOff,
  },
};

export function ConnectionIndicator({
  status,
  reconnectAttempts = 0,
  className = '',
}: ConnectionIndicatorProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  // Derive animation state directly from status (no effect needed)
  const isAnimating = status === 'reconnecting' || status === 'connecting';

  const tooltipContent = (
    <div className="text-sm">
      <div className="font-medium">{config.label}</div>
      {reconnectAttempts > 0 && (
        <div className="text-xs text-muted-foreground">
          Attempt {reconnectAttempts} of 5
        </div>
      )}
      {status === 'connected' && (
        <div className="text-xs text-muted-foreground">
          Real-time updates active
        </div>
      )}
    </div>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full
              text-xs font-medium transition-all ${className}`}
          >
            <span className="relative flex h-2 w-2">
              <span
                className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${config.bgColor} ${
                  isAnimating ? 'animate-ping' : ''
                }`}
              />
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${config.bgColor}`}
              />
            </span>
            <Icon className={`h-3.5 w-3.5 ${config.color}`} />
            <span className={`hidden sm:inline ${config.color}`}>
              {status === 'reconnecting'
                ? `Retry ${reconnectAttempts}`
                : config.label}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom">{tooltipContent}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Compact version for use in tight spaces
 */
export function ConnectionDot({
  status,
  className = '',
}: {
  status: ConnectionStatus;
  className?: string;
}) {
  const config = STATUS_CONFIG[status];
  const isAnimating = status === 'reconnecting' || status === 'connecting';

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={`relative flex h-2.5 w-2.5 ${className}`}>
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${config.bgColor} ${
                isAnimating ? 'animate-ping' : ''
              }`}
            />
            <span
              className={`relative inline-flex h-2.5 w-2.5 rounded-full ${config.bgColor}`}
            />
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <span className="text-xs">{config.label}</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default ConnectionIndicator;
