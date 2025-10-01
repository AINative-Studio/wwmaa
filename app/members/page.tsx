import { DirectoryContent } from "./directory-content";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "WWMAA Member Directory | Find Martial Arts Students & Instructors",
  description: "Connect with WWMAA martial arts students, instructors, and dojos across the United States. Join our growing community of martial artists.",
  openGraph: {
    title: "WWMAA Member Directory | Find Martial Arts Students & Instructors",
    description: "Connect with WWMAA martial arts students, instructors, and dojos across the United States. Join our growing community of martial artists.",
    type: "website",
  },
};

export default function MembersPage() {
  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-dojo-navy via-dojo-green to-dojo-navy py-24 overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-20"></div>
        <div className="relative mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-6">
            WWMAA Member Directory
          </h1>
          <p className="text-2xl text-white/90 mb-8 max-w-3xl mx-auto">
            Connect with martial arts students, certified instructors, and dojos across the United States
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 text-white">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div className="text-left">
                <p className="text-3xl font-bold">40+</p>
                <p className="text-white/80">Members</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div className="text-left">
                <p className="text-3xl font-bold">10</p>
                <p className="text-white/80">States</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div className="text-left">
                <p className="text-3xl font-bold">20+</p>
                <p className="text-white/80">Dojos</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Directory Content */}
      <DirectoryContent />

      {/* Join CTA Section */}
      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
            Ready to Join Our Community?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Become part of the world's premier martial arts association and connect with practitioners nationwide
          </p>
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="bg-white rounded-xl shadow-card p-6 border border-gray-100">
              <div className="w-12 h-12 rounded-full bg-dojo-green/10 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-dojo-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                Network
              </h3>
              <p className="text-sm text-gray-600">
                Connect with students and instructors across the country
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-card p-6 border border-gray-100">
              <div className="w-12 h-12 rounded-full bg-dojo-orange/10 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-dojo-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                Get Certified
              </h3>
              <p className="text-sm text-gray-600">
                Earn recognized belt ranks and instructor certifications
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-card p-6 border border-gray-100">
              <div className="w-12 h-12 rounded-full bg-dojo-navy/10 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-dojo-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                Compete
              </h3>
              <p className="text-sm text-gray-600">
                Participate in tournaments and showcase your skills
              </p>
            </div>
          </div>
          <Link
            href="/membership"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-dojo-navy to-dojo-green text-white text-lg font-semibold shadow-lg hover:shadow-xl transition-all"
          >
            Become a Member
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>
    </main>
  );
}
