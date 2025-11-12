import { api } from "@/lib/api";

export const dynamic = 'force-dynamic';

export default async function AdminMembersPage() {
  const apps = await api.getApplications();
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="font-display text-3xl">Applications Queue</h1>
      <table className="mt-6 w-full text-sm">
        <thead><tr className="text-left border-b border-border"><th className="pb-2">User ID</th><th className="pb-2">Discipline</th><th className="pb-2">Experience</th><th className="pb-2">Status</th></tr></thead>
        <tbody>
          {apps.map(a=>(
            <tr key={a.id} className="border-t border-border">
              <td className="py-2">{a.user_id}</td><td>{a.discipline}</td><td>{a.experience}</td><td>{a.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
