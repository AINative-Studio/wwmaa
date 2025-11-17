# E2E Testing Quick Start Guide

## Quick Setup (First Time)

```bash
# 1. Install Playwright browsers
npx playwright install --with-deps chromium

# 2. Start the development server (in one terminal)
npm run dev

# 3. Run tests with UI mode (in another terminal)
npm run test:e2e:ui
```

## Common Commands

### Run All Tests
```bash
npm run test:e2e
```

### Run Tests with UI (Recommended for Development)
```bash
npm run test:e2e:ui
```
Interactive mode with visual test runner, debugging, and inspection tools.

### Run Specific Test File
```bash
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/membership.spec.ts
npx playwright test e2e/events.spec.ts
npx playwright test e2e/search.spec.ts
npx playwright test e2e/admin.spec.ts
```

### Run Tests by Pattern
```bash
npx playwright test -g "login"
npx playwright test -g "admin"
npx playwright test -g "membership"
```

### Run in Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### Run Specific Browser
```bash
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit
```

### View Test Report
```bash
npm run test:e2e:report
```

## Test Files Overview

| File | Tests | Description |
|------|-------|-------------|
| `e2e/auth.spec.ts` | 12 | Login, logout, registration, password reset |
| `e2e/membership.spec.ts` | 11 | Membership application and tiers |
| `e2e/events.spec.ts` | 12 | Event browsing and RSVP |
| `e2e/search.spec.ts` | 12 | Search functionality and feedback |
| `e2e/admin.spec.ts` | 15 | Admin dashboard operations |
| **Total** | **62** | Complete E2E coverage |

## Prerequisites for Running Tests

1. **Development Server Running**
   ```bash
   npm run dev
   ```
   Server should be running on http://localhost:3000

2. **Test User Credentials**
   - Admin user should exist in database
   - Email: admin@wwmaa.com
   - Password: AdminPass123!

3. **Database Setup**
   - Database should be running
   - Backend API should be accessible

## Troubleshooting

### Tests Fail with "Connection Refused"
**Solution:** Make sure dev server is running on port 3000
```bash
npm run dev
```

### Tests Fail with "Timeout"
**Solution:** Increase timeout in playwright.config.ts or wait for server to fully start

### Element Not Found
**Solution:** Check if the UI element exists in the application. Update selectors if needed.

### Authentication Tests Fail
**Solution:** Verify test credentials exist in database
```bash
# Check if admin user exists
# Use your database query tool or API
```

## CI/CD

Tests run automatically on:
- Pull requests to main/develop
- Pushes to main/develop
- Can be triggered manually in GitHub Actions

## Next Steps

1. Start dev server: `npm run dev`
2. Run tests with UI: `npm run test:e2e:ui`
3. Review test results
4. Adjust selectors if needed for your UI implementation
5. Add new tests for new features

## More Information

- Full documentation: `/e2e/README.md`
- Implementation details: `/E2E_TESTING_IMPLEMENTATION.md`
- Playwright docs: https://playwright.dev

## Test Data Location

All test data and helper functions are in:
```
/e2e/fixtures/test-data.ts
```

This includes:
- Test user credentials
- Sample application data
- Helper functions (login, logout, etc.)
