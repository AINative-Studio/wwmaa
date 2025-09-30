export const dict = {
  en: {
    hero_title: "Uniting martial artists across the globe",
    hero_sub: "Tradition, discipline, and community in the modern age.",
    cta_join: "Join WWMAA Today",
    programs_title: "Explore Programs",
    events_title: "Upcoming Events",
    membership_title: "Membership",
    apply: "Apply",
    rsvp: "RSVP",
    search_placeholder: "Search techniques, kata, sparring, and more…",
    helpful: "Helpful",
    not_helpful: "Not helpful",
  },
} as const;
export type Locale = keyof typeof dict;
