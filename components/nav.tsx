"use client";

import Link from "next/link";
import { useState, useRef } from "react";
import { ChevronDown } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { UserMenu } from "@/components/user-menu";
import { Button } from "@/components/ui/button";

export function Nav() {
  const [isProgramsOpen, setIsProgramsOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { user, isAuthenticated } = useAuth();

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsProgramsOpen(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setIsProgramsOpen(false);
    }, 150);
  };

  const getDashboardPath = () => {
    if (!user) return "/dashboard";
    switch (user.role) {
      case "admin":
        return "/admin";
      case "instructor":
        return "/instructor/dashboard";
      case "student":
      default:
        return "/dashboard";
    }
  };

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
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <button className="flex items-center gap-1 text-gray-600 hover:text-dojo-navy transition-colors">
              Programs
              <ChevronDown className={`w-4 h-4 transition-transform ${isProgramsOpen ? 'rotate-180' : ''}`} />
            </button>

            {isProgramsOpen && (
              <div className="absolute top-full left-0 pt-2">
                <div className="w-48 bg-white rounded-lg shadow-lg border border-border py-2">
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
              </div>
            )}
          </div>

          <Link href="/events" className="text-gray-600 hover:text-dojo-navy transition-colors">Events</Link>
          <Link href="/founder" className="text-gray-600 hover:text-dojo-navy transition-colors">Founder</Link>
          <Link href="/resources" className="text-gray-600 hover:text-dojo-navy transition-colors">Resources</Link>

          {isAuthenticated && (
            <Link href={getDashboardPath()} className="text-gray-600 hover:text-dojo-navy transition-colors">
              Dashboard
            </Link>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <UserMenu />
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Login</Link>
              </Button>
              <Button asChild size="sm" className="bg-gradient-to-r from-dojo-navy to-dojo-green hover:opacity-90">
                <Link href="/register">Register</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
