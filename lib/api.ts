import { tiers, me, applications, events, articles, certifications, searchSample } from "./mock/db";
import { MembershipTier, User, Application, EventItem, SearchResult, Article, Certification } from "./types";

const MODE = process.env.NEXT_PUBLIC_API_MODE ?? "mock";
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
    if (MODE === "mock") return tiers;
    const r = await fetch(LIVE.memberships);
    if (!r.ok) throw new Error(`Failed to fetch tiers: ${r.status} ${r.statusText}`);
    const data = await r.json();
    // Backend returns {tiers: [...]} so extract the array
    return data.tiers || data;
  },
  async getCurrentUser(): Promise<User> {
    if (MODE === "mock") return me;
    const r = await fetch(LIVE.me, { credentials: "include" });
    if (!r.ok) throw new Error(`Failed to fetch user: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async submitApplication(payload: Partial<Application>): Promise<{ ok: boolean; id: string }> {
    if (MODE === "mock") return { ok: true, id: "a_mock_new" };
    const r = await fetch(LIVE.applications, { method: "POST", body: JSON.stringify(payload) });
    if (!r.ok) throw new Error(`Failed to submit application: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getApplications(): Promise<Application[]> {
    if (MODE === "mock") return applications;
    const r = await fetch(`${LIVE.applications}?status=pending`);
    if (!r.ok) throw new Error(`Failed to fetch applications: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getEvents(): Promise<EventItem[]> {
    if (MODE === "mock") return events;
    const r = await fetch(LIVE.events);
    if (!r.ok) throw new Error(`Failed to fetch events: ${r.status} ${r.statusText}`);
    const data = await r.json();
    // Backend returns { events: [...], total, limit, offset, has_more }
    return data.events || [];
  },
  async getEvent(id: string): Promise<EventItem | null> {
    if (MODE === "mock") return events.find(e => e.id === id) ?? null;
    const r = await fetch(LIVE.event(id));
    if (!r.ok) return null;
    return r.json();
  },
  async rsvpEvent(id: string): Promise<{ ok: boolean }> {
    if (MODE === "mock") return { ok: true };
    const r = await fetch(LIVE.rsvp(id), { method: "POST" });
    if (!r.ok) throw new Error(`Failed to RSVP event: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async search(q: string): Promise<SearchResult> {
    if (MODE === "mock") return { ...searchSample, id: "s_mock", latency_ms: 180, answer: searchSample.answer + ` (Q="${q}")` };
    const r = await fetch(LIVE.search, { method:"POST", body: JSON.stringify({ q }) });
    if (!r.ok) throw new Error(`Failed to search: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getArticles(): Promise<Article[]> {
    if (MODE === "mock") return articles;
    const r = await fetch(LIVE.beehiivFeed);
    if (!r.ok) throw new Error(`Failed to fetch articles: ${r.status} ${r.statusText}`);
    return r.json();
  },
  async getCertifications(): Promise<Certification[]> {
    if (MODE === "mock") return certifications;
    const r = await fetch(LIVE.certifications);
    if (!r.ok) throw new Error(`Failed to fetch certifications: ${r.status} ${r.statusText}`);
    const data = await r.json();
    // Backend returns {data: [...], total: ...} so extract the array
    return data.data || data;
  },
};
