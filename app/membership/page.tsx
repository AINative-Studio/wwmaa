import { api } from "@/lib/api";
import { TierCard } from "@/components/cards/tier-card";
import { ApplicationForm } from "@/components/forms/application-form";

export default async function MembershipPage() {
  const tiers = await api.getTiers();
  return (
    <div className="min-h-screen">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Join the WWMAA Community
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Connect with martial artists worldwide, gain recognition for your achievements, and access exclusive training opportunities.
          </p>
        </div>
      </section>

      <section className="relative py-24 -mt-20">
        <div className="mx-auto max-w-7xl px-6">
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

      <section id="apply" className="py-24 bg-gradient-to-b from-white to-bg">
        <div className="mx-auto max-w-7xl px-6">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="font-display text-4xl font-bold text-dojo-navy">
                Apply for Membership
              </h2>
              <p className="mt-4 text-lg text-gray-600">
                All applications are reviewed by our board to ensure quality and authenticity.
              </p>
            </div>
            <div className="bg-white rounded-2xl shadow-glow p-8 md:p-12">
              <ApplicationForm />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
