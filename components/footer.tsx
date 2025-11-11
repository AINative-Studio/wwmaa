'use client';

import { useState } from 'react';
import { NewsletterSignup } from './newsletter-signup';
import { CookieSettingsModal } from './cookie-consent/cookie-settings-modal';

export function Footer() {
  const [showCookieSettings, setShowCookieSettings] = useState(false);

  return (
    <>
      <footer className="bg-gradient-to-br from-dojo-navy via-dojo-navy to-dojo-green text-white">
        <NewsletterSignup />
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="grid gap-12 sm:grid-cols-4">
            <div className="sm:col-span-2">
              <h4 className="font-display text-3xl font-bold bg-gradient-to-r from-white to-dojo-light bg-clip-text text-transparent">
                WWMAA
              </h4>
              <p className="mt-4 text-white/80 text-lg leading-relaxed max-w-md">
                Preserving martial arts traditions while fostering a global community of practitioners dedicated to excellence and discipline.
              </p>
              <div className="mt-6 flex gap-4">
                <a
                  href="https://x.com/wwmaa"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
                  aria-label="Follow WWMAA on X (Twitter)"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </a>
              </div>
            </div>
            <nav aria-label="Quick links">
              <h5 className="font-display text-sm font-semibold uppercase tracking-wider text-white/60 mb-4">
                Quick Links
              </h5>
              <ul className="space-y-3 text-sm">
                <li>
                  <a href="/membership" className="text-white/80 hover:text-white transition-colors">
                    Membership
                  </a>
                </li>
                <li>
                  <a href="/programs" className="text-white/80 hover:text-white transition-colors">
                    Programs
                  </a>
                </li>
                <li>
                  <a href="/events" className="text-white/80 hover:text-white transition-colors">
                    Events
                  </a>
                </li>
                <li>
                  <a href="/resources" className="text-white/80 hover:text-white transition-colors">
                    Resources
                  </a>
                </li>
              </ul>
            </nav>
            <nav aria-label="Company links">
              <h5 className="font-display text-sm font-semibold uppercase tracking-wider text-white/60 mb-4">
                Company
              </h5>
              <ul className="space-y-3 text-sm">
                <li>
                  <a href="/about" className="text-white/80 hover:text-white transition-colors">
                    About Us
                  </a>
                </li>
                <li>
                  <a href="/blog" className="text-white/80 hover:text-white transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="/contact" className="text-white/80 hover:text-white transition-colors">
                    Contact
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>
        <div className="border-t border-white/10">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <div className="flex flex-col items-center justify-between gap-4 sm:flex-row text-sm text-white/60">
              <div>© {new Date().getFullYear()} World Wide Martial Arts Association. All rights reserved.</div>
              <div className="flex flex-wrap items-center justify-center gap-4">
                <a href="/privacy" className="hover:text-white transition-colors">
                  Privacy Policy
                </a>
                <span className="text-white/40">•</span>
                <a href="/terms" className="hover:text-white transition-colors">
                  Terms of Service
                </a>
                <span className="text-white/40">•</span>
                <a href="/cookie-policy" className="hover:text-white transition-colors">
                  Cookie Policy
                </a>
                <span className="text-white/40">•</span>
                <button
                  onClick={() => setShowCookieSettings(true)}
                  className="hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 rounded px-1"
                  aria-label="Manage cookie preferences"
                >
                  Cookie Preferences
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>

      <CookieSettingsModal open={showCookieSettings} onOpenChange={setShowCookieSettings} />
    </>
  );
}
