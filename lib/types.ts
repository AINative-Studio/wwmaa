export type Role = "Guest" | "Member" | "BoardMember" | "Admin" | "SuperAdmin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  locale?: string;
  belt_rank?: string;
  dojo?: string;
  country?: string;
}

export interface MembershipTier {
  id: string;
  code: "basic" | "premium" | "instructor";
  name: string;
  price_usd: number;
  benefits: string[];
}

export interface Application {
  id: string;
  user_id: string;
  discipline: string;
  experience: string;
  refs?: string;
  status: "Pending" | "Approved" | "Rejected";
  created_at: string;
}

export interface EventItem {
  id: string;
  title: string;
  start: string;
  end: string;
  location: string;
  type: "live" | "training" | "seminar" | "tournament";
  price?: number;
  visibility: "public" | "member";
  teaser?: string;
  image?: string;
}

export interface RSVP {
  id: string;
  event_id: string;
  user_id: string;
  status: "going" | "waitlist" | "canceled";
  payment_id?: string;
}

export interface TrainingSession {
  id: string;
  event_id: string;
  rtc_room_id: string;
  vod_id?: string;
}

export interface SearchResult {
  id: string;
  answer: string;
  sources: { title: string; url: string }[];
  media?: { type: "image" | "video"; url: string; license?: string }[];
  latency_ms: number;
}

export interface Article {
  id: string;
  title: string;
  url: string;
  excerpt: string;
  published_at: string;
}

export interface Certification {
  id: string;
  name: string;
  description: string;
  level?: string;
}
