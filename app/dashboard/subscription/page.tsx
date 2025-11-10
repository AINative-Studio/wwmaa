'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SubscriptionCard } from '@/components/subscription/subscription-card';
import { getSubscriptionDetails, createPortalSession } from '@/lib/subscription-api';
import { SubscriptionDetails } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, FileText, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function SubscriptionPage() {
  const router = useRouter();
  const [subscriptionDetails, setSubscriptionDetails] = useState<SubscriptionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    loadSubscriptionDetails();
  }, []);

  const loadSubscriptionDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const details = await getSubscriptionDetails();
      setSubscriptionDetails(details);
    } catch (err) {
      console.error('Error loading subscription:', err);
      setError(err instanceof Error ? err.message : 'Failed to load subscription details');
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      setPortalLoading(true);
      const returnUrl = `${window.location.origin}/dashboard/subscription`;
      const { url } = await createPortalSession(returnUrl);

      // Redirect to Stripe Customer Portal
      window.location.href = url;
    } catch (err) {
      console.error('Error creating portal session:', err);
      setError(err instanceof Error ? err.message : 'Failed to open billing portal');
      setPortalLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <div className="mx-auto max-w-6xl px-6 py-24">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy mb-2">
            Subscription Management
          </h1>
          <p className="text-gray-600">
            Manage your membership, billing, and payment information
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {loading && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-4 w-48 mt-2" />
              </CardHeader>
              <CardContent className="space-y-4">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          </div>
        )}

        {/* Subscription Content */}
        {!loading && subscriptionDetails && (
          <div className="space-y-6">
            {/* Main Subscription Card */}
            <SubscriptionCard
              subscriptionDetails={subscriptionDetails}
              onManageClick={handleManageSubscription}
              isLoading={portalLoading}
            />

            {/* Recent Invoices */}
            {subscriptionDetails.recent_invoices.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-dojo-navy">
                    <FileText className="w-5 h-5" />
                    Recent Invoices
                  </CardTitle>
                  <CardDescription>View and download your payment history</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {subscriptionDetails.recent_invoices.map((invoice) => (
                      <div
                        key={invoice.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900">
                            Invoice {invoice.number}
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatDate(invoice.created)}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="font-semibold text-gray-900">
                              {new Intl.NumberFormat('en-US', {
                                style: 'currency',
                                currency: invoice.currency.toUpperCase()
                              }).format(invoice.amount_paid)}
                            </div>
                            <div className="text-xs text-gray-600 capitalize">
                              {invoice.status}
                            </div>
                          </div>
                          {invoice.invoice_pdf && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => window.open(invoice.invoice_pdf, '_blank')}
                              className="gap-2"
                            >
                              <Download className="w-4 h-4" />
                              PDF
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Help Section */}
            <Card className="bg-gradient-to-br from-dojo-navy/5 to-dojo-green/5">
              <CardHeader>
                <CardTitle className="text-dojo-navy">Need Help?</CardTitle>
                <CardDescription>
                  Questions about your subscription or billing?
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-gray-600">
                  Using the "Manage Subscription" button above, you can:
                </p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 ml-2">
                  <li>Update your payment method</li>
                  <li>View all past invoices and receipts</li>
                  <li>Download payment history</li>
                  <li>Cancel your subscription (access retained until period end)</li>
                  <li>Reactivate a canceled subscription</li>
                  <li>Update billing information</li>
                </ul>
                <div className="pt-3 mt-3 border-t">
                  <p className="text-sm text-gray-600">
                    For additional support, please{' '}
                    <a href="/contact" className="text-dojo-green hover:underline font-semibold">
                      contact us
                    </a>
                    .
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* No Subscription State */}
        {!loading && !subscriptionDetails && !error && (
          <Card>
            <CardHeader>
              <CardTitle className="text-dojo-navy">No Active Subscription</CardTitle>
              <CardDescription>
                You don't have an active membership subscription yet.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                Become a member to access exclusive benefits, training resources, and community events.
              </p>
              <Button
                onClick={() => router.push('/membership')}
                className="bg-gradient-to-r from-dojo-navy to-dojo-green hover:from-dojo-navy/90 hover:to-dojo-green/90"
              >
                View Membership Plans
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Back to Dashboard */}
        <div className="mt-8">
          <Button
            variant="outline"
            onClick={() => router.push('/dashboard')}
            className="gap-2"
          >
            ← Back to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
