import { Page } from '@playwright/test';

/**
 * Test user credentials for different roles
 */
export const testUsers = {
  admin: {
    email: 'admin@wwmaa.com',
    password: 'AdminPass123!',
    firstName: 'Admin',
    lastName: 'User',
  },
  member: {
    email: 'member@wwmaa.com',
    password: 'MemberPass123!',
    firstName: 'Member',
    lastName: 'User',
  },
  instructor: {
    email: 'instructor@wwmaa.com',
    password: 'InstructorPass123!',
    firstName: 'Instructor',
    lastName: 'User',
  },
  new: {
    email: `testuser+${Date.now()}@example.com`,
    password: 'TestPass123!',
    firstName: 'Test',
    lastName: 'User',
  },
};

/**
 * Test membership application data
 */
export const testMembershipApplication = {
  firstName: 'John',
  lastName: 'Doe',
  email: `john.doe+${Date.now()}@example.com`,
  phone: '555-0123-4567',
  tier: 'professional',
  discipline: 'Karate',
  experience: '5 years of training',
  goals: 'Improve skills and teach others',
};

/**
 * Test event data
 */
export const testEvent = {
  title: 'Test Training Session',
  description: 'A test training session for E2E testing',
  date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  location: 'Main Dojo',
};

/**
 * Helper function to login a user
 *
 * This function handles the complete login flow including:
 * - Navigating to login page and waiting for it to load
 * - Filling login form
 * - Submitting credentials
 * - Waiting for authentication API response
 * - Waiting for navigation to complete (handles multi-step redirects)
 *
 * @throws Error if login fails (shows on login page, has error message, or times out)
 */
export async function login(page: Page, email: string, password: string) {
  // Navigate to login page and wait for it to fully load
  await page.goto('/login', { waitUntil: 'networkidle' });

  // Wait for login form to be visible and ready
  await page.waitForSelector('input[name="email"], input[type="email"]', { state: 'visible', timeout: 10000 });
  await page.waitForSelector('input[name="password"], input[type="password"]', { state: 'visible', timeout: 10000 });
  await page.waitForSelector('button[type="submit"]', { state: 'visible', timeout: 10000 });

  // Fill form fields
  await page.fill('input[name="email"], input[type="email"]', email);
  await page.fill('input[name="password"], input[type="password"]', password);

  // Wait for login API response before checking navigation
  const responsePromise = page.waitForResponse(
    response => response.url().includes('/api/auth/login') || response.url().includes('/login'),
    { timeout: 15000 }
  ).catch(() => null); // Don't fail if no API call detected

  // Submit the form
  await page.click('button[type="submit"]');

  // Wait for API response
  const response = await responsePromise;

  // Check for error messages on page (indicates login failed)
  const errorVisible = await page.locator('text=/invalid.*email.*password|authentication.*failed|incorrect|login.*failed/i')
    .isVisible({ timeout: 2000 })
    .catch(() => false);

  if (errorVisible) {
    throw new Error('Login failed: Invalid credentials or authentication error displayed');
  }

  // Wait for navigation away from login page - increased timeout to 30s to handle:
  // 1. Login API call to backend
  // 2. Redirect to /dashboard
  // 3. Role-based redirect to /dashboard/admin, /dashboard/student, or /dashboard/instructor
  // 4. Production environment latency
  try {
    await page.waitForURL(
      url => !url.pathname.includes('/login') && !url.pathname.includes('/auth'),
      { timeout: 30000 }
    );
  } catch (error) {
    // Provide helpful error message with current URL
    const currentUrl = page.url();
    throw new Error(
      `Login timeout: Still on ${currentUrl} after 30s. ` +
      `This usually means:\n` +
      `  1. Backend is not running or not accessible\n` +
      `  2. Test credentials don't exist in database\n` +
      `  3. Login API is failing\n` +
      `API Response status: ${response?.status() || 'none'}`
    );
  }
}

/**
 * Helper function to logout a user
 */
export async function logout(page: Page) {
  // Try common logout button selectors
  const logoutSelectors = [
    'button:has-text("Logout")',
    'button:has-text("Log out")',
    'button:has-text("Sign out")',
    'a:has-text("Logout")',
    'a:has-text("Log out")',
    '[data-testid="logout-button"]',
  ];

  for (const selector of logoutSelectors) {
    try {
      const element = page.locator(selector).first();
      if (await element.isVisible({ timeout: 2000 })) {
        await element.click();
        await page.waitForURL('/', { timeout: 5000 });
        return;
      }
    } catch (e) {
      // Continue to next selector
    }
  }

  // If no logout button found, just navigate to home
  await page.goto('/');
}

/**
 * Helper function to wait for API response
 */
export async function waitForAPI(page: Page, url: string | RegExp) {
  return await page.waitForResponse(
    response => {
      if (typeof url === 'string') {
        return response.url().includes(url);
      }
      return url.test(response.url());
    },
    { timeout: 10000 }
  );
}

/**
 * Helper function to check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  try {
    // Check for common authenticated indicators
    const indicators = [
      'text=Dashboard',
      'text=Profile',
      'text=Logout',
      '[data-testid="user-menu"]',
    ];

    for (const indicator of indicators) {
      if (await page.locator(indicator).isVisible({ timeout: 2000 })) {
        return true;
      }
    }
    return false;
  } catch (e) {
    return false;
  }
}

/**
 * Helper function to fill form fields by label
 */
export async function fillFormByLabel(
  page: Page,
  label: string,
  value: string
) {
  const input = page.locator(`label:has-text("${label}") + input, label:has-text("${label}") input`).first();
  await input.fill(value);
}

/**
 * Helper function to wait for toast/notification
 */
export async function waitForToast(page: Page, message: string) {
  const toastSelectors = [
    `[role="status"]:has-text("${message}")`,
    `[role="alert"]:has-text("${message}")`,
    `.toast:has-text("${message}")`,
    `[data-testid="toast"]:has-text("${message}")`,
  ];

  for (const selector of toastSelectors) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      return;
    } catch (e) {
      // Continue to next selector
    }
  }
}

/**
 * Helper function to clear browser storage
 */
export async function clearStorage(page: Page) {
  await page.context().clearCookies();

  // Navigate to the base URL first to ensure we can access storage
  // Try-catch in case we're on a page without storage access
  try {
    await page.evaluate(() => {
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (e) {
        // Ignore storage access errors - may be on about:blank
      }
    });
  } catch (e) {
    // Ignore if we can't access storage APIs
  }
}
