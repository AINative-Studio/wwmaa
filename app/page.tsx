import { Hero } from "@/components/hero";
import { api } from "@/lib/api";
import { dict } from "@/lib/i18n";
import { TierCard } from "@/components/cards/tier-card";

export default async function HomePage() {
  const tiers = await api.getTiers();
  const t = dict.en;
  return (
    <>
      <Hero />

      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 gradient-accent"></div>
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-dojo-navy">
              {t.membership_title}
            </h2>
            <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
              From Karate to Kendo, explore styles across the WWMAA community and find the perfect path for your martial arts journey.
            </p>
          </div>
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
    </>
  );
}
