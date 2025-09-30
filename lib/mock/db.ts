import { MembershipTier, User, Application, EventItem, SearchResult, Article, Certification } from "./../types";

export const tiers: MembershipTier[] = [
  { id: "t_basic", code: "basic", name: "Basic", price_usd: 29, benefits: ["News & blog", "Public events"] },
  { id: "t_premium", code: "premium", name: "Premium", price_usd: 79, benefits: ["Belt recognition", "Member training", "Event discounts"] },
  { id: "t_instr", code: "instructor", name: "Instructor", price_usd: 149, benefits: ["Instructor pathway", "Advanced seminars", "Directory listing"] },
];

export const me: User = {
  id: "u_001",
  name: "Alex Kim",
  email: "alex@example.com",
  role: "Member",
  locale: "en",
  belt_rank: "Brown",
  dojo: "Seaside Dojo",
  country: "US",
};

export const applications: Application[] = [
  { id: "a_101", user_id: "u_200", discipline: "Karate", experience: "5 years", refs: "Sensei Ito", status: "Pending", created_at: "2025-09-01T10:00:00Z" },
  { id: "a_102", user_id: "u_201", discipline: "Kendo", experience: "3 years", status: "Pending", created_at: "2025-09-05T16:30:00Z" },
];

export const events: EventItem[] = [
  { id: "e_300", title: "Live Ju-Jitsu Seminar", start: "2025-10-05T17:00:00Z", end:"2025-10-05T19:00:00Z", location: "Online", type:"training", price:25, visibility:"member", teaser:"Train with senior masters live.", image:"/images/jujitsu.jpg" },
  { id: "e_301", title: "Karate Kata Workshop", start: "2025-10-12T18:00:00Z", end:"2025-10-12T20:00:00Z", location: "Tokyo", type:"seminar", price:80, visibility:"public", teaser:"Traditional kata refinement.", image:"/images/karate.jpg" },
];

export const articles: Article[] = [
  { id: "ar_1", title:"Foundations of Kendo", url:"https://beehiiv.example.com/kendo", excerpt:"Spirit, posture, and the way of the sword.", published_at:"2025-09-10" },
  { id: "ar_2", title:"Ju-Jitsu: Technique over Strength", url:"https://beehiiv.example.com/jujitsu", excerpt:"Leverage, timing, and control.", published_at:"2025-09-20" },
];

export const certifications: Certification[] = [
  { id:"c_bb", name:"Black Belt Certification", description:"Formal recognition of rank and lineage." },
  { id:"c_instr", name:"Instructor Certification", description:"Pathway for certified instructors." },
];

export const searchSample: SearchResult = {
  id: "s_1",
  answer: "Ju-Jitsu emphasizes leverage, timing, and technique to overcome strength.",
  sources: [{ title: "Ju-Jitsu Basics", url:"https://example.com/jujitsu/basics" }],
  media: [{ type:"video", url:"https://videos.example.com/jujitsu_intro.mp4" }],
  latency_ms: 220,
};
