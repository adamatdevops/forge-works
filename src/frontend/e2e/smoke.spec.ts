/**
 * Smoke Tests
 * ForgeWorks Frontend
 *
 * Quick sanity checks to verify critical paths work after deployment
 * These tests should complete in under 30 seconds total
 */

import { test, expect } from '@playwright/test';

// =============================================================================
// Health Check Tests
// =============================================================================

test.describe('Health Checks', () => {
  test('backend API is healthy', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.app_name).toBe('ForgeWorks');
  });

  test('frontend loads successfully', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.ok()).toBeTruthy();
  });

  test('login page loads', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();
  });

  test('register page loads', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible();
  });
});

// =============================================================================
// API Endpoint Smoke Tests
// =============================================================================

test.describe('API Endpoints', () => {
  test('services endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/services');
    // May return 200 (with data) or 401 (if auth required)
    expect([200, 401]).toContain(response.status());
  });

  test('templates endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/templates');
    expect([200, 401]).toContain(response.status());
  });

  test('ML recommend endpoint responds', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/ml/recommend', {
      data: {
        workload_type: 'api',
        language: 'python',
      },
    });
    expect([200, 401, 422]).toContain(response.status());
  });

  test('detailed health endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health/detailed');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.components).toBeDefined();
  });
});

// =============================================================================
// Critical UI Flows
// =============================================================================

test.describe('Critical UI Flows', () => {
  test('can navigate between login and register', async ({ page }) => {
    await page.goto('/login');

    // Navigate to register
    await page.getByRole('link', { name: /create one/i }).click();
    await expect(page).toHaveURL('/register');

    // Navigate back to login
    await page.getByRole('link', { name: /sign in/i }).click();
    await expect(page).toHaveURL('/login');
  });

  test('form inputs are interactive', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.getByLabel(/email/i);
    const passwordInput = page.getByLabel(/password/i);

    // Type in inputs
    await emailInput.fill('test@example.com');
    await passwordInput.fill('password123');

    // Verify values
    await expect(emailInput).toHaveValue('test@example.com');
    await expect(passwordInput).toHaveValue('password123');
  });

  test('submit button is clickable', async ({ page }) => {
    await page.goto('/login');

    const submitButton = page.getByRole('button', { name: /sign in/i });
    await expect(submitButton).toBeEnabled();

    // Click should not throw
    await submitButton.click();
  });
});

// =============================================================================
// Performance Smoke Tests
// =============================================================================

test.describe('Performance', () => {
  test('login page loads in under 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/login');
    await page.getByRole('heading', { name: /welcome back/i }).waitFor();
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('register page loads in under 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/register');
    await page.getByRole('heading', { name: /create account/i }).waitFor();
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('API health check responds in under 1 second', async ({ request }) => {
    const startTime = Date.now();
    await request.get('http://localhost:8000/health');
    const responseTime = Date.now() - startTime;

    expect(responseTime).toBeLessThan(1000);
  });
});

// =============================================================================
// Error Handling Smoke Tests
// =============================================================================

test.describe('Error Handling', () => {
  test('404 page for unknown routes', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist-12345');

    // Should either show 404 or redirect
    // Next.js may return 200 with 404 content or actual 404
    expect(response?.status()).toBeLessThan(500);
  });

  test('API returns proper error for invalid endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/nonexistent');
    expect(response.status()).toBe(404);
  });
});
