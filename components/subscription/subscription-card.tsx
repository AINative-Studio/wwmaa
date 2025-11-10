'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from './status-badge';
import { SubscriptionDetails } from '@/lib/types';
import { CreditCard, Calendar, DollarSign } from 'lucide-react';

interface SubscriptionCardProps {
  subscriptionDetails: SubscriptionDetails;
  onManageClick: () => void;
  isLoading?: boolean;
}

export function SubscriptionCard({ subscriptionDetails, onManageClick, isLoading }: SubscriptionCardProps) {
  const { subscription, payment_method, upcoming_invoice } = subscriptionDetails;

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatPrice = (amount: number, currency: string = 'usd') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase()
    }).format(amount);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-bold text-dojo-navy">
              {subscription.tier_name} Membership
            </CardTitle>
            <CardDescription>Manage your subscription and billing</CardDescription>
          </div>
          <StatusBadge status={subscription.status} />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Price Section */}
        <div className="flex items-center gap-3 p-4 bg-gradient-to-br from-dojo-navy/5 to-dojo-navy/10 rounded-lg">
          <div className="w-10 h-10 rounded-full bg-dojo-navy flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-600">Current Price</div>
            <div className="text-2xl font-bold text-dojo-navy">
              {formatPrice(subscription.price, subscription.currency)}
              <span className="text-sm font-normal text-gray-600">/month</span>
            </div>
          </div>
        </div>

        {/* Billing Date Section */}
        <div className="flex items-center gap-3 p-4 bg-gradient-to-br from-dojo-green/5 to-dojo-green/10 rounded-lg">
          <div className="w-10 h-10 rounded-full bg-dojo-green flex items-center justify-center">
            <Calendar className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-sm font-medium text-gray-600">
              {subscription.cancel_at_period_end ? 'Expires On' : 'Next Billing Date'}
            </div>
            <div className="text-lg font-semibold text-dojo-green">
              {formatDate(subscription.next_billing_date)}
            </div>
          </div>
        </div>

        {/* Payment Method Section */}
        {payment_method && (
          <div className="flex items-center gap-3 p-4 bg-gradient-to-br from-dojo-orange/5 to-dojo-orange/10 rounded-lg">
            <div className="w-10 h-10 rounded-full bg-dojo-orange flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-sm font-medium text-gray-600">Payment Method</div>
              <div className="text-lg font-semibold text-dojo-orange capitalize">
                {payment_method.brand} •••• {payment_method.last4}
              </div>
              {payment_method.exp_month && payment_method.exp_year && (
                <div className="text-xs text-gray-500">
                  Expires {payment_method.exp_month}/{payment_method.exp_year}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Trial Period */}
        {subscription.status === 'trialing' && subscription.trial_end && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm font-medium text-blue-900">Trial Period</div>
            <div className="text-sm text-blue-700">
              Your trial ends on {formatDate(subscription.trial_end)}
            </div>
          </div>
        )}

        {/* Cancellation Notice */}
        {subscription.cancel_at_period_end && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="text-sm font-medium text-yellow-900">Subscription Canceling</div>
            <div className="text-sm text-yellow-700">
              Your subscription will end on {formatDate(subscription.next_billing_date)}.
              You'll retain access until then.
            </div>
          </div>
        )}

        {/* Past Due Notice */}
        {subscription.status === 'past_due' && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-sm font-medium text-red-900">Payment Required</div>
            <div className="text-sm text-red-700">
              Your payment is past due. Please update your payment method to maintain access.
            </div>
          </div>
        )}

        {/* Upcoming Invoice */}
        {upcoming_invoice && subscription.status === 'active' && !subscription.cancel_at_period_end && (
          <div className="pt-4 border-t">
            <div className="text-sm text-gray-600">Next charge</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatPrice(upcoming_invoice.amount_due, upcoming_invoice.currency)} on{' '}
              {formatDate(subscription.next_billing_date)}
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-3">
        <Button
          onClick={onManageClick}
          disabled={isLoading}
          className="flex-1 bg-gradient-to-r from-dojo-navy to-dojo-green hover:from-dojo-navy/90 hover:to-dojo-green/90"
        >
          {isLoading ? 'Loading...' : 'Manage Subscription'}
        </Button>
      </CardFooter>
    </Card>
  );
}
