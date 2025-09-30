import { api } from "@/lib/api";

export default async function DashboardPage() {
  const me = await api.getCurrentUser();
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy">Welcome, {me.name}</h1>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-dojo-navy/5 to-dojo-navy/10 rounded-xl p-6">
              <div className="text-sm font-semibold text-dojo-navy uppercase tracking-wider mb-2">Belt Rank</div>
              <div className="text-2xl font-bold text-dojo-navy">{me.belt_rank}</div>
            </div>
            <div className="bg-gradient-to-br from-dojo-green/5 to-dojo-green/10 rounded-xl p-6">
              <div className="text-sm font-semibold text-dojo-green uppercase tracking-wider mb-2">Dojo</div>
              <div className="text-2xl font-bold text-dojo-green">{me.dojo}</div>
            </div>
            <div className="bg-gradient-to-br from-dojo-orange/5 to-dojo-orange/10 rounded-xl p-6">
              <div className="text-sm font-semibold text-dojo-orange uppercase tracking-wider mb-2">Country</div>
              <div className="text-2xl font-bold text-dojo-orange">{me.country}</div>
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <a href="/dashboard/profile" className="block bg-white rounded-2xl shadow-hover p-8 group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg gradient-navy flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="font-display text-xl font-bold text-dojo-navy group-hover:text-dojo-green transition-colors">My Profile</h3>
                <p className="text-sm text-gray-600 mt-1">View and update your information</p>
              </div>
              <svg className="w-5 h-5 text-gray-400 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </a>

          <a href="/dashboard/payments" className="block bg-white rounded-2xl shadow-hover p-8 group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg gradient-green flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="font-display text-xl font-bold text-dojo-navy group-hover:text-dojo-green transition-colors">Payment History</h3>
                <p className="text-sm text-gray-600 mt-1">View your membership payments</p>
              </div>
              <svg className="w-5 h-5 text-gray-400 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
