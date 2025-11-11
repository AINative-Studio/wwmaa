'use client';

import React, { useState } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import Link from 'next/link';
import { AlertCircle } from 'lucide-react';

interface TermsAcceptanceCheckboxProps {
  /**
   * Controlled value for the checkbox
   */
  checked: boolean;

  /**
   * Callback when checkbox state changes
   */
  onCheckedChange: (checked: boolean) => void;

  /**
   * Whether to show error state
   */
  showError?: boolean;

  /**
   * Custom error message
   */
  errorMessage?: string;

  /**
   * Whether the checkbox is disabled
   */
  disabled?: boolean;

  /**
   * Custom ID for the checkbox (for form association)
   */
  id?: string;

  /**
   * Terms version being accepted (defaults to current)
   */
  termsVersion?: string;

  /**
   * Privacy policy version being accepted (defaults to current)
   */
  privacyVersion?: string;

  /**
   * Whether to show version numbers in the label
   */
  showVersions?: boolean;
}

/**
 * Terms Acceptance Checkbox Component
 *
 * Displays a checkbox for accepting Terms of Service and Privacy Policy
 * with links to the legal documents. Used during registration and when
 * terms are updated.
 *
 * Features:
 * - Links to Terms and Privacy Policy pages
 * - Error state display
 * - Version tracking
 * - Accessibility compliant
 * - Opens legal documents in new tab
 *
 * @example
 * ```tsx
 * const [termsAccepted, setTermsAccepted] = useState(false);
 * const [showError, setShowError] = useState(false);
 *
 * <TermsAcceptanceCheckbox
 *   checked={termsAccepted}
 *   onCheckedChange={setTermsAccepted}
 *   showError={showError}
 * />
 * ```
 */
export function TermsAcceptanceCheckbox({
  checked,
  onCheckedChange,
  showError = false,
  errorMessage = 'You must accept the Terms of Service and Privacy Policy to continue',
  disabled = false,
  id = 'terms-acceptance',
  termsVersion = '1.0',
  privacyVersion = '1.0',
  showVersions = false,
}: TermsAcceptanceCheckboxProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-start space-x-2">
        <Checkbox
          id={id}
          checked={checked}
          onCheckedChange={onCheckedChange}
          disabled={disabled}
          className={showError && !checked ? 'border-destructive' : ''}
          aria-invalid={showError && !checked}
          aria-describedby={showError && !checked ? `${id}-error` : undefined}
        />
        <div className="grid gap-1.5 leading-none">
          <Label
            htmlFor={id}
            className={`text-sm font-medium leading-relaxed cursor-pointer ${
              showError && !checked ? 'text-destructive' : ''
            }`}
          >
            I accept the{' '}
            <Link
              href="/terms"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline hover:text-primary/80 font-semibold"
              onClick={(e) => e.stopPropagation()}
            >
              Terms of Service
              {showVersions && ` (v${termsVersion})`}
            </Link>{' '}
            and{' '}
            <Link
              href="/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline hover:text-primary/80 font-semibold"
              onClick={(e) => e.stopPropagation()}
            >
              Privacy Policy
              {showVersions && ` (v${privacyVersion})`}
            </Link>
            <span className="text-destructive ml-1" aria-label="required">
              *
            </span>
          </Label>
          <p className="text-xs text-muted-foreground">
            By checking this box, you acknowledge that you have read and understood both documents.
            {showVersions && ' The version numbers indicate which version you are accepting.'}
          </p>
        </div>
      </div>

      {showError && !checked && (
        <div
          id={`${id}-error`}
          className="flex items-center gap-2 text-sm text-destructive mt-2"
          role="alert"
        >
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}

/**
 * Hook for managing terms acceptance state
 *
 * Provides state management and validation for terms acceptance
 *
 * @example
 * ```tsx
 * const {
 *   termsAccepted,
 *   setTermsAccepted,
 *   showError,
 *   validate,
 *   reset
 * } = useTermsAcceptance();
 *
 * const handleSubmit = () => {
 *   if (!validate()) {
 *     return; // Terms not accepted
 *   }
 *   // Proceed with form submission
 * };
 * ```
 */
export function useTermsAcceptance() {
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [showError, setShowError] = useState(false);

  /**
   * Validate that terms have been accepted
   * Shows error if not accepted
   * @returns true if accepted, false otherwise
   */
  const validate = (): boolean => {
    if (!termsAccepted) {
      setShowError(true);
      return false;
    }
    setShowError(false);
    return true;
  };

  /**
   * Reset the acceptance state
   */
  const reset = () => {
    setTermsAccepted(false);
    setShowError(false);
  };

  /**
   * Handle checkbox change with automatic error clearing
   */
  const handleChange = (checked: boolean) => {
    setTermsAccepted(checked);
    if (checked) {
      setShowError(false);
    }
  };

  return {
    termsAccepted,
    setTermsAccepted: handleChange,
    showError,
    setShowError,
    validate,
    reset,
  };
}

/**
 * Terms Update Banner Component
 *
 * Displays a banner when terms have been updated and user needs to accept new version.
 * Typically shown at the top of the app for logged-in users.
 *
 * @example
 * ```tsx
 * <TermsUpdateBanner
 *   onAccept={handleAcceptUpdatedTerms}
 *   onDismiss={handleDismiss}
 *   newTermsVersion="1.1"
 *   newPrivacyVersion="1.1"
 * />
 * ```
 */
interface TermsUpdateBannerProps {
  onAccept: () => Promise<void>;
  onDismiss?: () => void;
  newTermsVersion?: string;
  newPrivacyVersion?: string;
}

export function TermsUpdateBanner({
  onAccept,
  onDismiss,
  newTermsVersion = '1.0',
  newPrivacyVersion = '1.0',
}: TermsUpdateBannerProps) {
  const [isAccepting, setIsAccepting] = useState(false);
  const { termsAccepted, setTermsAccepted, showError, validate } = useTermsAcceptance();

  const handleAccept = async () => {
    if (!validate()) {
      return;
    }

    setIsAccepting(true);
    try {
      await onAccept();
    } catch (error) {
      console.error('Failed to accept terms:', error);
    } finally {
      setIsAccepting(false);
    }
  };

  return (
    <div className="bg-amber-50 border-b border-amber-200 dark:bg-amber-950 dark:border-amber-800">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-1">
              Updated Terms of Service and Privacy Policy
            </h3>
            <p className="text-sm text-amber-700 dark:text-amber-300">
              We&apos;ve updated our legal documents. Please review and accept the changes to continue
              using WWMAA services.
            </p>
            <div className="mt-3">
              <TermsAcceptanceCheckbox
                checked={termsAccepted}
                onCheckedChange={setTermsAccepted}
                showError={showError}
                termsVersion={newTermsVersion}
                privacyVersion={newPrivacyVersion}
                showVersions
                errorMessage="You must accept the updated terms to continue using our services"
              />
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleAccept}
              disabled={isAccepting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
            >
              {isAccepting ? 'Accepting...' : 'Accept & Continue'}
            </button>
            {onDismiss && (
              <button
                onClick={onDismiss}
                disabled={isAccepting}
                className="px-4 py-2 bg-transparent text-amber-900 dark:text-amber-100 border border-amber-300 dark:border-amber-700 rounded-md hover:bg-amber-100 dark:hover:bg-amber-900 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
              >
                Remind Me Later
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
