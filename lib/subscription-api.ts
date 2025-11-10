/**
 * Subscription API Client
 *
 * Functions for interacting with subscription and billing endpoints.
 * Handles subscription details retrieval and Stripe Customer Portal session creation.
 */

import { SubscriptionDetails } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Get current user's subscription details
 *
 * Fetches subscription information from ZeroDB including tier, status,
 * billing dates, payment method, and recent invoices.
 *
 * @returns Promise with subscription details
 * @throws Error if request fails
 */
export async function getSubscriptionDetails(): Promise<SubscriptionDetails> {
  const response = await fetch(`${API_BASE}/api/billing/subscription`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch subscription details' }));
    throw new Error(error.detail || 'Failed to fetch subscription details');
  }

  return response.json();
}

/**
 * Create a Stripe Customer Portal session
 *
 * Generates a secure URL to the Stripe Customer Portal where users can:
 * - Update payment methods
 * - View invoices and receipts
 * - Cancel or reactivate subscriptions
 * - Update billing information
 *
 * @param returnUrl URL to redirect to after portal session
 * @returns Promise with portal URL
 * @throws Error if portal session creation fails
 */
export async function createPortalSession(returnUrl: string): Promise<{ url: string }> {
  const response = await fetch(`${API_BASE}/api/billing/portal`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ return_url: returnUrl }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create portal session' }));
    throw new Error(error.detail || 'Failed to create portal session');
  }

  return response.json();
}

/**
 * Mock subscription details for development/testing
 *
 * Provides realistic mock data for subscription details when backend is unavailable
 * or for testing purposes.
 */
export const mockSubscriptionDetails: SubscriptionDetails = {
  subscription: {
    id: 'sub_mock_123',
    user_id: 'user_mock_123',
    tier: 'premium',
    tier_name: 'Premium',
    status: 'active',
    price: 29.99,
    currency: 'usd',
    stripe_subscription_id: 'sub_stripe_123',
    stripe_customer_id: 'cus_stripe_123',
    current_period_start: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    current_period_end: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
    next_billing_date: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
    cancel_at_period_end: false,
    created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  payment_method: {
    id: 'pm_mock_123',
    type: 'card',
    brand: 'visa',
    last4: '4242',
    exp_month: 12,
    exp_year: 2025,
  },
  upcoming_invoice: {
    amount_due: 29.99,
    currency: 'usd',
    next_payment_attempt: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
  },
  recent_invoices: [
    {
      id: 'in_mock_1',
      number: 'INV-001',
      amount_paid: 29.99,
      currency: 'usd',
      status: 'paid',
      created: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      invoice_pdf: 'https://example.com/invoice.pdf',
      hosted_invoice_url: 'https://example.com/invoice',
    },
    {
      id: 'in_mock_2',
      number: 'INV-002',
      amount_paid: 29.99,
      currency: 'usd',
      status: 'paid',
      created: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
      invoice_pdf: 'https://example.com/invoice-2.pdf',
      hosted_invoice_url: 'https://example.com/invoice-2',
    },
  ],
};
