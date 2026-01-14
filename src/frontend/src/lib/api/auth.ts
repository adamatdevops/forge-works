/**
 * Authentication API Functions
 * ForgeWorks Frontend
 */

import type {
  LoginCredentials,
  MessageResponse,
  PasswordChangeData,
  RegisterData,
  TokenResponse,
  User,
  UserUpdateData,
} from '@/types/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const AUTH_ENDPOINT = `${API_BASE_URL}/api/v1/auth`;

// Storage keys
const ACCESS_TOKEN_KEY = 'forge_access_token';
const USER_KEY = 'forge_user';

// =============================================================================
// Token Management
// =============================================================================

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(USER_KEY);
}

// =============================================================================
// API Request Helpers
// =============================================================================

interface ApiError extends Error {
  status: number;
  detail: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: Partial<ApiError> = new Error();
    error.status = response.status;

    try {
      const data = await response.json();
      error.detail = data.detail || response.statusText;
      error.message = data.detail || `API Error: ${response.status}`;
    } catch {
      error.detail = response.statusText;
      error.message = `API Error: ${response.status} ${response.statusText}`;
    }

    throw error as ApiError;
  }

  return response.json();
}

function authHeaders(includeToken = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (includeToken) {
    const token = getStoredToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

// =============================================================================
// Auth API Functions
// =============================================================================

/**
 * Register a new user account
 */
export async function register(data: RegisterData): Promise<TokenResponse> {
  const response = await fetch(`${AUTH_ENDPOINT}/register`, {
    method: 'POST',
    headers: authHeaders(false),
    credentials: 'include', // For refresh token cookie
    body: JSON.stringify(data),
  });

  const result = await handleResponse<TokenResponse>(response);

  // Store token and user
  setStoredToken(result.access_token);
  setStoredUser(result.user);

  return result;
}

/**
 * Login with email and password
 */
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await fetch(`${AUTH_ENDPOINT}/login`, {
    method: 'POST',
    headers: authHeaders(false),
    credentials: 'include', // For refresh token cookie
    body: JSON.stringify(credentials),
  });

  const result = await handleResponse<TokenResponse>(response);

  // Store token and user
  setStoredToken(result.access_token);
  setStoredUser(result.user);

  return result;
}

/**
 * Refresh access token using stored refresh token
 */
export async function refreshToken(token?: string): Promise<TokenResponse> {
  const response = await fetch(`${AUTH_ENDPOINT}/refresh`, {
    method: 'POST',
    headers: authHeaders(false),
    credentials: 'include', // Include refresh token cookie
    body: token ? JSON.stringify({ refresh_token: token }) : undefined,
  });

  const result = await handleResponse<TokenResponse>(response);

  // Store new token and user
  setStoredToken(result.access_token);
  setStoredUser(result.user);

  return result;
}

/**
 * Logout and revoke all tokens
 */
export async function logout(): Promise<MessageResponse> {
  try {
    const response = await fetch(`${AUTH_ENDPOINT}/logout`, {
      method: 'POST',
      headers: authHeaders(true),
      credentials: 'include',
    });

    return await handleResponse<MessageResponse>(response);
  } finally {
    // Always clear local storage even if API call fails
    clearStoredToken();
    clearStoredUser();
  }
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
  const response = await fetch(`${AUTH_ENDPOINT}/me`, {
    method: 'GET',
    headers: authHeaders(true),
  });

  const user = await handleResponse<User>(response);
  setStoredUser(user);

  return user;
}

/**
 * Update user profile
 */
export async function updateProfile(data: UserUpdateData): Promise<User> {
  const response = await fetch(`${AUTH_ENDPOINT}/me`, {
    method: 'PATCH',
    headers: authHeaders(true),
    body: JSON.stringify(data),
  });

  const user = await handleResponse<User>(response);
  setStoredUser(user);

  return user;
}

/**
 * Change password
 */
export async function changePassword(data: PasswordChangeData): Promise<MessageResponse> {
  const response = await fetch(`${AUTH_ENDPOINT}/change-password`, {
    method: 'POST',
    headers: authHeaders(true),
    body: JSON.stringify(data),
  });

  const result = await handleResponse<MessageResponse>(response);

  // Password change invalidates all sessions, clear stored data
  clearStoredToken();
  clearStoredUser();

  return result;
}

/**
 * Check if user is authenticated (has valid stored token)
 */
export function isAuthenticated(): boolean {
  return !!getStoredToken();
}
