'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { EventCalendar } from '@/components/events/event-calendar';
import { EventList } from '@/components/events/event-list';
import { EventFilters } from '@/components/events/event-filters';
import { ViewToggle } from '@/components/events/view-toggle';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Skeleton } from '@/components/ui/skeleton';
import { Filter, Calendar as CalendarIcon, List } from 'lucide-react';
import { eventApi } from '@/lib/event-api';
import type { EventItem, EventFilters as EventFiltersType, EventType, EventLocationType } from '@/lib/types';
import { startOfMonth, endOfMonth, addMonths, format } from 'date-fns';

type ViewType = 'list' | 'calendar';

export function EventsClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // State
  const [view, setView] = useState<ViewType>('list');
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<EventFiltersType>({});
  const [currentDate, setCurrentDate] = useState(new Date());

  // Initialize view from URL
  useEffect(() => {
    const viewParam = searchParams.get('view');
    if (viewParam === 'calendar' || viewParam === 'list') {
      setView(viewParam);
    }
  }, [searchParams]);

  // Fetch events based on filters and view
  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      let dateFrom: string | undefined;
      let dateTo: string | undefined;

      // For calendar view, fetch events for the visible month range
      if (view === 'calendar') {
        const start = startOfMonth(currentDate);
        const end = endOfMonth(addMonths(currentDate, 1)); // Fetch current and next month
        dateFrom = start.toISOString();
        dateTo = end.toISOString();
      }

      const response = await eventApi.getEvents({
        ...filters,
        date_from: dateFrom || filters.date_from,
        date_to: dateTo || filters.date_to,
        sort_by: 'date',
        sort_order: 'asc',
        limit: view === 'calendar' ? 100 : 12, // Fetch more for calendar view
      });

      setEvents(response.events);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  }, [filters, view, currentDate]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Handle view change
  const handleViewChange = useCallback((newView: ViewType) => {
    setView(newView);
    const params = new URLSearchParams(searchParams.toString());
    params.set('view', newView);
    router.push(`?${params.toString()}`, { scroll: false });
  }, [searchParams, router]);

  // Handle filter changes
  const handleFilterChange = useCallback((key: string, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Handle calendar date range change
  const handleDateRangeChange = useCallback((start: Date, end: Date) => {
    setCurrentDate(start);
  }, []);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.type) count++;
    if (filters.location) count++;
    if (filters.price) count++;
    if (filters.date_from || filters.date_to) count++;
    return count;
  }, [filters]);

  return (
    <div className="py-12 bg-gray-50">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header with Controls */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            {/* View Toggle */}
            <div className="flex items-center gap-4">
              <h2 className="font-display text-2xl font-bold text-dojo-navy">
                {view === 'calendar' ? 'Event Calendar' : 'Upcoming Events'}
              </h2>
              <ViewToggle view={view} onViewChange={handleViewChange} />
            </div>

            {/* Mobile Filter Button */}
            <div className="flex items-center gap-4">
              {activeFilterCount > 0 && (
                <span className="text-sm text-gray-600">
                  {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active
                </span>
              )}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" className="lg:hidden">
                    <Filter className="h-4 w-4 mr-2" />
                    Filters
                    {activeFilterCount > 0 && (
                      <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-dojo-orange rounded-full">
                        {activeFilterCount}
                      </span>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-80">
                  <SheetHeader>
                    <SheetTitle>Filter Events</SheetTitle>
                  </SheetHeader>
                  <div className="mt-6">
                    <EventFilters
                      filters={filters}
                      onFilterChange={handleFilterChange}
                      onClearAll={handleClearFilters}
                    />
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>

          {/* Event Count */}
          {!loading && (
            <p className="mt-2 text-gray-600">
              {events.length} event{events.length !== 1 ? 's' : ''} found
            </p>
          )}
        </div>

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Filters (Desktop) */}
          <aside className="hidden lg:block lg:w-64 flex-shrink-0">
            <div className="sticky top-24 bg-white rounded-xl shadow-card p-6">
              <EventFilters
                filters={filters}
                onFilterChange={handleFilterChange}
                onClearAll={handleClearFilters}
              />
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 min-w-0">
            {loading ? (
              <LoadingSkeleton view={view} />
            ) : (
              <>
                {view === 'calendar' ? (
                  <div className="bg-white rounded-xl shadow-card p-6">
                    <EventCalendar
                      events={events}
                      onDateRangeChange={handleDateRangeChange}
                    />
                  </div>
                ) : (
                  <EventList events={events} />
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

function LoadingSkeleton({ view }: { view: ViewType }) {
  if (view === 'calendar') {
    return (
      <div className="bg-white rounded-xl shadow-card p-6">
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="bg-white rounded-2xl overflow-hidden shadow-card">
          <Skeleton className="h-48 w-full" />
          <div className="p-6 space-y-3">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
