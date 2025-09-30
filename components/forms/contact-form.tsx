"use client";
import { useState } from "react";

export function ContactForm() {
  const [sent, setSent] = useState(false);

  if (sent) {
    return (
      <div className="rounded-2xl bg-gradient-to-br from-dojo-green/10 to-dojo-green/5 border-2 border-dojo-green/20 p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-dojo-green mx-auto flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="font-display text-2xl font-bold text-dojo-green mb-2">Message Sent!</h3>
        <p className="text-gray-600">We'll get back to you as soon as possible.</p>
      </div>
    );
  }

  return (
    <form onSubmit={(e)=>{e.preventDefault(); setSent(true);}} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2">
          Your Name <span className="text-dojo-red">*</span>
        </label>
        <input
          id="name"
          required
          placeholder="John Doe"
          className="w-full rounded-xl border-2 border-border bg-white px-4 py-3 focus:border-dojo-navy focus:outline-none focus:ring-2 focus:ring-dojo-navy/20 transition-all"
        />
      </div>
      <div>
        <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
          Email Address <span className="text-dojo-red">*</span>
        </label>
        <input
          id="email"
          required
          type="email"
          placeholder="john@example.com"
          className="w-full rounded-xl border-2 border-border bg-white px-4 py-3 focus:border-dojo-navy focus:outline-none focus:ring-2 focus:ring-dojo-navy/20 transition-all"
        />
      </div>
      <div>
        <label htmlFor="message" className="block text-sm font-semibold text-gray-700 mb-2">
          Message <span className="text-dojo-red">*</span>
        </label>
        <textarea
          id="message"
          required
          placeholder="How can we help you?"
          rows={6}
          className="w-full rounded-xl border-2 border-border bg-white px-4 py-3 focus:border-dojo-navy focus:outline-none focus:ring-2 focus:ring-dojo-navy/20 transition-all resize-none"
        />
      </div>
      <button
        type="submit"
        className="w-full gradient-orange text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all"
      >
        Send Message
      </button>
    </form>
  );
}
