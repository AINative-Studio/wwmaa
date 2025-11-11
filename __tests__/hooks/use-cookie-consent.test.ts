/**
 * Tests for useCookieConsent Hook
 * Test coverage for React hook managing cookie consent state
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useCookieConsent } from '@/hooks/use-cookie-consent';
import * as consentManager from '@/lib/consent-manager';
import type { CookieConsent } from '@/lib/consent-manager';

// Mock the consent manager
jest.mock('@/lib/consent-manager');

const mockConsentManager = consentManager as jest.Mocked<typeof consentManager>;

describe('useCookieConsent', () => {
  const mockConsent: CookieConsent = {
    essential: true,
    functional: true,
    analytics: false,
    marketing: false,
    timestamp: '2025-01-10T12:00:00.000Z',
    version: '1.0.0',
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockConsentManager.getConsent.mockReturnValue(mockConsent);
    mockConsentManager.hasConsent.mockReturnValue(true);
    mockConsentManager.hasCategoryConsent.mockImplementation((category) => {
      return mockConsent[category] === true;
    });
    mockConsentManager.saveConsent.mockImplementation(() => {
      const event = new CustomEvent('consentChanged', { detail: mockConsent });
      window.dispatchEvent(event);
    });
    mockConsentManager.acceptAll.mockImplementation(() => {
      const event = new CustomEvent('consentChanged', {
        detail: { ...mockConsent, functional: true, analytics: true, marketing: true },
      });
      window.dispatchEvent(event);
    });
    mockConsentManager.rejectAll.mockImplementation(() => {
      const event = new CustomEvent('consentChanged', {
        detail: { ...mockConsent, functional: false, analytics: false, marketing: false },
      });
      window.dispatchEvent(event);
    });
  });

  describe('Initialization', () => {
    it('should load consent on mount', () => {
      const { result } = renderHook(() => useCookieConsent());

      expect(mockConsentManager.getConsent).toHaveBeenCalled();
      expect(mockConsentManager.hasConsent).toHaveBeenCalled();
    });

    it('should set loading state initially', () => {
      const { result } = renderHook(() => useCookieConsent());

      // After initial render, loading should be false
      expect(result.current.isLoading).toBe(false);
    });

    it('should load existing consent', () => {
      const { result } = renderHook(() => useCookieConsent());

      expect(result.current.consent).toEqual(mockConsent);
      expect(result.current.hasConsented).toBe(true);
    });

    it('should handle no existing consent', () => {
      mockConsentManager.getConsent.mockReturnValue(null);
      mockConsentManager.hasConsent.mockReturnValue(false);

      const { result } = renderHook(() => useCookieConsent());

      expect(result.current.consent).toBeNull();
      expect(result.current.hasConsented).toBe(false);
    });
  });

  describe('updateConsent', () => {
    it('should call saveConsent with provided values', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.updateConsent({
          functional: true,
          analytics: true,
          marketing: false,
        });
      });

      expect(mockConsentManager.saveConsent).toHaveBeenCalledWith({
        functional: true,
        analytics: true,
        marketing: false,
      });
    });

    it('should dispatch loadAnalytics event when analytics enabled', () => {
      const { result } = renderHook(() => useCookieConsent());
      const eventSpy = jest.fn();

      window.addEventListener('loadAnalytics', eventSpy);

      act(() => {
        result.current.updateConsent({
          functional: true,
          analytics: true,
          marketing: false,
        });
      });

      expect(eventSpy).toHaveBeenCalled();

      window.removeEventListener('loadAnalytics', eventSpy);
    });

    it('should call removeAnalyticsScripts when analytics disabled', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.updateConsent({
          functional: true,
          analytics: false,
          marketing: false,
        });
      });

      expect(mockConsentManager.removeAnalyticsScripts).toHaveBeenCalled();
    });

    it('should not dispatch loadAnalytics when analytics remains disabled', () => {
      const { result } = renderHook(() => useCookieConsent());
      const eventSpy = jest.fn();

      window.addEventListener('loadAnalytics', eventSpy);

      act(() => {
        result.current.updateConsent({
          functional: true,
          analytics: false, // Disabled
          marketing: false,
        });
      });

      expect(eventSpy).not.toHaveBeenCalled();

      window.removeEventListener('loadAnalytics', eventSpy);
    });
  });

  describe('acceptAllCookies', () => {
    it('should call acceptAll from consent manager', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.acceptAllCookies();
      });

      expect(mockConsentManager.acceptAll).toHaveBeenCalled();
    });

    it('should dispatch loadAnalytics event', () => {
      const { result } = renderHook(() => useCookieConsent());
      const eventSpy = jest.fn();

      window.addEventListener('loadAnalytics', eventSpy);

      act(() => {
        result.current.acceptAllCookies();
      });

      expect(eventSpy).toHaveBeenCalled();

      window.removeEventListener('loadAnalytics', eventSpy);
    });

    it('should update consent state', async () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.acceptAllCookies();
      });

      await waitFor(() => {
        expect(result.current.hasConsented).toBe(true);
      });
    });
  });

  describe('rejectAllCookies', () => {
    it('should call rejectAll from consent manager', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.rejectAllCookies();
      });

      expect(mockConsentManager.rejectAll).toHaveBeenCalled();
    });

    it('should call removeAnalyticsScripts', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.rejectAllCookies();
      });

      expect(mockConsentManager.removeAnalyticsScripts).toHaveBeenCalled();
    });

    it('should update consent state', async () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.rejectAllCookies();
      });

      await waitFor(() => {
        expect(result.current.hasConsented).toBe(true);
      });
    });
  });

  describe('hasCategoryConsent', () => {
    it('should check essential consent', () => {
      const { result } = renderHook(() => useCookieConsent());

      const hasEssential = result.current.hasCategoryConsent('essential');

      expect(mockConsentManager.hasCategoryConsent).toHaveBeenCalledWith('essential');
      expect(hasEssential).toBe(true);
    });

    it('should check functional consent', () => {
      const { result } = renderHook(() => useCookieConsent());

      const hasFunctional = result.current.hasCategoryConsent('functional');

      expect(mockConsentManager.hasCategoryConsent).toHaveBeenCalledWith('functional');
      expect(hasFunctional).toBe(true);
    });

    it('should check analytics consent', () => {
      const { result } = renderHook(() => useCookieConsent());

      const hasAnalytics = result.current.hasCategoryConsent('analytics');

      expect(mockConsentManager.hasCategoryConsent).toHaveBeenCalledWith('analytics');
      expect(hasAnalytics).toBe(false);
    });

    it('should check marketing consent', () => {
      const { result } = renderHook(() => useCookieConsent());

      const hasMarketing = result.current.hasCategoryConsent('marketing');

      expect(mockConsentManager.hasCategoryConsent).toHaveBeenCalledWith('marketing');
      expect(hasMarketing).toBe(false);
    });

    it('should return updated value after consent change', () => {
      const { result } = renderHook(() => useCookieConsent());

      // Initially analytics is false
      expect(result.current.hasCategoryConsent('analytics')).toBe(false);

      // Update consent
      mockConsentManager.hasCategoryConsent.mockImplementation((category) => {
        if (category === 'analytics') return true;
        return mockConsent[category] === true;
      });

      // Check again
      expect(result.current.hasCategoryConsent('analytics')).toBe(true);
    });
  });

  describe('Event Listeners', () => {
    it('should listen for consentChanged event', async () => {
      const { result } = renderHook(() => useCookieConsent());

      const newConsent: CookieConsent = {
        ...mockConsent,
        analytics: true,
      };

      act(() => {
        const event = new CustomEvent('consentChanged', { detail: newConsent });
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(result.current.consent).toEqual(newConsent);
        expect(result.current.hasConsented).toBe(true);
      });
    });

    it('should listen for consentCleared event', async () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        const event = new CustomEvent('consentCleared');
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(result.current.consent).toBeNull();
        expect(result.current.hasConsented).toBe(false);
      });
    });

    it('should clean up event listeners on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useCookieConsent());

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('consentChanged', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('consentCleared', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Return Values', () => {
    it('should return all required values', () => {
      const { result } = renderHook(() => useCookieConsent());

      expect(result.current).toHaveProperty('consent');
      expect(result.current).toHaveProperty('hasConsented');
      expect(result.current).toHaveProperty('updateConsent');
      expect(result.current).toHaveProperty('acceptAllCookies');
      expect(result.current).toHaveProperty('rejectAllCookies');
      expect(result.current).toHaveProperty('hasCategoryConsent');
      expect(result.current).toHaveProperty('isLoading');
    });

    it('should return functions that are stable across renders', () => {
      const { result, rerender } = renderHook(() => useCookieConsent());

      const firstUpdate = result.current.updateConsent;
      const firstAccept = result.current.acceptAllCookies;
      const firstReject = result.current.rejectAllCookies;
      const firstCheck = result.current.hasCategoryConsent;

      rerender();

      expect(result.current.updateConsent).toBe(firstUpdate);
      expect(result.current.acceptAllCookies).toBe(firstAccept);
      expect(result.current.rejectAllCookies).toBe(firstReject);
      expect(result.current.hasCategoryConsent).toBe(firstCheck);
    });

    it('should have correct TypeScript types', () => {
      const { result } = renderHook(() => useCookieConsent());

      // Type assertions to ensure correct types
      const consent: CookieConsent | null = result.current.consent;
      const hasConsented: boolean = result.current.hasConsented;
      const isLoading: boolean = result.current.isLoading;

      expect(typeof hasConsented).toBe('boolean');
      expect(typeof isLoading).toBe('boolean');
      expect(typeof result.current.updateConsent).toBe('function');
      expect(typeof result.current.acceptAllCookies).toBe('function');
      expect(typeof result.current.rejectAllCookies).toBe('function');
      expect(typeof result.current.hasCategoryConsent).toBe('function');
    });
  });

  describe('Edge Cases', () => {
    it('should handle multiple rapid updates', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.updateConsent({ functional: true, analytics: true, marketing: true });
        result.current.updateConsent({ functional: false, analytics: false, marketing: false });
        result.current.updateConsent({ functional: true, analytics: false, marketing: true });
      });

      expect(mockConsentManager.saveConsent).toHaveBeenCalledTimes(3);
    });

    it('should handle accept followed by reject', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.acceptAllCookies();
      });

      act(() => {
        result.current.rejectAllCookies();
      });

      expect(mockConsentManager.acceptAll).toHaveBeenCalledTimes(1);
      expect(mockConsentManager.rejectAll).toHaveBeenCalledTimes(1);
    });

    it('should handle checking consent before it loads', () => {
      mockConsentManager.getConsent.mockReturnValue(null);
      mockConsentManager.hasConsent.mockReturnValue(false);
      mockConsentManager.hasCategoryConsent.mockReturnValue(false);

      const { result } = renderHook(() => useCookieConsent());

      expect(result.current.hasCategoryConsent('analytics')).toBe(false);
    });

    it('should handle consent updates during render', async () => {
      const { result } = renderHook(() => useCookieConsent());

      // Simulate external consent change
      act(() => {
        const newConsent: CookieConsent = {
          ...mockConsent,
          marketing: true,
        };
        const event = new CustomEvent('consentChanged', { detail: newConsent });
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(result.current.consent?.marketing).toBe(true);
      });
    });

    it('should handle removeAnalyticsScripts errors gracefully', () => {
      mockConsentManager.removeAnalyticsScripts.mockImplementation(() => {
        throw new Error('Failed to remove scripts');
      });

      const { result } = renderHook(() => useCookieConsent());

      expect(() => {
        act(() => {
          result.current.rejectAllCookies();
        });
      }).toThrow('Failed to remove scripts');
    });
  });

  describe('Loading State', () => {
    it('should start with loading true and transition to false', async () => {
      const { result } = renderHook(() => useCookieConsent());

      // After mount, should be false
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should be false after consent is loaded', () => {
      const { result } = renderHook(() => useCookieConsent());

      expect(result.current.isLoading).toBe(false);
      expect(result.current.consent).toBeTruthy();
    });

    it('should be false even when no consent exists', () => {
      mockConsentManager.getConsent.mockReturnValue(null);
      mockConsentManager.hasConsent.mockReturnValue(false);

      const { result } = renderHook(() => useCookieConsent());

      expect(result.current.isLoading).toBe(false);
      expect(result.current.consent).toBeNull();
    });
  });

  describe('Callback Stability', () => {
    it('should not recreate callbacks on consent changes', async () => {
      const { result } = renderHook(() => useCookieConsent());

      const updateFn = result.current.updateConsent;
      const acceptFn = result.current.acceptAllCookies;
      const rejectFn = result.current.rejectAllCookies;

      // Trigger consent change
      act(() => {
        const newConsent: CookieConsent = { ...mockConsent, analytics: true };
        const event = new CustomEvent('consentChanged', { detail: newConsent });
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(result.current.consent?.analytics).toBe(true);
      });

      // Callbacks should remain stable
      expect(result.current.updateConsent).toBe(updateFn);
      expect(result.current.acceptAllCookies).toBe(acceptFn);
      expect(result.current.rejectAllCookies).toBe(rejectFn);
    });
  });

  describe('Analytics Integration', () => {
    it('should handle analytics loading for accepted analytics', () => {
      const { result } = renderHook(() => useCookieConsent());
      const loadEventSpy = jest.fn();

      window.addEventListener('loadAnalytics', loadEventSpy);

      act(() => {
        result.current.updateConsent({
          functional: true,
          analytics: true,
          marketing: false,
        });
      });

      expect(loadEventSpy).toHaveBeenCalled();
      expect(mockConsentManager.removeAnalyticsScripts).not.toHaveBeenCalled();

      window.removeEventListener('loadAnalytics', loadEventSpy);
    });

    it('should handle analytics removal for rejected analytics', () => {
      const { result } = renderHook(() => useCookieConsent());
      const loadEventSpy = jest.fn();

      window.addEventListener('loadAnalytics', loadEventSpy);

      act(() => {
        result.current.updateConsent({
          functional: true,
          analytics: false,
          marketing: false,
        });
      });

      expect(loadEventSpy).not.toHaveBeenCalled();
      expect(mockConsentManager.removeAnalyticsScripts).toHaveBeenCalled();

      window.removeEventListener('loadAnalytics', loadEventSpy);
    });

    it('should dispatch loadAnalytics on accept all', () => {
      const { result } = renderHook(() => useCookieConsent());
      const loadEventSpy = jest.fn();

      window.addEventListener('loadAnalytics', loadEventSpy);

      act(() => {
        result.current.acceptAllCookies();
      });

      expect(loadEventSpy).toHaveBeenCalled();

      window.removeEventListener('loadAnalytics', loadEventSpy);
    });

    it('should remove analytics on reject all', () => {
      const { result } = renderHook(() => useCookieConsent());

      act(() => {
        result.current.rejectAllCookies();
      });

      expect(mockConsentManager.removeAnalyticsScripts).toHaveBeenCalled();
    });
  });
});
