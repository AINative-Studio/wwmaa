"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PaymentStatusBadge } from "./payment-status-badge";
import { paymentApi, Payment, PaymentFilters } from "@/lib/payment-api";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  FileText,
  Receipt,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PaymentTableProps {
  className?: string;
}

export function PaymentTable({ className }: PaymentTableProps) {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  // Pagination state
  const [page, setPage] = useState(1);
  const [perPage] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Fetch payments
  const fetchPayments = async () => {
    setLoading(true);
    setError(null);

    try {
      const filters: PaymentFilters = {
        page,
        per_page: perPage,
      };

      if (statusFilter && statusFilter !== "all") {
        filters.status = statusFilter;
      }

      if (startDate) {
        filters.start_date = new Date(startDate).toISOString();
      }

      if (endDate) {
        filters.end_date = new Date(endDate).toISOString();
      }

      const response = await paymentApi.getPayments(filters);
      setPayments(response.payments);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      console.error("Error fetching payments:", err);
      setError("Failed to load payment history. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Fetch payments on mount and when filters change
  useEffect(() => {
    fetchPayments();
  }, [page, statusFilter, startDate, endDate]);

  // Export to CSV
  const handleExport = async () => {
    setExporting(true);
    try {
      const filters: Omit<PaymentFilters, "page" | "per_page"> = {};

      if (statusFilter && statusFilter !== "all") {
        filters.status = statusFilter;
      }

      if (startDate) {
        filters.start_date = new Date(startDate).toISOString();
      }

      if (endDate) {
        filters.end_date = new Date(endDate).toISOString();
      }

      await paymentApi.exportToCSV(filters);
    } catch (err) {
      console.error("Error exporting payments:", err);
      alert("Failed to export payments. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number, currency: string = "USD") => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy");
    } catch {
      return dateString;
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          {/* Status Filter */}
          <div className="w-full sm:w-[180px]">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="succeeded">Paid</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="refunded">Refunded</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Date Range Filters */}
          <div className="flex gap-2">
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full sm:w-[150px]"
              placeholder="Start date"
            />
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full sm:w-[150px]"
              placeholder="End date"
            />
          </div>
        </div>

        {/* Export Button */}
        <Button
          variant="outline"
          onClick={handleExport}
          disabled={exporting || loading}
        >
          {exporting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Export CSV
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Payment Method</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                  <p className="text-sm text-muted-foreground mt-2">
                    Loading payments...
                  </p>
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <p className="text-sm text-destructive">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchPayments}
                    className="mt-4"
                  >
                    Try Again
                  </Button>
                </TableCell>
              </TableRow>
            ) : payments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <p className="text-sm text-muted-foreground">
                    No payments found.
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              payments.map((payment) => (
                <TableRow key={payment.id}>
                  <TableCell className="font-medium">
                    {formatDate(payment.created_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {formatCurrency(payment.amount, payment.currency)}
                      </span>
                      {payment.refunded_amount && payment.refunded_amount > 0 && (
                        <span className="text-xs text-muted-foreground">
                          Refunded: {formatCurrency(payment.refunded_amount, payment.currency)}
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <PaymentStatusBadge status={payment.status} />
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {payment.description || "—"}
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {payment.payment_method || "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {payment.receipt_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          asChild
                          title="View Receipt"
                        >
                          <a
                            href={payment.receipt_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Receipt className="h-4 w-4" />
                          </a>
                        </Button>
                      )}
                      {payment.invoice_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          asChild
                          title="View Invoice"
                        >
                          <a
                            href={payment.invoice_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <FileText className="h-4 w-4" />
                          </a>
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {!loading && !error && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * perPage + 1} to{" "}
            {Math.min(page * perPage, total)} of {total} payments
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
