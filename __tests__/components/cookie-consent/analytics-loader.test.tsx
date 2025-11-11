/**
 * Tests for Analytics Loader Component
 * Test coverage for conditional Google Analytics loading based on consent
 */

import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AnalyticsLoader } from '@/components/cookie-consent/analytics-loader';
import * as consentManager from '@/lib/consent-manager';

// Mock the consent manager
jest.mock('@/lib/consent-manager');

const mockConsentManager = consentManager as jest.Mocked<typeof consentManager>;

// Set env var before tests
process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID = 'G-TEST123456';

describe('AnalyticsLoader', () => {
  const mockMeasurementId = 'G-TEST123456';

  beforeEach(() => {
    jest.clearAllMocks();

    // Clear any existing analytics scripts
    document.querySelectorAll('script[src*="googletagmanager"]').forEach(s => s.remove());
    delete (window as any).gtag;
    delete (window as any).dataLayer;

    // Default mock implementation
    mockConsentManager.loadAnalyticsIfConsented.mockImplementation(() => {});
  });

  describe('Component Rendering', () => {
    it('should render without errors', () => {
      expect(() => {
        render(<AnalyticsLoader />);
      }).not.toThrow();
    });

    it('should not render any visible content', () => {
      const { container } = render(<AnalyticsLoader />);

      expect(container.firstChild).toBeNull();
    });

    it('should be a functional component', () => {
      const { container } = render(<AnalyticsLoader />);

      expect(container).toBeInTheDocument();
    });
  });

  describe('Initial Load', () => {
    it('should attempt to load analytics on mount', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledWith(mockMeasurementId);
    });

    it('should only load analytics once on mount', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledTimes(1);
    });

    it('should call loadAnalyticsIfConsented from consent manager', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalled();
    });
  });

  describe('Event Listeners', () => {
    it('should attach event listeners on mount', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');

      render(<AnalyticsLoader />);

      expect(addEventListenerSpy).toHaveBeenCalledWith('loadAnalytics', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('consentChanged', expect.any(Function));

      addEventListenerSpy.mockRestore();
    });

    it('should have both event listeners attached', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');

      render(<AnalyticsLoader />);

      const loadAnalyticsListener = addEventListenerSpy.mock.calls.find(
        call => call[0] === 'loadAnalytics'
      );
      const consentChangedListener = addEventListenerSpy.mock.calls.find(
        call => call[0] === 'consentChanged'
      );

      expect(loadAnalyticsListener).toBeTruthy();
      expect(consentChangedListener).toBeTruthy();

      addEventListenerSpy.mockRestore();
    });
  });

  describe('Cleanup', () => {
    it('should remove event listeners on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = render(<AnalyticsLoader />);

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('loadAnalytics', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('consentChanged', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });

    it('should handle multiple mount/unmount cycles', () => {
      const { unmount: unmount1 } = render(<AnalyticsLoader />);
      unmount1();

      const { unmount: unmount2 } = render(<AnalyticsLoader />);
      unmount2();

      const { unmount: unmount3 } = render(<AnalyticsLoader />);
      unmount3();

      // Should have been called once per mount
      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledTimes(3);
    });
  });

  describe('Integration with Consent Manager', () => {
    it('should use loadAnalyticsIfConsented function', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalled();
    });

    it('should pass measurement ID to loadAnalyticsIfConsented', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledWith(mockMeasurementId);
    });

    it('should respect consent manager decisions', () => {
      // Mock that consent manager doesn't load analytics
      mockConsentManager.loadAnalyticsIfConsented.mockImplementation(() => {
        // Don't actually load analytics
      });

      render(<AnalyticsLoader />);

      // Should call but not load scripts (handled by consent manager)
      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalled();
      expect(document.querySelector('script[src*="googletagmanager"]')).toBeNull();
    });
  });

  describe('Environment Variables', () => {
    it('should use measurement ID from environment', () => {
      render(<AnalyticsLoader />);

      // Should be called with the configured measurement ID
      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledWith(mockMeasurementId);
    });

    it('should pass measurement ID to loadAnalyticsIfConsented', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledWith(expect.any(String));
    });
  });

  describe('Error Handling', () => {
    it('should handle errors from loadAnalyticsIfConsented', () => {
      mockConsentManager.loadAnalyticsIfConsented.mockImplementation(() => {
        throw new Error('Failed to load analytics');
      });

      expect(() => {
        render(<AnalyticsLoader />);
      }).toThrow('Failed to load analytics');
    });
  });

  describe('Multiple Instances', () => {
    it('should handle multiple AnalyticsLoader instances', () => {
      render(<AnalyticsLoader />);
      render(<AnalyticsLoader />);

      // Each instance should attempt to load analytics
      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledTimes(2);
    });
  });

  describe('Performance', () => {
    it('should not re-render unnecessarily', () => {
      const { rerender } = render(<AnalyticsLoader />);

      mockConsentManager.loadAnalyticsIfConsented.mockClear();

      // Force re-render
      rerender(<AnalyticsLoader />);

      // Should not call loadAnalyticsIfConsented again on re-render
      expect(mockConsentManager.loadAnalyticsIfConsented).not.toHaveBeenCalled();
    });

    it('should set up listeners only once', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener');

      render(<AnalyticsLoader />);

      // Should add two listeners: loadAnalytics and consentChanged
      const loadAnalyticsCalls = addEventListenerSpy.mock.calls.filter(
        call => call[0] === 'loadAnalytics'
      );
      const consentChangedCalls = addEventListenerSpy.mock.calls.filter(
        call => call[0] === 'consentChanged'
      );

      expect(loadAnalyticsCalls.length).toBe(1);
      expect(consentChangedCalls.length).toBe(1);

      addEventListenerSpy.mockRestore();
    });
  });

  describe('Edge Cases', () => {
    it('should work in client-side environment', () => {
      // This component is marked as 'use client', so it runs in client
      expect(() => {
        render(<AnalyticsLoader />);
      }).not.toThrow();
    });

    it('should have access to window object', () => {
      render(<AnalyticsLoader />);

      expect(typeof window).toBe('object');
      expect(window.addEventListener).toBeDefined();
      expect(window.removeEventListener).toBeDefined();
    });

    it('should handle component being rendered multiple times', () => {
      const { rerender } = render(<AnalyticsLoader />);

      rerender(<AnalyticsLoader />);
      rerender(<AnalyticsLoader />);

      // Should only load analytics once (on initial mount)
      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledTimes(1);
    });
  });

  describe('useEffect Hook', () => {
    it('should run effect on mount', () => {
      mockConsentManager.loadAnalyticsIfConsented.mockClear();

      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalled();
    });

    it('should have empty dependency array', () => {
      // This test ensures the effect runs only on mount
      const { rerender } = render(<AnalyticsLoader />);

      const callCount = mockConsentManager.loadAnalyticsIfConsented.mock.calls.length;

      // Rerender several times
      rerender(<AnalyticsLoader />);
      rerender(<AnalyticsLoader />);
      rerender(<AnalyticsLoader />);

      // Call count should not increase
      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledTimes(callCount);
    });

    it('should cleanup on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = render(<AnalyticsLoader />);
      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalled();

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Measurement ID Configuration', () => {
    it('should use configured measurement ID', () => {
      render(<AnalyticsLoader />);

      expect(mockConsentManager.loadAnalyticsIfConsented).toHaveBeenCalledWith('G-TEST123456');
    });

    it('should pass non-empty measurement ID', () => {
      render(<AnalyticsLoader />);

      const calls = mockConsentManager.loadAnalyticsIfConsented.mock.calls;
      expect(calls.length).toBeGreaterThan(0);
      expect(calls[0][0]).toBeTruthy();
      expect(typeof calls[0][0]).toBe('string');
    });
  });
});
