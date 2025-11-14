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

// TEMPORARY: Hardcoded for production deployment
// TODO: Fix Railway environment variable passing
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? 'https://athletic-curiosity-production.up.railway.app';

export const paymentApi = {
  /**
   * Fetch paginated payment history
   */
  async getPayments(filters: PaymentFilters = {}): Promise<PaymentListResponse> {
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
