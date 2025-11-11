'use client';

/**
 * Cookie Settings Modal
 * Allows users to update their cookie preferences at any time
 * Accessible via footer link
 */

import { useState, useEffect } from 'react';
import { useCookieConsent } from '@/hooks/use-cookie-consent';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Cookie, Info } from 'lucide-react';

interface CookieSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CookieSettingsModal({ open, onOpenChange }: CookieSettingsModalProps) {
  const { consent, updateConsent, acceptAllCookies, rejectAllCookies } = useCookieConsent();

  // Local state for preferences
  const [functional, setFunctional] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);

  // Load current consent when modal opens
  useEffect(() => {
    if (open && consent) {
      setFunctional(consent.functional);
      setAnalytics(consent.analytics);
      setMarketing(consent.marketing);
    }
  }, [open, consent]);

  const handleSave = () => {
    updateConsent({
      functional,
      analytics,
      marketing,
    });
    onOpenChange(false);
  };

  const handleAcceptAll = () => {
    acceptAllCookies();
    onOpenChange(false);
  };

  const handleRejectAll = () => {
    rejectAllCookies();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-dojo-gold/10 p-2">
              <Cookie className="h-6 w-6 text-dojo-gold" aria-hidden="true" />
            </div>
            <DialogTitle className="text-2xl">Cookie Preferences</DialogTitle>
          </div>
          <DialogDescription className="text-base">
            Manage your cookie preferences. You can enable or disable different types of cookies below.
            Changes will take effect immediately.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Current Consent Info */}
          {consent && (
            <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-950/30">
              <div className="flex gap-3">
                <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-medium">Current Consent Status</p>
                  <p className="mt-1">
                    Last updated: {new Date(consent.timestamp).toLocaleDateString()} at{' '}
                    {new Date(consent.timestamp).toLocaleTimeString()}
                  </p>
                  <p className="mt-1 text-xs text-blue-700 dark:text-blue-300">
                    Policy Version: {consent.version}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Cookie Categories */}
          <div className="space-y-6">
            {/* Essential Cookies */}
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Checkbox
                  id="modal-essential"
                  checked={true}
                  disabled
                  className="mt-0.5"
                  aria-describedby="modal-essential-description"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="modal-essential"
                    className="text-base font-semibold text-gray-900 dark:text-white cursor-not-allowed"
                  >
                    Essential Cookies
                    <span className="ml-2 inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                      Always Active
                    </span>
                  </Label>
                  <p id="modal-essential-description" className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    These cookies are necessary for the website to function and cannot be disabled. They are
                    usually only set in response to actions made by you, such as setting your privacy preferences,
                    logging in, or filling in forms. Without these cookies, some parts of our website would not work.
                  </p>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                    Examples: Session management, security tokens, consent preferences
                  </div>
                </div>
              </div>
            </div>

            {/* Functional Cookies */}
            <div className="space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
              <div className="flex items-start gap-3">
                <Checkbox
                  id="modal-functional"
                  checked={functional}
                  onCheckedChange={(checked) => setFunctional(checked as boolean)}
                  className="mt-0.5"
                  aria-describedby="modal-functional-description"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="modal-functional"
                    className="text-base font-semibold text-gray-900 dark:text-white cursor-pointer"
                  >
                    Functional Cookies
                  </Label>
                  <p id="modal-functional-description" className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    These cookies enable enhanced functionality and personalization. They may be set by us or by
                    third-party providers whose services we have added to our pages. If you do not allow these
                    cookies, some or all of these features may not work properly.
                  </p>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                    Examples: Language preferences, theme settings, form auto-fill, video players
                  </div>
                </div>
              </div>
            </div>

            {/* Analytics Cookies */}
            <div className="space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
              <div className="flex items-start gap-3">
                <Checkbox
                  id="modal-analytics"
                  checked={analytics}
                  onCheckedChange={(checked) => setAnalytics(checked as boolean)}
                  className="mt-0.5"
                  aria-describedby="modal-analytics-description"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="modal-analytics"
                    className="text-base font-semibold text-gray-900 dark:text-white cursor-pointer"
                  >
                    Analytics Cookies
                  </Label>
                  <p id="modal-analytics-description" className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    These cookies help us understand how visitors interact with our website by collecting and
                    reporting information anonymously. This helps us improve our website and understand which
                    pages are most popular. All information is aggregated and anonymous.
                  </p>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                    Examples: Google Analytics, page views, bounce rate, traffic sources
                  </div>
                </div>
              </div>
            </div>

            {/* Marketing Cookies */}
            <div className="space-y-3 border-t border-gray-200 pt-6 dark:border-gray-700">
              <div className="flex items-start gap-3">
                <Checkbox
                  id="modal-marketing"
                  checked={marketing}
                  onCheckedChange={(checked) => setMarketing(checked as boolean)}
                  className="mt-0.5"
                  aria-describedby="modal-marketing-description"
                />
                <div className="flex-1">
                  <Label
                    htmlFor="modal-marketing"
                    className="text-base font-semibold text-gray-900 dark:text-white cursor-pointer"
                  >
                    Marketing Cookies
                  </Label>
                  <p id="modal-marketing-description" className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    These cookies track your online activity to help advertisers deliver more relevant advertising
                    or to limit how many times you see an advertisement. These cookies may share information with
                    other organizations or advertisers.
                  </p>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                    Examples: Ad targeting, retargeting campaigns, social media advertising, conversion tracking
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Information */}
          <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Need More Information?
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              For more details about how we use cookies and protect your data, please read our{' '}
              <a
                href="/privacy"
                className="font-medium text-dojo-navy hover:text-dojo-gold underline dark:text-dojo-light dark:hover:text-dojo-gold transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >
                Privacy Policy
              </a>{' '}
              and{' '}
              <a
                href="/cookie-policy"
                className="font-medium text-dojo-navy hover:text-dojo-gold underline dark:text-dojo-light dark:hover:text-dojo-gold transition-colors"
                target="_blank"
                rel="noopener noreferrer"
              >
                Cookie Policy
              </a>
              .
            </p>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-row">
          <div className="flex flex-1 gap-2">
            <Button
              variant="outline"
              onClick={handleRejectAll}
              className="flex-1 sm:flex-none"
            >
              Reject All
            </Button>
            <Button
              variant="outline"
              onClick={handleAcceptAll}
              className="flex-1 sm:flex-none"
            >
              Accept All
            </Button>
          </div>
          <Button
            onClick={handleSave}
            className="w-full sm:w-auto bg-dojo-navy hover:bg-dojo-navy/90"
          >
            Save Preferences
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
