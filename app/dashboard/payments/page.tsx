"use client";

import { PaymentTable } from "@/components/payments/payment-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CreditCard, TrendingUp, RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { paymentApi } from "@/lib/payment-api";

export default function PaymentsPage() {
  const [stats, setStats] = useState({
    total_spent: 0,
    successful_payments: 0,
    refunded_amount: 0,
  });
  const [loadingStats, setLoadingStats] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await paymentApi.getPaymentStats();
        setStats(data);
      } catch (error) {
        console.error("Error fetching payment stats:", error);
      } finally {
        setLoadingStats(false);
      }
    };

    fetchStats();
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold tracking-tight">
          Payment History
        </h1>
        <p className="text-muted-foreground mt-2">
          View your payment history, download receipts, and track expenses.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Spent</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : formatCurrency(stats.total_spent)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              All-time total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Successful Payments
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : stats.successful_payments}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Completed transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Refunded</CardTitle>
            <RefreshCcw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : formatCurrency(stats.refunded_amount)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Total refunds
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Payment Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Payments</CardTitle>
          <CardDescription>
            A complete history of all your payments and transactions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PaymentTable />
        </CardContent>
      </Card>
    </div>
  );
}
