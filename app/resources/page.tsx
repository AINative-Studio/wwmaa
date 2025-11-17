import { ResourcesClient } from "./ResourcesClient";
import type { Metadata } from "next";

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "Martial Arts Training Resources & Certifications | Belt Requirements | WWMAA",
  description: "Access comprehensive martial arts training materials, belt promotion requirements, tournament rules, instructor certifications, and technical resources. Everything you need for martial arts excellence.",
  keywords: ["martial arts resources", "training materials", "belt requirements", "tournament rules", "instructor certification", "martial arts certification", "training guides"],
  openGraph: {
    title: "Martial Arts Training Resources & Certifications | WWMAA",
    description: "Access comprehensive martial arts training materials, belt requirements, and instructor certifications for martial artists worldwide.",
    type: "website",
  }
};

export default function ResourcesPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      {/* Hero Section */}
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Training Resources
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Access comprehensive martial arts training materials, videos, documents, and certifications to support your martial arts journey.
          </p>
        </div>
      </section>

      {/* Resources Section - Client Component */}
      <ResourcesClient />

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-br from-dojo-navy to-dojo-green">
        <div className="mx-auto max-w-4xl px-6 text-center text-white">
          <h2 className="font-display text-3xl font-bold mb-4">
            Access All Training Resources with WWMAA Membership
          </h2>
          <p className="text-xl text-white/90 mb-8 leading-relaxed">
            Premium and Instructor members receive unlimited access to our complete library of training materials, belt testing resources, tournament guidelines, and exclusive instructor certifications.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/membership"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-dojo-orange text-white font-bold rounded-lg hover:bg-dojo-orange/90 transition-colors text-lg"
            >
              View Membership Plans
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
            <a
              href="/faq"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-dojo-navy font-bold rounded-lg hover:bg-white/90 transition-colors text-lg"
            >
              Common Questions
            </a>
          </div>
        </div>
      </section>

      {/* Additional Info Section */}
      <section className="py-16 bg-white">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-8 md:grid-cols-3">
            <div className="bg-dojo-navy/5 rounded-xl p-6">
              <div className="w-12 h-12 rounded-lg bg-dojo-navy flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                Video Library
              </h3>
              <p className="text-gray-600 text-sm">
                Technique demonstrations, kata tutorials, and training sessions from master instructors
              </p>
            </div>

            <div className="bg-dojo-navy/5 rounded-xl p-6">
              <div className="w-12 h-12 rounded-lg bg-dojo-green flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                Study Guides
              </h3>
              <p className="text-gray-600 text-sm">
                Downloadable PDFs covering techniques, terminology, history, and testing requirements
              </p>
            </div>

            <div className="bg-dojo-navy/5 rounded-xl p-6">
              <div className="w-12 h-12 rounded-lg bg-dojo-orange flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                Certifications
              </h3>
              <p className="text-gray-600 text-sm">
                Official certification programs and requirements for instructors and advanced practitioners
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
