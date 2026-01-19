/**
 * GlueBus Store
 * Zustand store for cross-layer communication
 * The "Glue" represents connection points between layers
 */

import { create } from 'zustand';
import type { GlueKey, GlueValue, LayerType } from '@/types';

interface GlueStore {
  // State
  values: Record<GlueKey, GlueValue>;
  history: GlueValue[];

  // Actions
  publish: (key: GlueKey, value: string | number | null, source: LayerType) => void;
  clear: (key?: GlueKey) => void;
  clearAll: () => void;

  // Selectors
  get: (key: GlueKey) => GlueValue | undefined;
  getBySource: (source: LayerType) => GlueValue[];
}

export const useGlueStore = create<GlueStore>((set, get) => ({
  values: {} as Record<GlueKey, GlueValue>,
  history: [],

  publish: (key, value, source) => {
    const glueValue: GlueValue = {
      key,
      value,
      source,
      timestamp: Date.now(),
    };

    set((state) => ({
      values: {
        ...state.values,
        [key]: glueValue,
      },
      history: [...state.history.slice(-99), glueValue], // Keep last 100 entries
    }));
  },

  clear: (key) => {
    if (key) {
      set((state) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { [key]: _, ...rest } = state.values;
        return { values: rest as Record<GlueKey, GlueValue> };
      });
    }
  },

  clearAll: () => set({ values: {} as Record<GlueKey, GlueValue>, history: [] }),

  get: (key) => get().values[key],

  getBySource: (source) =>
    Object.values(get().values).filter((v) => v.source === source),
}));

/**
 * Custom hook for subscribing to a specific glue value
 */
export function useGlueValue(key: GlueKey): GlueValue | undefined {
  return useGlueStore((state) => state.values[key]);
}

/**
 * Custom hook for publishing glue values
 */
export function useGluePublish() {
  return useGlueStore((state) => state.publish);
}

/**
 * Custom hook for getting the selected service
 */
export function useSelectedService(): string | null {
  const serviceGlue = useGlueStore((state) => state.values.service_id);
  return serviceGlue?.value as string | null;
}

/**
 * Custom hook for getting the selected template
 */
export function useSelectedTemplate(): string | null {
  const templateGlue = useGlueStore((state) => state.values.template_id);
  return templateGlue?.value as string | null;
}

export default useGlueStore;
