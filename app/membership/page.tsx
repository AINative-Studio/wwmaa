import { api } from "@/lib/api";
import { TierCard } from "@/components/cards/tier-card";
import { ApplicationForm } from "@/components/forms/application-form";
import type { Metadata } from "next";

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "Martial Arts Membership Plans | Join WWMAA Today | World Wide Martial Arts",
  description: "Choose from Basic, Premium, or Instructor membership plans. Access exclusive training, tournaments, and certifications with WWMAA.",
  openGraph: {
    title: "Martial Arts Membership Plans | Join WWMAA Today",
    description: "Choose from Basic, Premium, or Instructor membership plans. Access exclusive training, tournaments, and certifications with WWMAA.",
    type: "website",
    url: "https://wwmaa.ainative.studio/membership",
    images: [
      {
        url: "https://wwmaa.ainative.studio/images/logo.png",
        width: 1200,
        height: 630,
        alt: "WWMAA Membership",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Martial Arts Membership Plans | Join WWMAA Today",
    description: "Choose from Basic, Premium, or Instructor membership plans. Access exclusive training, tournaments, and certifications with WWMAA.",
  },
};

export default async function MembershipPage() {
  const tiers = await api.getTiers();

  // Create schema for each membership tier following SEO plan structure
  const membershipSchemas = tiers.map((tier) => ({
    "@context": "https://schema.org",
    "@type": "MembershipProgramTier",
    "name": `${tier.name} Membership`,
    "description": `WWMAA ${tier.name} membership - ${tier.benefits[0]}`,
    "membershipPointsEarned": tier.name === "Premium" ? 100 : tier.name === "Instructor" ? 150 : 50,
    "offers": {
      "@type": "Offer",
      "price": tier.price_usd.toString(),
      "priceCurrency": "USD",
      "priceValidUntil": "2025-12-31",
      "availability": "https://schema.org/InStock",
      "url": "https://wwmaa.ainative.studio/membership"
    },
    "programBenefits": tier.benefits
  }));

  return (
    <main className="min-h-screen">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(membershipSchemas) }}
      />
      <header className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Martial Arts Membership Plans
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Connect with martial artists worldwide, gain recognition for your achievements, and access exclusive judo and karate training opportunities.
          </p>
        </div>
      </header>

      <section className="relative py-24 -mt-20" aria-labelledby="membership-tiers-heading">
        <div className="mx-auto max-w-7xl px-6">
          <h2 id="membership-tiers-heading" className="sr-only">Membership Tier Options</h2>
          <div className="grid gap-8 md:grid-cols-3">
            {tiers.map((t, idx) => (
              <TierCard
                key={t.id}
                name={t.name}
                price={t.price_usd}
                benefits={t.benefits}
                featured={idx === 1}
              />
            ))}
          </div>
        </div>
      </section>

      <section id="apply" className="py-24 bg-gradient-to-b from-white to-bg" aria-labelledby="apply-heading">
        <div className="mx-auto max-w-7xl px-6">
          <div className="max-w-3xl mx-auto">
            <header className="text-center mb-12">
              <h2 id="apply-heading" className="font-display text-4xl font-bold text-dojo-navy">
                Apply for Membership
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                All applications are reviewed by our board to ensure quality and authenticity.
              </p>
            </header>
            <div className="bg-white rounded-2xl shadow-glow p-8 md:p-12">
              <ApplicationForm />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
