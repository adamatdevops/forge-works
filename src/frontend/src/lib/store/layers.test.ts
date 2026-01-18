import { describe, it, expect, beforeEach } from 'vitest';
import { useLayerStore } from './layers';

describe('Layers Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useLayerStore.getState().resetLayers();
  });

  describe('initial state', () => {
    it('should have default layers', () => {
      const { layers } = useLayerStore.getState();

      expect(layers).toHaveLength(6);
      expect(layers.map((l) => l.id)).toEqual([
        'services',
        'templates',
        'anomalies',
        'pipeline',
        'metrics',
        'kubernetes',
      ]);
    });

    it('should have services and templates visible by default', () => {
      const { layers } = useLayerStore.getState();

      const services = layers.find((l) => l.id === 'services');
      const templates = layers.find((l) => l.id === 'templates');
      const anomalies = layers.find((l) => l.id === 'anomalies');

      expect(services?.visible).toBe(true);
      expect(templates?.visible).toBe(true);
      expect(anomalies?.visible).toBe(false);
    });

    it('should have no active layer initially', () => {
      const { activeLayerId } = useLayerStore.getState();
      expect(activeLayerId).toBeNull();
    });
  });

  describe('toggleLayer', () => {
    it('should toggle layer visibility', () => {
      const store = useLayerStore.getState();

      // Services is visible by default
      expect(store.layers.find((l) => l.id === 'services')?.visible).toBe(true);

      store.toggleLayer('services');

      // Now it should be hidden
      const updatedLayers = useLayerStore.getState().layers;
      expect(updatedLayers.find((l) => l.id === 'services')?.visible).toBe(false);

      store.toggleLayer('services');

      // Now it should be visible again
      const finalLayers = useLayerStore.getState().layers;
      expect(finalLayers.find((l) => l.id === 'services')?.visible).toBe(true);
    });
  });

  describe('setLayerVisibility', () => {
    it('should set layer visibility to specific value', () => {
      const store = useLayerStore.getState();

      store.setLayerVisibility('anomalies', true);
      expect(useLayerStore.getState().layers.find((l) => l.id === 'anomalies')?.visible).toBe(true);

      store.setLayerVisibility('anomalies', false);
      expect(useLayerStore.getState().layers.find((l) => l.id === 'anomalies')?.visible).toBe(false);
    });
  });

  describe('setActiveLayer', () => {
    it('should set the active layer', () => {
      const store = useLayerStore.getState();

      store.setActiveLayer('services');
      expect(useLayerStore.getState().activeLayerId).toBe('services');

      store.setActiveLayer('templates');
      expect(useLayerStore.getState().activeLayerId).toBe('templates');
    });

    it('should allow clearing active layer', () => {
      const store = useLayerStore.getState();

      store.setActiveLayer('services');
      store.setActiveLayer(null);

      expect(useLayerStore.getState().activeLayerId).toBeNull();
    });
  });

  describe('moveLayer', () => {
    it('should move layer up', () => {
      const store = useLayerStore.getState();

      // Templates is at index 1
      store.moveLayer('templates', 'up');

      const layers = useLayerStore.getState().layers;
      expect(layers[0].id).toBe('templates');
      expect(layers[1].id).toBe('services');
    });

    it('should move layer down', () => {
      const store = useLayerStore.getState();

      // Services is at index 0
      store.moveLayer('services', 'down');

      const layers = useLayerStore.getState().layers;
      expect(layers[0].id).toBe('templates');
      expect(layers[1].id).toBe('services');
    });

    it('should not move first layer up', () => {
      const store = useLayerStore.getState();
      const originalFirst = store.layers[0].id;

      store.moveLayer(originalFirst, 'up');

      expect(useLayerStore.getState().layers[0].id).toBe(originalFirst);
    });

    it('should not move last layer down', () => {
      const store = useLayerStore.getState();
      const originalLast = store.layers[store.layers.length - 1].id;

      store.moveLayer(originalLast, 'down');

      const layers = useLayerStore.getState().layers;
      expect(layers[layers.length - 1].id).toBe(originalLast);
    });

    it('should update zIndex when moving layers', () => {
      const store = useLayerStore.getState();

      store.moveLayer('templates', 'up');

      const layers = useLayerStore.getState().layers;
      // First layer should have highest zIndex
      expect(layers[0].zIndex).toBeGreaterThan(layers[1].zIndex);
    });
  });

  describe('getVisibleLayers', () => {
    it('should return only visible layers', () => {
      const store = useLayerStore.getState();

      const visibleLayers = store.getVisibleLayers();

      expect(visibleLayers.every((l) => l.visible)).toBe(true);
      expect(visibleLayers.length).toBe(2); // services and templates by default
    });
  });

  describe('getLayerByType', () => {
    it('should return layer by type', () => {
      const store = useLayerStore.getState();

      const servicesLayer = store.getLayerByType('services');
      expect(servicesLayer?.id).toBe('services');

      const anomaliesLayer = store.getLayerByType('anomalies');
      expect(anomaliesLayer?.id).toBe('anomalies');
    });

    it('should return undefined for non-existent type', () => {
      const store = useLayerStore.getState();

      const layer = store.getLayerByType('nonexistent' as any);
      expect(layer).toBeUndefined();
    });
  });

  describe('resetLayers', () => {
    it('should reset to default state', () => {
      const store = useLayerStore.getState();

      // Make some changes
      store.toggleLayer('services');
      store.setActiveLayer('templates');
      store.moveLayer('templates', 'up');

      // Reset
      store.resetLayers();

      const state = useLayerStore.getState();
      expect(state.layers.find((l) => l.id === 'services')?.visible).toBe(true);
      expect(state.activeLayerId).toBeNull();
      expect(state.layers[0].id).toBe('services');
    });
  });
});
