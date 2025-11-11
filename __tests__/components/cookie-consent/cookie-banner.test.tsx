/**
 * Tests for Cookie Consent Banner
 * Test coverage for GDPR/CCPA compliant banner UI and interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { CookieBanner } from '@/components/cookie-consent/cookie-banner';
import * as consentManager from '@/lib/consent-manager';

// Mock the consent manager
jest.mock('@/lib/consent-manager', () => ({
  getConsent: jest.fn(),
  saveConsent: jest.fn(),
  acceptAll: jest.fn(),
  rejectAll: jest.fn(),
  hasConsent: jest.fn(),
  hasCategoryConsent: jest.fn(),
  CONSENT_VERSION: '1.0.0',
}));

// Mock the hook
jest.mock('@/hooks/use-cookie-consent', () => ({
  useCookieConsent: () => ({
    hasConsented: (consentManager.hasConsent as jest.Mock)(),
    consent: (consentManager.getConsent as jest.Mock)(),
    acceptAllCookies: consentManager.acceptAll,
    rejectAllCookies: consentManager.rejectAll,
    updateConsent: consentManager.saveConsent,
    hasCategoryConsent: consentManager.hasCategoryConsent,
    isLoading: false,
  }),
}));

describe('CookieBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Visibility', () => {
    it('should not render when user has already consented', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(true);

      render(<CookieBanner />);

      // Wait for the delay
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        expect(screen.queryByText('We Value Your Privacy')).not.toBeInTheDocument();
      });
    });

    it('should render when user has not consented', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);

      // Wait for the delay
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        expect(screen.getByText('We Value Your Privacy')).toBeInTheDocument();
      });
    });

    it('should have proper ARIA attributes', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const banner = screen.getByRole('dialog');
        expect(banner).toHaveAttribute('aria-live', 'polite');
        expect(banner).toHaveAttribute('aria-label', 'Cookie consent banner');
      });
    });
  });

  describe('Accept All Button', () => {
    it('should call acceptAll when clicked', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const acceptButton = screen.getByText('Accept All');
        fireEvent.click(acceptButton);
      });

      expect(consentManager.acceptAll).toHaveBeenCalled();
    });

    it('should hide banner after accepting', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      const { container } = render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const acceptButton = screen.getByText('Accept All');
        fireEvent.click(acceptButton);
      });

      await waitFor(() => {
        expect(container.firstChild).toBeNull();
      });
    });
  });

  describe('Reject All Button', () => {
    it('should call rejectAll when clicked', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const rejectButton = screen.getByText('Reject All');
        fireEvent.click(rejectButton);
      });

      expect(consentManager.rejectAll).toHaveBeenCalled();
    });

    it('should hide banner after rejecting', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      const { container } = render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const rejectButton = screen.getByText('Reject All');
        fireEvent.click(rejectButton);
      });

      await waitFor(() => {
        expect(container.firstChild).toBeNull();
      });
    });
  });

  describe('Customize Options', () => {
    it('should toggle customize view when clicked', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Cookie Preferences')).toBeInTheDocument();
      });
    });

    it('should show all cookie categories in customize view', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Essential Cookies (Required)')).toBeInTheDocument();
        expect(screen.getByText('Functional Cookies')).toBeInTheDocument();
        expect(screen.getByText('Analytics Cookies')).toBeInTheDocument();
        expect(screen.getByText('Marketing Cookies')).toBeInTheDocument();
      });
    });

    it('should disable essential cookies checkbox', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      await waitFor(() => {
        const essentialCheckbox = screen.getByLabelText(/Essential Cookies/);
        expect(essentialCheckbox).toBeDisabled();
        expect(essentialCheckbox).toBeChecked();
      });
    });

    it('should allow toggling functional cookies', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);
      const user = userEvent.setup({ delay: null });

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      const functionalCheckbox = await screen.findByLabelText(/Functional Cookies/);
      expect(functionalCheckbox).not.toBeChecked();

      await user.click(functionalCheckbox);
      expect(functionalCheckbox).toBeChecked();
    });

    it('should allow toggling analytics cookies', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);
      const user = userEvent.setup({ delay: null });

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      const analyticsCheckbox = await screen.findByLabelText(/Analytics Cookies/);
      expect(analyticsCheckbox).not.toBeChecked();

      await user.click(analyticsCheckbox);
      expect(analyticsCheckbox).toBeChecked();
    });

    it('should allow toggling marketing cookies', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);
      const user = userEvent.setup({ delay: null });

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      const marketingCheckbox = await screen.findByLabelText(/Marketing Cookies/);
      expect(marketingCheckbox).not.toBeChecked();

      await user.click(marketingCheckbox);
      expect(marketingCheckbox).toBeChecked();
    });
  });

  describe('Save Preferences', () => {
    it('should save custom preferences when save button clicked', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);
      const user = userEvent.setup({ delay: null });

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      // Open customize
      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      // Toggle some options
      const functionalCheckbox = await screen.findByLabelText(/Functional Cookies/);
      const analyticsCheckbox = await screen.findByLabelText(/Analytics Cookies/);

      await user.click(functionalCheckbox);
      await user.click(analyticsCheckbox);

      // Save
      const saveButton = screen.getByText('Save Preferences');
      fireEvent.click(saveButton);

      expect(consentManager.saveConsent).toHaveBeenCalledWith({
        functional: true,
        analytics: true,
        marketing: false,
      });
    });

    it('should hide banner after saving preferences', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      const { container } = render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      // Open customize
      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      // Save
      const saveButton = await screen.findByText('Save Preferences');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(container.firstChild).toBeNull();
      });
    });
  });

  describe('Close Button', () => {
    it('should have accessible close button', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const closeButton = screen.getByLabelText('Close and reject all cookies');
        expect(closeButton).toBeInTheDocument();
      });
    });

    it('should reject all cookies when close button clicked', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const closeButton = screen.getByLabelText('Close and reject all cookies');
        fireEvent.click(closeButton);
      });

      expect(consentManager.rejectAll).toHaveBeenCalled();
    });
  });

  describe('Content and Links', () => {
    it('should display privacy policy link', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const privacyLink = screen.getByText('Read our Privacy Policy');
        expect(privacyLink).toHaveAttribute('href', '/privacy');
      });
    });

    it('should display compliance notice', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        expect(screen.getByText(/GDPR and CCPA regulations/)).toBeInTheDocument();
      });
    });

    it('should display cookie descriptions', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/necessary for the website to function/)).toBeInTheDocument();
        expect(screen.getByText(/remember your preferences/)).toBeInTheDocument();
        expect(screen.getByText(/understand how visitors interact/)).toBeInTheDocument();
        expect(screen.getByText(/track your online activity/)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper checkbox labels', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      await waitFor(() => {
        expect(screen.getByLabelText(/Essential Cookies/)).toBeInTheDocument();
        expect(screen.getByLabelText(/Functional Cookies/)).toBeInTheDocument();
        expect(screen.getByLabelText(/Analytics Cookies/)).toBeInTheDocument();
        expect(screen.getByLabelText(/Marketing Cookies/)).toBeInTheDocument();
      });
    });

    it('should have aria-describedby for checkbox descriptions', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        fireEvent.click(customizeButton);
      });

      await waitFor(() => {
        const essentialCheckbox = screen.getByLabelText(/Essential Cookies/);
        expect(essentialCheckbox).toHaveAttribute('aria-describedby', 'essential-description');

        const functionalCheckbox = screen.getByLabelText(/Functional Cookies/);
        expect(functionalCheckbox).toHaveAttribute('aria-describedby', 'functional-description');
      });
    });

    it('should have aria-expanded on customize button', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const customizeButton = screen.getByText(/Customize/);
        expect(customizeButton).toHaveAttribute('aria-expanded');
      });
    });
  });

  describe('Responsive Design', () => {
    it('should render with proper mobile-friendly classes', async () => {
      (consentManager.hasConsent as jest.Mock).mockReturnValue(false);

      const { container } = render(<CookieBanner />);
      jest.advanceTimersByTime(500);

      await waitFor(() => {
        const banner = container.querySelector('.fixed');
        expect(banner).toHaveClass('pb-4', 'px-4');
      });
    });
  });
});
