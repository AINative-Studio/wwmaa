import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Clock, RefreshCcw, AlertCircle } from "lucide-react";

type PaymentStatus = "pending" | "processing" | "succeeded" | "failed" | "refunded";

interface PaymentStatusBadgeProps {
  status: PaymentStatus;
  className?: string;
  showIcon?: boolean;
}

const statusConfig: Record<
  PaymentStatus,
  {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
    className: string;
    icon: typeof CheckCircle2;
  }
> = {
  succeeded: {
    label: "Paid",
    variant: "outline",
    className: "bg-green-50 text-green-700 border-green-200 hover:bg-green-50",
    icon: CheckCircle2,
  },
  pending: {
    label: "Pending",
    variant: "outline",
    className: "bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-50",
    icon: Clock,
  },
  processing: {
    label: "Processing",
    variant: "outline",
    className: "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-50",
    icon: RefreshCcw,
  },
  failed: {
    label: "Failed",
    variant: "destructive",
    className: "bg-red-50 text-red-700 border-red-200 hover:bg-red-50",
    icon: XCircle,
  },
  refunded: {
    label: "Refunded",
    variant: "outline",
    className: "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-50",
    icon: AlertCircle,
  },
};

export function PaymentStatusBadge({
  status,
  className,
  showIcon = true,
}: PaymentStatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <Badge
      variant={config.variant}
      className={cn(
        "inline-flex items-center gap-1.5 font-medium",
        config.className,
        className
      )}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      {config.label}
    </Badge>
  );
}
