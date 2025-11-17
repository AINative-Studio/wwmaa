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
  async getCurrentUser(token?: string): Promise<User> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const r = await fetch(LIVE.me, {
      credentials: "include",
      headers
    });
    if (!r.ok) throw new Error(`Failed to fetch user: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async updateProfile(profileData: {
    first_name?: string;
    last_name?: string;
    phone?: string;
    address?: string;
    city?: string;
    state?: string;
    zip_code?: string;
    country?: string;
    emergency_contact?: {
      name: string;
      relationship: string;
      phone: string;
      email?: string;
    };
  }): Promise<{ message: string; user: any }> {
    const token = getToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const r = await fetch(`${API_URL}/api/me/profile`, {
      method: 'PATCH',
      credentials: 'include',
      headers,
      body: JSON.stringify(profileData),
    });
    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to update profile' }));
      throw new Error(error.detail || `Failed to update profile: ${r.status}`);
    }
    return r.json();
  },
  async uploadProfilePhoto(file: File): Promise<{ message: string; photo_url: string }> {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);

    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const r = await fetch(`${API_URL}/api/me/profile/photo`, {
      method: 'POST',
      credentials: 'include',
      headers,
      body: formData,
    });
    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to upload photo' }));
      throw new Error(error.detail || `Failed to upload photo: ${r.status}`);
    }
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

  // Members Management
  async getMembers(params?: {
    limit?: number;
    offset?: number;
    role?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<{ members: User[]; total: number; limit: number; offset: number }> {
    const token = getToken();
    const queryParams = new URLSearchParams();

    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.role) queryParams.append('role', params.role);
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    if (params?.search) queryParams.append('search', params.search);

    const url = `${API_URL}/api/admin/members${queryParams.toString() ? '?' + queryParams.toString() : ''}`;

    const r = await fetch(url, {
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      }
    });

    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to fetch members' }));
      throw new Error(error.detail || `Failed to fetch members: ${r.status}`);
    }

    return r.json();
  },

  async createMember(memberData: {
    email: string;
    first_name: string;
    last_name: string;
    password: string;
    role?: string;
    is_active?: boolean;
    phone?: string;
  }): Promise<User> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/admin/members`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(memberData),
    });

    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to create member' }));
      throw new Error(error.detail || `Failed to create member: ${r.status}`);
    }

    return r.json();
  },

  async updateMember(id: string, memberData: {
    email?: string;
    first_name?: string;
    last_name?: string;
    role?: string;
    is_active?: boolean;
    phone?: string;
    password?: string;
  }): Promise<User> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/admin/members/${id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(memberData),
    });

    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to update member' }));
      throw new Error(error.detail || `Failed to update member: ${r.status}`);
    }

    return r.json();
  },

  async deleteMember(id: string): Promise<void> {
    const token = getToken();
    const r = await fetch(`${API_URL}/api/admin/members/${id}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });

    if (!r.ok) {
      const error = await r.json().catch(() => ({ detail: 'Failed to delete member' }));
      throw new Error(error.detail || `Failed to delete member: ${r.status}`);
    }
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
