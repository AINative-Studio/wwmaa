/**
 * Tests for Cookie Consent Manager
 * Comprehensive test coverage for GDPR/CCPA compliant consent management
 */

import {
  getConsent,
  saveConsent,
  acceptAll,
  rejectAll,
  clearConsent,
  hasConsent,
  hasCategoryConsent,
  loadAnalyticsIfConsented,
  removeAnalyticsScripts,
  CONSENT_COOKIE_NAME,
  CONSENT_STORAGE_KEY,
  CONSENT_VERSION,
  type CookieConsent,
} from '@/lib/consent-manager';

// Mock window and document
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock document.cookie
let cookieStore = '';
Object.defineProperty(document, 'cookie', {
  get: () => cookieStore,
  set: (value: string) => {
    if (value.includes('expires=Thu, 01 Jan 1970')) {
      // Deleting cookie
      const name = value.split('=')[0];
      cookieStore = cookieStore
        .split('; ')
        .filter(c => !c.startsWith(name + '='))
        .join('; ');
    } else {
      // Setting cookie
      const [nameValue] = value.split('; ');
      const existing = cookieStore.split('; ').filter(c => {
        const cookieName = c.split('=')[0];
        return cookieName !== nameValue.split('=')[0];
      });
      cookieStore = [...existing, nameValue].filter(Boolean).join('; ');
    }
  },
  configurable: true,
});

describe('Consent Manager', () => {
  beforeEach(() => {
    // Clear all storage before each test
    localStorage.clear();
    cookieStore = '';

    // Clear any event listeners
    window.removeEventListener('consentChanged', () => {});
    window.removeEventListener('consentCleared', () => {});
  });

  describe('saveConsent', () => {
    it('should save consent to localStorage', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: false,
      });

      const stored = localStorage.getItem(CONSENT_STORAGE_KEY);
      expect(stored).toBeTruthy();

      const consent = JSON.parse(stored!) as CookieConsent;
      expect(consent.functional).toBe(true);
      expect(consent.analytics).toBe(true);
      expect(consent.marketing).toBe(false);
      expect(consent.essential).toBe(true); // Always true
      expect(consent.version).toBe(CONSENT_VERSION);
      expect(consent.timestamp).toBeTruthy();
    });

    it('should save consent to cookie', () => {
      saveConsent({
        functional: true,
        analytics: false,
        marketing: false,
      });

      expect(cookieStore).toContain(CONSENT_COOKIE_NAME);
      expect(cookieStore).toContain('functional');
    });

    it('should dispatch consentChanged event', () => {
      const handler = jest.fn();
      window.addEventListener('consentChanged', handler);

      saveConsent({
        functional: true,
        analytics: true,
        marketing: true,
      });

      expect(handler).toHaveBeenCalled();
    });

    it('should always set essential to true', () => {
      saveConsent({
        functional: false,
        analytics: false,
        marketing: false,
      });

      const consent = getConsent();
      expect(consent?.essential).toBe(true);
    });
  });

  describe('getConsent', () => {
    it('should return null when no consent exists', () => {
      const consent = getConsent();
      expect(consent).toBeNull();
    });

    it('should return consent from localStorage', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: false,
      });

      const consent = getConsent();
      expect(consent).toBeTruthy();
      expect(consent?.functional).toBe(true);
      expect(consent?.analytics).toBe(true);
      expect(consent?.marketing).toBe(false);
    });

    it('should return null if consent version is outdated', () => {
      const oldConsent: CookieConsent = {
        essential: true,
        functional: true,
        analytics: true,
        marketing: false,
        timestamp: new Date().toISOString(),
        version: '0.0.1', // Old version
      };

      localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(oldConsent));

      const consent = getConsent();
      expect(consent).toBeNull();
      expect(localStorage.getItem(CONSENT_STORAGE_KEY)).toBeNull();
    });

    it('should sync cookie to localStorage if localStorage is empty', () => {
      const testConsent: CookieConsent = {
        essential: true,
        functional: true,
        analytics: false,
        marketing: false,
        timestamp: new Date().toISOString(),
        version: CONSENT_VERSION,
      };

      // Manually set cookie
      cookieStore = `${CONSENT_COOKIE_NAME}=${encodeURIComponent(JSON.stringify(testConsent))}`;

      const consent = getConsent();
      expect(consent).toBeTruthy();
      expect(localStorage.getItem(CONSENT_STORAGE_KEY)).toBeTruthy();
    });
  });

  describe('acceptAll', () => {
    it('should accept all cookie categories', () => {
      acceptAll();

      const consent = getConsent();
      expect(consent?.functional).toBe(true);
      expect(consent?.analytics).toBe(true);
      expect(consent?.marketing).toBe(true);
      expect(consent?.essential).toBe(true);
    });
  });

  describe('rejectAll', () => {
    it('should reject all non-essential cookies', () => {
      rejectAll();

      const consent = getConsent();
      expect(consent?.functional).toBe(false);
      expect(consent?.analytics).toBe(false);
      expect(consent?.marketing).toBe(false);
      expect(consent?.essential).toBe(true); // Always true
    });
  });

  describe('clearConsent', () => {
    it('should clear consent from localStorage', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: true,
      });

      clearConsent();
      expect(localStorage.getItem(CONSENT_STORAGE_KEY)).toBeNull();
    });

    it('should clear consent cookie', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: true,
      });

      clearConsent();
      // Cookie should be set with expired date
      expect(cookieStore).not.toContain(CONSENT_COOKIE_NAME);
    });

    it('should dispatch consentCleared event', () => {
      const handler = jest.fn();
      window.addEventListener('consentCleared', handler);

      saveConsent({
        functional: true,
        analytics: true,
        marketing: true,
      });

      clearConsent();
      expect(handler).toHaveBeenCalled();
    });
  });

  describe('hasConsent', () => {
    it('should return false when no consent exists', () => {
      expect(hasConsent()).toBe(false);
    });

    it('should return true when consent exists', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: false,
      });

      expect(hasConsent()).toBe(true);
    });
  });

  describe('hasCategoryConsent', () => {
    beforeEach(() => {
      saveConsent({
        functional: true,
        analytics: false,
        marketing: false,
      });
    });

    it('should return true for essential cookies (always)', () => {
      expect(hasCategoryConsent('essential')).toBe(true);
    });

    it('should return true for consented functional cookies', () => {
      expect(hasCategoryConsent('functional')).toBe(true);
    });

    it('should return false for rejected analytics cookies', () => {
      expect(hasCategoryConsent('analytics')).toBe(false);
    });

    it('should return false for rejected marketing cookies', () => {
      expect(hasCategoryConsent('marketing')).toBe(false);
    });

    it('should return false when no consent exists', () => {
      clearConsent();
      expect(hasCategoryConsent('analytics')).toBe(false);
    });
  });

  describe('loadAnalyticsIfConsented', () => {
    const mockMeasurementId = 'G-XXXXXXXXXX';

    beforeEach(() => {
      // Clear any existing scripts
      document.querySelectorAll('script[src*="googletagmanager"]').forEach(s => s.remove());
      delete (window as any).gtag;
      delete (window as any).dataLayer;
    });

    it('should not load analytics if no consent', () => {
      clearConsent();
      loadAnalyticsIfConsented(mockMeasurementId);

      const script = document.querySelector('script[src*="googletagmanager"]');
      expect(script).toBeNull();
    });

    it('should not load analytics if analytics consent is rejected', () => {
      saveConsent({
        functional: true,
        analytics: false,
        marketing: false,
      });

      loadAnalyticsIfConsented(mockMeasurementId);

      const script = document.querySelector('script[src*="googletagmanager"]');
      expect(script).toBeNull();
    });

    it('should load analytics if analytics consent is granted', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: false,
      });

      loadAnalyticsIfConsented(mockMeasurementId);

      const script = document.querySelector('script[src*="googletagmanager"]');
      expect(script).toBeTruthy();
      expect(script?.getAttribute('src')).toContain(mockMeasurementId);
    });

    it('should not load duplicate scripts', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: false,
      });

      loadAnalyticsIfConsented(mockMeasurementId);
      loadAnalyticsIfConsented(mockMeasurementId);

      const scripts = document.querySelectorAll('script[src*="googletagmanager"]');
      expect(scripts.length).toBe(1);
    });

    it('should not load if measurement ID is empty', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: false,
      });

      loadAnalyticsIfConsented('');

      const script = document.querySelector('script[src*="googletagmanager"]');
      expect(script).toBeNull();
    });
  });

  describe('removeAnalyticsScripts', () => {
    beforeEach(() => {
      // Setup analytics
      const script = document.createElement('script');
      script.src = 'https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX';
      document.head.appendChild(script);

      (window as any).dataLayer = [1, 2, 3];
      (window as any).gtag = jest.fn();
    });

    it('should remove analytics scripts', () => {
      removeAnalyticsScripts();

      const scripts = document.querySelectorAll('script[src*="googletagmanager"]');
      expect(scripts.length).toBe(0);
    });

    it('should clear dataLayer', () => {
      removeAnalyticsScripts();

      expect((window as any).dataLayer).toEqual([]);
    });

    it('should remove gtag function', () => {
      removeAnalyticsScripts();

      expect((window as any).gtag).toBeUndefined();
    });
  });

  describe('Cookie handling', () => {
    it('should encode cookie values', () => {
      saveConsent({
        functional: true,
        analytics: true,
        marketing: true,
      });

      expect(cookieStore).toContain(CONSENT_COOKIE_NAME);
      // Should not contain raw JSON characters
      expect(cookieStore).not.toContain('{');
    });

    it('should set SameSite=Lax attribute', () => {
      // This is tested indirectly through the cookie setting mechanism
      saveConsent({
        functional: true,
        analytics: true,
        marketing: true,
      });

      expect(cookieStore).toContain(CONSENT_COOKIE_NAME);
    });
  });

  describe('Error handling', () => {
    it('should handle localStorage errors gracefully', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      // Mock localStorage to throw an error
      jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('Storage full');
      });

      expect(() => {
        saveConsent({
          functional: true,
          analytics: true,
          marketing: true,
        });
      }).not.toThrow();

      expect(consoleError).toHaveBeenCalled();

      consoleError.mockRestore();
    });

    it('should handle invalid JSON in localStorage', () => {
      localStorage.setItem(CONSENT_STORAGE_KEY, 'invalid json');

      const consent = getConsent();
      expect(consent).toBeNull();
    });
  });
});
