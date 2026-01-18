/**
 * Register Form Component Tests
 * ForgeWorks Frontend
 *
 * Tests for registration form validation and submission
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { RegisterForm } from './RegisterForm';

// Mock the auth hook
const mockRegister = vi.fn();

vi.mock('@/lib/auth', () => ({
  useAuth: () => ({
    register: mockRegister,
    isAuthenticated: false,
    isLoading: false,
    user: null,
  }),
}));

// =============================================================================
// Test Helpers
// =============================================================================

function renderRegisterForm(props = {}) {
  const defaultProps = {
    onSuccess: vi.fn(),
    onLoginClick: vi.fn(),
  };

  return render(<RegisterForm {...defaultProps} {...props} />);
}

// =============================================================================
// Rendering Tests
// =============================================================================

describe('RegisterForm Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders registration form with all fields', () => {
    renderRegisterForm();

    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /create account/i })
    ).toBeInTheDocument();
  });

  it('renders password requirements hint', () => {
    renderRegisterForm();

    expect(
      screen.getByText(/must be 8\+ characters with uppercase, lowercase, and number/i)
    ).toBeInTheDocument();
  });

  it('renders login link when onLoginClick provided', () => {
    renderRegisterForm({ onLoginClick: vi.fn() });

    expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('does not render login link when onLoginClick not provided', () => {
    renderRegisterForm({ onLoginClick: undefined });

    expect(screen.queryByText(/already have an account/i)).not.toBeInTheDocument();
  });
});

// =============================================================================
// Input Handling Tests
// =============================================================================

describe('RegisterForm Input Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('updates all fields on input', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');

    expect(screen.getByLabelText(/full name/i)).toHaveValue('John Doe');
    expect(screen.getByLabelText(/email/i)).toHaveValue('john@example.com');
    expect(screen.getByLabelText(/^password$/i)).toHaveValue('SecurePass123');
    expect(screen.getByLabelText(/confirm password/i)).toHaveValue('SecurePass123');
  });

  it('has correct input types', () => {
    renderRegisterForm();

    expect(screen.getByLabelText(/full name/i)).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('type', 'email');
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText(/confirm password/i)).toHaveAttribute(
      'type',
      'password'
    );
  });

  it('has correct autocomplete attributes', () => {
    renderRegisterForm();

    expect(screen.getByLabelText(/full name/i)).toHaveAttribute('autocomplete', 'name');
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('autocomplete', 'email');
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute(
      'autocomplete',
      'new-password'
    );
    expect(screen.getByLabelText(/confirm password/i)).toHaveAttribute(
      'autocomplete',
      'new-password'
    );
  });
});

// =============================================================================
// Password Validation Tests
// =============================================================================

describe('RegisterForm Password Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows error for password less than 8 characters', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'Short1');
    await user.type(screen.getByLabelText(/confirm password/i), 'Short1');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/password must be at least 8 characters/i)
      ).toBeInTheDocument();
    });

    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows error for password without uppercase', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'lowercase123');
    await user.type(screen.getByLabelText(/confirm password/i), 'lowercase123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/password must contain at least one uppercase letter/i)
      ).toBeInTheDocument();
    });

    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows error for password without lowercase', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'UPPERCASE123');
    await user.type(screen.getByLabelText(/confirm password/i), 'UPPERCASE123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/password must contain at least one lowercase letter/i)
      ).toBeInTheDocument();
    });

    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows error for password without number', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'NoNumbers');
    await user.type(screen.getByLabelText(/confirm password/i), 'NoNumbers');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/password must contain at least one number/i)
      ).toBeInTheDocument();
    });

    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows error when passwords do not match', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'DifferentPass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });

    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('accepts valid password', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValue(undefined);
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalled();
    });
  });
});

// =============================================================================
// Form Submission Tests
// =============================================================================

describe('RegisterForm Submission', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRegister.mockResolvedValue(undefined);
  });

  it('calls register with form data on submit', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'john@example.com',
        password: 'SecurePass123',
        full_name: 'John Doe',
      });
    });
  });

  it('calls onSuccess after successful registration', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    renderRegisterForm({ onSuccess });

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();
    mockRegister.mockImplementation(() => new Promise(() => {}));
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/creating account/i)).toBeInTheDocument();
    });
  });

  it('disables inputs during submission', async () => {
    const user = userEvent.setup();
    mockRegister.mockImplementation(() => new Promise(() => {}));
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/full name/i)).toBeDisabled();
      expect(screen.getByLabelText(/email/i)).toBeDisabled();
      expect(screen.getByLabelText(/^password$/i)).toBeDisabled();
      expect(screen.getByLabelText(/confirm password/i)).toBeDisabled();
    });
  });

  it('requires all fields', () => {
    renderRegisterForm();

    expect(screen.getByLabelText(/full name/i)).toBeRequired();
    expect(screen.getByLabelText(/email/i)).toBeRequired();
    expect(screen.getByLabelText(/^password$/i)).toBeRequired();
    expect(screen.getByLabelText(/confirm password/i)).toBeRequired();
  });
});

// =============================================================================
// Error Handling Tests
// =============================================================================

describe('RegisterForm Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays error message on registration failure', async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue(new Error('Email already registered'));
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'existing@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already registered/i)).toBeInTheDocument();
    });
  });

  it('displays generic error for non-Error exceptions', async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue('Some error');
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
    });
  });

  it('does not call onSuccess on registration failure', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockRegister.mockRejectedValue(new Error('Registration failed'));
    renderRegisterForm({ onSuccess });

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'SecurePass123');
    await user.type(screen.getByLabelText(/confirm password/i), 'SecurePass123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
    });

    expect(onSuccess).not.toHaveBeenCalled();
  });
});

// =============================================================================
// Navigation Tests
// =============================================================================

describe('RegisterForm Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls onLoginClick when login link clicked', async () => {
    const user = userEvent.setup();
    const onLoginClick = vi.fn();
    renderRegisterForm({ onLoginClick });

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(onLoginClick).toHaveBeenCalled();
  });
});
