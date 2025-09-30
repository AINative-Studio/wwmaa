interface Params { slug: string }

const programs: Record<string, { title: string; subtitle: string; description: string }> = {
  karate: {
    title: "Karate",
    subtitle: "The Way of the Empty Hand",
    description: "Discipline, strength, and tradition",
  },
  jujitsu: {
    title: "Ju-Jitsu",
    subtitle: "Technique Over Strength",
    description: "Leverage and mastery in combat",
  },
  kendo: {
    title: "Kendo",
    subtitle: "The Way of the Sword",
    description: "Spirit and form in harmony",
  },
  "self-defense": {
    title: "Self-Defense",
    subtitle: "Practical Protection Skills",
    description: "Modern life safety training",
  },
};

export function generateStaticParams() {
  return Object.keys(programs).map((slug) => ({ slug }));
}

export default function ProgramDetail({ params }: { params: Params }) {
  const program = programs[params.slug];

  if (!program) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-bg to-white">
        <div className="text-center px-6">
          <h1 className="font-display text-4xl font-bold text-dojo-navy">Program Not Found</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              {program.title}
            </h1>
            <p className="text-2xl text-white/90 mb-2">{program.subtitle}</p>
            <p className="text-xl text-white/80">{program.description}</p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-4xl px-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full gradient-hero mb-8">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
              Program Details Coming Soon
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-12">
              We're developing comprehensive training materials and curriculum information for {program.title}. Check back soon for detailed program information, training schedules, and requirements.
            </p>

            <div className="grid gap-6 md:grid-cols-3 max-w-3xl mx-auto mb-12">
              <div className="bg-gradient-to-br from-dojo-navy/5 to-dojo-navy/10 rounded-xl p-6">
                <svg className="w-10 h-10 text-dojo-navy mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <h3 className="font-semibold text-dojo-navy mb-2">Curriculum</h3>
                <p className="text-sm text-gray-600">Structured learning path</p>
              </div>
              <div className="bg-gradient-to-br from-dojo-green/5 to-dojo-green/10 rounded-xl p-6">
                <svg className="w-10 h-10 text-dojo-green mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="font-semibold text-dojo-green mb-2">Schedule</h3>
                <p className="text-sm text-gray-600">Class times and dates</p>
              </div>
              <div className="bg-gradient-to-br from-dojo-orange/5 to-dojo-orange/10 rounded-xl p-6">
                <svg className="w-10 h-10 text-dojo-orange mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
                <h3 className="font-semibold text-dojo-orange mb-2">Requirements</h3>
                <p className="text-sm text-gray-600">Prerequisites and ranks</p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="/membership"
                className="inline-flex items-center justify-center gap-2 rounded-xl gradient-orange px-8 py-4 text-lg font-semibold text-white shadow-lg hover:shadow-xl transition-all"
              >
                Join WWMAA
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </a>
              <a
                href="/programs"
                className="inline-flex items-center justify-center rounded-xl border-2 border-dojo-navy px-8 py-4 text-lg font-semibold text-dojo-navy hover:bg-dojo-navy hover:text-white transition-all"
              >
                View All Programs
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
