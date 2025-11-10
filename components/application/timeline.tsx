import React from 'react';
import { CheckCircle2, Circle, Clock, XCircle, AlertCircle } from 'lucide-react';
import { ApplicationTimeline as TimelineEvent } from '@/lib/types';
import { cn } from '@/lib/utils';

interface TimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export function Timeline({ events, className }: TimelineProps) {
  const getEventIcon = (event: string) => {
    if (event.toLowerCase().includes('approved') || event.toLowerCase().includes('accepted')) {
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    }
    if (event.toLowerCase().includes('rejected') || event.toLowerCase().includes('declined')) {
      return <XCircle className="h-5 w-5 text-red-600" />;
    }
    if (event.toLowerCase().includes('review') || event.toLowerCase().includes('pending')) {
      return <Clock className="h-5 w-5 text-yellow-600" />;
    }
    if (event.toLowerCase().includes('info') || event.toLowerCase().includes('additional')) {
      return <AlertCircle className="h-5 w-5 text-blue-600" />;
    }
    return <Circle className="h-5 w-5 text-gray-400" />;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  return (
    <div className={cn('space-y-8', className)}>
      {events.map((event, index) => (
        <div key={index} className="relative flex gap-4">
          {/* Timeline line */}
          {index < events.length - 1 && (
            <div className="absolute left-[10px] top-8 h-full w-0.5 bg-gray-200" />
          )}

          {/* Icon */}
          <div className="relative z-10 flex-shrink-0">
            {getEventIcon(event.event)}
          </div>

          {/* Content */}
          <div className="flex-1 space-y-1 pb-8">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 className="font-semibold text-gray-900">{event.event}</h4>
                <p className="text-sm text-gray-600">{event.description}</p>
                {event.actor && (
                  <p className="text-xs text-gray-500 mt-1">by {event.actor}</p>
                )}
              </div>
              <time className="text-xs text-gray-500 whitespace-nowrap">
                {formatTimestamp(event.timestamp)}
              </time>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
