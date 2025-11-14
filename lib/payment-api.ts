/**
 * Payment API Client
 *
 * Provides methods for fetching payment history, downloading receipts,
 * and exporting payment data to CSV.
 */

export interface Payment {
  id: string;
  user_id: string;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'succeeded' | 'failed' | 'refunded';
  payment_method?: string;
  description?: string;
  receipt_url?: string;
  invoice_url?: string;
  refunded_amount?: number;
  refunded_at?: string;
  refund_reason?: string;
  created_at: string;
  processed_at?: string;
}

export interface PaymentListResponse {
  payments: Payment[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface PaymentFilters {
  page?: number;
  per_page?: number;
  start_date?: string;
  end_date?: string;
  status?: string;
}

const MODE = process.env.NEXT_PUBLIC_API_MODE ?? 'mock';
// TEMPORARY: Hardcoded for production deployment
// TODO: Fix Railway environment variable passing
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? 'https://athletic-curiosity-production.up.railway.app';

// Mock data for development
const mockPayments: Payment[] = [
  {
    id: 'pay_1',
    user_id: 'user_123',
    amount: 99.00,
    currency: 'USD',
    status: 'succeeded',
    payment_method: '****4242',
    description: 'Annual Membership - Premium',
    receipt_url: 'https://stripe.com/receipts/mock_receipt_1',
    invoice_url: 'https://stripe.com/invoices/mock_invoice_1',
    created_at: '2025-01-15T10:30:00Z',
    processed_at: '2025-01-15T10:30:15Z',
  },
  {
    id: 'pay_2',
    user_id: 'user_123',
    amount: 49.00,
    currency: 'USD',
    status: 'succeeded',
    payment_method: '****4242',
    description: 'Monthly Membership - Basic',
    receipt_url: 'https://stripe.com/receipts/mock_receipt_2',
    invoice_url: 'https://stripe.com/invoices/mock_invoice_2',
    created_at: '2024-12-15T10:30:00Z',
    processed_at: '2024-12-15T10:30:20Z',
  },
  {
    id: 'pay_3',
    user_id: 'user_123',
    amount: 49.00,
    currency: 'USD',
    status: 'refunded',
    payment_method: '****4242',
    description: 'Monthly Membership - Basic',
    receipt_url: 'https://stripe.com/receipts/mock_receipt_3',
    invoice_url: 'https://stripe.com/invoices/mock_invoice_3',
    refunded_amount: 49.00,
    refunded_at: '2024-11-20T14:00:00Z',
    refund_reason: 'Customer request',
    created_at: '2024-11-15T10:30:00Z',
    processed_at: '2024-11-15T10:30:18Z',
  },
  {
    id: 'pay_4',
    user_id: 'user_123',
    amount: 99.00,
    currency: 'USD',
    status: 'failed',
    payment_method: '****1234',
    description: 'Annual Membership - Premium',
    created_at: '2024-10-15T10:30:00Z',
  },
];

export const paymentApi = {
  /**
   * Fetch paginated payment history
   */
  async getPayments(filters: PaymentFilters = {}): Promise<PaymentListResponse> {
    if (MODE === 'mock') {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 300));

      // Apply filters to mock data
      let filtered = [...mockPayments];

      if (filters.status) {
        filtered = filtered.filter(p => p.status === filters.status);
      }

      if (filters.start_date) {
        const startDate = new Date(filters.start_date);
        filtered = filtered.filter(p => new Date(p.created_at) >= startDate);
      }

      if (filters.end_date) {
        const endDate = new Date(filters.end_date);
        filtered = filtered.filter(p => new Date(p.created_at) <= endDate);
      }

      // Pagination
      const page = filters.page || 1;
      const per_page = filters.per_page || 10;
      const total = filtered.length;
      const total_pages = Math.ceil(total / per_page);
      const offset = (page - 1) * per_page;
      const payments = filtered.slice(offset, offset + per_page);

      return {
        payments,
        total,
        page,
        per_page,
        total_pages,
      };
    }

    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.per_page) params.append('per_page', filters.per_page.toString());
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.status) params.append('status', filters.status);

      const url = `${BACKEND_URL}/api/payments?${params.toString()}`;

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch payments');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching payments:', error);
      throw error;
    }
  },

  /**
   * Fetch single payment by ID
   */
  async getPaymentById(paymentId: string): Promise<Payment | null> {
    if (MODE === 'mock') {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 200));
      return mockPayments.find(p => p.id === paymentId) || null;
    }

    try {
      const url = `${BACKEND_URL}/api/payments/${paymentId}`;

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) return null;
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch payment');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching payment:', error);
      throw error;
    }
  },

  /**
   * Export payments to CSV
   */
  async exportToCSV(filters: Omit<PaymentFilters, 'page' | 'per_page'> = {}): Promise<void> {
    if (MODE === 'mock') {
      // Create mock CSV
      const csv = [
        'Date,Amount,Currency,Status,Payment Method,Description,Refunded Amount,Receipt URL,Invoice URL',
        ...mockPayments.map(p =>
          `${p.created_at},${p.amount},${p.currency},${p.status},${p.payment_method || ''},${p.description || ''},${p.refunded_amount || 0},${p.receipt_url || ''},${p.invoice_url || ''}`
        ),
      ].join('\n');

      // Download CSV
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `wwmaa_payments_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      return;
    }

    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.status) params.append('status', filters.status);

      const url = `${BACKEND_URL}/api/payments/export/csv?${params.toString()}`;

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to export payments');
      }

      // Download the CSV file
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;

      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `wwmaa_payments_${new Date().toISOString().split('T')[0]}.csv`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error exporting payments:', error);
      throw error;
    }
  },

  /**
   * Get payment statistics
   */
  async getPaymentStats(): Promise<{
    total_spent: number;
    successful_payments: number;
    refunded_amount: number;
  }> {
    const { payments } = await this.getPayments({ per_page: 1000 });

    const stats = payments.reduce(
      (acc, payment) => {
        if (payment.status === 'succeeded') {
          acc.total_spent += payment.amount;
          acc.successful_payments += 1;
        }
        if (payment.status === 'refunded' && payment.refunded_amount) {
          acc.refunded_amount += payment.refunded_amount;
        }
        return acc;
      },
      { total_spent: 0, successful_payments: 0, refunded_amount: 0 }
    );

    return stats;
  },
};
