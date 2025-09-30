export default function DashboardEventsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full gradient-hero mb-6">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h1 className="font-display text-4xl font-bold text-dojo-navy mb-4">
            My Events
          </h1>
          <p className="text-lg text-gray-600 max-w-xl mx-auto">
            Your personalized events calendar will be available soon. We're working on bringing you the best training opportunities.
          </p>
        </div>
      </div>
    </div>
  );
}
