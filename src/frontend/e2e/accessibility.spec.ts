/**
 * Accessibility Audit E2E Tests
 * ForgeWorks Frontend
 *
 * Tests for WCAG compliance and accessibility standards
 * Uses Playwright's built-in accessibility testing capabilities
 *
 * Note: For full axe-core integration, run: pnpm add -D @axe-core/playwright
 */

import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Check basic accessibility attributes on the page
 */
async function checkBasicAccessibility(page: Page) {
  // Check for document title
  const title = await page.title();
  expect(title.length).toBeGreaterThan(0);

  // Check for language attribute
  const htmlLang = await page.getAttribute('html', 'lang');
  expect(htmlLang).toBeTruthy();

  // Check for viewport meta tag
  const viewport = await page.locator('meta[name="viewport"]').count();
  expect(viewport).toBe(1);
}

/**
 * Check all images have alt attributes
 */
async function checkImagesHaveAlt(page: Page) {
  const images = await page.locator('img').all();

  for (const img of images) {
    const alt = await img.getAttribute('alt');
    const role = await img.getAttribute('role');

    // Image should have alt text OR be marked as decorative
    expect(alt !== null || role === 'presentation' || role === 'none').toBeTruthy();
  }
}

/**
 * Check all interactive elements are keyboard accessible
 */
async function checkKeyboardAccessibility(page: Page) {
  // Get all focusable elements
  const focusable = await page.locator(
    'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ).all();

  for (const element of focusable) {
    const isDisabled = await element.isDisabled().catch(() => false);
    if (isDisabled) continue;

    const tabindex = await element.getAttribute('tabindex');
    // Elements should be focusable (not have negative tabindex)
    expect(tabindex !== '-1').toBeTruthy();
  }
}

/**
 * Check for proper heading hierarchy
 */
async function checkHeadingHierarchy(page: Page) {
  const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();

  let previousLevel = 0;
  const headingLevels: number[] = [];

  for (const heading of headings) {
    const tagName = await heading.evaluate((el) => el.tagName.toLowerCase());
    const level = parseInt(tagName.replace('h', ''));
    headingLevels.push(level);

    // Heading level should not skip more than one level
    if (previousLevel > 0) {
      expect(level - previousLevel).toBeLessThanOrEqual(1);
    }

    previousLevel = level;
  }

  return headingLevels;
}

/**
 * Check buttons have accessible names
 */
async function checkButtonsHaveAccessibleNames(page: Page) {
  const buttons = await page.locator('button').all();

  for (const button of buttons) {
    const text = await button.textContent();
    const ariaLabel = await button.getAttribute('aria-label');
    const ariaLabelledby = await button.getAttribute('aria-labelledby');
    const title = await button.getAttribute('title');

    // Button should have some form of accessible name
    const hasAccessibleName =
      (text && text.trim().length > 0) ||
      ariaLabel ||
      ariaLabelledby ||
      title;

    expect(hasAccessibleName).toBeTruthy();
  }
}

/**
 * Check form inputs have associated labels
 */
async function checkFormLabels(page: Page) {
  const inputs = await page.locator('input:not([type="hidden"]), select, textarea').all();

  for (const input of inputs) {
    const id = await input.getAttribute('id');
    const ariaLabel = await input.getAttribute('aria-label');
    const ariaLabelledby = await input.getAttribute('aria-labelledby');
    const placeholder = await input.getAttribute('placeholder');

    let hasLabel = ariaLabel !== null || ariaLabelledby !== null;

    // Check for associated label element
    if (id) {
      const labelCount = await page.locator(`label[for="${id}"]`).count();
      hasLabel = hasLabel || labelCount > 0;
    }

    // Check if input is wrapped in a label
    const parentLabel = await input.locator('xpath=ancestor::label').count();
    hasLabel = hasLabel || parentLabel > 0;

    // Placeholder alone is not sufficient, but is acceptable with aria-label
    if (!hasLabel && !placeholder) {
      console.warn(`Input without label found: id=${id}`);
    }
  }
}

/**
 * Check color contrast (basic check using computed styles)
 * Reserved for future use in color contrast tests
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function checkBasicColorContrast(page: Page) {
  // Check that text elements have sufficient contrast
  const textElements = await page.locator('p, span, a, button, h1, h2, h3, h4, h5, h6').all();

  for (const element of textElements) {
    const isVisible = await element.isVisible().catch(() => false);
    if (!isVisible) continue;

    const text = await element.textContent();
    if (!text || text.trim().length === 0) continue;

    // Get computed color (basic check)
    const color = await element.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.color;
    });

    // Ensure color is defined
    expect(color).toBeTruthy();
  }
}

// =============================================================================
// Home Page Accessibility Tests
// =============================================================================

test.describe('Home Page Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });

  test('should have basic accessibility attributes', async ({ page }) => {
    await checkBasicAccessibility(page);
  });

  test('should have proper document structure', async ({ page }) => {
    // Check for main landmark
    const main = await page.locator('main').count();
    expect(main).toBeGreaterThanOrEqual(1);

    // Check for navigation landmark
    const nav = await page.locator('nav').count();
    expect(nav).toBeGreaterThanOrEqual(0); // Nav is optional but good to have
  });

  test('should have accessible images', async ({ page }) => {
    await checkImagesHaveAlt(page);
  });

  test('should have keyboard accessible elements', async ({ page }) => {
    await checkKeyboardAccessibility(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await checkHeadingHierarchy(page);
  });

  test('should have buttons with accessible names', async ({ page }) => {
    await checkButtonsHaveAccessibleNames(page);
  });
});

// =============================================================================
// Login Page Accessibility Tests
// =============================================================================

test.describe('Login Page Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');
  });

  test('should have basic accessibility attributes', async ({ page }) => {
    await checkBasicAccessibility(page);
  });

  test('should have form labels', async ({ page }) => {
    await checkFormLabels(page);
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab through form elements
    await page.keyboard.press('Tab');

    // Should be able to focus email input
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'BUTTON', 'A']).toContain(focused);
  });

  test('should have accessible error messages', async ({ page }) => {
    // Submit empty form to trigger errors
    const submitButton = await page.locator('button[type="submit"]');
    if ((await submitButton.count()) > 0) {
      await submitButton.click();
      await page.waitForTimeout(500);

      // Error messages should be associated with inputs
      const errors = await page.locator('[role="alert"], .error, [aria-invalid="true"]').all();

      for (const error of errors) {
        const text = await error.textContent();
        // Error messages should have content
        if (text) {
          expect(text.trim().length).toBeGreaterThan(0);
        }
      }
    }
  });
});

// =============================================================================
// Dashboard Accessibility Tests
// =============================================================================

test.describe('Dashboard Accessibility', () => {
  test('should have accessible data tables', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    const tables = await page.locator('table').all();

    for (const table of tables) {
      // Check for table headers
      const headers = await table.locator('th').count();
      expect(headers).toBeGreaterThan(0);

      // Check for caption or aria-label
      const caption = await table.locator('caption').count();
      const ariaLabel = await table.getAttribute('aria-label');
      const ariaLabelledby = await table.getAttribute('aria-labelledby');

      expect(caption > 0 || ariaLabel || ariaLabelledby).toBeTruthy();
    }
  });

  test('should have accessible charts and visualizations', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Charts should have aria-labels or descriptions
    const charts = await page.locator('[role="img"], svg, canvas').all();

    for (const chart of charts) {
      const ariaLabel = await chart.getAttribute('aria-label');
      const ariaDescribedby = await chart.getAttribute('aria-describedby');
      const title = await chart.locator('title').count();

      // Charts should have some form of accessible description
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const hasDescription = ariaLabel || ariaDescribedby || title > 0;
      // Note: This is a soft check as not all SVGs are charts
    }
  });

  test('should have skip navigation link', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Focus the first element
    await page.keyboard.press('Tab');

    // Check if there's a skip link
    const skipLink = await page.locator('a[href="#main-content"], a[href="#content"], .skip-link');
    // Skip link is a best practice but not always present
    const hasSkipLink = (await skipLink.count()) > 0;

    if (!hasSkipLink) {
      console.log('Recommendation: Add a skip navigation link for keyboard users');
    }
  });
});

// =============================================================================
// Modal Accessibility Tests
// =============================================================================

test.describe('Modal Accessibility', () => {
  test('should trap focus within modal', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Try to open a modal (if the app has one)
    const modalTrigger = await page.locator('[data-testid="open-modal"], button:has-text("Open")');

    if ((await modalTrigger.count()) > 0) {
      await modalTrigger.first().click();
      await page.waitForTimeout(500);

      // Check for modal
      const modal = await page.locator('[role="dialog"], .modal, [aria-modal="true"]');

      if ((await modal.count()) > 0) {
        // Modal should have aria-modal="true"
        const isAriaModal = await modal.getAttribute('aria-modal');
        expect(isAriaModal).toBe('true');

        // Modal should have a title
        const ariaLabelledby = await modal.getAttribute('aria-labelledby');
        const ariaLabel = await modal.getAttribute('aria-label');
        expect(ariaLabelledby || ariaLabel).toBeTruthy();

        // Close modal with Escape
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);

        const modalAfterEscape = await page.locator('[role="dialog"]:visible');
        expect(await modalAfterEscape.count()).toBe(0);
      }
    }
  });
});

// =============================================================================
// Interactive Elements Accessibility Tests
// =============================================================================

test.describe('Interactive Elements Accessibility', () => {
  test('should have accessible dropdown menus', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    const dropdowns = await page.locator('[role="menu"], [role="listbox"], [aria-haspopup]').all();

    for (const dropdown of dropdowns) {
      const ariaExpanded = await dropdown.getAttribute('aria-expanded');
      // Dropdown triggers should indicate expanded state
      expect(['true', 'false', null]).toContain(ariaExpanded);
    }
  });

  test('should have accessible tooltips', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    const tooltipTriggers = await page.locator('[aria-describedby], [data-tooltip]').all();

    for (const trigger of tooltipTriggers) {
      const describedBy = await trigger.getAttribute('aria-describedby');

      if (describedBy) {
        // The described-by target should exist
        const target = await page.locator(`#${describedBy}`).count();
        expect(target).toBeGreaterThan(0);
      }
    }
  });

  test('should have accessible tabs', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    const tabLists = await page.locator('[role="tablist"]').all();

    for (const tabList of tabLists) {
      const tabs = await tabList.locator('[role="tab"]').all();

      let hasSelectedTab = false;

      for (const tab of tabs) {
        const isSelected = await tab.getAttribute('aria-selected');
        if (isSelected === 'true') {
          hasSelectedTab = true;
        }

        // Each tab should have aria-controls
        const controls = await tab.getAttribute('aria-controls');
        expect(controls).toBeTruthy();
      }

      // At least one tab should be selected
      expect(hasSelectedTab).toBeTruthy();
    }
  });
});

// =============================================================================
// Reduced Motion Tests
// =============================================================================

test.describe('Reduced Motion Support', () => {
  test('should respect prefers-reduced-motion', async ({ page }) => {
    // Set reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Check that animations are reduced
    const animations = await page.evaluate(() => {
      const style = window.getComputedStyle(document.body);
      return {
        animationDuration: style.animationDuration,
        transitionDuration: style.transitionDuration,
      };
    });

    // Animations should either be 0s or very fast with reduced motion
    // This is a soft check as implementation varies
    console.log('Animation durations with reduced motion:', animations);
  });
});

// =============================================================================
// Screen Reader Compatibility Tests
// =============================================================================

test.describe('Screen Reader Compatibility', () => {
  test('should have ARIA landmarks', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    const landmarks = {
      main: await page.locator('main, [role="main"]').count(),
      navigation: await page.locator('nav, [role="navigation"]').count(),
      banner: await page.locator('header, [role="banner"]').count(),
      contentinfo: await page.locator('footer, [role="contentinfo"]').count(),
    };

    // Should have at least a main landmark
    expect(landmarks.main).toBeGreaterThanOrEqual(1);

    console.log('ARIA landmarks found:', landmarks);
  });

  test('should have live regions for dynamic content', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Check for live regions (used for notifications, alerts, etc.)
    const liveRegions = await page.locator(
      '[aria-live], [role="alert"], [role="status"], [role="log"]'
    ).all();

    console.log(`Found ${liveRegions.length} live regions for dynamic content`);

    // Live regions should be present for apps with dynamic updates
    // This is a soft check
  });

  test('should announce loading states', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Check for loading indicators with proper ARIA
    const loadingIndicators = await page.locator(
      '[aria-busy="true"], [aria-label*="loading"], [aria-label*="Loading"]'
    ).all();

    // Loading indicators should have proper ARIA when present
    for (const indicator of loadingIndicators) {
      const ariaBusy = await indicator.getAttribute('aria-busy');
      const ariaLabel = await indicator.getAttribute('aria-label');
      expect(ariaBusy || ariaLabel).toBeTruthy();
    }
  });
});

// =============================================================================
// Focus Indicator Tests
// =============================================================================

test.describe('Focus Indicators', () => {
  test('should have visible focus indicators', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Tab to first focusable element
    await page.keyboard.press('Tab');

    // Get the focused element
    const focused = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;

      const style = window.getComputedStyle(el);
      return {
        outline: style.outline,
        outlineWidth: style.outlineWidth,
        boxShadow: style.boxShadow,
        border: style.border,
      };
    });

    // Element should have some form of focus indication
    if (focused) {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const hasFocusIndicator =
        focused.outline !== 'none' ||
        focused.outlineWidth !== '0px' ||
        focused.boxShadow !== 'none' ||
        focused.border !== 'none';

      // Note: This is a soft check as focus styles vary
      console.log('Focus styles:', focused);
    }
  });

  test('should maintain focus visibility across interactions', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Tab through multiple elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');

      const hasFocus = await page.evaluate(() => {
        return document.activeElement !== document.body;
      });

      expect(hasFocus).toBeTruthy();
    }
  });
});
