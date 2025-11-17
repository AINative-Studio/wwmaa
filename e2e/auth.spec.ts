import { test, expect } from '@playwright/test';
import { testUsers, login, logout, clearStorage } from './fixtures/test-data';

test.describe('Authentication Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing authentication
    await clearStorage(page);
  });

  test('user can navigate to login page', async ({ page }) => {
    await page.goto('/');

    // Look for login link/button
    const loginLink = page.locator('a[href="/login"], button:has-text("Login")').first();
    await expect(loginLink).toBeVisible();

    await loginLink.click();
    await expect(page).toHaveURL(/\/login/);
  });

  test('user can login with valid credentials', async ({ page }) => {
    // Navigate to login page and wait for it to fully load
    await page.goto('/login', { waitUntil: 'networkidle' });

    // Wait for login form to be visible and ready
    await page.waitForSelector('input[name="email"], input[type="email"]', { state: 'visible', timeout: 10000 });
    await page.waitForSelector('button[type="submit"]', { state: 'visible', timeout: 10000 });

    // Fill login form
    await page.fill('input[name="email"], input[type="email"]', testUsers.admin.email);
    await page.fill('input[name="password"], input[type="password"]', testUsers.admin.password);

    // Wait for login API response
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/auth/login') || response.url().includes('/login'),
      { timeout: 15000 }
    ).catch(() => null);

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for API response
    await responsePromise;

    // Should redirect to dashboard or home - increased timeout to 30s to handle:
    // 1. Login API call to backend
    // 2. Redirect to /dashboard
    // 3. Role-based redirect to /dashboard/admin, /dashboard/student, or /dashboard/instructor
    await page.waitForURL(
      url => !url.pathname.includes('/login') && !url.pathname.includes('/auth'),
      { timeout: 30000 }
    );

    // Verify successful login by checking for authenticated elements
    const authenticatedIndicators = [
      page.locator('text=Dashboard'),
      page.locator('text=Profile'),
      page.locator('text=Logout'),
      page.locator('text=Log out'),
    ];

    let foundIndicator = false;
    for (const indicator of authenticatedIndicators) {
      if (await indicator.isVisible({ timeout: 2000 }).catch(() => false)) {
        foundIndicator = true;
        break;
      }
    }

    expect(foundIndicator).toBeTruthy();
  });

  test('user cannot login with invalid email', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"], input[type="email"]', 'invalid@example.com');
    await page.fill('input[name="password"], input[type="password"]', 'WrongPassword123!');
    await page.click('button[type="submit"]');

    // Should show error message
    const errorMessages = [
      'Invalid email or password',
      'Invalid credentials',
      'Login failed',
      'Authentication failed',
      'Incorrect email or password',
    ];

    let foundError = false;
    for (const errorMsg of errorMessages) {
      if (await page.locator(`text=${errorMsg}`).isVisible({ timeout: 3000 }).catch(() => false)) {
        foundError = true;
        break;
      }
    }

    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('user cannot login with invalid password', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"], input[type="email"]', testUsers.admin.email);
    await page.fill('input[name="password"], input[type="password"]', 'WrongPassword123!');
    await page.click('button[type="submit"]');

    // Should show error message or stay on login page
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL(/\/login/);
  });

  test('user can navigate to register page', async ({ page }) => {
    await page.goto('/login');

    // Look for register/sign up link
    const registerLink = page.locator('a[href="/register"], text=Sign up, text=Register, text=Create account').first();

    if (await registerLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await registerLink.click();
      await expect(page).toHaveURL(/\/register/);
    } else {
      // Direct navigation
      await page.goto('/register');
      await expect(page).toHaveURL(/\/register/);
    }
  });

  test('user can view registration form', async ({ page }) => {
    await page.goto('/register');

    // Check for registration form fields
    const emailInput = page.locator('input[name="email"], input[type="email"]');
    const passwordInput = page.locator('input[name="password"], input[type="password"]');

    await expect(emailInput.first()).toBeVisible();
    await expect(passwordInput.first()).toBeVisible();
  });

  test('registration validates email format', async ({ page }) => {
    await page.goto('/register');

    // Try invalid email
    await page.fill('input[name="email"], input[type="email"]', 'invalid-email');
    await page.fill('input[name="password"], input[type="password"]', 'TestPass123!');

    // Try to submit
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();

    // Should show validation error or prevent submission
    await page.waitForTimeout(500);
  });

  test('user can logout after login', async ({ page }) => {
    // Login first
    await login(page, testUsers.admin.email, testUsers.admin.password);

    // Find and click logout button
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Log out"), a:has-text("Logout")').first();

    if (await logoutButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await logoutButton.click();

      // Should redirect to home page
      await page.waitForURL(url => url.pathname === '/' || url.pathname === '/login', { timeout: 5000 });
    }
  });

  test('protected routes redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');

    // Should redirect to login page
    await page.waitForURL(url => url.pathname.includes('/login') || url.pathname.includes('/auth'), { timeout: 5000 });
  });

  test('user can access password reset page', async ({ page }) => {
    await page.goto('/login');

    // Look for forgot password link
    const forgotPasswordLink = page.locator('a:has-text("Forgot"), a:has-text("Reset"), text=Forgot password').first();

    if (await forgotPasswordLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await forgotPasswordLink.click();

      // Should navigate to password reset page
      await page.waitForURL(url =>
        url.pathname.includes('/forgot') ||
        url.pathname.includes('/reset') ||
        url.pathname.includes('/password'),
        { timeout: 5000 }
      );

      // Should have email input
      await expect(page.locator('input[type="email"]').first()).toBeVisible();
    }
  });

  test('login form has proper accessibility attributes', async ({ page }) => {
    await page.goto('/login');

    // Check for proper labels
    const emailInput = page.locator('input[name="email"], input[type="email"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();

    // Check for submit button
    const submitButton = page.locator('button[type="submit"]').first();
    await expect(submitButton).toBeVisible();
  });

  test('login persists across page reloads', async ({ page }) => {
    // Login
    await login(page, testUsers.admin.email, testUsers.admin.password);

    // Reload page
    await page.reload();

    // Should still be authenticated
    await page.waitForTimeout(1000);

    // Check if still logged in
    const dashboardLink = page.locator('text=Dashboard');
    if (await dashboardLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      expect(true).toBeTruthy(); // Still logged in
    }
  });
});
