/**
 * Login Form Component Tests
 * ForgeWorks Frontend
 *
 * Tests for login form validation and submission
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LoginForm } from './LoginForm';

// Mock the auth hook
const mockLogin = vi.fn();

vi.mock('@/lib/auth', () => ({
  useAuth: () => ({
    login: mockLogin,
    isAuthenticated: false,
    isLoading: false,
    user: null,
  }),
}));

// =============================================================================
// Test Helpers
// =============================================================================

function renderLoginForm(props = {}) {
  const defaultProps = {
    onSuccess: vi.fn(),
    onRegisterClick: vi.fn(),
  };

  return render(<LoginForm {...defaultProps} {...props} />);
}

// =============================================================================
// Rendering Tests
// =============================================================================

describe('LoginForm Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form with all fields', () => {
    renderLoginForm();

    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders register link when onRegisterClick provided', () => {
    renderLoginForm({ onRegisterClick: vi.fn() });

    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create one/i })).toBeInTheDocument();
  });

  it('does not render register link when onRegisterClick not provided', () => {
    renderLoginForm({ onRegisterClick: undefined });

    expect(screen.queryByText(/don't have an account/i)).not.toBeInTheDocument();
  });
});

// =============================================================================
// Input Handling Tests
// =============================================================================

describe('LoginForm Input Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('updates email field on input', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'test@example.com');

    expect(emailInput).toHaveValue('test@example.com');
  });

  it('updates password field on input', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    const passwordInput = screen.getByLabelText(/password/i);
    await user.type(passwordInput, 'mypassword');

    expect(passwordInput).toHaveValue('mypassword');
  });

  it('has correct input types', () => {
    renderLoginForm();

    expect(screen.getByLabelText(/email/i)).toHaveAttribute('type', 'email');
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('type', 'password');
  });

  it('has correct autocomplete attributes', () => {
    renderLoginForm();

    expect(screen.getByLabelText(/email/i)).toHaveAttribute('autocomplete', 'email');
    expect(screen.getByLabelText(/password/i)).toHaveAttribute(
      'autocomplete',
      'current-password'
    );
  });
});

// =============================================================================
// Form Submission Tests
// =============================================================================

describe('LoginForm Submission', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockResolvedValue(undefined);
  });

  it('calls login with credentials on submit', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });

  it('calls onSuccess after successful login', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockLogin.mockResolvedValue(undefined);

    renderLoginForm({ onSuccess });

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    // Make login hang
    mockLogin.mockImplementation(() => new Promise(() => {}));

    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/signing in/i)).toBeInTheDocument();
    });
  });

  it('disables inputs during submission', async () => {
    const user = userEvent.setup();
    mockLogin.mockImplementation(() => new Promise(() => {}));

    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeDisabled();
      expect(screen.getByLabelText(/password/i)).toBeDisabled();
    });
  });

  it('requires email field', () => {
    renderLoginForm();

    expect(screen.getByLabelText(/email/i)).toBeRequired();
  });

  it('requires password field', () => {
    renderLoginForm();

    expect(screen.getByLabelText(/password/i)).toBeRequired();
  });
});

// =============================================================================
// Error Handling Tests
// =============================================================================

describe('LoginForm Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays error message on login failure', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error('Invalid email or password'));

    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });

  it('displays generic error for non-Error exceptions', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue('Some error');

    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/login failed/i)).toBeInTheDocument();
    });
  });

  it('clears error on new submission', async () => {
    const user = userEvent.setup();
    mockLogin
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce(undefined);

    renderLoginForm();

    // First submission - error
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrong');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/first error/i)).toBeInTheDocument();
    });

    // Second submission - clears error
    await user.clear(screen.getByLabelText(/password/i));
    await user.type(screen.getByLabelText(/password/i), 'correct');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.queryByText(/first error/i)).not.toBeInTheDocument();
    });
  });

  it('does not call onSuccess on login failure', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockLogin.mockRejectedValue(new Error('Login failed'));

    renderLoginForm({ onSuccess });

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/login failed/i)).toBeInTheDocument();
    });

    expect(onSuccess).not.toHaveBeenCalled();
  });
});

// =============================================================================
// Navigation Tests
// =============================================================================

describe('LoginForm Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls onRegisterClick when register link clicked', async () => {
    const user = userEvent.setup();
    const onRegisterClick = vi.fn();

    renderLoginForm({ onRegisterClick });

    await user.click(screen.getByRole('button', { name: /create one/i }));

    expect(onRegisterClick).toHaveBeenCalled();
  });
});
