# Cookie Consent Implementation Guide

## Overview

The WWMAA website implements a comprehensive, GDPR/CCPA-compliant cookie consent system that gives users full control over their privacy preferences. This system includes:

- **Cookie Banner**: Appears on first visit with Accept All/Reject All/Customize options
- **Cookie Settings Modal**: Allows users to update preferences at any time via footer link
- **Consent Management**: Stores preferences in both cookies (12-month expiry) and localStorage
- **Conditional Script Loading**: Only loads analytics and marketing scripts if consented
- **Event-Driven Architecture**: Real-time updates when consent changes

## Architecture

### Core Components

```
/lib/consent-manager.ts         # Core consent logic and cookie management
/hooks/use-cookie-consent.ts    # React hook for consent state management
/components/cookie-consent/
  ├── cookie-banner.tsx         # First-visit consent banner
  ├── cookie-settings-modal.tsx # Preferences management modal
  └── analytics-loader.tsx      # Conditional Google Analytics loader
```

### Cookie Categories

| Category      | Required | Description                                         | Examples                                 |
|---------------|----------|-----------------------------------------------------|------------------------------------------|
| **Essential** | ✓ Yes    | Necessary for website functionality                 | Authentication, CSRF tokens, session    |
| **Functional**| No       | Enhance functionality and personalization           | Language, theme, user preferences        |
| **Analytics** | No       | Understand how visitors interact with the site      | Google Analytics, page views             |
| **Marketing** | No       | Track online activity for advertising               | Ad targeting, retargeting, social pixels |

## Implementation Details

### 1. Consent Storage

Consent is stored in two places for redundancy and performance:

#### Cookie Storage
```javascript
// Cookie: user_cookie_consent
// Expiry: 365 days (12 months)
// Attributes: SameSite=Lax, Secure (on HTTPS)
{
  "essential": true,
  "functional": true,
  "analytics": false,
  "marketing": false,
  "timestamp": "2025-01-10T12:00:00.000Z",
  "version": "1.0.0"
}
```

#### localStorage Storage
```javascript
// Key: cookieConsent
// Same structure as cookie
// Used for faster access and as backup
```

### 2. Consent Versioning

The system includes version control for the consent policy:

```typescript
export const CONSENT_VERSION = '1.0.0';
```

When the consent version changes:
1. Old consent is automatically invalidated
2. User sees the consent banner again
3. This ensures compliance when cookie policy updates

### 3. Event-Driven Updates

The system uses custom events for real-time updates:

```javascript
// Fired when consent is saved or updated
window.dispatchEvent(new CustomEvent('consentChanged', { detail: consent }));

// Fired when consent is cleared
window.dispatchEvent(new CustomEvent('consentCleared'));

// Fired to trigger analytics loading
window.dispatchEvent(new CustomEvent('loadAnalytics'));
```

### 4. Analytics Integration

Google Analytics 4 is loaded conditionally based on consent:

```typescript
// Only loads if analytics consent is granted
loadAnalyticsIfConsented(measurementId);

// Removes scripts if consent is revoked
removeAnalyticsScripts();
```

**Features:**
- IP anonymization enabled for GDPR compliance
- SameSite=Lax cookie flags
- Automatic cleanup when consent revoked
- Prevents duplicate script loading

## Usage Guide

### For Developers

#### Checking Consent Status

```typescript
import { hasCategoryConsent } from '@/lib/consent-manager';

// Check if user has consented to analytics
if (hasCategoryConsent('analytics')) {
  // Load analytics scripts
}

// Check if user has consented to marketing
if (hasCategoryConsent('marketing')) {
  // Load marketing pixels
}
```

#### Using the React Hook

```typescript
import { useCookieConsent } from '@/hooks/use-cookie-consent';

function MyComponent() {
  const {
    consent,           // Current consent object or null
    hasConsented,      // Boolean: has user made a choice?
    acceptAllCookies,  // Function: accept all categories
    rejectAllCookies,  // Function: reject all except essential
    updateConsent,     // Function: set specific categories
    hasCategoryConsent,// Function: check specific category
    isLoading          // Boolean: is consent loading?
  } = useCookieConsent();

  // Example: Conditionally render based on consent
  return (
    <div>
      {hasCategoryConsent('analytics') && <AnalyticsWidget />}
      {!hasConsented && <ConsentBanner />}
    </div>
  );
}
```

#### Updating Consent Programmatically

```typescript
import { saveConsent, acceptAll, rejectAll } from '@/lib/consent-manager';

// Save custom consent
saveConsent({
  functional: true,
  analytics: true,
  marketing: false
});

// Accept all cookies
acceptAll();

// Reject all non-essential cookies
rejectAll();
```

#### Listening for Consent Changes

```typescript
useEffect(() => {
  const handleConsentChange = (event: CustomEvent<CookieConsent>) => {
    console.log('Consent updated:', event.detail);
    // React to consent changes
  };

  window.addEventListener('consentChanged', handleConsentChange);

  return () => {
    window.removeEventListener('consentChanged', handleConsentChange);
  };
}, []);
```

### For End Users

#### First Visit Experience

1. **Banner Appears**: On first visit, a cookie banner appears at the bottom of the screen
2. **Clear Information**: Banner explains the four cookie categories
3. **Three Options**:
   - **Accept All**: Consent to all cookie categories
   - **Reject All**: Only essential cookies
   - **Customize**: Choose specific categories

#### Updating Preferences

1. **Footer Link**: Click "Cookie Preferences" in the footer
2. **Settings Modal**: Opens a detailed preferences modal
3. **Category Details**: Each category has a description and examples
4. **Save Changes**: Click "Save Preferences" to update

## Compliance

### GDPR Compliance

- ✓ Explicit consent required before non-essential cookies
- ✓ Clear information about each cookie category
- ✓ Easy way to withdraw consent at any time
- ✓ Cookie consent banner on first visit
- ✓ Granular control over cookie categories
- ✓ IP anonymization for analytics
- ✓ 12-month consent expiry (re-consent required annually)

### CCPA Compliance

- ✓ Clear notice of data collection
- ✓ Ability to opt-out of data sale/sharing
- ✓ Non-discrimination for opting out
- ✓ Accessible preferences management

### Cookie Policy Requirements

The implementation satisfies requirements for:
- Cookie consent banners
- Preference management
- Cookie categorization
- Consent documentation
- Revocation mechanisms

## API Reference

### ConsentManager (`/lib/consent-manager.ts`)

#### Functions

##### `getConsent(): CookieConsent | null`
Retrieves current consent from storage.

**Returns:** Consent object or null if not set

**Example:**
```typescript
const consent = getConsent();
if (consent?.analytics) {
  // Analytics is enabled
}
```

##### `saveConsent(consent: Partial<CookieConsent>): void`
Saves consent to cookie and localStorage.

**Parameters:**
- `consent.functional` (boolean): Functional cookies consent
- `consent.analytics` (boolean): Analytics cookies consent
- `consent.marketing` (boolean): Marketing cookies consent

**Example:**
```typescript
saveConsent({
  functional: true,
  analytics: true,
  marketing: false
});
```

##### `acceptAll(): void`
Accepts all cookie categories.

##### `rejectAll(): void`
Rejects all non-essential cookies.

##### `clearConsent(): void`
Clears all consent data.

##### `hasConsent(): boolean`
Checks if user has made a consent choice.

##### `hasCategoryConsent(category: string): boolean`
Checks if a specific category is consented.

**Parameters:**
- `category`: 'essential' | 'functional' | 'analytics' | 'marketing'

##### `loadAnalyticsIfConsented(measurementId: string): void`
Conditionally loads Google Analytics 4.

##### `removeAnalyticsScripts(): void`
Removes all analytics scripts and cookies.

### useCookieConsent Hook (`/hooks/use-cookie-consent.ts`)

#### Return Value

```typescript
interface UseCookieConsentReturn {
  consent: CookieConsent | null;
  hasConsented: boolean;
  updateConsent: (consent) => void;
  acceptAllCookies: () => void;
  rejectAllCookies: () => void;
  hasCategoryConsent: (category) => boolean;
  isLoading: boolean;
}
```

## Testing

### Test Coverage

The cookie consent system has comprehensive test coverage:

| File                      | Statements | Branches | Functions | Lines |
|---------------------------|------------|----------|-----------|-------|
| lib/consent-manager.ts    | 89.62%     | 82.35%   | 93.75%    | 88.88%|
| hooks/use-cookie-consent.ts| 100%      | 100%     | 100%      | 100%  |
| cookie-banner.tsx         | 100%       | 100%     | 100%      | 100%  |
| cookie-settings-modal.tsx | 100%       | 100%     | 100%      | 100%  |
| analytics-loader.tsx      | 87.5%      | 66.66%   | 100%      | 87.5% |
| **Overall**               | **94.19%** | **84.61%**| **98%**   | **93.98%**|

### Running Tests

```bash
# Run all cookie consent tests
npm test -- --testPathPatterns="cookie-consent|consent-manager|use-cookie-consent"

# Run with coverage
npm test -- --testPathPatterns="cookie-consent|consent-manager|use-cookie-consent" --coverage

# Run specific test file
npm test -- __tests__/lib/consent-manager.test.ts
```

### Test Files

- `__tests__/lib/consent-manager.test.ts` (46 tests)
- `__tests__/hooks/use-cookie-consent.test.ts` (34 tests)
- `__tests__/components/cookie-consent/cookie-banner.test.tsx` (25 tests)
- `__tests__/components/cookie-consent/cookie-settings-modal.test.tsx` (30 tests)
- `__tests__/components/cookie-consent/analytics-loader.test.tsx` (26 tests)

**Total: 161+ test cases**

## Configuration

### Environment Variables

```env
# Google Analytics 4 Measurement ID
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

### Consent Constants

Located in `/lib/consent-manager.ts`:

```typescript
// Cookie name for storing consent
export const CONSENT_COOKIE_NAME = 'user_cookie_consent';

// localStorage key for consent backup
export const CONSENT_STORAGE_KEY = 'cookieConsent';

// Current consent policy version
export const CONSENT_VERSION = '1.0.0';

// Consent expiry (days)
export const CONSENT_EXPIRY_DAYS = 365;
```

## Troubleshooting

### Banner Not Appearing

**Problem:** Cookie banner doesn't show on first visit

**Solutions:**
1. Clear cookies and localStorage
2. Check `hasConsent()` returns `false`
3. Verify `<CookieBanner />` is rendered in layout
4. Check console for React errors

### Consent Not Persisting

**Problem:** Consent choices aren't saved across sessions

**Solutions:**
1. Check browser allows cookies
2. Verify cookie domain matches current domain
3. Check for localStorage quota errors
4. Ensure HTTPS for Secure cookie attribute

### Analytics Not Loading

**Problem:** Google Analytics doesn't load after consent

**Solutions:**
1. Verify `NEXT_PUBLIC_GA_MEASUREMENT_ID` is set
2. Check analytics consent: `hasCategoryConsent('analytics')`
3. Verify `<AnalyticsLoader />` is rendered in layout
4. Check browser console for script loading errors
5. Ensure no ad blockers are interfering

### Consent Modal Not Opening

**Problem:** Footer link doesn't open preferences modal

**Solutions:**
1. Check `<CookieSettingsModal />` props
2. Verify `open` state is being set to `true`
3. Check for conflicting z-index values
4. Ensure Dialog component is properly imported

## Best Practices

### Do's

✓ **Always check consent before loading third-party scripts**
```typescript
if (hasCategoryConsent('analytics')) {
  loadAnalyticsScript();
}
```

✓ **Use the provided hook in React components**
```typescript
const { hasCategoryConsent } = useCookieConsent();
```

✓ **Listen for consent changes**
```typescript
window.addEventListener('consentChanged', handleConsentChange);
```

✓ **Test consent flows thoroughly**
```typescript
// Test accept all
// Test reject all
// Test custom preferences
// Test consent persistence
```

### Don'ts

✗ **Don't load tracking scripts without checking consent**
```typescript
// BAD
loadAnalyticsScript();

// GOOD
if (hasCategoryConsent('analytics')) {
  loadAnalyticsScript();
}
```

✗ **Don't store sensitive data in cookies without consent**
```typescript
// BAD
document.cookie = "user_data=...";

// GOOD
if (hasCategoryConsent('functional')) {
  document.cookie = "user_data=...";
}
```

✗ **Don't bypass the consent system**
```typescript
// BAD
// Directly setting cookies without checking consent

// GOOD
// Use the consent manager API
```

## Future Enhancements

Potential improvements for future releases:

1. **Geo-Location Based Consent**
   - Show different banners for EU vs non-EU visitors
   - Adjust compliance requirements by region

2. **A/B Testing**
   - Test different banner designs
   - Measure consent rates by variant

3. **Advanced Analytics**
   - Track consent choices (anonymously)
   - Monitor consent rates over time
   - Identify most common preferences

4. **Additional Integrations**
   - Facebook Pixel conditional loading
   - HotJar conditional loading
   - Custom third-party script management

5. **Multi-Language Support**
   - Translate banner and modal content
   - Detect browser language automatically

6. **Accessibility Improvements**
   - Enhanced screen reader support
   - Keyboard navigation improvements
   - High contrast mode

## Support

For issues or questions:

1. Check this documentation first
2. Review test files for usage examples
3. Check browser console for errors
4. Review GDPR/CCPA compliance requirements
5. Contact development team

## Changelog

### Version 1.0.0 (Sprint 8)
- ✓ Initial implementation
- ✓ Cookie banner component
- ✓ Settings modal component
- ✓ Consent manager library
- ✓ React hook for state management
- ✓ Google Analytics integration
- ✓ Comprehensive test suite (161+ tests)
- ✓ GDPR/CCPA compliance
- ✓ Accessibility features
- ✓ Documentation

## License

This cookie consent system is part of the WWMAA website codebase and follows the same license terms.

---

**Last Updated:** Sprint 8 - 2025-01-10
**Maintained By:** WWMAA Development Team
**Compliance:** GDPR, CCPA, ePrivacy Directive
