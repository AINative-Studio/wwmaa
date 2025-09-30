import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Martial Arts Programs & Training | Tournaments, Camps & Certifications | WWMAA",
  description: "Explore our martial arts programs: tournaments, summer camps, belt promotions, and instructor certifications. Train with the best!",
  openGraph: {
    title: "Martial Arts Programs & Training | Tournaments, Camps & Certifications | WWMAA",
    description: "Explore our martial arts programs: tournaments, summer camps, belt promotions, and instructor certifications. Train with the best!",
    type: "website",
    url: "https://wwmaa.ainative.studio/programs",
    images: [
      {
        url: "https://wwmaa.ainative.studio/images/logo.png",
        width: 1200,
        height: 630,
        alt: "WWMAA Programs",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Martial Arts Programs & Training | Tournaments, Camps & Certifications | WWMAA",
    description: "Explore our martial arts programs: tournaments, summer camps, belt promotions, and instructor certifications. Train with the best!",
  },
};

const programs = [
  { slug:"karate", title:"Karate", desc:"The way of the empty hand — discipline, strength, and tradition.", color: "from-dojo-navy to-dojo-green" },
  { slug:"jujitsu", title:"Ju-Jitsu", desc:"Technique over strength — leverage and mastery in combat.", color: "from-dojo-green to-dojo-navy" },
  { slug:"kendo", title:"Kendo", desc:"The way of the sword — spirit and form in harmony.", color: "from-dojo-orange to-dojo-red" },
  { slug:"self-defense", title:"Self-Defense", desc:"Practical protection skills for modern life.", color: "from-dojo-red to-dojo-orange" },
];

export default function ProgramsPage() {
  // Create comprehensive Course schemas for each martial arts program
  const courseSchemas = programs.map((program) => ({
    "@context": "https://schema.org",
    "@type": "Course",
    "name": `WWMAA ${program.title} Training Program`,
    "description": program.desc,
    "provider": {
      "@type": "SportsOrganization",
      "name": "World Wide Martial Arts Association",
      "url": "https://wwmaa.ainative.studio"
    },
    "hasCourseInstance": {
      "@type": "CourseInstance",
      "courseMode": "Blended",
      "courseWorkload": "PT",
      "instructor": {
        "@type": "Person",
        "name": "WWMAA Certified Instructors"
      }
    },
    "educationalCredentialAwarded": "Belt Rank Advancement",
    "about": {
      "@type": "Thing",
      "name": program.title
    }
  }));

  return (
    <div className="min-h-screen">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(courseSchemas) }}
      />
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="font-display text-5xl sm:text-6xl font-bold text-white mb-4">
              Martial Arts Programs
            </h1>
            <p className="text-xl text-white/90 max-w-2xl mx-auto">
              Explore diverse disciplines rooted in tradition and adapted for the modern practitioner.
            </p>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid gap-8 md:grid-cols-2">
            {programs.map(p=>(
              <Link key={p.slug} href={`/programs/${p.slug}`} className="group block rounded-2xl bg-white overflow-hidden shadow-hover border-2 border-border">
                <div className={`h-64 bg-gradient-to-br ${p.color} relative`}>
                  <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-30"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <h3 className="font-display text-4xl font-bold text-white">{p.title}</h3>
                  </div>
                </div>
                <div className="p-8">
                  <p className="text-lg text-gray-700 leading-relaxed">{p.desc}</p>
                  <div className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-dojo-orange group-hover:gap-3 transition-all">
                    Learn More
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
