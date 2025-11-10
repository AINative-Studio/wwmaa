'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, Loader2, AlertCircle } from 'lucide-react';

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [sessionData, setSessionData] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const sessionId = searchParams.get('session_id');

    if (!sessionId) {
      setStatus('error');
      setErrorMessage('No session ID provided');
      return;
    }

    // Verify and process the payment
    const processPayment = async () => {
      try {
        // Retrieve session details
        const retrieveResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/checkout/retrieve-session`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!retrieveResponse.ok) {
          throw new Error('Failed to retrieve session');
        }

        const sessionInfo = await retrieveResponse.json();

        // Check if payment was successful
        if (sessionInfo.payment_status !== 'paid') {
          setStatus('error');
          setErrorMessage('Payment was not completed');
          return;
        }

        // Process the payment to create subscription
        const processResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/checkout/process-payment`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!processResponse.ok) {
          throw new Error('Failed to process payment');
        }

        const processResult = await processResponse.json();
        setSessionData(processResult);
        setStatus('success');

        // Redirect to dashboard after 5 seconds
        setTimeout(() => {
          router.push('/dashboard');
        }, 5000);

      } catch (error: any) {
        console.error('Payment processing error:', error);
        setStatus('error');
        setErrorMessage(error.message || 'Failed to process payment');
      }
    };

    processPayment();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        {/* Loading State */}
        {status === 'loading' && (
          <div className="text-center">
            <Loader2 className="w-16 h-16 text-red-800 animate-spin mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Processing Your Payment
            </h1>
            <p className="text-gray-600">
              Please wait while we confirm your payment...
            </p>
          </div>
        )}

        {/* Success State */}
        {status === 'success' && (
          <div className="text-center">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Payment Successful!
            </h1>
            <p className="text-lg text-gray-600 mb-6">
              Thank you for your payment. Your WWMAA membership is now active!
            </p>

            {sessionData && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6 text-left">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Payment Details
                </h2>
                <div className="space-y-2 text-gray-700">
                  <div className="flex justify-between">
                    <span>Membership Tier:</span>
                    <span className="font-medium">{sessionData.tier?.charAt(0).toUpperCase() + sessionData.tier?.slice(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Amount Paid:</span>
                    <span className="font-medium">${sessionData.amount?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Transaction ID:</span>
                    <span className="font-medium text-sm">{sessionData.subscription_id?.substring(0, 24)}...</span>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-left">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                What's Next?
              </h2>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Access your member dashboard</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Browse and register for exclusive events</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Connect with other members</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  <span>Access training videos and resources</span>
                </li>
              </ul>
            </div>

            <p className="text-sm text-gray-500 mb-6">
              You will be automatically redirected to your dashboard in 5 seconds...
            </p>

            <div className="flex gap-4 justify-center">
              <Link
                href="/dashboard"
                className="inline-flex items-center px-6 py-3 bg-red-800 text-white font-semibold rounded-lg hover:bg-red-900 transition"
              >
                Go to Dashboard
              </Link>
              <Link
                href="/events"
                className="inline-flex items-center px-6 py-3 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300 transition"
              >
                Browse Events
              </Link>
            </div>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && (
          <div className="text-center">
            <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Payment Processing Error
            </h1>
            <p className="text-gray-600 mb-6">
              {errorMessage || 'There was an issue processing your payment. Please contact support if you believe this is an error.'}
            </p>

            <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6 text-left">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                What Should I Do?
              </h2>
              <ul className="space-y-2 text-gray-700">
                <li>Check your email for a payment confirmation</li>
                <li>Contact support at membership@wwmaa.org</li>
                <li>Try accessing your dashboard to check membership status</li>
              </ul>
            </div>

            <div className="flex gap-4 justify-center">
              <Link
                href="/dashboard"
                className="inline-flex items-center px-6 py-3 bg-red-800 text-white font-semibold rounded-lg hover:bg-red-900 transition"
              >
                Check Dashboard
              </Link>
              <Link
                href="/contact"
                className="inline-flex items-center px-6 py-3 bg-gray-200 text-gray-800 font-semibold rounded-lg hover:bg-gray-300 transition"
              >
                Contact Support
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
