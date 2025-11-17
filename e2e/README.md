# End-to-End Testing with Playwright

This directory contains comprehensive E2E tests for the WWMAA application using Playwright.

## Directory Structure

```
e2e/
├── README.md              # This file
├── fixtures/
│   └── test-data.ts      # Shared test data and helper functions
├── auth.spec.ts          # Authentication flow tests
├── membership.spec.ts    # Membership application tests
├── events.spec.ts        # Event management tests
├── search.spec.ts        # Search functionality tests
└── admin.spec.ts         # Admin dashboard tests
```

## Prerequisites

- Node.js 18 or higher
- npm or yarn package manager
- Playwright browsers installed

## Installation

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install --with-deps
```

Or install specific browsers:
```bash
npx playwright install chromium
npx playwright install firefox
npx playwright install webkit
```

## Running Tests

### Run all tests
```bash
npm run test:e2e
```

### Run tests with UI mode (recommended for development)
```bash
npm run test:e2e:ui
```

### Run tests in headed mode (see the browser)
```bash
npm run test:e2e:headed
```

### Run tests in debug mode
```bash
npm run test:e2e:debug
```

### Run tests for specific browser
```bash
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit
```

### Run specific test file
```bash
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/membership.spec.ts
```

### Run tests matching a pattern
```bash
npx playwright test -g "login"
npx playwright test -g "admin"
```

### View test report
```bash
npm run test:e2e:report
```

## Test Coverage

### Authentication Tests (`auth.spec.ts`)
- Navigate to login page
- Login with valid credentials
- Login with invalid credentials
- Navigate to register page
- View registration form
- Email validation
- Logout functionality
- Protected route redirection
- Password reset flow
- Accessibility attributes
- Session persistence

### Membership Tests (`membership.spec.ts`)
- View membership page
- Navigate to application form
- Required form fields
- Fill out application
- Submit application
- Email validation
- Required field validation
- Display membership tiers
- Show pricing information
- View membership benefits
- Application success confirmation

### Events Tests (`events.spec.ts`)
- View events page
- Display event list/calendar
- View event details
- Show event information
- RSVP options for logged-in users
- RSVP to events
- Login prompt for non-authenticated users
- Filter/search events
- Date and time information
- Location information
- Navigation between pages
- Public accessibility

### Search Tests (`search.spec.ts`)
- Access search page
- Search input field
- Enter search query
- Submit search query
- Display search results
- Show relevant information
- Display sources
- Provide feedback
- Handle empty queries
- Loading states
- Clickable results
- Query persistence
- Public accessibility

### Admin Tests (`admin.spec.ts`)
- Access admin dashboard
- Display navigation menu
- View members list
- Table headers
- Search/filter members
- Add member functionality
- View member details
- Events management
- Settings page access
- Access control
- Statistics/metrics
- Section navigation
- Responsive layout
- Member applications

## Test Data and Fixtures

The `fixtures/test-data.ts` file contains:

- **Test user credentials** for different roles (admin, member, instructor)
- **Test membership application data**
- **Test event data**
- **Helper functions:**
  - `login(page, email, password)` - Login helper
  - `logout(page)` - Logout helper
  - `clearStorage(page)` - Clear browser storage
  - `waitForAPI(page, url)` - Wait for API response
  - `isAuthenticated(page)` - Check authentication status
  - `fillFormByLabel(page, label, value)` - Fill form by label
  - `waitForToast(page, message)` - Wait for toast notification

## Writing New Tests

### Basic Test Structure
```typescript
import { test, expect } from '@playwright/test';
import { testUsers, login, clearStorage } from './fixtures/test-data';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should do something', async ({ page }) => {
    await page.goto('/page');

    // Arrange
    const element = page.locator('selector');

    // Act
    await element.click();

    // Assert
    await expect(element).toBeVisible();
  });
});
```

### Best Practices

1. **Use data-testid attributes** for reliable element selection
2. **Clear storage before each test** to ensure clean state
3. **Use helper functions** from test-data.ts
4. **Make tests independent** - each test should run in isolation
5. **Use meaningful test names** that describe expected behavior
6. **Add timeouts** for async operations
7. **Handle flaky tests** with proper waits and retries
8. **Use page object pattern** for complex pages
9. **Keep tests focused** - one assertion per test when possible
10. **Clean up after tests** - logout, clear data

## Configuration

The `playwright.config.ts` file contains:

- **Base URL:** http://localhost:3000 (configurable via `PLAYWRIGHT_BASE_URL`)
- **Timeout:** Action timeout 10s, Navigation timeout 30s
- **Retries:** 2 retries on CI, 0 locally
- **Workers:** 1 on CI, undefined locally (parallel)
- **Browsers:** Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Screenshots:** Only on failure
- **Videos:** Retained on failure
- **Trace:** On first retry
- **Web server:** Automatically starts dev server

## CI/CD Integration

The E2E tests run automatically on:
- Pull requests to main/develop
- Pushes to main/develop
- Manual workflow dispatch

See `.github/workflows/e2e-tests.yml` for workflow configuration.

### Test Artifacts

On failure, the following artifacts are uploaded:
- Test results (JSON)
- Screenshots
- Videos
- Trace files
- HTML report

## Debugging Tests

### Using UI Mode (Recommended)
```bash
npm run test:e2e:ui
```
This opens an interactive UI where you can:
- Run tests step-by-step
- See test execution in real-time
- Inspect DOM snapshots
- View network requests
- Access trace viewer

### Using Debug Mode
```bash
npm run test:e2e:debug
```
This runs tests with Playwright Inspector for:
- Setting breakpoints
- Stepping through tests
- Inspecting selectors
- Generating test code

### View Trace Files
```bash
npx playwright show-trace trace.zip
```

## Common Issues and Solutions

### Issue: Tests fail with timeout errors
**Solution:** Increase timeout in playwright.config.ts or use explicit waits

### Issue: Element not found
**Solution:** Add proper wait conditions or use more specific selectors

### Issue: Tests pass locally but fail in CI
**Solution:** Check for timing issues, add retries, or use CI-specific configuration

### Issue: Authentication tests fail
**Solution:** Verify test credentials exist in database

### Issue: Flaky tests
**Solution:** Use proper waits, avoid hard-coded timeouts, ensure test isolation

## Performance

- Tests run in parallel by default (locally)
- CI runs tests sequentially (workers: 1)
- Average test suite runtime: ~5-10 minutes
- Individual test timeout: 30 seconds

## Test Maintenance

### Regular Tasks
- [ ] Update test data when schemas change
- [ ] Review and update selectors when UI changes
- [ ] Add tests for new features
- [ ] Remove tests for deprecated features
- [ ] Update dependencies (Playwright)
- [ ] Review failed test screenshots
- [ ] Clean up old test artifacts

### When to Update Tests
- After UI/UX changes
- After API changes
- After adding new features
- After fixing bugs
- When tests become flaky

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [CI/CD Integration](https://playwright.dev/docs/ci)

## Support

For questions or issues with E2E tests, please:
1. Check this README
2. Review Playwright documentation
3. Check existing test examples
4. Create an issue on GitHub
5. Contact the development team
