import { EventItem, EventListResponse, EventFilters, EventSort } from "./types";
import { events } from "./mock/db";

const MODE = process.env.NEXT_PUBLIC_API_MODE ?? "live";
// TEMPORARY: Hardcoded for production deployment
// TODO: Fix Railway environment variable passing
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://athletic-curiosity-production.up.railway.app";

interface GetEventsParams extends EventFilters, Partial<EventSort> {
  limit?: number;
  offset?: number;
}

/**
 * Event API Client
 *
 * Provides methods to interact with the events API endpoints.
 * Supports both mock and live modes based on NEXT_PUBLIC_API_MODE environment variable.
 */
export const eventApi = {
  /**
   * Get a paginated, filtered, and sorted list of events
   */
  async getEvents(params: GetEventsParams = {}): Promise<EventListResponse> {
    if (MODE === "mock") {
      // Mock implementation with filtering and pagination
      let filteredEvents = [...events];

      // Filter by type
      if (params.type) {
        filteredEvents = filteredEvents.filter(e => e.type === params.type);
      }

      // Filter by location type
      if (params.location) {
        filteredEvents = filteredEvents.filter(e => e.location_type === params.location);
      }

      // Filter by price
      if (params.price === "free") {
        filteredEvents = filteredEvents.filter(e => e.price === 0);
      } else if (params.price === "paid") {
        filteredEvents = filteredEvents.filter(e => e.price > 0);
      }

      // Filter by date range
      if (params.date_from) {
        const fromDate = new Date(params.date_from);
        filteredEvents = filteredEvents.filter(e => new Date(e.start) >= fromDate);
      }
      if (params.date_to) {
        const toDate = new Date(params.date_to);
        filteredEvents = filteredEvents.filter(e => new Date(e.start) <= toDate);
      }

      // Filter by visibility (only show published events)
      filteredEvents = filteredEvents.filter(e => e.status === "published");

      // Sort
      const sortBy = params.sort_by ?? "date";
      const sortOrder = params.sort_order ?? "asc";

      filteredEvents.sort((a, b) => {
        let comparison = 0;
        if (sortBy === "date") {
          comparison = new Date(a.start).getTime() - new Date(b.start).getTime();
        } else if (sortBy === "price") {
          comparison = a.price - b.price;
        }
        return sortOrder === "asc" ? comparison : -comparison;
      });

      // Paginate
      const limit = params.limit ?? 12;
      const offset = params.offset ?? 0;
      const total = filteredEvents.length;
      const paginatedEvents = filteredEvents.slice(offset, offset + limit);

      return {
        events: paginatedEvents,
        total,
        limit,
        offset,
        has_more: offset + limit < total,
      };
    }

    // Live API implementation
    const queryParams = new URLSearchParams();

    if (params.type) queryParams.append("type", params.type);
    if (params.date_from) queryParams.append("date_from", params.date_from);
    if (params.date_to) queryParams.append("date_to", params.date_to);
    if (params.location) queryParams.append("location", params.location);
    if (params.price) queryParams.append("price", params.price);
    if (params.visibility) queryParams.append("visibility", params.visibility);
    if (params.sort_by) queryParams.append("sort", params.sort_by);
    if (params.sort_order) queryParams.append("order", params.sort_order);

    queryParams.append("limit", String(params.limit ?? 12));
    queryParams.append("offset", String(params.offset ?? 0));

    const response = await fetch(`${API_BASE_URL}/api/events/public?${queryParams.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch events: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get a single event by ID
   */
  async getEvent(id: string): Promise<EventItem | null> {
    if (MODE === "mock") {
      return events.find(e => e.id === id) ?? null;
    }

    const response = await fetch(`${API_BASE_URL}/api/events/public/${id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch event: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * RSVP to an event
   */
  async rsvpEvent(eventId: string): Promise<{ ok: boolean; message?: string }> {
    if (MODE === "mock") {
      return { ok: true, message: "RSVP successful" };
    }

    const response = await fetch(`${API_BASE_URL}/api/events/${eventId}/rsvp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response.json();
      return { ok: false, message: error.message ?? "RSVP failed" };
    }

    return response.json();
  },
};
