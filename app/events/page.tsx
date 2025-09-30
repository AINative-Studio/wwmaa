export default function EventsPage() {
  return (
    <div className="min-h-screen">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              Events
            </h1>
            <p className="text-2xl text-white/90">
              Seminars, tournaments, and training sessions
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-dojo-green to-dojo-navy mb-8">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
            Events Coming Soon
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-12 leading-relaxed">
            We're preparing an exciting calendar of seminars, tournaments, and live training sessions with masters from around the world. Check back soon for updates.
          </p>

          <div className="grid gap-6 md:grid-cols-3 max-w-3xl mx-auto mb-12">
            <div className="bg-gradient-to-br from-dojo-navy/5 to-dojo-navy/10 rounded-xl p-6">
              <svg className="w-10 h-10 text-dojo-navy mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h3 className="font-semibold text-dojo-navy mb-2">Seminars</h3>
              <p className="text-sm text-gray-600">Learn from masters</p>
            </div>
            <div className="bg-gradient-to-br from-dojo-green/5 to-dojo-green/10 rounded-xl p-6">
              <svg className="w-10 h-10 text-dojo-green mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              <h3 className="font-semibold text-dojo-green mb-2">Tournaments</h3>
              <p className="text-sm text-gray-600">Test your skills</p>
            </div>
            <div className="bg-gradient-to-br from-dojo-orange/5 to-dojo-orange/10 rounded-xl p-6">
              <svg className="w-10 h-10 text-dojo-orange mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <h3 className="font-semibold text-dojo-orange mb-2">Training Sessions</h3>
              <p className="text-sm text-gray-600">Live practice</p>
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
              Explore Programs
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
