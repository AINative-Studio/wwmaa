"use client";

import Link from "next/link";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface FAQ {
  question: string;
  answer: string;
}

interface FAQCategory {
  category: string;
  questions: FAQ[];
}

interface FAQContentProps {
  faqs: FAQCategory[];
}

// Helper function to convert markdown-style links to Next.js Link components
function renderAnswer(text: string) {
  const parts = text.split(/(\[[^\]]+\]\([^)]+\))/g);

  return parts.map((part, index) => {
    const linkMatch = part.match(/\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      const [, linkText, href] = linkMatch;
      return (
        <Link
          key={index}
          href={href}
          className="text-dojo-green font-semibold underline hover:text-dojo-orange transition-colors"
        >
          {linkText}
        </Link>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

export function FAQContent({ faqs }: FAQContentProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      <section className="gradient-hero py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h1 className="font-display text-5xl sm:text-6xl font-bold text-white">
            Martial Arts Frequently Asked Questions
          </h1>
          <p className="mt-6 text-xl text-white/90 max-w-2xl mx-auto">
            Everything you need to know about WWMAA membership, training programs, belt ranking systems, and martial arts tournaments.
          </p>
        </div>
      </section>

      <section className="py-24 -mt-12">
        <div className="mx-auto max-w-4xl px-6">
          <nav className="mb-12 bg-white rounded-2xl p-6 shadow-glow" aria-label="FAQ Categories">
            <h2 className="font-display text-lg font-bold text-dojo-navy mb-4">
              Quick Navigation
            </h2>
            <div className="flex flex-wrap gap-3">
              {faqs.map((category) => (
                <a
                  key={category.category}
                  href={`#${category.category.toLowerCase().replace(/\s+/g, "-")}`}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-dojo-navy/5 hover:bg-dojo-green/10 text-dojo-navy hover:text-dojo-green rounded-lg transition-colors font-semibold"
                >
                  {category.category}
                </a>
              ))}
            </div>
          </nav>

          <div className="space-y-16">
            {faqs.map((category) => (
              <article
                key={category.category}
                id={category.category.toLowerCase().replace(/\s+/g, "-")}
                className="scroll-mt-24"
              >
                <h2 className="font-display text-3xl font-bold text-dojo-navy mb-8 flex items-center gap-3">
                  <span className="w-12 h-12 rounded-lg bg-gradient-to-br from-dojo-navy to-dojo-green flex items-center justify-center text-white font-bold text-xl">
                    {category.category.charAt(0)}
                  </span>
                  {category.category}
                </h2>

                <Accordion type="single" collapsible className="space-y-4">
                  {category.questions.map((faq, idx) => (
                    <AccordionItem
                      key={idx}
                      value={`${category.category}-${idx}`}
                      className="bg-white rounded-2xl shadow-hover border-none overflow-hidden"
                    >
                      <AccordionTrigger className="px-6 py-5 text-left hover:bg-dojo-navy/5 hover:no-underline">
                        <h3 className="font-display text-xl font-bold text-dojo-navy pr-4">
                          {faq.question}
                        </h3>
                      </AccordionTrigger>
                      <AccordionContent className="px-6 pb-6 pt-2">
                        <p className="text-gray-700 leading-relaxed text-lg">
                          {renderAnswer(faq.answer)}
                        </p>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </article>
            ))}
          </div>

          <aside className="mt-16 bg-gradient-to-br from-dojo-navy to-dojo-green rounded-2xl p-8 text-white shadow-glow">
            <h2 className="font-display text-2xl font-bold mb-4">
              Still Have Questions?
            </h2>
            <p className="text-white/90 leading-relaxed mb-6">
              Can't find the answer you're looking for? Our team is here to help you with any questions about{" "}
              <Link href="/membership" className="underline font-semibold hover:text-dojo-orange transition-colors">
                membership plans
              </Link>
              ,{" "}
              <Link href="/programs" className="underline font-semibold hover:text-dojo-orange transition-colors">
                training programs
              </Link>
              ,{" "}
              <Link href="/programs/tournaments" className="underline font-semibold hover:text-dojo-orange transition-colors">
                upcoming tournaments
              </Link>
              , or anything else related to your martial arts journey with WWMAA.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/membership"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-dojo-navy font-semibold rounded-lg hover:bg-dojo-orange hover:text-white transition-colors"
              >
                Join WWMAA Today
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </aside>

          <section className="mt-12 bg-white rounded-2xl p-8 shadow-glow">
            <h2 className="font-display text-2xl font-bold text-dojo-navy mb-4">
              Related Resources
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Link
                href="/membership"
                className="flex items-center gap-3 p-4 bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-lg transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-dojo-navy flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-dojo-navy group-hover:text-dojo-green transition-colors">
                    Membership Plans
                  </h3>
                  <p className="text-sm text-gray-600">Compare tiers and benefits</p>
                </div>
              </Link>

              <Link
                href="/programs"
                className="flex items-center gap-3 p-4 bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-lg transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-dojo-green flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-dojo-navy group-hover:text-dojo-green transition-colors">
                    Training Programs
                  </h3>
                  <p className="text-sm text-gray-600">Explore our offerings</p>
                </div>
              </Link>

              <Link
                href="/programs/tournaments"
                className="flex items-center gap-3 p-4 bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-lg transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-dojo-orange flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-dojo-navy group-hover:text-dojo-green transition-colors">
                    Tournaments
                  </h3>
                  <p className="text-sm text-gray-600">Competition schedule</p>
                </div>
              </Link>

              <Link
                href="/resources"
                className="flex items-center gap-3 p-4 bg-dojo-navy/5 hover:bg-dojo-green/10 rounded-lg transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-dojo-navy flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-dojo-navy group-hover:text-dojo-green transition-colors">
                    Training Resources
                  </h3>
                  <p className="text-sm text-gray-600">Certifications & materials</p>
                </div>
              </Link>
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}
