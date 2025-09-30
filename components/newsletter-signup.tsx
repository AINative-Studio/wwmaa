"use client";

import { useState } from "react";

export function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage("");

    try {
      // TODO: Implement actual email list integration
      // For now, just simulate submission
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setMessage("Thank you for joining our dojo! Check your email for confirmation.");
      setEmail("");
    } catch (error) {
      setMessage("Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section
      className="bg-gradient-to-r from-dojo-navy to-dojo-green py-12"
      aria-labelledby="newsletter-heading"
    >
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h2
          id="newsletter-heading"
          className="font-display text-3xl font-bold text-white mb-3"
        >
          Stay Connected with WWMAA
        </h2>
        <p className="text-white/90 text-lg mb-6">
          Get exclusive training tips, event updates, and martial arts news delivered to your inbox.
        </p>
        <form
          onSubmit={handleSubmit}
          className="flex flex-col sm:flex-row gap-3 max-w-xl mx-auto"
          aria-label="Newsletter signup form"
        >
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            className="flex-1 px-6 py-3 rounded-lg text-gray-900"
            required
            aria-label="Email address"
            disabled={isSubmitting}
          />
          <button
            type="submit"
            className="px-8 py-3 bg-dojo-orange text-white font-semibold rounded-lg hover:bg-dojo-orange/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isSubmitting}
            aria-label="Subscribe to newsletter"
          >
            {isSubmitting ? "Joining..." : "Join Our Dojo"}
          </button>
        </form>
        {message && (
          <p
            className={`text-sm mt-4 ${message.includes("Thank you") ? "text-white" : "text-dojo-orange"}`}
            role="status"
            aria-live="polite"
          >
            {message}
          </p>
        )}
        <p className="text-white/70 text-sm mt-4">
          We respect your privacy. Unsubscribe at any time.
        </p>
      </div>
    </section>
  );
}
