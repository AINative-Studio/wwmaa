'use client';

import { EventCard } from '@/components/cards/event-card';
import type { EventItem } from '@/lib/types';

interface EventListProps {
  events: EventItem[];
  className?: string;
}

export function EventList({ events, className = '' }: EventListProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-green/10 to-dojo-navy/10 mb-6">
          <svg
            className="w-10 h-10 text-dojo-navy/50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">
          No Events Found
        </h3>
        <p className="text-gray-600 max-w-md mx-auto">
          No events match your current filters. Try adjusting your search criteria or check back later for new events.
        </p>
      </div>
    );
  }

  return (
    <div className={`grid gap-6 md:grid-cols-2 lg:grid-cols-3 ${className}`}>
      {events.map((event) => (
        <EventCard
          key={event.id}
          id={event.id}
          title={event.title}
          start={event.start}
          location={event.location}
          teaser={event.teaser}
        />
      ))}
    </div>
  );
}
