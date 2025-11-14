import { EventItem, EventListResponse, EventFilters, EventSort } from "./types";

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
 */
export const eventApi = {
  /**
   * Get a paginated, filtered, and sorted list of events
   */
  async getEvents(params: GetEventsParams = {}): Promise<EventListResponse> {
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
