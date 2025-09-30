import { dict } from "@/lib/i18n";

export function Hero() {
  const t = dict.en;
  return (
    <section className="relative overflow-hidden gradient-hero">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-30"></div>
      <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32">
        <div className="max-w-3xl">
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-white leading-tight">
            {t.hero_title}
          </h1>
          <p className="mt-6 text-xl text-white/90 leading-relaxed max-w-2xl">
            {t.hero_sub}
          </p>
          <div className="mt-10 flex gap-4">
            <a
              href="/membership"
              className="inline-flex items-center gap-2 rounded-xl bg-dojo-orange px-8 py-4 text-lg font-semibold text-white shadow-lg hover:shadow-xl hover:bg-dojo-orange/90 transition-all"
            >
              {t.cta_join}
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>
            <a
              href="/programs"
              className="inline-flex items-center rounded-xl border-2 border-white/30 px-8 py-4 text-lg font-semibold text-white hover:bg-white/10 transition-all"
            >
              Explore Programs
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
