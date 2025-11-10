'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { XCircle, RefreshCcw, HelpCircle } from 'lucide-react';

export default function PaymentCancelPage() {
  const [applicationId, setApplicationId] = useState<string | null>(null);

  useEffect(() => {
    // Try to get application ID from session storage if available
    const storedAppId = sessionStorage.getItem('pending_application_id');
    if (storedAppId) {
      setApplicationId(storedAppId);
    }
  }, []);

  const handleRetryPayment = () => {
    // Redirect back to create checkout session
    // This would typically redirect to a page that creates a new checkout session
    window.location.href = '/dashboard/membership';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <XCircle className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Payment Canceled
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            You canceled the payment process. No charges were made to your account.
          </p>

          {/* Information Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-left">
            <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
              <HelpCircle className="w-5 h-5 mr-2 text-blue-600" />
              What Happened?
            </h2>
            <p className="text-gray-700 mb-4">
              You navigated away from the payment page or clicked the back button before completing your payment. Your membership application is still approved and waiting for payment.
            </p>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Your application remains approved</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>No payment was processed</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>You can retry payment at any time</span>
              </li>
            </ul>
          </div>

          {/* Action Needed Box */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6 text-left">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Complete Your Membership
            </h2>
            <p className="text-gray-700 mb-4">
              To activate your WWMAA membership and access all member benefits, you'll need to complete the payment process.
            </p>
            <p className="text-sm text-gray-600">
              <strong>Note:</strong> Your payment link will remain active for 30 minutes from when it was created. If it has expired, you can request a new one from your dashboard.
            </p>
          </div>

          {/* Benefits Reminder */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-6 text-left">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              What You'll Get with Membership
            </h2>
            <div className="grid md:grid-cols-2 gap-3 text-gray-700">
              <div className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>Access to all member-only events</span>
              </div>
              <div className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>Training videos and resources</span>
              </div>
              <div className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>Member directory access</span>
              </div>
              <div className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>Monthly newsletter</span>
              </div>
              <div className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>Event discounts</span>
              </div>
              <div className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                <span>Community networking</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleRetryPayment}
              className="inline-flex items-center justify-center px-6 py-3 bg-red-800 text-white font-semibold rounded-lg hover:bg-red-900 transition"
            >
              <RefreshCcw className="w-5 h-5 mr-2" />
              Retry Payment
            </button>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center px-6 py-3 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300 transition"
            >
              Go to Dashboard
            </Link>
          </div>

          {/* Help Section */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              Need help with payment?{' '}
              <Link href="/contact" className="text-red-800 hover:text-red-900 font-semibold">
                Contact our support team
              </Link>
              {' '}or email{' '}
              <a href="mailto:membership@wwmaa.org" className="text-red-800 hover:text-red-900 font-semibold">
                membership@wwmaa.org
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
