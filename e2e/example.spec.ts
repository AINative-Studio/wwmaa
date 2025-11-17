import { test, expect } from '@playwright/test';

/**
 * Example test file demonstrating Playwright test structure
 * This test should always pass and serves as a sanity check
 */

test.describe('Example Tests - Sanity Check', () => {
  test('Playwright is configured correctly', async ({ page }) => {
    // This test verifies that Playwright can navigate and interact with pages
    await page.goto('https://playwright.dev');

    // Check page title
    await expect(page).toHaveTitle(/Playwright/);

    // Check that we can find elements
    const getStarted = page.locator('text=Get started');
    await expect(getStarted).toBeVisible();
  });

  test('Test environment variables work', async () => {
    // Check that we can access environment variables
    const baseUrl = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
    expect(baseUrl).toBeDefined();
    expect(baseUrl).toContain('localhost');
  });

  test('Browser context and page work', async ({ page, context }) => {
    // Verify browser context and page are available
    expect(page).toBeDefined();
    expect(context).toBeDefined();

    // Verify we can navigate
    await page.goto('about:blank');
    expect(page.url()).toBe('about:blank');
  });

  test('Assertions work correctly', async () => {
    // Basic assertion tests
    expect(1 + 1).toBe(2);
    expect('hello').toContain('ell');
    expect([1, 2, 3]).toHaveLength(3);
    expect({ name: 'test' }).toHaveProperty('name');
  });

  test('Async operations work', async ({ page }) => {
    // Test async/await
    await page.goto('about:blank');

    const title = await page.title();
    expect(typeof title).toBe('string');

    await page.waitForTimeout(100);
    expect(true).toBe(true);
  });
});
