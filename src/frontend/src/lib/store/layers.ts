/**
 * Layers Store
 * Zustand store for managing layer visibility and ordering
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Layer, LayerType } from '@/types';

// Default layers configuration
const defaultLayers: Layer[] = [
  {
    id: 'services',
    name: 'Services',
    type: 'services',
    visible: true,
    collapsed: false,
    zIndex: 5,
    apiEndpoint: '/api/v1/services',
    glueKeys: ['service_id'],
    subscriptions: [],
  },
  {
    id: 'templates',
    name: 'Templates',
    type: 'templates',
    visible: true,
    collapsed: false,
    zIndex: 4,
    apiEndpoint: '/api/v1/templates',
    glueKeys: ['template_id'],
    subscriptions: ['service_id'],
  },
  {
    id: 'anomalies',
    name: 'Anomalies',
    type: 'anomalies',
    visible: false,
    collapsed: false,
    zIndex: 3,
    glueKeys: ['anomaly_id'],
    subscriptions: ['service_id'],
  },
  {
    id: 'pipeline',
    name: 'Pipeline',
    type: 'pipeline',
    visible: false,
    collapsed: false,
    zIndex: 2,
    glueKeys: ['commit_sha', 'release_version'],
    subscriptions: ['service_id'],
  },
  {
    id: 'metrics',
    name: 'Metrics',
    type: 'metrics',
    visible: false,
    collapsed: false,
    zIndex: 1,
    glueKeys: [],
    subscriptions: ['service_id'],
  },
];

interface LayerStore {
  layers: Layer[];
  activeLayerId: string | null;

  // Actions
  setLayerVisibility: (id: string, visible: boolean) => void;
  toggleLayer: (id: string) => void;
  setLayerCollapsed: (id: string, collapsed: boolean) => void;
  setLayerOrder: (layers: Layer[]) => void;
  moveLayer: (id: string, direction: 'up' | 'down') => void;
  setActiveLayer: (id: string | null) => void;
  resetLayers: () => void;

  // Selectors
  getVisibleLayers: () => Layer[];
  getLayerByType: (type: LayerType) => Layer | undefined;
}

export const useLayerStore = create<LayerStore>()(
  persist(
    (set, get) => ({
      layers: defaultLayers,
      activeLayerId: null,

      setLayerVisibility: (id, visible) =>
        set((state) => ({
          layers: state.layers.map((layer) =>
            layer.id === id ? { ...layer, visible } : layer
          ),
        })),

      toggleLayer: (id) =>
        set((state) => ({
          layers: state.layers.map((layer) =>
            layer.id === id ? { ...layer, visible: !layer.visible } : layer
          ),
        })),

      setLayerCollapsed: (id, collapsed) =>
        set((state) => ({
          layers: state.layers.map((layer) =>
            layer.id === id ? { ...layer, collapsed } : layer
          ),
        })),

      setLayerOrder: (layers) => set({ layers }),

      moveLayer: (id, direction) =>
        set((state) => {
          const index = state.layers.findIndex((l) => l.id === id);
          if (index === -1) return state;

          const newIndex = direction === 'up' ? index - 1 : index + 1;
          if (newIndex < 0 || newIndex >= state.layers.length) return state;

          const newLayers = [...state.layers];
          [newLayers[index], newLayers[newIndex]] = [newLayers[newIndex], newLayers[index]];

          // Update zIndex based on new positions
          return {
            layers: newLayers.map((layer, i) => ({
              ...layer,
              zIndex: newLayers.length - i,
            })),
          };
        }),

      setActiveLayer: (id) => set({ activeLayerId: id }),

      resetLayers: () => set({ layers: defaultLayers, activeLayerId: null }),

      getVisibleLayers: () => get().layers.filter((l) => l.visible),

      getLayerByType: (type) => get().layers.find((l) => l.type === type),
    }),
    {
      name: 'forge-works-layers',
      partialize: (state) => ({
        layers: state.layers.map(({ id, visible, collapsed, zIndex }) => ({
          id,
          visible,
          collapsed,
          zIndex,
        })),
      }),
    }
  )
);

export default useLayerStore;
