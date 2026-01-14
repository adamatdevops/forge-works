/**
 * Authentication Module Exports
 * ForgeWorks Frontend
 */

// Context and Provider
export {
  AuthProvider,
  useAuth,
  useUser,
  useIsAuthenticated,
  useAuthLoading,
} from './AuthContext';

// Re-export types for convenience
export type {
  User,
  UserRole,
  AuthState,
  AuthContextValue,
  LoginCredentials,
  RegisterData,
  PasswordChangeData,
  UserUpdateData,
  TokenResponse,
  MessageResponse,
} from '@/types/auth';
