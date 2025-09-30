"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronDown } from "lucide-react";

export function Nav() {
  const [isProgramsOpen, setIsProgramsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-xl border-b border-border shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-display text-2xl font-bold bg-gradient-to-r from-dojo-navy to-dojo-green bg-clip-text text-transparent hover:opacity-80 transition-opacity">
          WWMAA
        </Link>
        <nav className="flex gap-8 text-sm font-medium">
          <Link href="/membership" className="text-gray-600 hover:text-dojo-navy transition-colors">Membership</Link>

          <div
            className="relative"
            onMouseEnter={() => setIsProgramsOpen(true)}
            onMouseLeave={() => setIsProgramsOpen(false)}
          >
            <button className="flex items-center gap-1 text-gray-600 hover:text-dojo-navy transition-colors">
              Programs
              <ChevronDown className={`w-4 h-4 transition-transform ${isProgramsOpen ? 'rotate-180' : ''}`} />
            </button>

            {isProgramsOpen && (
              <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-border py-2">
                <Link
                  href="/programs"
                  className="block px-4 py-2 text-gray-600 hover:bg-gray-50 hover:text-dojo-navy transition-colors"
                >
                  All Programs
                </Link>
                <Link
                  href="/programs/camp"
                  className="block px-4 py-2 text-gray-600 hover:bg-gray-50 hover:text-dojo-navy transition-colors"
                >
                  Summer Camp
                </Link>
                <Link
                  href="/programs/tournaments"
                  className="block px-4 py-2 text-gray-600 hover:bg-gray-50 hover:text-dojo-navy transition-colors"
                >
                  Tournaments
                </Link>
                <Link
                  href="/programs/promotions"
                  className="block px-4 py-2 text-gray-600 hover:bg-gray-50 hover:text-dojo-navy transition-colors"
                >
                  Promotions & Rank
                </Link>
              </div>
            )}
          </div>

          <Link href="/events" className="text-gray-600 hover:text-dojo-navy transition-colors">Events</Link>
          <Link href="/founder" className="text-gray-600 hover:text-dojo-navy transition-colors">Founder</Link>
          <Link href="/resources" className="text-gray-600 hover:text-dojo-navy transition-colors">Resources</Link>
        </nav>
      </div>
    </header>
  );
}
