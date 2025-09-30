export const dict = {
  en: {
    hero_title: "World Wide Martial Arts Association",
    hero_sub: "Uniting martial artists worldwide through tradition, discipline, and excellence. Join our global community of judo, karate, and martial arts practitioners.",
    cta_join: "Join WWMAA Today",
    programs_title: "Explore Programs",
    events_title: "Upcoming Events",
    membership_title: "Martial Arts Membership Plans",
    apply: "Apply",
    rsvp: "RSVP",
    search_placeholder: "Search techniques, kata, sparring, and more…",
    helpful: "Helpful",
    not_helpful: "Not helpful",
  },
} as const;
export type Locale = keyof typeof dict;
