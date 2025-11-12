import { api } from "@/lib/api";

export const dynamic = 'force-dynamic';

export default async function AdminEventsPage() {
  const events = await api.getEvents();
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="font-display text-3xl">Manage Events</h1>
      <table className="mt-6 w-full text-sm">
        <thead><tr className="text-left border-b border-border"><th className="pb-2">Title</th><th className="pb-2">Location</th><th className="pb-2">Type</th><th className="pb-2">Visibility</th></tr></thead>
        <tbody>
          {events.map(e=>(
            <tr key={e.id} className="border-t border-border">
              <td className="py-2">{e.title}</td><td>{e.location}</td><td>{e.type}</td><td>{e.visibility}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
