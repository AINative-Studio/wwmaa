'use client';

/**
 * Cookie Consent Banner
 * GDPR/CCPA compliant cookie consent banner
 * Displays on first visit, allows users to accept/reject/customize cookies
 */

import { useState, useEffect } from 'react';
import { useCookieConsent } from '@/hooks/use-cookie-consent';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { X, Cookie, ChevronDown, ChevronUp } from 'lucide-react';

export function CookieBanner() {
  const { hasConsented, acceptAllCookies, rejectAllCookies, updateConsent } = useCookieConsent();
  const [isVisible, setIsVisible] = useState(false);
  const [showCustomize, setShowCustomize] = useState(false);

  // Consent preferences for customize view
  const [functional, setFunctional] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);

  // Show banner only if user hasn't consented
  useEffect(() => {
    // Small delay to avoid flash on page load
    const timer = setTimeout(() => {
      setIsVisible(!hasConsented);
    }, 500);

    return () => clearTimeout(timer);
  }, [hasConsented]);

  const handleAcceptAll = () => {
    acceptAllCookies();
    setIsVisible(false);
  };

  const handleRejectAll = () => {
    rejectAllCookies();
    setIsVisible(false);
  };

  const handleCustomize = () => {
    setShowCustomize(!showCustomize);
  };

  const handleSavePreferences = () => {
    updateConsent({
      functional,
      analytics,
      marketing,
    });
    setIsVisible(false);
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="fixed inset-x-0 bottom-0 z-50 pb-4 px-4 sm:px-6 lg:px-8"
      role="dialog"
      aria-live="polite"
      aria-label="Cookie consent banner"
    >
      <div className="mx-auto max-w-7xl">
        <div className="rounded-lg bg-white shadow-2xl ring-1 ring-black/5 dark:bg-gray-900 dark:ring-white/10">
          <div className="p-6 sm:p-8">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <Cookie className="h-6 w-6 text-dojo-gold" aria-hidden="true" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  We Value Your Privacy
                </h2>
              </div>
              <button
                onClick={handleRejectAll}
                className="text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400 transition-colors"
                aria-label="Close and reject all cookies"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            {/* Description */}
            <div className="mt-4 text-sm text-gray-600 dark:text-gray-300">
              <p>
                We use cookies to enhance your browsing experience, analyze site traffic, and personalize content.
                By clicking "Accept All", you consent to our use of cookies.{' '}
                <a
                  href="/privacy"
                  className="font-medium text-dojo-navy hover:text-dojo-gold underline dark:text-dojo-light dark:hover:text-dojo-gold transition-colors"
                >
                  Read our Privacy Policy
                </a>
              </p>
            </div>

            {/* Customize Options */}
            {showCustomize && (
              <div className="mt-6 space-y-4 border-t border-gray-200 pt-6 dark:border-gray-700">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Cookie Preferences
                </div>

                {/* Essential Cookies - Always On */}
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="essential"
                    checked={true}
                    disabled
                    className="mt-0.5"
                    aria-describedby="essential-description"
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor="essential"
                      className="text-sm font-medium text-gray-900 dark:text-white cursor-not-allowed"
                    >
                      Essential Cookies (Required)
                    </Label>
                    <p id="essential-description" className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      These cookies are necessary for the website to function properly. They enable basic features like page navigation and access to secure areas.
                    </p>
                  </div>
                </div>

                {/* Functional Cookies */}
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="functional"
                    checked={functional}
                    onCheckedChange={(checked) => setFunctional(checked as boolean)}
                    className="mt-0.5"
                    aria-describedby="functional-description"
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor="functional"
                      className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer"
                    >
                      Functional Cookies
                    </Label>
                    <p id="functional-description" className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      These cookies remember your preferences and settings, such as language selection and login state, to provide a personalized experience.
                    </p>
                  </div>
                </div>

                {/* Analytics Cookies */}
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="analytics"
                    checked={analytics}
                    onCheckedChange={(checked) => setAnalytics(checked as boolean)}
                    className="mt-0.5"
                    aria-describedby="analytics-description"
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor="analytics"
                      className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer"
                    >
                      Analytics Cookies
                    </Label>
                    <p id="analytics-description" className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      These cookies help us understand how visitors interact with our website by collecting anonymous information about page visits and user behavior.
                    </p>
                  </div>
                </div>

                {/* Marketing Cookies */}
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="marketing"
                    checked={marketing}
                    onCheckedChange={(checked) => setMarketing(checked as boolean)}
                    className="mt-0.5"
                    aria-describedby="marketing-description"
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor="marketing"
                      className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer"
                    >
                      Marketing Cookies
                    </Label>
                    <p id="marketing-description" className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      These cookies track your online activity to help show you more relevant advertisements and measure the effectiveness of marketing campaigns.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Button
                variant="outline"
                onClick={handleCustomize}
                className="w-full sm:w-auto"
                aria-expanded={showCustomize}
              >
                {showCustomize ? (
                  <>
                    <ChevronUp className="mr-2 h-4 w-4" aria-hidden="true" />
                    Hide Options
                  </>
                ) : (
                  <>
                    <ChevronDown className="mr-2 h-4 w-4" aria-hidden="true" />
                    Customize
                  </>
                )}
              </Button>

              {showCustomize ? (
                <Button
                  onClick={handleSavePreferences}
                  className="w-full sm:w-auto bg-dojo-navy hover:bg-dojo-navy/90"
                >
                  Save Preferences
                </Button>
              ) : (
                <>
                  <Button
                    variant="outline"
                    onClick={handleRejectAll}
                    className="w-full sm:w-auto"
                  >
                    Reject All
                  </Button>
                  <Button
                    onClick={handleAcceptAll}
                    className="w-full sm:w-auto bg-dojo-navy hover:bg-dojo-navy/90"
                  >
                    Accept All
                  </Button>
                </>
              )}
            </div>

            {/* Compliance Notice */}
            <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
              This banner complies with GDPR and CCPA regulations. You can change your preferences at any time via the Cookie Preferences link in our footer.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
