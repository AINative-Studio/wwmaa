export function TierCard({ name, price, benefits, featured }: { name: string; price: number; benefits: string[]; featured?: boolean }) {
  return (
    <div className={`relative rounded-2xl bg-white p-8 shadow-hover ${featured ? 'ring-2 ring-dojo-orange scale-105' : 'shadow-lg'}`}>
      {featured && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="inline-flex rounded-full gradient-orange px-4 py-1.5 text-xs font-semibold text-white shadow-lg">
            Most Popular
          </span>
        </div>
      )}
      <div className="text-center">
        <h3 className="font-display text-2xl font-bold text-dojo-navy">{name}</h3>
        <div className="mt-4 flex items-baseline justify-center gap-1">
          <span className="text-5xl font-bold text-dojo-navy">${price}</span>
          <span className="text-lg text-gray-600">/month</span>
        </div>
      </div>
      <ul className="mt-8 space-y-4">
        {benefits.map((b,i)=>(
          <li key={i} className="flex items-start gap-3">
            <svg className="w-5 h-5 text-dojo-green flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-gray-700">{b}</span>
          </li>
        ))}
      </ul>
      <a
        href={`/checkout?tier=${name.toLowerCase()}`}
        className={`mt-8 w-full inline-flex justify-center items-center rounded-xl px-6 py-3.5 font-semibold transition-all ${
          featured
            ? 'gradient-orange text-white shadow-lg hover:shadow-xl'
            : 'bg-dojo-navy/10 text-dojo-navy hover:bg-dojo-navy hover:text-white'
        }`}
      >
        Get Started
      </a>
    </div>
  );
}
