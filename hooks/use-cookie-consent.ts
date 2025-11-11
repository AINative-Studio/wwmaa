/**
 * React Hook for Cookie Consent Management
 * Provides access to consent state and management functions
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getConsent,
  saveConsent,
  acceptAll,
  rejectAll,
  hasConsent,
  hasCategoryConsent,
  loadAnalyticsIfConsented,
  removeAnalyticsScripts,
  type CookieConsent,
} from '@/lib/consent-manager';

export interface UseCookieConsentReturn {
  consent: CookieConsent | null;
  hasConsented: boolean;
  updateConsent: (consent: Omit<CookieConsent, 'essential' | 'timestamp' | 'version'>) => void;
  acceptAllCookies: () => void;
  rejectAllCookies: () => void;
  hasCategoryConsent: (category: keyof Omit<CookieConsent, 'timestamp' | 'version'>) => boolean;
  isLoading: boolean;
}

/**
 * Hook to manage cookie consent state and actions
 */
export function useCookieConsent(): UseCookieConsentReturn {
  const [consent, setConsent] = useState<CookieConsent | null>(null);
  const [hasConsented, setHasConsented] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load consent on mount
  useEffect(() => {
    const loadConsent = () => {
      const currentConsent = getConsent();
      setConsent(currentConsent);
      setHasConsented(hasConsent());
      setIsLoading(false);
    };

    loadConsent();
  }, []);

  // Listen for consent changes
  useEffect(() => {
    const handleConsentChange = (event: CustomEvent<CookieConsent>) => {
      setConsent(event.detail);
      setHasConsented(true);
    };

    const handleConsentCleared = () => {
      setConsent(null);
      setHasConsented(false);
    };

    window.addEventListener('consentChanged', handleConsentChange as EventListener);
    window.addEventListener('consentCleared', handleConsentCleared);

    return () => {
      window.removeEventListener('consentChanged', handleConsentChange as EventListener);
      window.removeEventListener('consentCleared', handleConsentCleared);
    };
  }, []);

  // Update consent callback
  const updateConsent = useCallback((newConsent: Omit<CookieConsent, 'essential' | 'timestamp' | 'version'>) => {
    saveConsent(newConsent);

    // Handle analytics scripts based on consent
    if (newConsent.analytics) {
      // Load analytics if consented (will be handled by layout)
      window.dispatchEvent(new CustomEvent('loadAnalytics'));
    } else {
      // Remove analytics if consent revoked
      removeAnalyticsScripts();
    }
  }, []);

  // Accept all cookies callback
  const acceptAllCookies = useCallback(() => {
    acceptAll();
    window.dispatchEvent(new CustomEvent('loadAnalytics'));
  }, []);

  // Reject all cookies callback
  const rejectAllCookies = useCallback(() => {
    rejectAll();
    removeAnalyticsScripts();
  }, []);

  // Check category consent callback
  const checkCategoryConsent = useCallback((category: keyof Omit<CookieConsent, 'timestamp' | 'version'>) => {
    return hasCategoryConsent(category);
  }, [consent]);

  return {
    consent,
    hasConsented,
    updateConsent,
    acceptAllCookies,
    rejectAllCookies,
    hasCategoryConsent: checkCategoryConsent,
    isLoading,
  };
}
