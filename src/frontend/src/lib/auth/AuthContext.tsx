'use client';

/**
 * Authentication Context Provider
 * ForgeWorks Frontend
 *
 * Provides authentication state and methods throughout the app
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import type {
  AuthContextValue,
  AuthState,
  LoginCredentials,
  PasswordChangeData,
  RegisterData,
  User,
  UserUpdateData,
} from '@/types/auth';
import * as authApi from '@/lib/api/auth';

// Initial state
const initialState: AuthState = {
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,
};

// Context
const AuthContext = createContext<AuthContextValue | null>(null);

// Provider props
interface AuthProviderProps {
  children: ReactNode;
}

// Token refresh interval (every 10 minutes for 15-minute tokens)
const TOKEN_REFRESH_INTERVAL = 10 * 60 * 1000;

/**
 * Authentication Provider Component
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>(initialState);

  // Initialize auth state from storage on mount
  useEffect(() => {
    const initializeAuth = () => {
      const storedToken = authApi.getStoredToken();
      const storedUser = authApi.getStoredUser();

      if (storedToken && storedUser) {
        setState({
          user: storedUser,
          accessToken: storedToken,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };

    initializeAuth();
  }, []);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!state.isAuthenticated) return;

    const refreshInterval = setInterval(async () => {
      try {
        const result = await authApi.refreshToken();
        setState((prev) => ({
          ...prev,
          accessToken: result.access_token,
          user: result.user,
        }));
      } catch {
        // If refresh fails, log out
        setState({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    }, TOKEN_REFRESH_INTERVAL);

    return () => clearInterval(refreshInterval);
  }, [state.isAuthenticated]);

  // Login handler
  const login = useCallback(async (credentials: LoginCredentials) => {
    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      const result = await authApi.login(credentials);
      setState({
        user: result.user,
        accessToken: result.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      setState((prev) => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  // Register handler
  const register = useCallback(async (data: RegisterData) => {
    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      const result = await authApi.register(data);
      setState({
        user: result.user,
        accessToken: result.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      setState((prev) => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  // Logout handler
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setState({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  }, []);

  // Refresh token handler
  const refreshToken = useCallback(async () => {
    try {
      const result = await authApi.refreshToken();
      setState((prev) => ({
        ...prev,
        accessToken: result.access_token,
        user: result.user,
      }));
    } catch (error) {
      // If refresh fails, log out
      setState({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
      });
      throw error;
    }
  }, []);

  // Update profile handler
  const updateProfile = useCallback(async (data: UserUpdateData) => {
    const updatedUser = await authApi.updateProfile(data);
    setState((prev) => ({
      ...prev,
      user: updatedUser,
    }));
  }, []);

  // Change password handler
  const changePassword = useCallback(async (data: PasswordChangeData) => {
    await authApi.changePassword(data);
    // Password change logs out all sessions
    setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  }, []);

  // Memoize context value
  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      register,
      logout,
      refreshToken,
      updateProfile,
      changePassword,
    }),
    [state, login, register, logout, refreshToken, updateProfile, changePassword]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

/**
 * Hook to get current user (or null)
 */
export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

/**
 * Hook to check if user is authenticated
 */
export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

/**
 * Hook to check if auth is loading
 */
export function useAuthLoading(): boolean {
  const { isLoading } = useAuth();
  return isLoading;
}

export default AuthProvider;
