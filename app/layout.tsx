import "./globals.css";
import { ReactNode } from "react";
import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { AuthProvider } from "@/lib/auth-context";
import { CookieBanner } from "@/components/cookie-consent/cookie-banner";
import { AnalyticsLoader } from "@/components/cookie-consent/analytics-loader";
import { Toaster } from "@/components/ui/toaster";

export const metadata = {
  metadataBase: new URL("https://wwmaa.ainative.studio"),
  title: "WWMAA — World Wide Martial Arts Association",
  description: "Tradition, discipline, and community in the modern age.",
};

const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "SportsOrganization",
  "name": "World Wide Martial Arts Association",
  "alternateName": "WWMAA",
  "url": "https://wwmaa.ainative.studio",
  "logo": "https://wwmaa.ainative.studio/images/logo.png",
  "foundingDate": "1995",
  "founder": {
    "@type": "Person",
    "name": "Philip S. Porter",
    "honorificPrefix": "O-Sensei",
    "jobTitle": "Founder",
    "description": "10th Dan Judo Master, Father of American Judo"
  },
  "sport": ["Judo", "Karate", "Jiu-Jitsu", "Martial Arts"],
  "memberOf": {
    "@type": "SportsOrganization",
    "name": "International Judo Federation"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "Membership Services",
    "email": "info@wwmaa.com",
    "availableLanguage": ["English"]
  },
  "sameAs": [
    "https://facebook.com/wwmaa",
    "https://twitter.com/wwmaa",
    "https://instagram.com/wwmaa"
  ],
  "address": {
    "@type": "PostalAddress",
    "addressCountry": "US"
  }
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-bg text-fg">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />
        <AuthProvider>
          <AnalyticsLoader />
          <div className="flex min-h-screen flex-col">
            <Nav />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
          <CookieBanner />
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  );
}
