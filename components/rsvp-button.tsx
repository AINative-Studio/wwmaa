"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export function RSVPButton({ eventId }: { eventId: string }) {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleRSVP() {
    setLoading(true);
    await api.rsvpEvent(eventId);
    setDone(true);
    setLoading(false);
  }

  if (done) {
    return <p className="text-success">You're registered!</p>;
  }

  return (
    <button
      onClick={handleRSVP}
      disabled={loading}
      className="rounded-xl bg-primary px-4 py-2 text-primary-fg disabled:opacity-50"
    >
      {loading ? "Registering..." : "RSVP"}
    </button>
  );
}
