import { Award, Users, FileCheck, Shield, Star, TrendingUp } from "lucide-react";

const rankLevels = [
  { level: "1-5", name: "Beginner Ranks (Kyu)", color: "from-gray-600 to-gray-800", belt: "White to Brown" },
  { level: "6-10", name: "Intermediate Ranks (Kyu)", color: "from-dojo-orange to-dojo-red", belt: "Advanced Color Belts" },
  { level: "11-16", name: "Advanced Ranks (Dan)", color: "from-dojo-navy to-dojo-green", belt: "Black Belt Degrees" }
];

export default function PromotionsPage() {
  return (
    <div className="min-h-screen">
      <section className="relative bg-gradient-to-r from-dojo-navy via-dojo-green to-dojo-navy py-32 overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-30"></div>
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              Promotions & Rank
            </h1>
            <p className="text-2xl text-white/90">
              Recognition, advancement, and excellence in martial arts
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-navy to-dojo-green mb-6">
              <Award className="w-10 h-10 text-white" />
            </div>
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
              Rank Recognition
            </h2>
            <div className="max-w-4xl mx-auto text-lg text-gray-700 leading-relaxed space-y-4">
              <p>
                The United States Martial Arts Association uses a <strong className="text-dojo-navy">16 step rank system</strong>,
                broadly modeled on the Japanese system of Kyu and Dan ranks, the Japanese names for these ranks. All styles
                endorsed by the USMAA have a Rank Equivalency Table that aligns with these ranks.
              </p>
              <p>
                New members may have their current rank recognized by the USMAA by providing appropriate documentation to
                the designated style head for review by the appropriate board.
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {rankLevels.map((rank, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl border-2 border-border shadow-hover p-8 text-center"
              >
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br ${rank.color} mb-4`}>
                  <Star className="w-8 h-8 text-white" />
                </div>
                <h3 className="font-display text-2xl font-bold text-dojo-navy mb-2">
                  Level {rank.level}
                </h3>
                <p className="text-xl font-semibold text-gray-700 mb-2">{rank.name}</p>
                <p className="text-gray-600">{rank.belt}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-orange to-dojo-red mb-6">
              <TrendingUp className="w-10 h-10 text-white" />
            </div>
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
              Promotion
            </h2>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl border-2 border-border shadow-lg p-8 md:p-12">
              <div className="prose prose-lg max-w-none">
                <div className="mb-8">
                  <h3 className="font-display text-2xl font-bold text-dojo-navy mb-4 flex items-center gap-3">
                    <div className="w-2 h-8 bg-gradient-to-b from-dojo-orange to-dojo-red rounded-full"></div>
                    Up to Sixth Dan (Teacher Level)
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    Promotion up to and including that of "teacher" in the art (<strong>Sixth Dan</strong> in the Japanese system)
                    will be totally within the purview of the martial artist's sensei who, if active and in good standing with the
                    association, will be authorized to promote up to and including one rank below his/her own.
                  </p>
                </div>

                <div className="mb-8">
                  <h3 className="font-display text-2xl font-bold text-dojo-navy mb-4 flex items-center gap-3">
                    <div className="w-2 h-8 bg-gradient-to-b from-dojo-navy to-dojo-green rounded-full"></div>
                    Above Teacher Level
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    Martial artists wishing to be considered for rank above "teacher" in the art and martial artists without
                    teachers may submit dossiers for promotion consideration to their appropriate style head for consideration.
                    Testing for promotion (where appropriate) will be held at the yearly training camp or whenever three or more
                    members of the style promotion board may convene.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-green to-dojo-navy mb-6">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
              Member In Good Standing
            </h2>
          </div>

          <div className="max-w-5xl mx-auto">
            <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border-2 border-border shadow-lg p-8 md:p-12">
              <p className="text-lg text-gray-700 leading-relaxed mb-6">
                Members of the association are considered in good standing if they meet the following requirements:
              </p>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl border border-border p-6">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-dojo-green/10 flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-dojo-green"></div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-dojo-navy mb-2">School Standing</h4>
                      <p className="text-gray-600 text-sm">In good standing with their USMAA affiliated school</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-border p-6">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-dojo-green/10 flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-dojo-green"></div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-dojo-navy mb-2">Current Membership</h4>
                      <p className="text-gray-600 text-sm">Active and current USMAA membership</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-border p-6">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-dojo-green/10 flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-dojo-green"></div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-dojo-navy mb-2">Account Current</h4>
                      <p className="text-gray-600 text-sm">All financial obligations with USMAA are current</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-border p-6">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-dojo-green/10 flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-dojo-green"></div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-dojo-navy mb-2">Clean Record</h4>
                      <p className="text-gray-600 text-sm">Testimony of no convictions for violent, sex, or felony crimes</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 p-6 bg-amber-50 border-l-4 border-dojo-orange rounded-r-xl">
                <h4 className="font-display text-xl font-bold text-dojo-navy mb-3">
                  Professional Requirements
                </h4>
                <p className="text-gray-700 leading-relaxed">
                  Professionals who plan to promote within the USMAA must have, on file with the USMAA, a current background
                  check prepared by a governmental body or the private company authorized by the USMAA. Background checks must
                  pass the Ethics Committee review in order for the professional to remain in good standing in the association.
                  The Ethics Committee will rule on the appropriateness of membership in the association for students and
                  professional martial artists.
                </p>
              </div>

              <div className="mt-6 p-6 bg-blue-50 border-l-4 border-dojo-navy rounded-r-xl">
                <h4 className="font-display text-xl font-bold text-dojo-navy mb-3">
                  Free Standing Martial Artists
                </h4>
                <p className="text-gray-700 leading-relaxed">
                  Free standing martial artists are encouraged to associate with a USMAA school, but are in good standing
                  if they meet the above requirements less the school affiliation.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-red to-dojo-orange mb-6">
              <Users className="w-10 h-10 text-white" />
            </div>
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
              Recognition Of New Art Forms
            </h2>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl border-2 border-border shadow-lg p-8 md:p-12">
              <p className="text-lg text-gray-700 leading-relaxed mb-8">
                Designation of new art forms or systems will fall under the board of the style to which they are most
                closely aligned. To be a new system, it must meet one of the following criteria:
              </p>

              <div className="space-y-6 mb-8">
                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-dojo-navy to-dojo-green flex items-center justify-center text-white font-bold">
                    1
                  </div>
                  <div>
                    <h4 className="font-display text-xl font-bold text-dojo-navy mb-2">
                      Radical Change in Existing System
                    </h4>
                    <p className="text-gray-700">
                      A radical change in an existing system that is proven to be effective <span className="italic">(e.g., Judo vs. Jujitsu)</span>
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-dojo-orange to-dojo-red flex items-center justify-center text-white font-bold">
                    2
                  </div>
                  <div>
                    <h4 className="font-display text-xl font-bold text-dojo-navy mb-2">
                      Hybrid Art Form
                    </h4>
                    <p className="text-gray-700">
                      A melding of two or more systems with moves demonstrating clear transitions and continuity between
                      those systems <span className="italic">(e.g., Hapkido)</span>
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-dojo-green to-dojo-navy flex items-center justify-center text-white font-bold">
                    3
                  </div>
                  <div>
                    <h4 className="font-display text-xl font-bold text-dojo-navy mb-2">
                      Completely New System
                    </h4>
                    <p className="text-gray-700">
                      A completely new system <span className="italic">(e.g., Tiho Jitsu – one-on-one control tactics)</span>
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6 bg-gradient-to-r from-dojo-navy/5 to-dojo-green/5 border border-dojo-navy/20 rounded-xl mb-8">
                <h4 className="font-display text-xl font-bold text-dojo-navy mb-3">
                  Submission Requirements
                </h4>
                <p className="text-gray-700 leading-relaxed mb-4">
                  The martial artist must submit a complete portfolio of their art's system either in text or video for evaluation, including:
                </p>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-start gap-3">
                    <FileCheck className="w-5 h-5 text-dojo-green flex-shrink-0 mt-1" />
                    <span>Documented, demonstrated successes in the application of the art</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <FileCheck className="w-5 h-5 text-dojo-green flex-shrink-0 mt-1" />
                    <span>Proof of at least parity, if not superiority, to existing systems in that niche</span>
                  </li>
                </ul>
              </div>

              <div className="p-6 bg-amber-50 border-l-4 border-dojo-orange rounded-r-xl mb-6">
                <p className="text-gray-700 leading-relaxed">
                  <strong className="text-dojo-navy">Important:</strong> Simply adding moves from one system to another
                  does not constitute a new system. It might possibly represent a better-rounded martial artist, but not a new system.
                </p>
              </div>

              <p className="text-gray-700 leading-relaxed">
                Creation of a new system must be recommended by the appropriate style board(s) and approved by the
                Association's Board of Directors.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-dojo-navy to-dojo-green mb-6">
              <FileCheck className="w-10 h-10 text-white" />
            </div>
            <h2 className="font-display text-4xl font-bold text-dojo-navy mb-6">
              Rank Equivalency Table
            </h2>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border-2 border-border shadow-lg p-8 md:p-12">
              <p className="text-lg text-gray-700 leading-relaxed mb-6">
                The United States Martial Arts Association uses a <strong className="text-dojo-navy">16 step rank system</strong>,
                broadly modeled on the Japanese system of Kyu and Dan ranks. All styles endorsed by the WWMAA have a Rank
                Equivalency Table that aligns with these ranks.
              </p>

              <div className="space-y-4 mb-8">
                <div className="p-6 bg-white border-l-4 border-dojo-navy rounded-r-xl">
                  <h4 className="font-display text-xl font-bold text-dojo-navy mb-2">
                    New Member Recognition
                  </h4>
                  <p className="text-gray-700">
                    New members may have their current rank recognized by the WWMAA by providing appropriate documentation
                    to the designated style head for review by the appropriate board.
                  </p>
                </div>

                <div className="p-6 bg-white border-l-4 border-dojo-green rounded-r-xl">
                  <h4 className="font-display text-xl font-bold text-dojo-navy mb-2">
                    Rank Designation Code
                  </h4>
                  <p className="text-gray-700">
                    When applying for rank to be recognized by the WWMAA you must use a "Rank Designation Code". You can
                    look up the code in the core Rank Equivalency Table.
                  </p>
                </div>

                <div className="p-6 bg-white border-l-4 border-dojo-orange rounded-r-xl">
                  <h4 className="font-display text-xl font-bold text-dojo-navy mb-2">
                    Need Help?
                  </h4>
                  <p className="text-gray-700">
                    If you are unsure as to your Style's Rank Equivalency, you should contact your teacher, style head,
                    or a representative of the WWMAA.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 bg-gradient-to-r from-dojo-navy to-dojo-green">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="font-display text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Advance Your Journey?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Learn more about membership and begin your path to recognition
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/membership"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-8 py-4 text-lg font-semibold text-dojo-navy shadow-lg hover:shadow-xl transition-all"
            >
              Join WWMAA
            </a>
            <a
              href="/contact"
              className="inline-flex items-center justify-center rounded-xl border-2 border-white px-8 py-4 text-lg font-semibold text-white hover:bg-white hover:text-dojo-navy transition-all"
            >
              Contact Us
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
