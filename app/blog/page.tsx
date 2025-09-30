import { api } from "@/lib/api";

export default async function BlogPage() {
  const posts = await api.getArticles();
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Blog & Insights
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Latest articles, techniques, and wisdom from martial arts masters worldwide.
          </p>
        </div>
      </section>

      <section className="py-24 -mt-12">
        <div className="mx-auto max-w-4xl px-6">
          <div className="space-y-6">
            {posts.map(p=>(
              <a
                key={p.id}
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block group bg-white rounded-2xl p-8 shadow-hover"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h2 className="font-display text-2xl font-bold text-dojo-navy group-hover:text-dojo-green transition-colors">
                      {p.title}
                    </h2>
                    <p className="mt-3 text-gray-600 leading-relaxed">{p.excerpt}</p>
                    <div className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-dojo-orange">
                      Read Article
                      <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-lg gradient-navy flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
