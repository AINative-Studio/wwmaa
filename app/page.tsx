import { Hero } from "@/components/hero";
import { api } from "@/lib/api";
import { dict } from "@/lib/i18n";
import { TierCard } from "@/components/cards/tier-card";
import Link from "next/link";
import type { Metadata } from "next";
import type { MembershipTier } from "@/lib/types";

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "World Wide Martial Arts Association | Judo, Karate & Self-Defense Training | WWMAA",
  description: "Join the World Wide Martial Arts Association. Offering judo, karate, and martial arts training worldwide. Become a member today!",
  openGraph: {
    title: "World Wide Martial Arts Association | Judo, Karate & Self-Defense Training | WWMAA",
    description: "Join the World Wide Martial Arts Association. Offering judo, karate, and martial arts training worldwide. Become a member today!",
    type: "website",
    url: "https://wwmaa.ainative.studio",
    images: [
      {
        url: "https://wwmaa.ainative.studio/images/logo.png",
        width: 1200,
        height: 630,
        alt: "WWMAA Logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "World Wide Martial Arts Association | Judo, Karate & Self-Defense Training | WWMAA",
    description: "Join the World Wide Martial Arts Association. Offering judo, karate, and martial arts training worldwide. Become a member today!",
  },
};

export default async function HomePage() {
  // Fetch tiers from backend API
  let tiers: MembershipTier[];
  try {
    tiers = await api.getTiers();
  } catch (error) {
    console.error('Failed to fetch tiers:', error);
    // Return empty array on error
    tiers = [];
  }
  const t = dict.en;

  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "SportsOrganization",
    "name": "World Wide Martial Arts Association",
    "alternateName": "WWMAA",
    "url": "https://wwmaa.ainative.studio",
    "logo": "https://wwmaa.ainative.studio/images/logo.png",
    "foundingDate": "1995",
    "founder": {
      "@type": "Person",
      "name": "Philip S. Porter",
      "honorificPrefix": "O-Sensei",
      "jobTitle": "Founder",
      "description": "10th Dan Judo Master, Father of American Judo"
    },
    "sport": ["Judo", "Karate", "Jiu-Jitsu", "Martial Arts"],
    "memberOf": {
      "@type": "SportsOrganization",
      "name": "International Judo Federation"
    },
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "Membership Services",
      "email": "info@wwmaa.com",
      "availableLanguage": ["English"]
    },
    "sameAs": [
      "https://facebook.com/wwmaa",
      "https://twitter.com/wwmaa",
      "https://instagram.com/wwmaa"
    ],
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "US"
    }
  };

  return (
    <main>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
      />
      <Hero />

      <section className="relative py-24 overflow-hidden" aria-labelledby="membership-heading">
        <div className="absolute inset-0 gradient-accent"></div>
        <div className="relative mx-auto max-w-7xl px-6">
          <header className="text-center mb-16">
            <h2 id="membership-heading" className="font-display text-4xl sm:text-5xl font-bold text-dojo-navy">
              {t.membership_title}
            </h2>
            <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
              From Karate to Kendo, explore styles across the WWMAA community and find the perfect path for your martial arts journey.
            </p>
          </header>
          <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
            {tiers.map((tier, idx) => (
              <TierCard
                key={tier.id}
                name={tier.name}
                price={tier.price_usd}
                benefits={tier.benefits}
                featured={idx === 1}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Featured Programs Section */}
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <header className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-dojo-navy mb-4">
              Martial Arts Training Programs
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Discover our comprehensive <Link href="/programs" className="text-dojo-navy font-semibold hover:text-dojo-green transition-colors">martial arts programs</Link> designed for practitioners of all levels.
            </p>
          </header>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <article className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-card hover:shadow-glow transition-all p-8 border border-gray-100">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-r from-dojo-navy to-dojo-green flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Martial Arts Tournaments</h3>
              <p className="text-gray-600 mb-6">
                Compete in <Link href="/programs/tournaments" className="text-dojo-green hover:underline font-semibold">WWMAA-sanctioned tournaments</Link> and test your skills against martial artists worldwide.
              </p>
              <Link
                href="/programs/tournaments"
                className="inline-flex items-center text-dojo-navy font-semibold hover:text-dojo-green transition-colors"
              >
                Learn more
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </article>

            <article className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-card hover:shadow-glow transition-all p-8 border border-gray-100">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-r from-dojo-orange to-yellow-500 flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Summer Camp</h3>
              <p className="text-gray-600 mb-6">
                Join our intensive <Link href="/programs/camp" className="text-dojo-orange hover:underline font-semibold">martial arts summer camp</Link> for immersive training with master instructors.
              </p>
              <Link
                href="/programs/camp"
                className="inline-flex items-center text-dojo-navy font-semibold hover:text-dojo-orange transition-colors"
              >
                Learn more
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </article>

            <article className="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-card hover:shadow-glow transition-all p-8 border border-gray-100">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <h3 className="font-display text-2xl font-bold text-dojo-navy mb-3">Belt Promotions</h3>
              <p className="text-gray-600 mb-6">
                Progress through our <Link href="/programs/promotions" className="text-purple-600 hover:underline font-semibold">belt ranking system</Link> and achieve your martial arts goals.
              </p>
              <Link
                href="/programs/promotions"
                className="inline-flex items-center text-dojo-navy font-semibold hover:text-purple-600 transition-colors"
              >
                Learn more
                <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </article>
          </div>
          <div className="text-center mt-12">
            <Link
              href="/programs"
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl font-semibold text-lg bg-gradient-to-r from-dojo-navy to-dojo-green text-white shadow-lg hover:shadow-xl transition-all"
            >
              View All Programs
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Why Choose WWMAA Section */}
      <section className="py-24 bg-gradient-to-b from-gray-50 to-white">
        <div className="mx-auto max-w-7xl px-6">
          <header className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-dojo-navy mb-4">
              Why Choose WWMAA
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Founded by <Link href="/founder" className="text-dojo-navy font-semibold hover:text-dojo-green transition-colors">O-Sensei Philip S. Porter</Link>, the Father of American Judo, WWMAA has been uniting martial artists worldwide since 1995.
            </p>
          </header>
          <div className="grid md:grid-cols-2 gap-12 max-w-5xl mx-auto">
            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-lg bg-dojo-green/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-dojo-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="font-display text-xl font-bold text-dojo-navy mb-2">Recognized Certification</h3>
                <p className="text-gray-600">
                  Earn internationally recognized <Link href="/programs/promotions" className="text-dojo-green hover:underline">belt ranks</Link> and <Link href="/membership" className="text-dojo-green hover:underline">instructor certifications</Link> respected worldwide.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-lg bg-dojo-orange/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-dojo-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="font-display text-xl font-bold text-dojo-navy mb-2">Global Community</h3>
                <p className="text-gray-600">
                  Connect with martial artists worldwide through our <Link href="/events" className="text-dojo-orange hover:underline">events</Link>, <Link href="/programs/tournaments" className="text-dojo-orange hover:underline">tournaments</Link>, and online training resources.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-lg bg-dojo-navy/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-dojo-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="font-display text-xl font-bold text-dojo-navy mb-2">Expert Instruction</h3>
                <p className="text-gray-600">
                  Train with master instructors and access exclusive <Link href="/resources" className="text-dojo-navy hover:underline">training materials</Link> and techniques refined over decades.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="font-display text-xl font-bold text-dojo-navy mb-2">Flexible Programs</h3>
                <p className="text-gray-600">
                  From <Link href="/programs/camp" className="text-purple-600 hover:underline">intensive summer camps</Link> to local dojo training, find programs that fit your schedule and goals.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Latest from Blog Section */}
      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <header className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-dojo-navy mb-4">
              Martial Arts Training Tips & News
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Stay informed with expert advice and insights from the <Link href="/blog" className="text-dojo-navy font-semibold hover:text-dojo-green transition-colors">WWMAA blog</Link>.
            </p>
          </header>
          <div className="grid md:grid-cols-3 gap-8">
            <article className="group">
              <Link href="/blog/complete-guide-to-martial-arts-belt-ranking-systems" className="block">
                <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-card group-hover:shadow-glow transition-all p-6 border border-gray-100 h-full">
                  <div className="inline-block px-3 py-1 rounded-full bg-dojo-green/10 text-dojo-green text-sm font-semibold mb-4">
                    Training & Education
                  </div>
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-3 group-hover:text-dojo-green transition-colors">
                    Complete Guide to Martial Arts Belt Ranking Systems
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Learn everything about belt colors, advancement requirements, and the path to black belt mastery.
                  </p>
                  <span className="text-dojo-green font-semibold inline-flex items-center">
                    Read article
                    <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </Link>
            </article>

            <article className="group">
              <Link href="/blog/5-benefits-of-martial-arts-training-for-adults" className="block">
                <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-card group-hover:shadow-glow transition-all p-6 border border-gray-100 h-full">
                  <div className="inline-block px-3 py-1 rounded-full bg-dojo-orange/10 text-dojo-orange text-sm font-semibold mb-4">
                    Adult Training
                  </div>
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-3 group-hover:text-dojo-orange transition-colors">
                    5 Life-Changing Benefits of Martial Arts Training for Adults
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Discover how martial arts training transforms fitness, stress management, and personal confidence.
                  </p>
                  <span className="text-dojo-orange font-semibold inline-flex items-center">
                    Read article
                    <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </Link>
            </article>

            <article className="group">
              <Link href="/blog/preparing-for-your-first-martial-arts-tournament" className="block">
                <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-card group-hover:shadow-glow transition-all p-6 border border-gray-100 h-full">
                  <div className="inline-block px-3 py-1 rounded-full bg-purple-100 text-purple-600 text-sm font-semibold mb-4">
                    Competition
                  </div>
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-3 group-hover:text-purple-600 transition-colors">
                    Preparing for Your First Martial Arts Tournament
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Get expert tips on training, mental preparation, and what to expect on competition day.
                  </p>
                  <span className="text-purple-600 font-semibold inline-flex items-center">
                    Read article
                    <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </Link>
            </article>
          </div>
          <div className="text-center mt-12">
            <Link
              href="/blog"
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl font-semibold text-lg bg-gradient-to-r from-dojo-navy to-dojo-green text-white shadow-lg hover:shadow-xl transition-all"
            >
              View All Articles
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
