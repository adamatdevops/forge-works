/**
 * Auth API Unit Tests
 * ForgeWorks Frontend
 *
 * Tests for token management and API functions
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  clearStoredToken,
  clearStoredUser,
  getStoredToken,
  getStoredUser,
  isAuthenticated,
  login,
  logout,
  register,
  setStoredToken,
  setStoredUser,
} from './auth';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// =============================================================================
// Test Data
// =============================================================================

const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'user' as const,
  is_active: true,
  is_verified: true,
  created_at: '2025-01-01T00:00:00Z',
  last_login: '2025-01-18T00:00:00Z',
};

const mockTokenResponse = {
  access_token: 'mock-access-token',
  token_type: 'Bearer',
  expires_in: 900,
  user: mockUser,
};

// =============================================================================
// Token Management Tests
// =============================================================================

describe('Token Management', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    vi.clearAllMocks();
  });

  describe('getStoredToken', () => {
    it('returns null when no token stored', () => {
      expect(getStoredToken()).toBeNull();
    });

    it('returns stored token', () => {
      mockLocalStorage.setItem('forge_access_token', 'test-token');
      expect(getStoredToken()).toBe('test-token');
    });
  });

  describe('setStoredToken', () => {
    it('stores token in localStorage', () => {
      setStoredToken('new-token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'forge_access_token',
        'new-token'
      );
    });
  });

  describe('clearStoredToken', () => {
    it('removes token from localStorage', () => {
      clearStoredToken();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('forge_access_token');
    });
  });

  describe('getStoredUser', () => {
    it('returns null when no user stored', () => {
      expect(getStoredUser()).toBeNull();
    });

    it('returns parsed user object', () => {
      mockLocalStorage.setItem('forge_user', JSON.stringify(mockUser));
      mockLocalStorage.getItem.mockReturnValueOnce(JSON.stringify(mockUser));
      expect(getStoredUser()).toEqual(mockUser);
    });

    it('returns null for invalid JSON', () => {
      mockLocalStorage.getItem.mockReturnValueOnce('invalid-json');
      expect(getStoredUser()).toBeNull();
    });
  });

  describe('setStoredUser', () => {
    it('stores serialized user in localStorage', () => {
      setStoredUser(mockUser);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'forge_user',
        JSON.stringify(mockUser)
      );
    });
  });

  describe('clearStoredUser', () => {
    it('removes user from localStorage', () => {
      clearStoredUser();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('forge_user');
    });
  });

  describe('isAuthenticated', () => {
    it('returns false when no token', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('returns true when token exists', () => {
      mockLocalStorage.getItem.mockReturnValueOnce('some-token');
      expect(isAuthenticated()).toBe(true);
    });
  });
});

// =============================================================================
// API Function Tests
// =============================================================================

describe('Auth API Functions', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('register', () => {
    it('sends registration request and stores token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTokenResponse,
      });

      const result = await register({
        email: 'new@example.com',
        password: 'SecurePass123',
        full_name: 'New User',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({
            email: 'new@example.com',
            password: 'SecurePass123',
            full_name: 'New User',
          }),
        })
      );

      expect(result).toEqual(mockTokenResponse);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'forge_access_token',
        'mock-access-token'
      );
    });

    it('throws error on registration failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Email already registered' }),
      });

      await expect(
        register({
          email: 'existing@example.com',
          password: 'SecurePass123',
          full_name: 'Existing User',
        })
      ).rejects.toThrow('Email already registered');
    });
  });

  describe('login', () => {
    it('sends login request and stores token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTokenResponse,
      });

      const result = await login({
        email: 'test@example.com',
        password: 'password123',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123',
          }),
        })
      );

      expect(result).toEqual(mockTokenResponse);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'forge_access_token',
        'mock-access-token'
      );
    });

    it('throws error on invalid credentials', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ detail: 'Invalid email or password' }),
      });

      await expect(
        login({
          email: 'test@example.com',
          password: 'wrongpassword',
        })
      ).rejects.toThrow('Invalid email or password');
    });

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        login({
          email: 'test@example.com',
          password: 'password123',
        })
      ).rejects.toThrow('Network error');
    });
  });

  describe('logout', () => {
    it('sends logout request and clears storage', async () => {
      mockLocalStorage.setItem('forge_access_token', 'test-token');
      mockLocalStorage.getItem.mockReturnValue('test-token');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logged out successfully' }),
      });

      const result = await logout();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      );

      expect(result.message).toBe('Logged out successfully');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('forge_access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('forge_user');
    });

    it('clears storage even on API failure', async () => {
      mockLocalStorage.getItem.mockReturnValue('test-token');
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Server error' }),
      });

      // Should clear storage even if API fails
      await expect(logout()).rejects.toThrow();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('forge_access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('forge_user');
    });
  });
});

// =============================================================================
// Error Handling Tests
// =============================================================================

describe('API Error Handling', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockLocalStorage.clear();
    vi.clearAllMocks();
  });

  it('handles 400 Bad Request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'Invalid input data' }),
    });

    await expect(
      login({ email: 'invalid', password: 'short' })
    ).rejects.toThrow('Invalid input data');
  });

  it('handles 401 Unauthorized', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Authentication required' }),
    });

    await expect(
      login({ email: 'test@example.com', password: 'wrong' })
    ).rejects.toThrow('Authentication required');
  });

  it('handles 500 Internal Server Error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({}),
    });

    await expect(
      login({ email: 'test@example.com', password: 'password' })
    ).rejects.toThrow();
  });

  it('handles non-JSON error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => {
        throw new Error('Not JSON');
      },
    });

    await expect(
      login({ email: 'test@example.com', password: 'password' })
    ).rejects.toThrow('API Error: 503 Service Unavailable');
  });
});
