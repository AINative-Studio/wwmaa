export function orgJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "World Wide Martial Arts Association (WWMAA)",
    url: "https://wwmaa.org",
    sameAs: ["https://x.com/wwmaa"],
  };
}

export function eventJsonLd(e: { name: string; startDate: string; endDate?: string; location: string; url: string }) {
  return {
    "@context": "https://schema.org",
    "@type": "Event",
    name: e.name,
    startDate: e.startDate,
    endDate: e.endDate ?? e.startDate,
    eventAttendanceMode: "https://schema.org/MixedEventAttendanceMode",
    location: { "@type": "Place", name: e.location },
    url: e.url,
  };
}
