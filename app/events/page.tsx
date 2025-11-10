"use client";

import { useState, useEffect } from "react";
import type { Metadata } from "next";
import { EventCard } from "@/components/events/event-card";
import { EventFilters } from "@/components/events/event-filters";
import { EventSort } from "@/components/events/event-sort";
import { EventCalendar } from "@/components/events/event-calendar";
import { ViewToggle } from "@/components/events/view-toggle";
import { eventApi } from "@/lib/event-api";
import { EventItem, EventType, EventLocationType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Filter, Loader2 } from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";
import { addDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, addMonths, format } from "date-fns";

const EVENTS_PER_PAGE = 12;
type ViewType = "list" | "calendar";

export default function EventsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // State
  const [events, setEvents] = useState<EventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [view, setView] = useState<ViewType>((searchParams.get("view") as ViewType) || "list");
  const [currentDate, setCurrentDate] = useState(new Date());

  // Filters state from URL
  const [filters, setFilters] = useState<{
    type?: EventType;
    location?: EventLocationType;
    price?: "free" | "paid";
    date_range?: "upcoming" | "this_week" | "this_month";
  }>({
    type: (searchParams.get("type") as EventType) || undefined,
    location: (searchParams.get("location") as EventLocationType) || undefined,
    price: (searchParams.get("price") as "free" | "paid") || undefined,
    date_range: (searchParams.get("date_range") as "upcoming" | "this_week" | "this_month") || "upcoming",
  });

  // Sort state from URL
  const [sortBy, setSortBy] = useState<"date" | "price">((searchParams.get("sort") as "date" | "price") || "date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">((searchParams.get("order") as "asc" | "desc") || "asc");

  // Mobile filter sheet state
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Calculate date range based on filter and view
  const getDateRange = () => {
    const now = new Date();

    // For calendar view, fetch events for the visible month range
    if (view === "calendar") {
      const start = startOfMonth(currentDate);
      const end = endOfMonth(addMonths(currentDate, 1)); // Fetch current and next month
      return {
        date_from: format(start, "yyyy-MM-dd"),
        date_to: format(end, "yyyy-MM-dd"),
      };
    }

    // For list view, use filter-based date range
    switch (filters.date_range) {
      case "this_week":
        return {
          date_from: format(startOfWeek(now), "yyyy-MM-dd"),
          date_to: format(endOfWeek(now), "yyyy-MM-dd"),
        };
      case "this_month":
        return {
          date_from: format(startOfMonth(now), "yyyy-MM-dd"),
          date_to: format(endOfMonth(now), "yyyy-MM-dd"),
        };
      case "upcoming":
      default:
        return {
          date_from: format(now, "yyyy-MM-dd"),
          date_to: undefined,
        };
    }
  };

  // Fetch events
  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);

      const dateRange = getDateRange();
      const offset = (currentPage - 1) * EVENTS_PER_PAGE;

      const response = await eventApi.getEvents({
        type: filters.type,
        location: filters.location,
        price: filters.price,
        date_from: dateRange.date_from,
        date_to: dateRange.date_to,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: view === "calendar" ? 100 : EVENTS_PER_PAGE, // Fetch more for calendar view
        offset,
      });

      setEvents(response.events);
      setTotal(response.total);
    } catch (err) {
      setError("Failed to load events. Please try again later.");
      console.error("Error fetching events:", err);
    } finally {
      setLoading(false);
    }
  };

  // Update URL when filters/sort/view change
  useEffect(() => {
    const params = new URLSearchParams();
    if (view !== "list") params.set("view", view);
    if (filters.type) params.set("type", filters.type);
    if (filters.location) params.set("location", filters.location);
    if (filters.price) params.set("price", filters.price);
    if (filters.date_range && filters.date_range !== "upcoming") {
      params.set("date_range", filters.date_range);
    }
    if (sortBy !== "date") params.set("sort", sortBy);
    if (sortOrder !== "asc") params.set("order", sortOrder);
    if (currentPage > 1) params.set("page", String(currentPage));

    const queryString = params.toString();
    const newUrl = queryString ? `/events?${queryString}` : "/events";
    router.replace(newUrl, { scroll: false });
  }, [filters, sortBy, sortOrder, currentPage, view, router]);

  // Fetch events when filters/sort/page/view change
  useEffect(() => {
    fetchEvents();
  }, [filters, sortBy, sortOrder, currentPage, view, currentDate]);

  // View change handler
  const handleViewChange = (newView: ViewType) => {
    setView(newView);
    setCurrentPage(1);
  };

  // Calendar date range change handler
  const handleDateRangeChange = (start: Date, end: Date) => {
    setCurrentDate(start);
  };

  // Filter change handler
  const handleFilterChange = (key: string, value: string | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page
  };

  // Clear all filters
  const handleClearAllFilters = () => {
    setFilters({
      type: undefined,
      location: undefined,
      price: undefined,
      date_range: "upcoming",
    });
    setCurrentPage(1);
  };

  // Sort change handler
  const handleSortChange = (newSortBy: "date" | "price", newSortOrder: "asc" | "desc") => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setCurrentPage(1); // Reset to first page
  };

  // Pagination
  const totalPages = Math.ceil(total / EVENTS_PER_PAGE);
  const hasMore = currentPage < totalPages;

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <header className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              Martial Arts Events & Tournaments
            </h1>
            <p className="text-2xl text-white/90">
              Judo seminars, karate tournaments, and live martial arts training sessions
            </p>
          </div>
        </div>
      </header>

      {/* Events Listing Section */}
      <section className="py-12 bg-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Desktop Sidebar Filters */}
            <aside className="hidden lg:block lg:w-64 flex-shrink-0">
              <div className="sticky top-6 bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <EventFilters
                  filters={filters}
                  onFilterChange={handleFilterChange}
                  onClearAll={handleClearAllFilters}
                />
              </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 min-w-0">
              {/* View Toggle and Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
                <div className="flex items-center gap-4">
                  {/* Mobile Filter Button */}
                  <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
                    <SheetTrigger asChild>
                      <Button variant="outline" className="lg:hidden">
                        <Filter className="w-4 h-4 mr-2" />
                        Filters
                      </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="w-[300px] overflow-y-auto">
                      <div className="py-6">
                        <EventFilters
                          filters={filters}
                          onFilterChange={handleFilterChange}
                          onClearAll={handleClearAllFilters}
                        />
                      </div>
                    </SheetContent>
                  </Sheet>

                  {/* View Toggle */}
                  <ViewToggle view={view} onViewChange={handleViewChange} />

                  {/* Results Count */}
                  <div className="text-sm text-gray-600">
                    {loading ? (
                      <span>Loading...</span>
                    ) : (
                      <span>
                        {total} {total === 1 ? "event" : "events"} found
                      </span>
                    )}
                  </div>
                </div>

                {/* Sort Dropdown (only show in list view) */}
                {view === "list" && (
                  <EventSort sortBy={sortBy} sortOrder={sortOrder} onSortChange={handleSortChange} />
                )}
              </div>

              {/* Loading State */}
              {loading && (
                <div className="flex items-center justify-center py-24">
                  <Loader2 className="w-8 h-8 animate-spin text-dojo-green" />
                </div>
              )}

              {/* Error State */}
              {error && !loading && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                  <p className="text-red-800 font-semibold mb-2">Error Loading Events</p>
                  <p className="text-red-600 text-sm">{error}</p>
                  <Button onClick={fetchEvents} className="mt-4" variant="outline">
                    Try Again
                  </Button>
                </div>
              )}

              {/* Empty State */}
              {!loading && !error && events.length === 0 && (
                <div className="bg-white rounded-2xl p-12 text-center border border-gray-100">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                    <svg
                      className="w-8 h-8 text-gray-400"
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
                  <h3 className="text-xl font-semibold text-dojo-navy mb-2">No Events Found</h3>
                  <p className="text-gray-600 mb-6">Try adjusting your filters to see more events.</p>
                  <Button onClick={handleClearAllFilters} variant="outline">
                    Clear All Filters
                  </Button>
                </div>
              )}

              {/* Events Display - Calendar or List */}
              {!loading && !error && events.length > 0 && (
                <>
                  {view === "calendar" ? (
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                      <EventCalendar events={events} onDateRangeChange={handleDateRangeChange} />
                    </div>
                  ) : (
                    <>
                      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                        {events.map((event) => (
                          <EventCard key={event.id} event={event} />
                        ))}
                      </div>

                      {/* Pagination (only show in list view) */}
                      {totalPages > 1 && (
                        <div className="mt-12 flex items-center justify-center gap-4">
                          <Button
                            variant="outline"
                            onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                          >
                            Previous
                          </Button>
                          <span className="text-sm text-gray-600">
                            Page {currentPage} of {totalPages}
                          </span>
                          <Button
                            variant="outline"
                            onClick={() => setCurrentPage((prev) => prev + 1)}
                            disabled={!hasMore}
                          >
                            Next
                          </Button>
                        </div>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
