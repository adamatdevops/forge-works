/**
 * Auth Context Unit Tests
 * ForgeWorks Frontend
 *
 * Tests for AuthProvider and auth hooks
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

import {
  AuthProvider,
  useAuth,
  useAuthLoading,
  useIsAuthenticated,
  useUser,
} from './AuthContext';

// Mock the auth API module
vi.mock('@/lib/api/auth', () => ({
  getStoredToken: vi.fn(),
  getStoredUser: vi.fn(),
  setStoredToken: vi.fn(),
  setStoredUser: vi.fn(),
  clearStoredToken: vi.fn(),
  clearStoredUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  updateProfile: vi.fn(),
  changePassword: vi.fn(),
}));

import * as authApi from '@/lib/api/auth';

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
// Test Wrapper
// =============================================================================

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

// =============================================================================
// useAuth Hook Tests
// =============================================================================

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(authApi.getStoredToken).mockReturnValue(null);
    vi.mocked(authApi.getStoredUser).mockReturnValue(null);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('throws error when used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });

  it('initializes with unauthenticated state when no stored token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
  });

  it('initializes with authenticated state when token exists', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue('stored-token');
    vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.accessToken).toBe('stored-token');
  });

  describe('login', () => {
    it('updates state on successful login', async () => {
      vi.mocked(authApi.login).mockResolvedValue(mockTokenResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.accessToken).toBe('mock-access-token');
    });

    it('throws and maintains state on login failure', async () => {
      const loginError = new Error('Invalid credentials');
      vi.mocked(authApi.login).mockRejectedValue(loginError);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.login({
            email: 'test@example.com',
            password: 'wrongpassword',
          });
        })
      ).rejects.toThrow('Invalid credentials');

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('register', () => {
    it('updates state on successful registration', async () => {
      vi.mocked(authApi.register).mockResolvedValue(mockTokenResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.register({
          email: 'new@example.com',
          password: 'SecurePass123',
          full_name: 'New User',
        });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('throws on registration failure', async () => {
      vi.mocked(authApi.register).mockRejectedValue(
        new Error('Email already exists')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.register({
            email: 'existing@example.com',
            password: 'SecurePass123',
            full_name: 'Existing User',
          });
        })
      ).rejects.toThrow('Email already exists');
    });
  });

  describe('logout', () => {
    it('clears state on logout', async () => {
      vi.mocked(authApi.getStoredToken).mockReturnValue('stored-token');
      vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);
      vi.mocked(authApi.logout).mockResolvedValue({ message: 'Logged out' });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.accessToken).toBeNull();
    });

    it('clears state even on API failure', async () => {
      vi.mocked(authApi.getStoredToken).mockReturnValue('stored-token');
      vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);
      vi.mocked(authApi.logout).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Logout should clear state even if API fails
      // The implementation uses try/finally so state is always cleared
      await act(async () => {
        try {
          await result.current.logout();
        } catch {
          // Expected to throw, ignore
        }
      });

      // State should still be cleared
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('updateProfile', () => {
    it('updates user data on success', async () => {
      vi.mocked(authApi.getStoredToken).mockReturnValue('stored-token');
      vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);

      const updatedUser = { ...mockUser, full_name: 'Updated Name' };
      vi.mocked(authApi.updateProfile).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await result.current.updateProfile({ full_name: 'Updated Name' });
      });

      expect(result.current.user?.full_name).toBe('Updated Name');
    });
  });

  describe('changePassword', () => {
    it('logs out user after password change', async () => {
      vi.mocked(authApi.getStoredToken).mockReturnValue('stored-token');
      vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);
      vi.mocked(authApi.changePassword).mockResolvedValue({
        message: 'Password changed',
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await result.current.changePassword({
          current_password: 'oldpass',
          new_password: 'NewPass123',
        });
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });
});

// =============================================================================
// Convenience Hook Tests
// =============================================================================

describe('useUser', () => {
  it('returns null when not authenticated', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue(null);
    vi.mocked(authApi.getStoredUser).mockReturnValue(null);

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBeNull();
    });
  });

  it('returns user when authenticated', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue('token');
    vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);

    const { result } = renderHook(() => useUser(), { wrapper });

    await waitFor(() => {
      expect(result.current).toEqual(mockUser);
    });
  });
});

describe('useIsAuthenticated', () => {
  it('returns false when not authenticated', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue(null);
    vi.mocked(authApi.getStoredUser).mockReturnValue(null);

    const { result } = renderHook(() => useIsAuthenticated(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('returns true when authenticated', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue('token');
    vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);

    const { result } = renderHook(() => useIsAuthenticated(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });
});

describe('useAuthLoading', () => {
  it('returns false after initialization completes', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue(null);
    vi.mocked(authApi.getStoredUser).mockReturnValue(null);

    const { result } = renderHook(() => useAuthLoading(), { wrapper });

    // After initialization, loading should be false
    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('returns false when authenticated', async () => {
    vi.mocked(authApi.getStoredToken).mockReturnValue('token');
    vi.mocked(authApi.getStoredUser).mockReturnValue(mockUser);

    const { result } = renderHook(() => useAuthLoading(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });
});
