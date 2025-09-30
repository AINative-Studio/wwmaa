export default function AboutPage() {
  return (
    <div className="min-h-screen">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white text-center">
            About WWMAA
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-3xl mx-auto text-center leading-relaxed">
            Unifying Martial Arts in spirit by offering services and guidance to all Martial Artists since 1995.
          </p>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-4xl font-bold text-dojo-navy mb-8">Our Mission</h2>
          <div className="space-y-6">
            <p className="text-lg text-gray-700 leading-relaxed">
              The World Wide Martial Arts Association (WWMAA) is a non-profit organization first incorporated in 1995. To avoid the destructive effects of politics, the WWMAA, like most not for profit corporations, has a permanent Governing Board, which guides the policies of the WWMAA.
            </p>
            <p className="text-lg text-gray-700 leading-relaxed">
              The mission of the WWMAA is to unify Martial Arts in spirit by offering services and guidance to all Martial Artists. These services include:
            </p>
            <ul className="space-y-4 ml-6">
              <li className="flex items-start gap-3 text-lg text-gray-700">
                <svg className="w-6 h-6 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                <span>A national and international seminar program to provide expert instruction in the Martial Arts to all our members.</span>
              </li>
              <li className="flex items-start gap-3 text-lg text-gray-700">
                <svg className="w-6 h-6 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                <span>Fair promotion systems for all Martial Arts, which is open and known to all.</span>
              </li>
              <li className="flex items-start gap-3 text-lg text-gray-700">
                <svg className="w-6 h-6 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                <span>The finest Junior and Senior National Martial Arts and Law Enforcement Defensive Tactics Training Camp in the country.</span>
              </li>
              <li className="flex items-start gap-3 text-lg text-gray-700">
                <svg className="w-6 h-6 text-dojo-green flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                <span>The support of coaches and athletes who aspire to national and international excellence.</span>
              </li>
            </ul>
            <p className="text-lg text-gray-700 leading-relaxed">
              The WWMAA has published a series of books and videos on the Martial Arts, created by O-Sensei Phil Porter and other experts. These include "The 65 Throws of Kodokan Judo."
            </p>
            <p className="text-lg text-gray-700 leading-relaxed font-semibold">
              With more than 10,000 members, the WWMAA is the center of American Martial Arts. It is the only organization devoted to all Martial Arts without exception. We are the rallying point for all leaders, whatever their arts, who are devoted to the true spirit of the Martial Arts and who wish the progress and prestige of the Martial Arts to continue to grow.
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-gradient-to-b from-bg to-white">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-4xl font-bold text-dojo-navy mb-8">Structure</h2>
          <div className="space-y-6">
            <p className="text-lg text-gray-700 leading-relaxed">
              Volunteer workers run the WWMAA. The WWMAA is not a political group. A permanent three person Board of Governors governs the WWMAA. The Board consists of: Dr. Michael Makoid, Mr. Steven Jimerfield, and Mr. Ronald Treem. All governors serve without pay. The WWMAA has several Boards of Directors including Martial Arts Style planning and examinations, Administrative, and Regional Development Directors.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3 mt-12">
            <div className="bg-white rounded-2xl p-8 shadow-hover text-center">
              <div className="w-24 h-24 rounded-full gradient-navy mx-auto mb-6 flex items-center justify-center">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="font-display text-xl font-bold text-dojo-navy">Board of Governors</h3>
              <p className="mt-3 text-gray-600">Dr. Michael Makoid, Mr. Steven Jimerfield, and Mr. Ronald Treem</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-hover text-center">
              <div className="w-24 h-24 rounded-full gradient-green mx-auto mb-6 flex items-center justify-center">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <h3 className="font-display text-xl font-bold text-dojo-navy">Boards of Directors</h3>
              <p className="mt-3 text-gray-600">Style planning, examinations, administrative, and regional development</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-hover text-center">
              <div className="w-24 h-24 rounded-full gradient-orange mx-auto mb-6 flex items-center justify-center">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="font-display text-xl font-bold text-dojo-navy">Volunteer Network</h3>
              <p className="mt-3 text-gray-600">Dedicated volunteers serving the martial arts community</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-4xl font-bold text-dojo-navy mb-8">Background</h2>
          <div className="bg-gradient-to-br from-dojo-navy/5 to-dojo-green/5 rounded-2xl p-8 border-l-4 border-dojo-navy">
            <p className="text-lg text-gray-700 leading-relaxed">
              The Founder of the WWMAA was O-Sensei Phil Porter, 10th Dan in several Martial Arts and the most successful coach in US Judo history.
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-gradient-to-b from-bg to-white">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-4xl font-bold text-dojo-navy mb-8">Progress</h2>
          <div className="space-y-8">
            <div className="flex gap-6">
              <div className="flex-shrink-0 w-32 text-right">
                <span className="inline-block gradient-navy text-white font-bold px-4 py-2 rounded-lg">1995</span>
              </div>
              <div className="flex-1 text-lg text-gray-700">
                Founded as a non-profit organization dedicated to unifying martial arts
              </div>
            </div>
            <div className="flex gap-6">
              <div className="flex-shrink-0 w-32 text-right">
                <span className="inline-block gradient-green text-white font-bold px-4 py-2 rounded-lg">Growth</span>
              </div>
              <div className="flex-1 text-lg text-gray-700">
                In its first 15 years the WWMAA grew to over 1,000 clubs, over 10,000 Life Members
              </div>
            </div>
            <div className="flex gap-6">
              <div className="flex-shrink-0 w-32 text-right">
                <span className="inline-block gradient-orange text-white font-bold px-4 py-2 rounded-lg">Today</span>
              </div>
              <div className="flex-1 text-lg text-gray-700">
                The association represents hundreds of different Martial Arts
              </div>
            </div>
          </div>
          <div className="mt-12 bg-white rounded-2xl p-8 shadow-hover">
            <p className="text-lg text-gray-700 leading-relaxed">
              Further information, DVDs, videos and books may be obtained by contacting the WWMAA at the mailing address or email address below.
            </p>
            <div className="mt-6 flex gap-4">
              <a href="/contact" className="inline-flex items-center gap-2 rounded-xl gradient-orange px-6 py-3 font-semibold text-white shadow-lg hover:shadow-xl transition-all">
                Contact Us
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </a>
              <a href="/resources" className="inline-flex items-center rounded-xl border-2 border-dojo-navy px-6 py-3 font-semibold text-dojo-navy hover:bg-dojo-navy hover:text-white transition-all">
                View Resources
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
