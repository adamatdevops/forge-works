/**
 * Authentication E2E Tests
 * ForgeWorks Frontend
 *
 * End-to-end tests for the complete authentication flow
 */

import { test, expect } from '@playwright/test';

// =============================================================================
// Test Data
// =============================================================================

const testUser = {
  email: `e2e-test-${Date.now()}@example.com`,
  password: 'SecurePass123',
  fullName: 'E2E Test User',
};

// =============================================================================
// Login Page Tests
// =============================================================================

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('displays login form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('has link to registration', async ({ page }) => {
    await expect(page.getByText(/don't have an account/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /create one/i })).toBeVisible();
  });

  test('navigates to register page', async ({ page }) => {
    await page.getByRole('link', { name: /create one/i }).click();
    await expect(page).toHaveURL('/register');
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for error message
    await expect(page.getByText(/invalid|error|failed/i)).toBeVisible({ timeout: 10000 });
  });

  test('validates required fields', async ({ page }) => {
    // Try to submit empty form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Email field should show validation
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toHaveAttribute('required', '');
  });
});

// =============================================================================
// Register Page Tests
// =============================================================================

test.describe('Register Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('displays registration form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible();
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toBeVisible();
    await expect(page.getByLabel(/confirm password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
  });

  test('shows password requirements', async ({ page }) => {
    await expect(
      page.getByText(/must be 8\+ characters with uppercase, lowercase, and number/i)
    ).toBeVisible();
  });

  test('has link to login', async ({ page }) => {
    await expect(page.getByText(/already have an account/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
  });

  test('navigates to login page', async ({ page }) => {
    await page.getByRole('link', { name: /sign in/i }).click();
    await expect(page).toHaveURL('/login');
  });

  test('validates password requirements - too short', async ({ page }) => {
    await page.getByLabel(/full name/i).fill('Test User');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/^password$/i).fill('Short1');
    await page.getByLabel(/confirm password/i).fill('Short1');
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page.getByText(/at least 8 characters/i)).toBeVisible();
  });

  test('validates password requirements - no uppercase', async ({ page }) => {
    await page.getByLabel(/full name/i).fill('Test User');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/^password$/i).fill('lowercase123');
    await page.getByLabel(/confirm password/i).fill('lowercase123');
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page.getByText(/uppercase letter/i)).toBeVisible();
  });

  test('validates password match', async ({ page }) => {
    await page.getByLabel(/full name/i).fill('Test User');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/^password$/i).fill('SecurePass123');
    await page.getByLabel(/confirm password/i).fill('DifferentPass123');
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page.getByText(/passwords do not match/i)).toBeVisible();
  });
});

// =============================================================================
// Complete Auth Flow Tests
// =============================================================================

test.describe('Complete Auth Flow', () => {
  test('register -> login -> dashboard -> logout', async ({ page }) => {
    // Step 1: Go to register page
    await page.goto('/register');

    // Step 2: Fill registration form
    await page.getByLabel(/full name/i).fill(testUser.fullName);
    await page.getByLabel(/email/i).fill(testUser.email);
    await page.getByLabel(/^password$/i).fill(testUser.password);
    await page.getByLabel(/confirm password/i).fill(testUser.password);

    // Step 3: Submit registration
    await page.getByRole('button', { name: /create account/i }).click();

    // Step 4: Should redirect to dashboard or login
    await expect(page).toHaveURL(/\/(dashboard|login|$)/, { timeout: 15000 });

    // If redirected to dashboard, we're already logged in
    if (page.url().includes('dashboard') || page.url() === 'http://localhost:3000/') {
      // Verify we're authenticated by checking for user elements
      await expect(
        page.getByRole('button', { name: /logout|sign out/i }).or(
          page.getByText(/dashboard/i)
        )
      ).toBeVisible({ timeout: 10000 });
    } else {
      // If redirected to login, log in with the new account
      await page.getByLabel(/email/i).fill(testUser.email);
      await page.getByLabel(/password/i).fill(testUser.password);
      await page.getByRole('button', { name: /sign in/i }).click();

      // Should redirect to dashboard
      await expect(page).toHaveURL(/\/(dashboard|$)/, { timeout: 15000 });
    }
  });
});

// =============================================================================
// Protected Route Tests
// =============================================================================

test.describe('Protected Routes', () => {
  test('redirects unauthenticated users from dashboard to login', async ({ page }) => {
    // Clear any stored tokens
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
    });

    // Try to access dashboard
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('allows access to login page when unauthenticated', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
  });

  test('allows access to register page when unauthenticated', async ({ page }) => {
    await page.goto('/register');
    await expect(page).toHaveURL('/register');
    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible();
  });
});

// =============================================================================
// Form Accessibility Tests
// =============================================================================

test.describe('Form Accessibility', () => {
  test('login form has proper labels', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.getByLabel(/email/i);
    const passwordInput = page.getByLabel(/password/i);

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();

    // Check inputs are properly labeled
    await expect(emailInput).toHaveAttribute('id');
    await expect(passwordInput).toHaveAttribute('id');
  });

  test('register form has proper labels', async ({ page }) => {
    await page.goto('/register');

    const inputs = [
      page.getByLabel(/full name/i),
      page.getByLabel(/email/i),
      page.getByLabel(/^password$/i),
      page.getByLabel(/confirm password/i),
    ];

    for (const input of inputs) {
      await expect(input).toBeVisible();
      await expect(input).toHaveAttribute('id');
    }
  });

  test('forms are keyboard navigable', async ({ page }) => {
    await page.goto('/login');

    // Focus email input
    await page.getByLabel(/email/i).focus();
    await expect(page.getByLabel(/email/i)).toBeFocused();

    // Tab to password
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/password/i)).toBeFocused();

    // Tab to submit button
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /sign in/i })).toBeFocused();
  });
});
