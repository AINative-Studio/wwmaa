import React from 'react';
import { Badge } from '@/components/ui/badge';
import { ApplicationStatus } from '@/lib/types';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status: ApplicationStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const getStatusConfig = (status: ApplicationStatus) => {
    switch (status) {
      case 'DRAFT':
        return {
          label: 'Draft',
          className: 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-100',
        };
      case 'SUBMITTED':
        return {
          label: 'Submitted',
          className: 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-100',
        };
      case 'UNDER_REVIEW':
        return {
          label: 'Under Review',
          className: 'bg-yellow-100 text-yellow-800 border-yellow-300 hover:bg-yellow-100',
        };
      case 'APPROVED':
        return {
          label: 'Approved',
          className: 'bg-green-100 text-green-800 border-green-300 hover:bg-green-100',
        };
      case 'REJECTED':
        return {
          label: 'Rejected',
          className: 'bg-red-100 text-red-800 border-red-300 hover:bg-red-100',
        };
      default:
        return {
          label: status,
          className: 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-100',
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Badge
      variant="outline"
      className={cn(config.className, className)}
    >
      {config.label}
    </Badge>
  );
}
