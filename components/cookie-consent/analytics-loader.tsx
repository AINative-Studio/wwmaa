'use client';

/**
 * Analytics Loader Component
 * Conditionally loads Google Analytics 4 based on user consent
 */

import { useEffect } from 'react';
import { loadAnalyticsIfConsented } from '@/lib/consent-manager';

const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID || '';

export function AnalyticsLoader() {
  useEffect(() => {
    // Load analytics on mount if already consented
    if (GA_MEASUREMENT_ID) {
      loadAnalyticsIfConsented(GA_MEASUREMENT_ID);
    }

    // Listen for consent changes to load analytics
    const handleLoadAnalytics = () => {
      if (GA_MEASUREMENT_ID) {
        loadAnalyticsIfConsented(GA_MEASUREMENT_ID);
      }
    };

    window.addEventListener('loadAnalytics', handleLoadAnalytics);
    window.addEventListener('consentChanged', handleLoadAnalytics);

    return () => {
      window.removeEventListener('loadAnalytics', handleLoadAnalytics);
      window.removeEventListener('consentChanged', handleLoadAnalytics);
    };
  }, []);

  return null;
}
