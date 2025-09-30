import { api } from "@/lib/api";

export default async function ProfilePage() {
  const me = await api.getCurrentUser();
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="font-display text-3xl">Profile</h1>
      <div className="mt-6 space-y-3 rounded-xl border border-border bg-card p-6">
        <div><span className="font-semibold">Name:</span> {me.name}</div>
        <div><span className="font-semibold">Email:</span> {me.email}</div>
        <div><span className="font-semibold">Role:</span> {me.role}</div>
        <div><span className="font-semibold">Belt Rank:</span> {me.belt_rank}</div>
        <div><span className="font-semibold">Dojo:</span> {me.dojo}</div>
        <div><span className="font-semibold">Country:</span> {me.country}</div>
      </div>
    </div>
  );
}
