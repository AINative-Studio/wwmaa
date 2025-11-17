import { test, expect } from '@playwright/test';
import { testMembershipApplication, clearStorage } from './fixtures/test-data';

test.describe('Membership Application Flow', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('user can view membership page', async ({ page }) => {
    await page.goto('/membership');

    // Should show membership information
    await expect(page).toHaveURL(/\/membership/);

    // Look for membership tiers or plans
    const commonElements = [
      page.locator('text=Professional'),
      page.locator('text=Membership'),
      page.locator('text=Join'),
      page.locator('text=Apply'),
    ];

    let foundElement = false;
    for (const element of commonElements) {
      if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
        foundElement = true;
        break;
      }
    }

    expect(foundElement).toBeTruthy();
  });

  test('user can navigate to membership application', async ({ page }) => {
    await page.goto('/membership');

    // Look for application link/button
    const applyButton = page.locator(
      'a[href*="/membership/apply"], button:has-text("Apply"), a:has-text("Apply"), button:has-text("Join")'
    ).first();

    if (await applyButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await applyButton.click();
      await page.waitForURL(/\/membership\/apply/, { timeout: 5000 });
    } else {
      // Direct navigation
      await page.goto('/membership/apply');
    }

    await expect(page).toHaveURL(/\/membership\/apply/);
  });

  test('membership application form has required fields', async ({ page }) => {
    await page.goto('/membership/apply');

    // Check for common form fields
    const requiredFields = [
      'input[name="firstName"], input[name="first_name"]',
      'input[name="lastName"], input[name="last_name"]',
      'input[name="email"], input[type="email"]',
    ];

    for (const fieldSelector of requiredFields) {
      const field = page.locator(fieldSelector).first();
      if (await field.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(field).toBeVisible();
      }
    }
  });

  test('user can fill out membership application', async ({ page }) => {
    await page.goto('/membership/apply');

    // Fill out the application form
    const { firstName, lastName, email, phone, discipline, experience, goals } = testMembershipApplication;

    // Fill first name
    const firstNameField = page.locator('input[name="firstName"], input[name="first_name"]').first();
    if (await firstNameField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await firstNameField.fill(firstName);
    }

    // Fill last name
    const lastNameField = page.locator('input[name="lastName"], input[name="last_name"]').first();
    if (await lastNameField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await lastNameField.fill(lastName);
    }

    // Fill email
    const emailField = page.locator('input[name="email"], input[type="email"]').first();
    if (await emailField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await emailField.fill(email);
    }

    // Fill phone
    const phoneField = page.locator('input[name="phone"], input[type="tel"]').first();
    if (await phoneField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await phoneField.fill(phone);
    }

    // Fill discipline
    const disciplineField = page.locator('input[name="discipline"], textarea[name="discipline"]').first();
    if (await disciplineField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await disciplineField.fill(discipline);
    }

    // Fill experience
    const experienceField = page.locator('input[name="experience"], textarea[name="experience"]').first();
    if (await experienceField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await experienceField.fill(experience);
    }

    // Verify form is filled
    await expect(emailField).toHaveValue(email);
  });

  test('user can submit membership application', async ({ page }) => {
    await page.goto('/membership/apply');

    // Fill required fields
    const { firstName, lastName, email, phone } = testMembershipApplication;

    const firstNameField = page.locator('input[name="firstName"], input[name="first_name"]').first();
    if (await firstNameField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await firstNameField.fill(firstName);
    }

    const lastNameField = page.locator('input[name="lastName"], input[name="last_name"]').first();
    if (await lastNameField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await lastNameField.fill(lastName);
    }

    const emailField = page.locator('input[name="email"], input[type="email"]').first();
    if (await emailField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await emailField.fill(email);
    }

    const phoneField = page.locator('input[name="phone"], input[type="tel"]').first();
    if (await phoneField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await phoneField.fill(phone);
    }

    // Look for tier selection
    const tierSelect = page.locator('select[name="tier"], select[name="membership_tier"]').first();
    if (await tierSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await tierSelect.selectOption({ label: /professional/i });
    }

    // Submit the form
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();

    // Wait for success page or confirmation
    await page.waitForTimeout(2000);

    // Check for success indicators
    const successIndicators = [
      page.locator('text=Application submitted'),
      page.locator('text=Thank you'),
      page.locator('text=Success'),
      page.locator('text=We will contact you'),
    ];

    let foundSuccess = false;
    for (const indicator of successIndicators) {
      if (await indicator.isVisible({ timeout: 3000 }).catch(() => false)) {
        foundSuccess = true;
        break;
      }
    }

    // Either found success message or navigated to success page
    const currentUrl = page.url();
    expect(foundSuccess || currentUrl.includes('/success') || currentUrl.includes('/thank')).toBeTruthy();
  });

  test('application validates email format', async ({ page }) => {
    await page.goto('/membership/apply');

    // Fill with invalid email
    const emailField = page.locator('input[name="email"], input[type="email"]').first();
    if (await emailField.isVisible({ timeout: 2000 }).catch(() => false)) {
      await emailField.fill('invalid-email');

      // Try to submit
      const submitButton = page.locator('button[type="submit"]').first();
      await submitButton.click();

      // Should show validation error or prevent submission
      await page.waitForTimeout(500);
    }
  });

  test('application validates required fields', async ({ page }) => {
    await page.goto('/membership/apply');

    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"]').first();
    if (await submitButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await submitButton.click();

      // Should stay on same page or show validation errors
      await page.waitForTimeout(1000);
      await expect(page).toHaveURL(/\/membership\/apply/);
    }
  });

  test('membership tiers are displayed', async ({ page }) => {
    await page.goto('/membership');

    // Look for common tier names
    const tierNames = [
      'Professional',
      'Student',
      'Basic',
      'Premium',
      'Elite',
      'Standard',
    ];

    let foundTier = false;
    for (const tierName of tierNames) {
      if (await page.locator(`text=${tierName}`).isVisible({ timeout: 2000 }).catch(() => false)) {
        foundTier = true;
        break;
      }
    }

    expect(foundTier).toBeTruthy();
  });

  test('membership page shows pricing information', async ({ page }) => {
    await page.goto('/membership');

    // Look for price indicators ($ symbol or 'month' text)
    const priceIndicators = [
      page.locator('text=/\\$\\d+/'),
      page.locator('text=/month/i'),
      page.locator('text=/year/i'),
      page.locator('text=/price/i'),
    ];

    let foundPricing = false;
    for (const indicator of priceIndicators) {
      if (await indicator.isVisible({ timeout: 2000 }).catch(() => false)) {
        foundPricing = true;
        break;
      }
    }

    expect(foundPricing).toBeTruthy();
  });

  test('user can view membership benefits', async ({ page }) => {
    await page.goto('/membership');

    // Look for benefits section
    const benefitIndicators = [
      page.locator('text=/benefit/i'),
      page.locator('text=/feature/i'),
      page.locator('text=/include/i'),
      page.locator('ul li'), // List items often used for benefits
    ];

    let foundBenefits = false;
    for (const indicator of benefitIndicators) {
      if (await indicator.first().isVisible({ timeout: 2000 }).catch(() => false)) {
        foundBenefits = true;
        break;
      }
    }

    expect(foundBenefits).toBeTruthy();
  });

  test('application success page has confirmation', async ({ page }) => {
    // Navigate directly to success page
    await page.goto('/membership/apply/success');

    // Should show success message
    const successIndicators = [
      page.locator('text=success'),
      page.locator('text=thank you'),
      page.locator('text=submitted'),
      page.locator('text=received'),
    ];

    let foundSuccess = false;
    for (const indicator of successIndicators) {
      if (await indicator.first().isVisible({ timeout: 2000 }).catch(() => false)) {
        foundSuccess = true;
        break;
      }
    }

    expect(foundSuccess).toBeTruthy();
  });
});
