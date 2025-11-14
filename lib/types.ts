export type Role = "guest" | "member" | "board_member" | "admin" | "superadmin" | "student" | "instructor";

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

export type ApplicationStatus = "DRAFT" | "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED";

export interface Application {
  id: string;
  user_id: string;
  discipline: string;
  experience: string;
  refs?: string;
  status: "Pending" | "Approved" | "Rejected";
  created_at: string;
}

export interface MembershipApplication {
  id: string;
  applicant_email: string;
  applicant_name: string;
  applicant_phone?: string;
  applicant_address?: string;
  martial_arts_style: string;
  years_experience: number;
  current_rank?: string;
  instructor_name?: string;
  school_affiliation?: string;
  reason_for_joining: string;
  status: ApplicationStatus;
  submitted_at?: string;
  first_approval_at?: string;
  approved_at?: string;
  rejected_at?: string;
  rejection_reason?: string;
  can_reapply?: boolean;
  reapply_after?: string;
  approval_count: number;
  required_approvals: number;
  approved_by?: string[];
  created_at: string;
  updated_at: string;
}

export interface ApplicationApproval {
  id: string;
  application_id: string;
  board_member_id: string;
  board_member_name: string;
  approved_at: string;
  comments?: string;
}

export interface ApplicationTimeline {
  event: string;
  timestamp: string;
  description: string;
  actor?: string;
}

export type EventType = "live_training" | "seminar" | "tournament" | "certification";
export type EventLocationType = "in_person" | "online";
export type EventVisibility = "public" | "members_only";
export type EventStatus = "draft" | "published" | "canceled" | "completed" | "deleted";

export interface EventItem {
  id: string;
  title: string;
  description?: string;
  start: string;
  end: string;
  location: string;
  location_type: EventLocationType;
  type: EventType;
  price: number;
  visibility: EventVisibility;
  status: EventStatus;
  teaser?: string;
  image?: string;
  max_participants?: number;
  current_participants?: number;
  instructor?: string;
  created_at: string;
  updated_at: string;
}

export interface EventFilters {
  type?: EventType;
  date_from?: string;
  date_to?: string;
  location?: EventLocationType;
  price?: "free" | "paid";
  visibility?: EventVisibility;
}

export interface EventSort {
  sort_by: "date" | "price";
  sort_order: "asc" | "desc";
}

export interface EventListResponse {
  events: EventItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
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

export type SubscriptionStatus = "active" | "past_due" | "canceled" | "trialing" | "incomplete" | "incomplete_expired" | "unpaid";

export interface Subscription {
  id: string;
  user_id: string;
  tier: string;
  tier_name: string;
  status: SubscriptionStatus;
  price: number;
  currency: string;
  stripe_subscription_id?: string;
  stripe_customer_id?: string;
  current_period_start: string;
  current_period_end: string;
  next_billing_date?: string;
  cancel_at_period_end: boolean;
  canceled_at?: string;
  trial_end?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  brand?: string;
  last4?: string;
  exp_month?: number;
  exp_year?: number;
}

export interface Invoice {
  id: string;
  number: string;
  amount_paid: number;
  currency: string;
  status: string;
  created: string;
  invoice_pdf?: string;
  hosted_invoice_url?: string;
}

export interface SubscriptionDetails {
  subscription: Subscription;
  payment_method?: PaymentMethod;
  upcoming_invoice?: {
    amount_due: number;
    currency: string;
    next_payment_attempt?: string;
  };
  recent_invoices: Invoice[];
}
