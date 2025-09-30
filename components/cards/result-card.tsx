export function ResultCard({ answer, sources }:{ answer:string; sources:{title:string;url:string}[]}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p>{answer}</p>
      <div className="mt-3 text-sm">
        <span className="font-semibold">Sources: </span>
        {sources.map((s,i)=><a key={i} className="underline mr-2" href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a>)}
      </div>
    </div>
  );
}
