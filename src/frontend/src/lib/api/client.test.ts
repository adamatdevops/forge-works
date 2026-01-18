/**
 * API Client Unit Tests
 * ForgeWorks Frontend
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { apiClient } from './client';

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  // =============================================================================
  // GET Method Tests
  // =============================================================================

  describe('get', () => {
    it('should make GET request to correct URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' }),
      });

      await apiClient.get('/api/v1/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should append query params to URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' }),
      });

      await apiClient.get('/api/v1/test', {
        params: { page: 1, limit: 10, active: true },
      });

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toContain('page=1');
      expect(calledUrl).toContain('limit=10');
      expect(calledUrl).toContain('active=true');
    });

    it('should return parsed JSON response', async () => {
      const mockData = { items: [{ id: 1 }, { id: 2 }] };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const result = await apiClient.get('/api/v1/test');

      expect(result).toEqual(mockData);
    });

    it('should throw error on non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(apiClient.get('/api/v1/test')).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });

    it('should accept custom headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await apiClient.get('/api/v1/test', {
        headers: { Authorization: 'Bearer token123' },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            Authorization: 'Bearer token123',
          }),
        })
      );
    });
  });

  // =============================================================================
  // POST Method Tests
  // =============================================================================

  describe('post', () => {
    it('should make POST request with JSON body', async () => {
      const requestData = { name: 'test', value: 123 };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, ...requestData }),
      });

      await apiClient.post('/api/v1/test', requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(requestData),
        })
      );
    });

    it('should handle POST without body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      await apiClient.post('/api/v1/test');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      );
    });

    it('should return parsed JSON response', async () => {
      const mockResponse = { id: 1, created: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await apiClient.post('/api/v1/test', {});

      expect(result).toEqual(mockResponse);
    });

    it('should throw error on 400 Bad Request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
      });

      await expect(apiClient.post('/api/v1/test', {})).rejects.toThrow(
        'API Error: 400 Bad Request'
      );
    });

    it('should throw error on 500 Internal Server Error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(apiClient.post('/api/v1/test', {})).rejects.toThrow(
        'API Error: 500 Internal Server Error'
      );
    });
  });

  // =============================================================================
  // PUT Method Tests
  // =============================================================================

  describe('put', () => {
    it('should make PUT request with JSON body', async () => {
      const updateData = { name: 'updated' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1, ...updateData }),
      });

      await apiClient.put('/api/v1/test/1', updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
    });

    it('should handle PUT without body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ updated: true }),
      });

      await apiClient.put('/api/v1/test/1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'PUT',
          body: undefined,
        })
      );
    });

    it('should throw error on 404 Not Found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(apiClient.put('/api/v1/test/999', {})).rejects.toThrow(
        'API Error: 404 Not Found'
      );
    });
  });

  // =============================================================================
  // DELETE Method Tests
  // =============================================================================

  describe('delete', () => {
    it('should make DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ deleted: true }),
      });

      await apiClient.delete('/api/v1/test/1');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/test/1',
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should throw error on 403 Forbidden', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
      });

      await expect(apiClient.delete('/api/v1/test/1')).rejects.toThrow(
        'API Error: 403 Forbidden'
      );
    });
  });

  // =============================================================================
  // URL Building Tests
  // =============================================================================

  describe('URL building', () => {
    it('should handle empty params object', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await apiClient.get('/api/v1/test', { params: {} });

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toBe('http://localhost:8000/api/v1/test');
    });

    it('should encode special characters in params', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await apiClient.get('/api/v1/test', {
        params: { query: 'hello world' },
      });

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toContain('query=hello+world');
    });

    it('should handle boolean params correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      await apiClient.get('/api/v1/test', {
        params: { active: false },
      });

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toContain('active=false');
    });
  });

  // =============================================================================
  // Error Handling Tests
  // =============================================================================

  describe('error handling', () => {
    it('should throw on network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.get('/api/v1/test')).rejects.toThrow('Network error');
    });

    it('should throw on 401 Unauthorized', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
      });

      await expect(apiClient.get('/api/v1/test')).rejects.toThrow(
        'API Error: 401 Unauthorized'
      );
    });

    it('should throw on 503 Service Unavailable', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
      });

      await expect(apiClient.get('/api/v1/test')).rejects.toThrow(
        'API Error: 503 Service Unavailable'
      );
    });
  });
});
