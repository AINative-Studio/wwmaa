# Cookie Consent Components

GDPR/CCPA-compliant cookie consent system for WWMAA website.

## Components

### Cookie Banner (`cookie-banner.tsx`)
First-visit consent banner with Accept All/Reject All/Customize options.

**Usage:**
```tsx
import { CookieBanner } from '@/components/cookie-consent/cookie-banner';

<CookieBanner />
```

**Features:**
- Appears only on first visit
- Customizable cookie preferences
- Keyboard accessible
- Mobile responsive
- Auto-dismisses after action

---

### Cookie Settings Modal (`cookie-settings-modal.tsx`)
Full preferences management modal accessible from footer.

**Usage:**
```tsx
import { CookieSettingsModal } from '@/components/cookie-consent/cookie-settings-modal';

const [open, setOpen] = useState(false);

<button onClick={() => setOpen(true)}>Cookie Preferences</button>
<CookieSettingsModal open={open} onOpenChange={setOpen} />
```

**Features:**
- Detailed category descriptions
- Current consent status display
- Accept All / Reject All / Save Custom
- Links to Privacy Policy and Cookie Policy
- Fully accessible

---

### Analytics Loader (`analytics-loader.tsx`)
Conditionally loads Google Analytics based on consent.

**Usage:**
```tsx
import { AnalyticsLoader } from '@/components/cookie-consent/analytics-loader';

// In layout.tsx
<AnalyticsLoader />
```

**Features:**
- Only loads GA4 if analytics consent granted
- Listens for consent changes
- Automatically cleans up scripts on revoke
- Prevents duplicate loading

---

## Hook

### `useCookieConsent()`

React hook for managing cookie consent state.

```typescript
import { useCookieConsent } from '@/hooks/use-cookie-consent';

const {
  consent,           // Current consent object
  hasConsented,      // Has user made a choice?
  acceptAllCookies,  // Accept all categories
  rejectAllCookies,  // Reject all except essential
  updateConsent,     // Update specific categories
  hasCategoryConsent,// Check specific category
  isLoading          // Is consent loading?
} = useCookieConsent();
```

---

## Consent Manager

Core library for managing consent (`/lib/consent-manager.ts`).

### Key Functions

```typescript
import {
  getConsent,
  saveConsent,
  acceptAll,
  rejectAll,
  hasConsent,
  hasCategoryConsent,
  loadAnalyticsIfConsented,
  removeAnalyticsScripts
} from '@/lib/consent-manager';

// Check if user has made a choice
if (!hasConsent()) {
  // Show banner
}

// Check specific category
if (hasCategoryConsent('analytics')) {
  // Load analytics
}

// Save custom consent
saveConsent({
  functional: true,
  analytics: true,
  marketing: false
});
```

---

## Cookie Categories

| Category      | Required | Description                    |
|---------------|----------|--------------------------------|
| **Essential** | ✓        | Authentication, CSRF, session  |
| **Functional**| -        | Preferences, language, theme   |
| **Analytics** | -        | Google Analytics, page views   |
| **Marketing** | -        | Ad tracking, retargeting       |

---

## Quick Start

### 1. Add to Layout

```tsx
// app/layout.tsx
import { CookieBanner } from '@/components/cookie-consent/cookie-banner';
import { AnalyticsLoader } from '@/components/cookie-consent/analytics-loader';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AnalyticsLoader />
        {children}
        <Footer />
        <CookieBanner />
      </body>
    </html>
  );
}
```

### 2. Add Footer Link

```tsx
// components/footer.tsx
import { CookieSettingsModal } from '@/components/cookie-consent/cookie-settings-modal';
import { useState } from 'react';

export function Footer() {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <footer>
      {/* ... */}
      <button onClick={() => setShowSettings(true)}>
        Cookie Preferences
      </button>
      <CookieSettingsModal open={showSettings} onOpenChange={setShowSettings} />
    </footer>
  );
}
```

### 3. Configure Environment

```env
# .env.local
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

### 4. Check Consent Before Loading Scripts

```typescript
import { hasCategoryConsent } from '@/lib/consent-manager';

if (hasCategoryConsent('analytics')) {
  // Load analytics scripts
}

if (hasCategoryConsent('marketing')) {
  // Load marketing pixels
}
```

---

## Testing

```bash
# Run all cookie consent tests
npm test -- --testPathPatterns="cookie-consent|consent-manager|use-cookie-consent"

# Run with coverage
npm test -- --coverage --testPathPatterns="cookie-consent"
```

**Test Coverage: 94%+**

---

## Documentation

Full documentation available at:
- [`/docs/privacy/cookie-consent-implementation.md`](/docs/privacy/cookie-consent-implementation.md)

---

## Compliance

✓ GDPR compliant
✓ CCPA compliant
✓ ePrivacy Directive compliant
✓ IP anonymization
✓ 12-month consent expiry
✓ Easy preference management
✓ Granular category control

---

## Support

For issues or questions, refer to the full documentation or contact the development team.

---

**Version:** 1.0.0
**Sprint:** 8
**Last Updated:** 2025-01-10
