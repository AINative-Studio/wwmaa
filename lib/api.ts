import { MembershipTier, User, Application, EventItem, SearchResult, Article, Certification } from "./types";

// TEMPORARY: Hardcoded for production deployment
// TODO: Fix Railway environment variable passing
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://athletic-curiosity-production.up.railway.app";

const LIVE = {
  memberships: `${API_URL}/api/subscriptions`,
  applications: `${API_URL}/api/applications`,
  events: `${API_URL}/api/events/public`,
  event: (id: string) => `${API_URL}/api/events/public/${id}`,
  rsvp: (id: string) => `${API_URL}/api/events/${id}/rsvp`,
  search: `${API_URL}/api/search/query`,
  searchFeedback: `${API_URL}/api/search/feedback`,
  trainingJoin: (id: string) => `${API_URL}/api/training/${id}/join`,
  beehiivFeed: `${API_URL}/api/blog`,
  me: `${API_URL}/api/me`,
  certifications: `${API_URL}/api/certifications`,
};

export const api = {
  async getTiers(): Promise<MembershipTier[]> {
    const r = await fetch(LIVE.memberships);
    if (!r.ok) throw new Error(`Failed to fetch tiers: ${r.status} ${r.statusText}`);
    const data = await r.json();
    // Backend returns {tiers: [...]} so extract the array
    return data.tiers || data;
  },
  async getCurrentUser(): Promise<User> {
    const r = await fetch(LIVE.me, { credentials: "include" });
    if (!r.ok) throw new Error(`Failed to fetch user: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async submitApplication(payload: Partial<Application>): Promise<{ ok: boolean; id: string }> {
    const r = await fetch(LIVE.applications, { method: "POST", body: JSON.stringify(payload) });
    if (!r.ok) throw new Error(`Failed to submit application: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getApplications(): Promise<Application[]> {
    const r = await fetch(`${LIVE.applications}?status=pending`);
    if (!r.ok) throw new Error(`Failed to fetch applications: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getEvents(): Promise<EventItem[]> {
    const r = await fetch(LIVE.events);
    if (!r.ok) throw new Error(`Failed to fetch events: ${r.status} ${r.statusText}`);
    const data = await r.json();
    // Backend returns { events: [...], total, limit, offset, has_more }
    return data.events || [];
  },
  async getEvent(id: string): Promise<EventItem | null> {
    const r = await fetch(LIVE.event(id));
    if (!r.ok) return null;
    return r.json();
  },
  async rsvpEvent(id: string): Promise<{ ok: boolean }> {
    const r = await fetch(LIVE.rsvp(id), { method: "POST" });
    if (!r.ok) throw new Error(`Failed to RSVP event: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async search(q: string): Promise<SearchResult> {
    const r = await fetch(LIVE.search, { method:"POST", body: JSON.stringify({ q }) });
    if (!r.ok) throw new Error(`Failed to search: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getArticles(): Promise<Article[]> {
    const r = await fetch(LIVE.beehiivFeed);
    if (!r.ok) throw new Error(`Failed to fetch articles: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getCertifications(): Promise<Certification[]> {
    const r = await fetch(LIVE.certifications);
    if (!r.ok) throw new Error(`Failed to fetch certifications: ${r.status} ${r.statusText}`);
    const data = await r.json();
    // Backend returns {data: [...], total: ...} so extract the array
    return data.data || data;
  },
};

// Helper to get auth token from cookie
function getToken(): string | null {
  if (typeof document === 'undefined') return null;
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'access_token') {
      return value;
    }
  }
  return null;
}

// Admin API namespace
export const adminApi = {
  // Events Management
  async getEvents(): Promise<EventItem[]> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/events`, {
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      }
    });
    if (!r.ok) throw new Error(`Failed to fetch events: ${r.status} ${r.statusText}`);
    const data = await r.json();
    return data.events || [];
  },

  async createEvent(eventData: {
    title: string;
    description?: string;
    event_type: string;
    visibility?: string;
    start_date: string;
    end_date: string;
    timezone?: string;
    location?: string;
    is_online?: boolean;
    capacity?: number;
    price?: number;
    instructor_info?: string;
    featured_image_url?: string;
  }): Promise<EventItem> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/events`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData),
    });
    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to create event' }));
      throw new Error(error.detail || `Failed to create event: ${r.status}`);
    }
    return r.json();
  },

  async updateEvent(id: string, eventData: {
    title?: string;
    description?: string;
    event_type?: string;
    visibility?: string;
    start_date?: string;
    end_date?: string;
    timezone?: string;
    location?: string;
    is_online?: boolean;
    capacity?: number;
    price?: number;
    instructor_info?: string;
    featured_image_url?: string;
  }): Promise<EventItem> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/events/${id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData),
    });
    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to update event' }));
      throw new Error(error.detail || `Failed to update event: ${r.status}`);
    }
    return r.json();
  },

  async deleteEvent(id: string): Promise<void> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/events/${id}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to delete event' }));
      throw new Error(error.detail || `Failed to delete event: ${r.status}`);
    }
  },

  // Members Management (placeholder - backend endpoints to be created)
  async getMembers(): Promise<User[]> {
    // TODO: Backend endpoint needed for listing all users
    // For now, return empty array
    return [];
  },

  async createMember(memberData: {
    email: string;
    name: string;
    password: string;
    role?: string;
    belt_rank?: string;
    dojo?: string;
    country?: string;
  }): Promise<User> {
    // TODO: Backend endpoint needed for creating users
    // For now, throw error indicating feature not yet implemented
    throw new Error('Create member endpoint not yet implemented in backend');
  },

  async updateMember(id: string, memberData: {
    name?: string;
    role?: string;
    belt_rank?: string;
    dojo?: string;
    country?: string;
  }): Promise<User> {
    // TODO: Backend endpoint needed for updating users
    throw new Error('Update member endpoint not yet implemented in backend');
  },

  async deleteMember(id: string): Promise<void> {
    // TODO: Backend endpoint needed for deleting users
    throw new Error('Delete member endpoint not yet implemented in backend');
  },

  // Metrics/Analytics
  async getMetrics(): Promise<{
    total_members: number;
    revenue_monthly: number;
    active_events: number;
    retention_rate: number;
  }> {
    // TODO: Backend endpoint needed for admin metrics
    // Return mock data for now
    return {
      total_members: 248,
      revenue_monthly: 42300,
      active_events: 12,
      retention_rate: 0.94,
    };
  },
};
