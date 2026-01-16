'use client';

/**
 * ForgeWorks Dashboard
 * Main entry point with Layers Architecture
 * Includes real-time WebSocket integration
 */

import { useRouter } from 'next/navigation';
import { Hammer } from 'lucide-react';
import { LayerPanel, LayerRenderer, ServiceDetailSidebar } from '@/components/layers';
import { ConnectionIndicator } from '@/components/ui/ConnectionIndicator';
import { AuthButton } from '@/components/auth';
import { useRealtimeAll, useEventToasts } from '@/hooks';

export default function Dashboard() {
  const router = useRouter();

  // Real-time updates via WebSocket (subscribes to all channels)
  const { wsStatus, reconnectAttempts } = useRealtimeAll();

  // Enable toast notifications for critical WebSocket events
  useEventToasts({
    showAnomalies: true,
    showPipelines: true,
    soundEnabled: true,
  });

  const handleLoginClick = () => {
    router.push('/login');
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Hammer className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">ForgeWorks</h1>
          <span className="text-sm text-muted-foreground">Internal Developer Platform</span>
        </div>
        <div className="flex items-center gap-4">
          <ConnectionIndicator
            status={wsStatus}
            reconnectAttempts={reconnectAttempts}
          />
          <div className="h-6 w-px bg-border" />
          <AuthButton onLoginClick={handleLoginClick} />
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Layer Panel - Figma-like sidebar */}
        <LayerPanel />

        {/* Layer Content - Rendered layers */}
        <LayerRenderer />

        {/* Service Detail Sidebar - Shows when service selected */}
        <ServiceDetailSidebar />
      </div>
    </div>
  );
}
