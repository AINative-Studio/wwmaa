import React from 'react';
import { Badge } from '@/components/ui/badge';
import { SubscriptionStatus } from '@/lib/types';

interface StatusBadgeProps {
  status: SubscriptionStatus;
  className?: string;
}

const statusConfig: Record<SubscriptionStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  active: {
    label: 'Active',
    variant: 'default'
  },
  trialing: {
    label: 'Trial',
    variant: 'secondary'
  },
  past_due: {
    label: 'Past Due',
    variant: 'destructive'
  },
  canceled: {
    label: 'Canceled',
    variant: 'outline'
  },
  incomplete: {
    label: 'Incomplete',
    variant: 'outline'
  },
  incomplete_expired: {
    label: 'Expired',
    variant: 'destructive'
  },
  unpaid: {
    label: 'Unpaid',
    variant: 'destructive'
  }
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.active;

  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}
