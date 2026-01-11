'use client';

/**
 * ForgeWorks Dashboard
 * Main entry point with Layers Architecture
 */

import { Hammer } from 'lucide-react';
import { LayerPanel, LayerRenderer, ServiceDetailSidebar } from '@/components/layers';

export default function Dashboard() {
  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Hammer className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">ForgeWorks</h1>
          <span className="text-sm text-muted-foreground">Internal Developer Platform</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Layers Architecture Demo</span>
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
