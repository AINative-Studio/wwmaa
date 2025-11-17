import { EventItem, EventListResponse, EventFilters, EventSort } from "./types";

// Use relative URL to leverage Next.js API routes (avoids CORS)
// The Next.js API route at /api/events/public will proxy to the backend
const API_BASE_URL = "";

interface GetEventsParams extends EventFilters, Partial<EventSort> {
  limit?: number;
  offset?: number;
}

/**
 * Map backend event type to frontend EventType
 */
function mapEventType(backendType: string): EventItem["type"] {
  const typeMap: Record<string, EventItem["type"]> = {
    "workshop": "seminar",
    "seminar": "seminar",
    "competition": "tournament",
    "tournament": "tournament",
    "live_training": "live_training",
    "training": "live_training",
    "certification": "certification",
    "WORKSHOP": "seminar",
    "SEMINAR": "seminar",
    "COMPETITION": "tournament",
    "TOURNAMENT": "tournament",
    "LIVE_TRAINING": "live_training",
    "TRAINING": "live_training",
    "CERTIFICATION": "certification",
  };

  return typeMap[backendType] || "seminar";
}

/**
 * Map frontend EventType to backend event type
 */
function mapToBackendEventType(frontendType?: EventItem["type"]): string | undefined {
  if (!frontendType) return undefined;

  const typeMap: Record<EventItem["type"], string> = {
    "live_training": "live_training",
    "seminar": "seminar",
    "tournament": "tournament",
    "certification": "certification",
  };

  return typeMap[frontendType];
}

/**
 * Map backend event to frontend EventItem format
 */
function mapBackendEvent(backendEvent: any): EventItem {
  const data = backendEvent.data || backendEvent;

  return {
    id: backendEvent.id,
    title: data.title || "Untitled Event",
    description: data.description,
    start: data.start_date,
    end: data.end_date,
    location: data.location || (data.is_online ? "Online" : "TBD"),
    location_type: data.is_online ? "online" : "in_person",
    type: mapEventType(data.event_type),
    price: data.price !== undefined ? data.price : 0,
    visibility: data.visibility || "public",
    status: data.status || "published",
    teaser: data.teaser || data.description?.substring(0, 150),
    image: data.featured_image_url,
    max_participants: data.capacity,
    current_participants: data.registered_count || 0,
    instructor: data.instructor_info,
    created_at: data.created_at || new Date().toISOString(),
    updated_at: data.updated_at || new Date().toISOString(),
  };
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

    // Map frontend type to backend type
    const backendType = mapToBackendEventType(params.type);
    if (backendType) queryParams.append("type", backendType);

    if (params.date_from) queryParams.append("date_from", params.date_from);
    if (params.date_to) queryParams.append("date_to", params.date_to);
    if (params.location) queryParams.append("location", params.location);
    if (params.price) queryParams.append("price", params.price);
    if (params.visibility) queryParams.append("visibility", params.visibility);
    if (params.sort_by) queryParams.append("sort", params.sort_by);
    if (params.sort_order) queryParams.append("order", params.sort_order);

    queryParams.append("limit", String(params.limit ?? 12));
    queryParams.append("offset", String(params.offset ?? 0));

    const url = `${API_BASE_URL}/api/events/public?${queryParams.toString()}`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch events: ${response.statusText}`);
    }

    const data = await response.json();

    // Map backend events to frontend format
    const mappedEvents = (data.events || []).map(mapBackendEvent);

    return {
      events: mappedEvents,
      total: data.total || 0,
      limit: data.limit || params.limit || 12,
      offset: data.offset || params.offset || 0,
      has_more: data.has_more || false,
    };
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
