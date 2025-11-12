import { api } from "@/lib/api";
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

export default async function ResourcesPage() {
  const certs = await api.getCertifications();
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Training Resources & Certifications
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Comprehensive martial arts training materials, belt promotion requirements, tournament guidelines, and professional certifications for practitioners at every level.
          </p>
        </div>
      </section>

      <section className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12">
            <h2 className="font-display text-4xl font-bold text-dojo-navy text-center">
              Official Martial Arts Certifications
            </h2>
            <p className="mt-4 text-lg text-gray-600 text-center max-w-2xl mx-auto">
              Recognized credentials that validate your expertise and dedication to martial arts excellence. WWMAA certifications are accepted worldwide by schools, organizations, and competitions.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {certs.map((c)=>(
              <div key={c.id} className="group bg-white rounded-2xl overflow-hidden shadow-hover">
                <div className="h-32 gradient-navy relative">
                  <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-30"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                    </svg>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="font-display text-xl font-bold text-dojo-navy group-hover:text-dojo-green transition-colors">
                    {c.name}
                  </h3>
                  <p className="mt-3 text-gray-600 leading-relaxed">{c.description}</p>
                  <button className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-dojo-orange">
                    Learn More
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="mx-auto max-w-6xl px-6">
          <article className="mb-16">
            <h2 className="font-display text-3xl font-bold text-dojo-navy mb-6">
              Belt Ranking Requirements and Progression
            </h2>
            <div className="prose prose-lg max-w-none text-gray-700">
              <p className="text-lg leading-relaxed mb-4">
                Understanding the <strong>belt ranking system</strong> is essential for every martial artist's journey. WWMAA maintains traditional standards across multiple disciplines including Judo, Karate, Jiu-Jitsu, and Taekwondo. Each belt rank represents specific technical proficiency, training time, and character development milestones.
              </p>
              <div className="grid gap-6 md:grid-cols-2 my-8">
                <div className="bg-dojo-navy/5 rounded-xl p-6">
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-3">
                    Colored Belt Requirements
                  </h3>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Minimum training time: 3-6 months between ranks</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Technical proficiency in required techniques</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Knowledge of terminology and history</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Demonstration of proper etiquette and spirit</span>
                    </li>
                  </ul>
                </div>
                <div className="bg-dojo-navy/5 rounded-xl p-6">
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-3">
                    Black Belt Standards
                  </h3>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-orange flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Minimum 4-6 years of consistent training</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-orange flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Mastery of fundamental techniques</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-orange flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Competition or teaching experience</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-dojo-orange flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Comprehensive written and practical examination</span>
                    </li>
                  </ul>
                </div>
              </div>
              <p className="text-lg leading-relaxed">
                For detailed belt promotion requirements specific to your discipline, <a href="/membership" className="text-dojo-green font-semibold hover:text-dojo-orange transition-colors">WWMAA members</a> have access to comprehensive testing manuals, video demonstrations, and downloadable study guides. Learn more in our <a href="/blog/complete-guide-to-martial-arts-belt-ranking-systems" className="text-dojo-green font-semibold hover:text-dojo-orange transition-colors">Complete Guide to Belt Ranking Systems</a>.
              </p>
            </div>
          </article>

          <article className="mb-16">
            <h2 className="font-display text-3xl font-bold text-dojo-navy mb-6">
              Tournament Rules and Competition Guidelines
            </h2>
            <div className="prose prose-lg max-w-none text-gray-700">
              <p className="text-lg leading-relaxed mb-4">
                <strong>WWMAA-sanctioned tournaments</strong> follow internationally recognized rules ensuring fair, safe, and exciting competition. Whether you're competing in kata, kumite, or grappling divisions, understanding tournament regulations is crucial for success.
              </p>
              <div className="bg-gradient-to-br from-dojo-navy/5 to-dojo-green/5 rounded-xl p-8 my-8">
                <h3 className="font-display text-2xl font-bold text-dojo-navy mb-4">
                  Competition Divisions
                </h3>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div>
                    <h4 className="font-bold text-dojo-navy mb-2">Forms (Kata)</h4>
                    <p className="text-sm text-gray-600">Solo performance of choreographed techniques judged on precision, power, and presentation</p>
                  </div>
                  <div>
                    <h4 className="font-bold text-dojo-navy mb-2">Sparring (Kumite)</h4>
                    <p className="text-sm text-gray-600">Point-based or continuous fighting formats with protective equipment</p>
                  </div>
                  <div>
                    <h4 className="font-bold text-dojo-navy mb-2">Grappling</h4>
                    <p className="text-sm text-gray-600">Submission-based or points-based ground fighting competitions</p>
                  </div>
                </div>
              </div>
              <p className="text-lg leading-relaxed">
                Preparing for your first tournament? Our comprehensive guide <a href="/blog/preparing-for-your-first-martial-arts-tournament" className="text-dojo-green font-semibold hover:text-dojo-orange transition-colors">Preparing for Your First Martial Arts Tournament</a> covers training strategies, mental preparation, and competition day success tips. View <a href="/programs/tournaments" className="text-dojo-green font-semibold hover:text-dojo-orange transition-colors">upcoming WWMAA tournaments</a> and register today.
              </p>
            </div>
          </article>

          <article className="mb-16">
            <h2 className="font-display text-3xl font-bold text-dojo-navy mb-6">
              Training Materials and Technical Resources
            </h2>
            <div className="prose prose-lg max-w-none text-gray-700">
              <p className="text-lg leading-relaxed mb-6">
                WWMAA members receive access to an extensive library of <strong>martial arts training materials</strong> designed to supplement dojo practice and accelerate skill development.
              </p>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 my-8">
                <div className="bg-white rounded-xl p-6 shadow-hover">
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
                <div className="bg-white rounded-xl p-6 shadow-hover">
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
                <div className="bg-white rounded-xl p-6 shadow-hover">
                  <div className="w-12 h-12 rounded-lg bg-dojo-orange flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                    Testing Checklists
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Belt-specific requirement lists ensuring you're prepared for promotion examinations
                  </p>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-hover">
                  <div className="w-12 h-12 rounded-lg bg-dojo-navy flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                    Training Plans
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Structured workout programs for skill development, conditioning, and competition preparation
                  </p>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-hover">
                  <div className="w-12 h-12 rounded-lg bg-dojo-green flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                    Event Calendars
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Tournament schedules, seminar dates, and training camp information updated monthly
                  </p>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-hover">
                  <div className="w-12 h-12 rounded-lg bg-dojo-orange flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <h3 className="font-display text-lg font-bold text-dojo-navy mb-2">
                    Instructor Resources
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Lesson plans, teaching methodologies, and curriculum guides for certified instructors
                  </p>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className="py-16 bg-gradient-to-br from-dojo-navy to-dojo-green">
        <div className="mx-auto max-w-4xl px-6 text-center text-white">
          <h2 className="font-display text-3xl font-bold mb-4">
            Access All Training Resources with WWMAA Membership
          </h2>
          <p className="text-xl text-white/90 mb-8 leading-relaxed">
            Premium and Instructor members receive unlimited access to our complete library of training materials, belt testing resources, tournament guidelines, and exclusive instructor certifications. Accelerate your martial arts journey with professional resources trusted by practitioners worldwide.
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

      <section className="py-16 bg-white">
        <div className="mx-auto max-w-4xl px-6">
          <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6 text-center">
            Related Articles
          </h2>
          <div className="grid gap-6 sm:grid-cols-3">
            <a
              href="/blog/complete-guide-to-martial-arts-belt-ranking-systems"
              className="group bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-xl p-6 transition-colors"
            >
              <h3 className="font-display text-lg font-bold text-dojo-navy group-hover:text-dojo-green transition-colors mb-2">
                Belt Ranking Guide
              </h3>
              <p className="text-sm text-gray-600">
                Complete guide to belt progression and requirements
              </p>
            </a>
            <a
              href="/blog/how-to-choose-the-right-martial-arts-style"
              className="group bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-xl p-6 transition-colors"
            >
              <h3 className="font-display text-lg font-bold text-dojo-navy group-hover:text-dojo-green transition-colors mb-2">
                Choosing Your Style
              </h3>
              <p className="text-sm text-gray-600">
                Find the martial art that matches your goals
              </p>
            </a>
            <a
              href="/blog/preparing-for-your-first-martial-arts-tournament"
              className="group bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-xl p-6 transition-colors"
            >
              <h3 className="font-display text-lg font-bold text-dojo-navy group-hover:text-dojo-green transition-colors mb-2">
                Tournament Prep
              </h3>
              <p className="text-sm text-gray-600">
                Expert strategies for competition success
              </p>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
