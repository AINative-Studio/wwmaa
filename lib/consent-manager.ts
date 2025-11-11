/**
 * Cookie Consent Manager
 * Handles GDPR/CCPA compliant cookie consent storage and retrieval
 */

export const CONSENT_COOKIE_NAME = 'user_cookie_consent';
export const CONSENT_STORAGE_KEY = 'cookieConsent';
export const CONSENT_VERSION = '1.0.0'; // Update when cookie policy changes
export const CONSENT_EXPIRY_DAYS = 365; // 12 months

export interface CookieConsent {
  essential: true; // Always true - required for site functionality
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
  timestamp: string;
  version: string;
}

export const DEFAULT_CONSENT: CookieConsent = {
  essential: true,
  functional: false,
  analytics: false,
  marketing: false,
  timestamp: new Date().toISOString(),
  version: CONSENT_VERSION,
};

/**
 * Get consent from storage (checks both cookie and localStorage)
 */
export function getConsent(): CookieConsent | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    // First try localStorage (faster)
    const localStorageConsent = localStorage.getItem(CONSENT_STORAGE_KEY);
    if (localStorageConsent) {
      const consent = JSON.parse(localStorageConsent) as CookieConsent;

      // Verify version matches current policy
      if (consent.version === CONSENT_VERSION) {
        return consent;
      }

      // Version mismatch - clear old consent
      clearConsent();
      return null;
    }

    // Fallback to cookie
    const cookieConsent = getCookie(CONSENT_COOKIE_NAME);
    if (cookieConsent) {
      const consent = JSON.parse(cookieConsent) as CookieConsent;

      if (consent.version === CONSENT_VERSION) {
        // Sync to localStorage
        localStorage.setItem(CONSENT_STORAGE_KEY, cookieConsent);
        return consent;
      }

      clearConsent();
      return null;
    }

    return null;
  } catch (error) {
    console.error('Error reading consent:', error);
    return null;
  }
}

/**
 * Save consent to both cookie and localStorage
 */
export function saveConsent(consent: Omit<CookieConsent, 'essential' | 'timestamp' | 'version'>): void {
  if (typeof window === 'undefined') {
    return;
  }

  const fullConsent: CookieConsent = {
    essential: true, // Always true
    functional: consent.functional,
    analytics: consent.analytics,
    marketing: consent.marketing,
    timestamp: new Date().toISOString(),
    version: CONSENT_VERSION,
  };

  const consentString = JSON.stringify(fullConsent);

  try {
    // Save to cookie (12 months)
    setCookie(CONSENT_COOKIE_NAME, consentString, CONSENT_EXPIRY_DAYS);

    // Save to localStorage
    localStorage.setItem(CONSENT_STORAGE_KEY, consentString);

    // Dispatch event for listeners
    window.dispatchEvent(new CustomEvent('consentChanged', { detail: fullConsent }));
  } catch (error) {
    console.error('Error saving consent:', error);
  }
}

/**
 * Accept all cookie categories
 */
export function acceptAll(): void {
  saveConsent({
    functional: true,
    analytics: true,
    marketing: true,
  });
}

/**
 * Reject all non-essential cookies
 */
export function rejectAll(): void {
  saveConsent({
    functional: false,
    analytics: false,
    marketing: false,
  });
}

/**
 * Clear all consent data
 */
export function clearConsent(): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    deleteCookie(CONSENT_COOKIE_NAME);
    localStorage.removeItem(CONSENT_STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('consentCleared'));
  } catch (error) {
    console.error('Error clearing consent:', error);
  }
}

/**
 * Check if user has given consent
 */
export function hasConsent(): boolean {
  return getConsent() !== null;
}

/**
 * Check if a specific category is consented
 */
export function hasCategoryConsent(category: keyof Omit<CookieConsent, 'timestamp' | 'version'>): boolean {
  const consent = getConsent();
  if (!consent) {
    return false;
  }
  return consent[category] === true;
}

/**
 * Helper: Set cookie
 */
function setCookie(name: string, value: string, days: number): void {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);

  // SameSite=Lax for CSRF protection, Secure for HTTPS only
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires.toUTCString()}; path=/; SameSite=Lax${secure}`;
}

/**
 * Helper: Get cookie
 */
function getCookie(name: string): string | null {
  const nameEQ = name + '=';
  const cookies = document.cookie.split(';');

  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i];
    while (cookie.charAt(0) === ' ') {
      cookie = cookie.substring(1, cookie.length);
    }
    if (cookie.indexOf(nameEQ) === 0) {
      return decodeURIComponent(cookie.substring(nameEQ.length, cookie.length));
    }
  }

  return null;
}

/**
 * Helper: Delete cookie
 */
function deleteCookie(name: string): void {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

/**
 * Load Google Analytics 4 if analytics consent is granted
 */
export function loadAnalyticsIfConsented(measurementId: string): void {
  if (!hasCategoryConsent('analytics')) {
    return;
  }

  if (typeof window === 'undefined' || !measurementId) {
    return;
  }

  // Check if already loaded
  if ((window as any).gtag) {
    return;
  }

  // Load GA4 script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
  document.head.appendChild(script);

  // Initialize GA4
  (window as any).dataLayer = (window as any).dataLayer || [];
  function gtag(...args: any[]) {
    (window as any).dataLayer.push(args);
  }
  (window as any).gtag = gtag;

  gtag('js', new Date());
  gtag('config', measurementId, {
    anonymize_ip: true, // GDPR compliance
    cookie_flags: 'SameSite=Lax;Secure',
  });
}

/**
 * Remove analytics scripts if consent is revoked
 */
export function removeAnalyticsScripts(): void {
  if (typeof window === 'undefined') {
    return;
  }

  // Remove GA4 scripts
  const scripts = document.querySelectorAll('script[src*="googletagmanager.com"]');
  scripts.forEach(script => script.remove());

  // Clear dataLayer
  (window as any).dataLayer = [];
  delete (window as any).gtag;

  // Clear GA cookies
  const gaCookies = document.cookie.split(';').filter(cookie => {
    const name = cookie.trim().split('=')[0];
    return name.startsWith('_ga') || name.startsWith('_gid');
  });

  gaCookies.forEach(cookie => {
    const name = cookie.trim().split('=')[0];
    deleteCookie(name);
  });
}
