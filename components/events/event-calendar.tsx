'use client';

import { Calendar, dateFnsLocalizer, Views, View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';
import { useRouter } from 'next/navigation';
import { useMemo, useState, useCallback } from 'react';
import type { EventItem } from '@/lib/types';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  resource: EventItem;
}

interface EventCalendarProps {
  events: EventItem[];
  onDateRangeChange?: (start: Date, end: Date) => void;
  className?: string;
}

const eventTypeColors: Record<string, { bg: string; border: string }> = {
  live_training: {
    bg: '#eff6ff',
    border: '#3b82f6',
  },
  seminar: {
    bg: '#f0fdf4',
    border: '#22c55e',
  },
  tournament: {
    bg: '#fef2f2',
    border: '#ef4444',
  },
  certification: {
    bg: '#faf5ff',
    border: '#a855f7',
  },
};

export function EventCalendar({ events, onDateRangeChange, className = '' }: EventCalendarProps) {
  const router = useRouter();
  const [view, setView] = useState<View>(Views.MONTH);
  const [date, setDate] = useState(new Date());

  // Transform events to calendar format
  const calendarEvents = useMemo<CalendarEvent[]>(() => {
    return events.map((event) => ({
      id: event.id,
      title: event.title,
      start: new Date(event.start),
      end: new Date(event.end),
      resource: event,
    }));
  }, [events]);

  // Handle event selection
  const handleSelectEvent = useCallback(
    (event: CalendarEvent) => {
      router.push(`/events/${event.id}`);
    },
    [router]
  );

  // Handle date range changes
  const handleRangeChange = useCallback(
    (range: Date[] | { start: Date; end: Date }) => {
      if (onDateRangeChange) {
        if (Array.isArray(range)) {
          onDateRangeChange(range[0], range[range.length - 1]);
        } else {
          onDateRangeChange(range.start, range.end);
        }
      }
    },
    [onDateRangeChange]
  );

  // Custom event style getter
  const eventStyleGetter = useCallback((event: CalendarEvent) => {
    const eventType = event.resource.type;
    const colors = eventTypeColors[eventType] || {
      bg: '#f9fafb',
      border: '#6b7280',
    };

    return {
      style: {
        backgroundColor: colors.bg,
        borderLeft: `4px solid ${colors.border}`,
        borderRadius: '4px',
        opacity: 0.9,
        color: '#1f2937',
        padding: '2px 5px',
        fontSize: '0.875rem',
      },
    };
  }, []);

  // Custom event component
  const EventComponent = ({ event }: { event: CalendarEvent }) => {
    const startTime = format(event.start, 'h:mm a');

    return (
      <div className="flex flex-col">
        <span className="font-medium truncate">{event.title}</span>
        <span className="text-xs opacity-75">{startTime}</span>
        {event.resource.location_type === 'online' && (
          <span className="text-xs opacity-75">Online</span>
        )}
      </div>
    );
  };

  // Handle view change
  const handleViewChange = useCallback((newView: View) => {
    setView(newView);
  }, []);

  // Handle navigate
  const handleNavigate = useCallback((newDate: Date) => {
    setDate(newDate);
  }, []);

  return (
    <div className={`event-calendar ${className}`}>
      <style jsx global>{`
        .rbc-calendar {
          font-family: inherit;
        }

        .rbc-header {
          padding: 12px 8px;
          font-weight: 600;
          color: #023e72;
          border-bottom: 2px solid #e5e7eb;
        }

        .rbc-today {
          background-color: #fef3c7;
        }

        .rbc-event {
          cursor: pointer;
          transition: all 0.2s;
        }

        .rbc-event:hover {
          opacity: 1 !important;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }

        .rbc-toolbar {
          padding: 16px 0;
          margin-bottom: 16px;
          gap: 12px;
        }

        .rbc-toolbar button {
          border: 1px solid #d1d5db;
          border-radius: 8px;
          padding: 8px 16px;
          background: white;
          color: #374151;
          font-weight: 500;
          transition: all 0.2s;
        }

        .rbc-toolbar button:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
        }

        .rbc-toolbar button.rbc-active {
          background: #023e72;
          color: white;
          border-color: #023e72;
        }

        .rbc-toolbar button.rbc-active:hover {
          background: #015ea8;
          border-color: #015ea8;
        }

        .rbc-month-view,
        .rbc-time-view,
        .rbc-agenda-view {
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          overflow: hidden;
        }

        .rbc-off-range {
          color: #9ca3af;
        }

        .rbc-off-range-bg {
          background: #f9fafb;
        }

        .rbc-show-more {
          color: #023e72;
          font-weight: 600;
        }

        .rbc-show-more:hover {
          text-decoration: underline;
        }

        .rbc-time-slot {
          min-height: 40px;
        }

        .rbc-day-slot .rbc-time-slot {
          border-top: 1px solid #f3f4f6;
        }

        .rbc-current-time-indicator {
          background-color: #ef4444;
          height: 2px;
        }

        @media (max-width: 768px) {
          .rbc-toolbar {
            flex-direction: column;
            align-items: stretch;
          }

          .rbc-toolbar-label {
            text-align: center;
            margin: 8px 0;
            font-size: 1.125rem;
            font-weight: 700;
          }

          .rbc-toolbar button {
            padding: 6px 12px;
            font-size: 0.875rem;
          }

          .rbc-header {
            padding: 8px 4px;
            font-size: 0.75rem;
          }

          .rbc-event {
            font-size: 0.75rem;
            padding: 1px 3px;
          }
        }
      `}</style>

      {/* Color Legend */}
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: eventTypeColors.live_training.bg, borderLeft: `3px solid ${eventTypeColors.live_training.border}` }}></div>
          <span>Live Training</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: eventTypeColors.seminar.bg, borderLeft: `3px solid ${eventTypeColors.seminar.border}` }}></div>
          <span>Seminar</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: eventTypeColors.tournament.bg, borderLeft: `3px solid ${eventTypeColors.tournament.border}` }}></div>
          <span>Tournament</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: eventTypeColors.certification.bg, borderLeft: `3px solid ${eventTypeColors.certification.border}` }}></div>
          <span>Certification</span>
        </div>
      </div>

      <Calendar
        localizer={localizer}
        events={calendarEvents}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 700 }}
        view={view}
        onView={handleViewChange}
        date={date}
        onNavigate={handleNavigate}
        onSelectEvent={handleSelectEvent}
        onRangeChange={handleRangeChange}
        eventPropGetter={eventStyleGetter}
        components={{
          event: EventComponent,
        }}
        views={[Views.MONTH, Views.WEEK, Views.DAY]}
        popup
        tooltipAccessor={(event: CalendarEvent) => {
          const { resource } = event;
          return `${resource.title}\n${resource.location}\n${
            resource.price === 0 ? 'Free' : `$${resource.price}`
          }`;
        }}
      />
    </div>
  );
}
