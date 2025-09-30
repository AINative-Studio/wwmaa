"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export function ApplicationForm() {
  const [loading, setLoading] = useState(false);
  const [ok, setOk] = useState<null | boolean>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const payload = {
      discipline: String(formData.get("discipline") || ""),
      experience: String(formData.get("experience") || ""),
      refs: String(formData.get("refs") || ""),
    };
    const res = await api.submitApplication(payload);
    setOk(res.ok);
    setLoading(false);
  }

  if (ok === true) {
    return (
      <div className="rounded-2xl bg-gradient-to-br from-dojo-green/10 to-dojo-green/5 border-2 border-dojo-green/20 p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-dojo-green mx-auto flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="font-display text-2xl font-bold text-dojo-green mb-2">Application Submitted!</h3>
        <p className="text-gray-600">Our board will review your application and get back to you soon.</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6 max-w-2xl">
      <div>
        <label htmlFor="discipline" className="block text-sm font-semibold text-gray-700 mb-2">
          Discipline <span className="text-dojo-red">*</span>
        </label>
        <input
          id="discipline"
          name="discipline"
          required
          placeholder="e.g., Karate, Ju-Jitsu, Kendo"
          className="w-full rounded-xl border-2 border-border bg-white px-4 py-3 focus:border-dojo-navy focus:outline-none focus:ring-2 focus:ring-dojo-navy/20 transition-all"
        />
      </div>
      <div>
        <label htmlFor="experience" className="block text-sm font-semibold text-gray-700 mb-2">
          Years of Experience <span className="text-dojo-red">*</span>
        </label>
        <input
          id="experience"
          name="experience"
          required
          placeholder="e.g., 5 years"
          className="w-full rounded-xl border-2 border-border bg-white px-4 py-3 focus:border-dojo-navy focus:outline-none focus:ring-2 focus:ring-dojo-navy/20 transition-all"
        />
      </div>
      <div>
        <label htmlFor="refs" className="block text-sm font-semibold text-gray-700 mb-2">
          References
        </label>
        <input
          id="refs"
          name="refs"
          placeholder="Optional: Names of instructors or dojos"
          className="w-full rounded-xl border-2 border-border bg-white px-4 py-3 focus:border-dojo-navy focus:outline-none focus:ring-2 focus:ring-dojo-navy/20 transition-all"
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full gradient-orange text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Submitting..." : "Submit Application"}
      </button>
      {ok === false && (
        <div className="rounded-xl bg-dojo-red/10 border border-dojo-red/20 p-4 text-dojo-red text-sm">
          Something went wrong. Please try again.
        </div>
      )}
    </form>
  );
}
