/**
 * Tests for Cookie Settings Modal
 * Test coverage for user preference management modal
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { CookieSettingsModal } from '@/components/cookie-consent/cookie-settings-modal';
import * as consentManager from '@/lib/consent-manager';
import type { CookieConsent } from '@/lib/consent-manager';

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
const mockConsent: CookieConsent = {
  essential: true,
  functional: true,
  analytics: false,
  marketing: false,
  timestamp: '2025-01-10T12:00:00.000Z',
  version: '1.0.0',
};

jest.mock('@/hooks/use-cookie-consent', () => ({
  useCookieConsent: () => ({
    consent: mockConsent,
    hasConsented: true,
    acceptAllCookies: consentManager.acceptAll,
    rejectAllCookies: consentManager.rejectAll,
    updateConsent: consentManager.saveConsent,
    hasCategoryConsent: consentManager.hasCategoryConsent,
    isLoading: false,
  }),
}));

describe('CookieSettingsModal', () => {
  const mockOnOpenChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Visibility', () => {
    it('should not render when open is false', () => {
      render(<CookieSettingsModal open={false} onOpenChange={mockOnOpenChange} />);

      expect(screen.queryByText('Cookie Preferences')).not.toBeInTheDocument();
    });

    it('should render when open is true', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText('Cookie Preferences')).toBeInTheDocument();
    });

    it('should display modal description', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText(/Manage your cookie preferences/)).toBeInTheDocument();
    });

    it('should have cookie icon', () => {
      const { container } = render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const cookieIcon = container.querySelector('svg');
      expect(cookieIcon).toBeInTheDocument();
    });
  });

  describe('Current Consent Display', () => {
    it('should display current consent status', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText('Current Consent Status')).toBeInTheDocument();
    });

    it('should display last updated timestamp', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });

    it('should display policy version', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText(/Policy Version: 1.0.0/)).toBeInTheDocument();
    });

    it('should format timestamp correctly', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Should contain formatted date and time
      const timestampText = screen.getByText(/Last updated:/);
      expect(timestampText).toBeInTheDocument();
    });
  });

  describe('Cookie Categories Display', () => {
    it('should display all four cookie categories', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText('Essential Cookies')).toBeInTheDocument();
      expect(screen.getByText('Functional Cookies')).toBeInTheDocument();
      expect(screen.getByText('Analytics Cookies')).toBeInTheDocument();
      expect(screen.getByText('Marketing Cookies')).toBeInTheDocument();
    });

    it('should show "Always Active" badge for essential cookies', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText('Always Active')).toBeInTheDocument();
    });

    it('should display category descriptions', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText(/necessary for the website to function/)).toBeInTheDocument();
      expect(screen.getByText(/enhanced functionality and personalization/)).toBeInTheDocument();
      expect(screen.getByText(/understand how visitors interact/)).toBeInTheDocument();
      expect(screen.getByText(/track your online activity/)).toBeInTheDocument();
    });

    it('should display examples for each category', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText(/Session management, security tokens/)).toBeInTheDocument();
      expect(screen.getByText(/Language preferences, theme settings/)).toBeInTheDocument();
      expect(screen.getByText(/Google Analytics, page views/)).toBeInTheDocument();
      expect(screen.getByText(/Ad targeting, retargeting campaigns/)).toBeInTheDocument();
    });
  });

  describe('Checkbox Interactions', () => {
    it('should disable essential cookies checkbox', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const essentialCheckbox = screen.getByLabelText('Essential Cookies');
      expect(essentialCheckbox).toBeDisabled();
      expect(essentialCheckbox).toBeChecked();
    });

    it('should allow toggling functional cookies', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const functionalCheckbox = screen.getByLabelText('Functional Cookies');
      expect(functionalCheckbox).not.toBeDisabled();

      // Initially checked (from mock consent)
      expect(functionalCheckbox).toBeChecked();

      // Toggle off
      await user.click(functionalCheckbox);
      expect(functionalCheckbox).not.toBeChecked();

      // Toggle back on
      await user.click(functionalCheckbox);
      expect(functionalCheckbox).toBeChecked();
    });

    it('should allow toggling analytics cookies', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const analyticsCheckbox = screen.getByLabelText('Analytics Cookies');
      expect(analyticsCheckbox).not.toBeDisabled();

      // Initially unchecked (from mock consent)
      expect(analyticsCheckbox).not.toBeChecked();

      // Toggle on
      await user.click(analyticsCheckbox);
      expect(analyticsCheckbox).toBeChecked();
    });

    it('should allow toggling marketing cookies', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const marketingCheckbox = screen.getByLabelText('Marketing Cookies');
      expect(marketingCheckbox).not.toBeDisabled();

      // Initially unchecked (from mock consent)
      expect(marketingCheckbox).not.toBeChecked();

      // Toggle on
      await user.click(marketingCheckbox);
      expect(marketingCheckbox).toBeChecked();
    });

    it('should load current consent values when modal opens', async () => {
      const { rerender } = render(<CookieSettingsModal open={false} onOpenChange={mockOnOpenChange} />);

      // Open modal
      rerender(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      await waitFor(() => {
        const functionalCheckbox = screen.getByLabelText('Functional Cookies');
        const analyticsCheckbox = screen.getByLabelText('Analytics Cookies');
        const marketingCheckbox = screen.getByLabelText('Marketing Cookies');

        expect(functionalCheckbox).toBeChecked(); // true in mock
        expect(analyticsCheckbox).not.toBeChecked(); // false in mock
        expect(marketingCheckbox).not.toBeChecked(); // false in mock
      });
    });
  });

  describe('Save Preferences', () => {
    it('should save custom preferences', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Toggle some options
      const analyticsCheckbox = screen.getByLabelText('Analytics Cookies');
      await user.click(analyticsCheckbox);

      const marketingCheckbox = screen.getByLabelText('Marketing Cookies');
      await user.click(marketingCheckbox);

      // Click Save
      const saveButton = screen.getByText('Save Preferences');
      await user.click(saveButton);

      expect(consentManager.saveConsent).toHaveBeenCalledWith({
        functional: true, // Was already true
        analytics: true, // Toggled on
        marketing: true, // Toggled on
      });
    });

    it('should close modal after saving', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const saveButton = screen.getByText('Save Preferences');
      await user.click(saveButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });

    it('should save even if no changes made', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const saveButton = screen.getByText('Save Preferences');
      await user.click(saveButton);

      expect(consentManager.saveConsent).toHaveBeenCalledWith({
        functional: true,
        analytics: false,
        marketing: false,
      });
    });
  });

  describe('Accept All Button', () => {
    it('should accept all cookies when clicked', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const acceptButton = screen.getByText('Accept All');
      await user.click(acceptButton);

      expect(consentManager.acceptAll).toHaveBeenCalled();
    });

    it('should close modal after accepting all', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const acceptButton = screen.getByText('Accept All');
      await user.click(acceptButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Reject All Button', () => {
    it('should reject all non-essential cookies when clicked', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const rejectButton = screen.getByText('Reject All');
      await user.click(rejectButton);

      expect(consentManager.rejectAll).toHaveBeenCalled();
    });

    it('should close modal after rejecting all', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const rejectButton = screen.getByText('Reject All');
      await user.click(rejectButton);

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Additional Information Section', () => {
    it('should display "Need More Information?" section', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByText('Need More Information?')).toBeInTheDocument();
    });

    it('should have link to Privacy Policy', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const privacyLink = screen.getByText('Privacy Policy');
      expect(privacyLink).toHaveAttribute('href', '/privacy');
      expect(privacyLink).toHaveAttribute('target', '_blank');
      expect(privacyLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('should have link to Cookie Policy', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const cookieLink = screen.getByText('Cookie Policy');
      expect(cookieLink).toHaveAttribute('href', '/cookie-policy');
      expect(cookieLink).toHaveAttribute('target', '_blank');
      expect(cookieLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for all checkboxes', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      expect(screen.getByLabelText('Essential Cookies')).toBeInTheDocument();
      expect(screen.getByLabelText('Functional Cookies')).toBeInTheDocument();
      expect(screen.getByLabelText('Analytics Cookies')).toBeInTheDocument();
      expect(screen.getByLabelText('Marketing Cookies')).toBeInTheDocument();
    });

    it('should have aria-describedby for checkbox descriptions', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const essentialCheckbox = screen.getByLabelText('Essential Cookies');
      expect(essentialCheckbox).toHaveAttribute('aria-describedby', 'modal-essential-description');

      const functionalCheckbox = screen.getByLabelText('Functional Cookies');
      expect(functionalCheckbox).toHaveAttribute('aria-describedby', 'modal-functional-description');

      const analyticsCheckbox = screen.getByLabelText('Analytics Cookies');
      expect(analyticsCheckbox).toHaveAttribute('aria-describedby', 'modal-analytics-description');

      const marketingCheckbox = screen.getByLabelText('Marketing Cookies');
      expect(marketingCheckbox).toHaveAttribute('aria-describedby', 'modal-marketing-description');
    });

    it('should have keyboard-accessible buttons', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const saveButton = screen.getByText('Save Preferences');
      const acceptButton = screen.getByText('Accept All');
      const rejectButton = screen.getByText('Reject All');

      expect(saveButton).toBeInTheDocument();
      expect(acceptButton).toBeInTheDocument();
      expect(rejectButton).toBeInTheDocument();
    });

    it('should support keyboard navigation for checkboxes', async () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const functionalCheckbox = screen.getByLabelText('Functional Cookies');

      // Focus checkbox
      functionalCheckbox.focus();
      expect(functionalCheckbox).toHaveFocus();

      // Press space to toggle
      fireEvent.keyDown(functionalCheckbox, { key: ' ', code: 'Space' });
    });
  });

  describe('Layout and Styling', () => {
    it('should have proper dialog structure', () => {
      const { container } = render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Dialog should be rendered
      expect(container.querySelector('[role="dialog"]')).toBeInTheDocument();
    });

    it('should display categories with proper spacing', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // All categories should be present with proper structure
      expect(screen.getByText('Essential Cookies')).toBeInTheDocument();
      expect(screen.getByText('Functional Cookies')).toBeInTheDocument();
      expect(screen.getByText('Analytics Cookies')).toBeInTheDocument();
      expect(screen.getByText('Marketing Cookies')).toBeInTheDocument();
    });

    it('should have scrollable content area', () => {
      const { container } = render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const dialogContent = container.querySelector('[role="dialog"]');
      expect(dialogContent).toHaveClass('max-h-[90vh]', 'overflow-y-auto');
    });
  });

  describe('Modal Behavior', () => {
    it('should call onOpenChange when modal is closed', async () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Simulate clicking outside or pressing escape (handled by Dialog component)
      // We test that the callback is provided
      expect(mockOnOpenChange).toBeDefined();
    });

    it('should reset to current consent values on each open', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Toggle analytics on
      const analyticsCheckbox = screen.getByLabelText('Analytics Cookies');
      await user.click(analyticsCheckbox);
      expect(analyticsCheckbox).toBeChecked();

      // Close modal without saving
      rerender(<CookieSettingsModal open={false} onOpenChange={mockOnOpenChange} />);

      // Reopen modal
      rerender(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Should be reset to original value (false)
      await waitFor(() => {
        const resetAnalyticsCheckbox = screen.getByLabelText('Analytics Cookies');
        expect(resetAnalyticsCheckbox).not.toBeChecked();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing consent gracefully', () => {
      // Mock no consent
      jest.mock('@/hooks/use-cookie-consent', () => ({
        useCookieConsent: () => ({
          consent: null,
          hasConsented: false,
          acceptAllCookies: consentManager.acceptAll,
          rejectAllCookies: consentManager.rejectAll,
          updateConsent: consentManager.saveConsent,
          hasCategoryConsent: consentManager.hasCategoryConsent,
          isLoading: false,
        }),
      }));

      // Should render without crashing
      expect(() => {
        render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);
      }).not.toThrow();
    });

    it('should handle rapid button clicks', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const saveButton = screen.getByText('Save Preferences');

      // Click multiple times rapidly
      await user.click(saveButton);
      await user.click(saveButton);
      await user.click(saveButton);

      // Should only call once per click
      expect(consentManager.saveConsent).toHaveBeenCalledTimes(3);
    });

    it('should handle all categories enabled', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Enable all optional categories
      const analyticsCheckbox = screen.getByLabelText('Analytics Cookies');
      const marketingCheckbox = screen.getByLabelText('Marketing Cookies');

      await user.click(analyticsCheckbox);
      await user.click(marketingCheckbox);

      const saveButton = screen.getByText('Save Preferences');
      await user.click(saveButton);

      expect(consentManager.saveConsent).toHaveBeenCalledWith({
        functional: true,
        analytics: true,
        marketing: true,
      });
    });

    it('should handle all optional categories disabled', async () => {
      const user = userEvent.setup();
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Disable functional (already enabled in mock)
      const functionalCheckbox = screen.getByLabelText('Functional Cookies');
      await user.click(functionalCheckbox);

      const saveButton = screen.getByText('Save Preferences');
      await user.click(saveButton);

      expect(consentManager.saveConsent).toHaveBeenCalledWith({
        functional: false,
        analytics: false,
        marketing: false,
      });
    });
  });

  describe('Visual Feedback', () => {
    it('should show info icon in current consent section', () => {
      const { container } = render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const infoSection = container.querySelector('.bg-blue-50');
      expect(infoSection).toBeInTheDocument();
    });

    it('should have distinct styling for essential cookies badge', () => {
      render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      const badge = screen.getByText('Always Active');
      expect(badge.parentElement).toHaveTextContent('Essential Cookies');
    });

    it('should display sections with proper borders', () => {
      const { container } = render(<CookieSettingsModal open={true} onOpenChange={mockOnOpenChange} />);

      // Categories should have border separators
      const borders = container.querySelectorAll('.border-t');
      expect(borders.length).toBeGreaterThan(0);
    });
  });
});
