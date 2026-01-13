import { describe, it, expect, beforeEach } from 'vitest';
import { useGlueStore } from './glue';

describe('GlueBus Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useGlueStore.getState().clearAll();
  });

  describe('publish', () => {
    it('should publish a value to the store', () => {
      const store = useGlueStore.getState();

      store.publish('service_id', 'service-123', 'services');

      const value = store.get('service_id');
      expect(value).toBeDefined();
      expect(value?.value).toBe('service-123');
      expect(value?.source).toBe('services');
      expect(value?.key).toBe('service_id');
    });

    it('should overwrite existing value for same key', () => {
      const store = useGlueStore.getState();

      store.publish('service_id', 'service-1', 'services');
      store.publish('service_id', 'service-2', 'services');

      const value = store.get('service_id');
      expect(value?.value).toBe('service-2');
    });

    it('should add to history', () => {
      const store = useGlueStore.getState();

      store.publish('service_id', 'service-1', 'services');
      store.publish('template_id', 'template-1', 'templates');

      // Get fresh state after mutations
      const updatedState = useGlueStore.getState();
      expect(updatedState.history).toHaveLength(2);
    });

    it('should keep only last 100 entries in history', () => {
      const store = useGlueStore.getState();

      // Publish 105 values
      for (let i = 0; i < 105; i++) {
        store.publish('service_id', `service-${i}`, 'services');
      }

      expect(store.history.length).toBeLessThanOrEqual(100);
    });
  });

  describe('clear', () => {
    it('should clear a specific key', () => {
      const store = useGlueStore.getState();

      store.publish('service_id', 'service-123', 'services');
      store.publish('template_id', 'template-456', 'templates');

      store.clear('service_id');

      expect(store.get('service_id')).toBeUndefined();
      expect(store.get('template_id')).toBeDefined();
    });
  });

  describe('clearAll', () => {
    it('should clear all values and history', () => {
      const store = useGlueStore.getState();

      store.publish('service_id', 'service-123', 'services');
      store.publish('template_id', 'template-456', 'templates');

      store.clearAll();

      expect(store.values).toEqual({});
      expect(store.history).toEqual([]);
    });
  });

  describe('getBySource', () => {
    it('should return all values from a specific source', () => {
      const store = useGlueStore.getState();

      store.publish('service_id', 'service-123', 'services');
      store.publish('template_id', 'template-456', 'templates');
      store.publish('commit_sha', 'abc123', 'pipeline');

      const servicesValues = store.getBySource('services');
      expect(servicesValues).toHaveLength(1);
      expect(servicesValues[0].value).toBe('service-123');

      const templatesValues = store.getBySource('templates');
      expect(templatesValues).toHaveLength(1);
      expect(templatesValues[0].value).toBe('template-456');
    });
  });
});
