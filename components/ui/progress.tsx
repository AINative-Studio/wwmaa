'use client';

import * as React from 'react';

import { cn } from '@/lib/utils';

// Simplified Progress component without Radix UI to avoid build issues
// TODO: Restore Radix UI Progress when upgrading to Next.js 14+
const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value?: number }
>(({ className, value = 0, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'relative h-4 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-800',
      className
    )}
    {...props}
  >
    <div
      className="h-full bg-primary transition-all duration-300 ease-in-out"
      style={{ width: `${Math.min(100, Math.max(0, value || 0))}%` }}
    />
  </div>
));
Progress.displayName = 'Progress';

export { Progress };
